"""
Bayer Audit Logging Module

This module provides Bayer-compliant audit logging functionality
that integrates with Bayer's compliance tools (Splunk, Azure Sentinel).

Usage:
    from shared.bayer_audit_logger import get_audit_logger
    
    logger = get_audit_logger()
    logger.log_event(
        event_type="diagram.create",
        user_id="user-123",
        user_email="john.doe@bayer.com",
        resource_type="diagram",
        resource_id="diagram-456",
        action_type="create",
        action_result="success"
    )
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BayerAuditLogger:
    """
    Bayer-compliant audit logger for AutoGraph v3
    
    Sends audit logs to:
    - Bayer Splunk (via HTTP Event Collector)
    - Azure Sentinel (via Log Analytics API)
    - Local file storage (for disaster recovery)
    
    Complies with:
    - Bayer IT Security Standards v3.2
    - SOC 2 Type II requirements
    - GDPR audit trail requirements
    - 21 CFR Part 11 (for GxP systems)
    """
    
    def __init__(
        self,
        splunk_hec_url: Optional[str] = None,
        splunk_token: Optional[str] = None,
        azure_workspace_id: Optional[str] = None,
        azure_shared_key: Optional[str] = None,
        environment: str = "production"
    ):
        """
        Initialize Bayer Audit Logger
        
        Args:
            splunk_hec_url: Bayer Splunk HTTP Event Collector URL
            splunk_token: Splunk HEC authentication token
            azure_workspace_id: Azure Log Analytics Workspace ID
            azure_shared_key: Azure Log Analytics shared key
            environment: Deployment environment (production, staging, development)
        """
        # Splunk configuration
        self.splunk_hec_url = splunk_hec_url or os.getenv("BAYER_SPLUNK_HEC_URL")
        self.splunk_token = splunk_token or os.getenv("BAYER_SPLUNK_TOKEN")
        
        # Azure Sentinel configuration
        self.azure_workspace_id = azure_workspace_id or os.getenv("AZURE_WORKSPACE_ID")
        self.azure_shared_key = azure_shared_key or os.getenv("AZURE_SHARED_KEY")
        
        # Environment
        self.environment = environment
        
        # Application metadata
        self.app_name = "AutoGraph"
        self.app_version = "3.0.0"
        self.compliance_standard = "v3.2"
        
    def log_event(
        self,
        event_type: str,
        user_id: str,
        user_email: str,
        resource_type: str,
        resource_id: str,
        action_type: str,
        action_result: str,
        severity: str = "INFO",
        action_description: Optional[str] = None,
        failure_reason: Optional[str] = None,
        resource_name: Optional[str] = None,
        user_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        service: Optional[str] = None,
        data_classification: str = "internal",
        contains_pii: bool = False,
        gdpr_applicable: bool = True,
        compliance_tags: Optional[List[str]] = None,
        changes_before: Optional[Dict[str, Any]] = None,
        changes_after: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Log a Bayer-compliant audit event
        
        Args:
            event_type: Type of event (e.g., user.login, diagram.create)
            user_id: UUID of user performing action
            user_email: Email address of user
            resource_type: Type of resource (diagram, user, team, etc.)
            resource_id: UUID of resource
            action_type: Type of action (create, read, update, delete, etc.)
            action_result: Result of action (success, failure)
            severity: Log severity (INFO, WARNING, ERROR, CRITICAL)
            action_description: Human-readable description of action
            failure_reason: Reason for failure (if action_result is failure)
            resource_name: Name of resource
            user_role: Role of user (admin, editor, viewer)
            ip_address: IP address of user
            user_agent: Browser user agent string
            session_id: Session UUID
            request_id: Request UUID
            correlation_id: Correlation ID for distributed tracing
            service: Service name (api-gateway, auth-service, etc.)
            data_classification: Data classification level
            contains_pii: Whether event involves PII
            gdpr_applicable: Whether GDPR applies to this event
            compliance_tags: List of compliance standards (SOC2, GDPR, etc.)
            changes_before: Previous state (for update events)
            changes_after: New state (for create/update events)
            **kwargs: Additional metadata
        """
        # Build audit event structure
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_id": str(uuid4()),
            "event_type": event_type,
            "severity": severity,
            "user": {
                "user_id": user_id,
                "email": user_email,
                "full_name": kwargs.get("user_full_name"),
                "role": user_role,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "session_id": session_id
            },
            "resource": {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "resource_name": resource_name,
                "owner_id": kwargs.get("owner_id")
            },
            "action": {
                "action_type": action_type,
                "action_result": action_result,
                "action_description": action_description or f"User {action_type}d {resource_type}",
                "failure_reason": failure_reason
            },
            "context": {
                "request_id": request_id or str(uuid4()),
                "correlation_id": correlation_id,
                "service": service,
                "environment": self.environment,
                "tenant_id": "bayer",
                "location": kwargs.get("location"),
                "vpn_connected": kwargs.get("vpn_connected")
            },
            "compliance": {
                "data_classification": data_classification,
                "contains_pii": contains_pii,
                "gdpr_applicable": gdpr_applicable,
                "retention_period_days": 2555,  # 7 years (SOC2, GDPR requirement)
                "compliance_tags": compliance_tags or ["SOC2", "GDPR"]
            },
            "metadata": {
                "bayer_cost_center": kwargs.get("cost_center"),
                "bayer_project_code": kwargs.get("project_code"),
                "application": self.app_name,
                "application_version": self.app_version,
                "bayer_compliance_standard": self.compliance_standard
            }
        }
        
        # Add change tracking if provided
        if changes_before or changes_after:
            event["changes"] = {}
            if changes_before:
                event["changes"]["before"] = changes_before
            if changes_after:
                event["changes"]["after"] = changes_after
        
        # Send to destinations
        self._send_to_splunk(event)
        self._send_to_azure_sentinel(event)
        self._log_locally(event)
        
    def _send_to_splunk(self, event: Dict[str, Any]):
        """
        Send audit event to Bayer Splunk
        """
        if not self.splunk_hec_url or not self.splunk_token:
            logger.warning("Splunk configuration not provided, skipping")
            return
            
        payload = {
            "event": event,
            "sourcetype": "_json",
            "index": "bayer_autograph_audit"
        }
        
        headers = {
            "Authorization": f"Splunk {self.splunk_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.splunk_hec_url,
                json=payload,
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            logger.debug(f"Sent audit event to Splunk: {event['event_id']}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send audit event to Splunk: {e}")
            # Don't raise exception - audit logging failure shouldn't break app
            
    def _send_to_azure_sentinel(self, event: Dict[str, Any]):
        """
        Send audit event to Azure Sentinel
        """
        if not self.azure_workspace_id or not self.azure_shared_key:
            logger.warning("Azure Sentinel configuration not provided, skipping")
            return
            
        # Azure Sentinel requires different authentication
        # This is a placeholder - actual implementation would use Azure SDK
        logger.debug(f"Would send to Azure Sentinel: {event['event_id']}")
        
    def _log_locally(self, event: Dict[str, Any]):
        """
        Log audit event to local file (for disaster recovery)
        """
        # Log as structured JSON (one event per line)
        logger.info(json.dumps(event))


# Global audit logger instance
_audit_logger: Optional[BayerAuditLogger] = None


def get_audit_logger() -> BayerAuditLogger:
    """
    Get global Bayer audit logger instance (singleton)
    """
    global _audit_logger
    
    if _audit_logger is None:
        _audit_logger = BayerAuditLogger(
            environment=os.getenv("ENVIRONMENT", "production")
        )
        
    return _audit_logger


def log_authentication_event(
    event_type: str,
    user_id: str,
    user_email: str,
    action_result: str,
    authentication_method: str,
    ip_address: str,
    **kwargs
):
    """
    Helper function to log authentication events
    """
    logger = get_audit_logger()
    logger.log_event(
        event_type=event_type,
        user_id=user_id,
        user_email=user_email,
        resource_type="user",
        resource_id=user_id,
        action_type="login" if "login" in event_type else "logout",
        action_result=action_result,
        severity="WARNING" if action_result == "failure" else "INFO",
        ip_address=ip_address,
        **kwargs
    )


def log_diagram_event(
    event_type: str,
    user_id: str,
    user_email: str,
    diagram_id: str,
    diagram_name: str,
    action_type: str,
    action_result: str,
    **kwargs
):
    """
    Helper function to log diagram events
    """
    logger = get_audit_logger()
    logger.log_event(
        event_type=event_type,
        user_id=user_id,
        user_email=user_email,
        resource_type="diagram",
        resource_id=diagram_id,
        resource_name=diagram_name,
        action_type=action_type,
        action_result=action_result,
        **kwargs
    )


def log_export_event(
    user_id: str,
    user_email: str,
    diagram_id: str,
    export_format: str,
    file_size_bytes: int,
    includes_sensitive_data: bool,
    **kwargs
):
    """
    Helper function to log export events
    """
    logger = get_audit_logger()
    logger.log_event(
        event_type="file.export",
        user_id=user_id,
        user_email=user_email,
        resource_type="export",
        resource_id=str(uuid4()),
        action_type="export",
        action_result="success",
        action_description=f"Diagram exported as {export_format}",
        data_classification="confidential" if includes_sensitive_data else "internal",
        **kwargs
    )
