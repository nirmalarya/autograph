"""SAML SSO Handler for AutoGraph v3."""
import os
import json
import redis
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.utils import OneLogin_Saml2_Utils


class SAMLHandler:
    """Handle SAML SSO authentication flows."""
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize SAML handler with Redis client for configuration storage."""
        self.redis = redis_client
        
    def get_saml_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """Get SAML configuration for a provider."""
        config_key = f"saml:config:{provider}"
        config_str = self.redis.get(config_key)
        if config_str:
            return json.loads(config_str)
        return None
    
    def set_saml_config(self, provider: str, config: Dict[str, Any]) -> bool:
        """Store SAML configuration for a provider."""
        config_key = f"saml:config:{provider}"
        self.redis.set(config_key, json.dumps(config))
        return True
    
    def get_all_providers(self) -> list:
        """Get list of all configured SAML providers."""
        keys = self.redis.keys("saml:config:*")
        providers = []
        for key in keys:
            provider_name = key.replace("saml:config:", "")
            config = self.get_saml_config(provider_name)
            if config:
                providers.append({
                    "name": provider_name,
                    "enabled": config.get("enabled", True),
                    "entity_id": config.get("idp", {}).get("entityId", ""),
                    "sso_url": config.get("idp", {}).get("singleSignOnService", {}).get("url", "")
                })
        return providers
    
    def delete_saml_config(self, provider: str) -> bool:
        """Delete SAML configuration for a provider."""
        config_key = f"saml:config:{provider}"
        return self.redis.delete(config_key) > 0
    
    def prepare_saml_request(self, provider: str, request_data: dict) -> Dict[str, Any]:
        """Prepare SAML authentication request."""
        config = self.get_saml_config(provider)
        if not config:
            raise ValueError(f"SAML provider '{provider}' not configured")
        
        # Build SAML settings
        saml_settings = self._build_saml_settings(config, request_data)
        
        # Initialize SAML Auth
        auth = OneLogin_Saml2_Auth(request_data, saml_settings)
        
        # Get SSO URL
        sso_url = auth.login()
        
        return {
            "sso_url": sso_url,
            "request_id": auth.get_last_request_id()
        }
    
    def process_saml_response(self, provider: str, request_data: dict) -> Dict[str, Any]:
        """Process SAML response after SSO authentication."""
        config = self.get_saml_config(provider)
        if not config:
            raise ValueError(f"SAML provider '{provider}' not configured")
        
        # Build SAML settings
        saml_settings = self._build_saml_settings(config, request_data)
        
        # Initialize SAML Auth
        auth = OneLogin_Saml2_Auth(request_data, saml_settings)
        
        # Process response
        auth.process_response()
        
        # Check for errors
        errors = auth.get_errors()
        if errors:
            error_reason = auth.get_last_error_reason()
            raise ValueError(f"SAML authentication failed: {error_reason}")
        
        # Verify authentication
        if not auth.is_authenticated():
            raise ValueError("SAML authentication failed: User not authenticated")
        
        # Get user attributes
        attributes = auth.get_attributes()
        nameid = auth.get_nameid()
        session_index = auth.get_session_index()
        
        # Extract user information
        user_info = self._extract_user_info(attributes, nameid, config)
        
        return {
            "authenticated": True,
            "user_info": user_info,
            "session_index": session_index,
            "nameid": nameid,
            "attributes": attributes
        }
    
    def _extract_user_info(self, attributes: dict, nameid: str, config: dict) -> dict:
        """Extract user information from SAML attributes."""
        # Get attribute mappings from config (or use defaults)
        attr_map = config.get("attribute_mapping", {
            "email": "email",
            "firstName": "firstName", 
            "lastName": "lastName",
            "groups": "groups"
        })
        
        def get_attr(attr_name: str) -> Optional[str]:
            """Get attribute value from SAML attributes."""
            mapped_name = attr_map.get(attr_name, attr_name)
            values = attributes.get(mapped_name, [])
            if values and len(values) > 0:
                return values[0]
            return None
        
        email = get_attr("email") or nameid
        first_name = get_attr("firstName") or ""
        last_name = get_attr("lastName") or ""
        
        # Get groups for role mapping
        groups = attributes.get(attr_map.get("groups", "groups"), [])
        
        return {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "nameid": nameid,
            "groups": groups
        }
    
    def map_groups_to_role(self, groups: list, provider: str) -> str:
        """Map SAML groups to AutoGraph role.

        If user is in multiple groups, returns the highest privilege role.
        Role hierarchy: admin > editor > viewer
        """
        config = self.get_saml_config(provider)
        if not config:
            return "viewer"

        # Get group mappings
        group_mappings = config.get("group_mapping", {})

        # Role hierarchy (higher number = higher privilege)
        role_hierarchy = {
            "viewer": 1,
            "editor": 2,
            "admin": 3
        }

        # Find all matching roles
        matched_roles = []
        for group in groups:
            if group in group_mappings:
                role = group_mappings[group]
                matched_roles.append(role)

        # If no matches, return default
        if not matched_roles:
            return config.get("default_role", "viewer")

        # Return highest privilege role
        return max(matched_roles, key=lambda r: role_hierarchy.get(r, 0))
    
    def _build_saml_settings(self, config: dict, request_data: dict) -> dict:
        """Build SAML settings dictionary for OneLogin library."""
        # Get base URL
        base_url = config.get("sp", {}).get("assertionConsumerService", {}).get("url", "")
        if not base_url:
            # Try to construct from request
            scheme = request_data.get("https", "on") == "on" and "https" or "http"
            host = request_data.get("http_host", "localhost")
            base_url = f"{scheme}://{host}"
        
        # Build SP (Service Provider - us) settings
        sp_settings = {
            "entityId": config.get("sp", {}).get("entityId", f"{base_url}/saml/metadata"),
            "assertionConsumerService": {
                "url": f"{base_url}/api/auth/saml/acs",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            },
            "singleLogoutService": {
                "url": f"{base_url}/api/auth/saml/sls",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
            "x509cert": config.get("sp", {}).get("x509cert", ""),
            "privateKey": config.get("sp", {}).get("privateKey", "")
        }
        
        # Build IdP (Identity Provider - them) settings  
        idp_settings = {
            "entityId": config.get("idp", {}).get("entityId", ""),
            "singleSignOnService": {
                "url": config.get("idp", {}).get("singleSignOnService", {}).get("url", ""),
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            },
            "singleLogoutService": {
                "url": config.get("idp", {}).get("singleLogoutService", {}).get("url", ""),
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            },
            "x509cert": config.get("idp", {}).get("x509cert", "")
        }
        
        # Security settings
        security_settings = {
            "nameIdEncrypted": False,
            "authnRequestsSigned": False,
            "logoutRequestSigned": False,
            "logoutResponseSigned": False,
            "signMetadata": False,
            "wantMessagesSigned": False,
            "wantAssertionsSigned": True,
            "wantAssertionsEncrypted": False,
            "wantNameId": True,
            "wantNameIdEncrypted": False,
            "wantAttributeStatement": True,
            "requestedAuthnContext": True,
            "requestedAuthnContextComparison": "exact",
            "allowRepeatAttributeName": True,
            "rejectUnsolicitedResponsesWithInResponseTo": False
        }
        
        return {
            "strict": True,
            "debug": os.getenv("SAML_DEBUG", "false").lower() == "true",
            "sp": sp_settings,
            "idp": idp_settings,
            "security": security_settings
        }
    
    def get_metadata(self, provider: str, request_data: dict) -> str:
        """Get SAML metadata XML for this service provider."""
        config = self.get_saml_config(provider)
        if not config:
            raise ValueError(f"SAML provider '{provider}' not configured")
        
        saml_settings = self._build_saml_settings(config, request_data)
        settings = OneLogin_Saml2_Settings(saml_settings)
        metadata = settings.get_sp_metadata()
        errors = settings.validate_metadata(metadata)
        
        if errors:
            raise ValueError(f"Invalid metadata: {', '.join(errors)}")
        
        return metadata
    
    def get_jit_config(self, provider: str) -> dict:
        """Get JIT (Just-In-Time) provisioning configuration."""
        config = self.get_saml_config(provider)
        if not config:
            return {"enabled": False}
        
        return {
            "enabled": config.get("jit_provisioning", {}).get("enabled", False),
            "default_role": config.get("jit_provisioning", {}).get("default_role", "viewer"),
            "create_team": config.get("jit_provisioning", {}).get("create_team", False),
            "team_name": config.get("jit_provisioning", {}).get("team_name", "")
        }
    
    def set_jit_config(self, provider: str, jit_config: dict) -> bool:
        """Update JIT provisioning configuration."""
        config = self.get_saml_config(provider)
        if not config:
            return False
        
        config["jit_provisioning"] = jit_config
        return self.set_saml_config(provider, config)
    
    def get_group_mapping(self, provider: str) -> dict:
        """Get group to role mapping configuration."""
        config = self.get_saml_config(provider)
        if not config:
            return {}
        
        return config.get("group_mapping", {})
    
    def set_group_mapping(self, provider: str, mappings: dict) -> bool:
        """Update group to role mapping configuration."""
        config = self.get_saml_config(provider)
        if not config:
            return False
        
        config["group_mapping"] = mappings
        return self.set_saml_config(provider, config)
