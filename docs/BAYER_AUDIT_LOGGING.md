# Bayer Audit Logging Format Specification

## Overview

This document defines the standardized audit log format for AutoGraph v3 that is compatible with Bayer's compliance tools (Splunk, Azure Sentinel, and Bayer SIEM).

## Log Format

All audit logs MUST be in JSON format with the following structure:

```json
{
  "timestamp": "2025-12-24T15:30:45.123Z",
  "event_id": "uuid-v4",
  "event_type": "user.login" | "diagram.create" | "diagram.edit" | "diagram.delete" | "diagram.share" | "file.export" | "user.permission_change" | "system.config_change",
  "severity": "INFO" | "WARNING" | "ERROR" | "CRITICAL",
  "user": {
    "user_id": "uuid",
    "email": "user@bayer.com",
    "full_name": "John Doe",
    "role": "admin" | "editor" | "viewer",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 ...",
    "session_id": "uuid"
  },
  "resource": {
    "resource_type": "diagram" | "user" | "team" | "folder" | "export" | "system",
    "resource_id": "uuid",
    "resource_name": "E-Commerce Architecture Diagram",
    "owner_id": "uuid"
  },
  "action": {
    "action_type": "create" | "read" | "update" | "delete" | "share" | "export" | "login" | "logout",
    "action_result": "success" | "failure",
    "action_description": "User created a new diagram",
    "failure_reason": "Insufficient permissions" // Only if action_result is "failure"
  },
  "context": {
    "request_id": "uuid",
    "correlation_id": "uuid", // For distributed tracing
    "service": "api-gateway" | "auth-service" | "diagram-service" | "collaboration-service",
    "environment": "production" | "staging" | "development",
    "tenant_id": "bayer",
    "location": "eu-central-1", // AWS region or Azure location
    "vpn_connected": true | false
  },
  "compliance": {
    "data_classification": "public" | "internal" | "confidential" | "restricted",
    "contains_pii": true | false,
    "gdpr_applicable": true | false,
    "retention_period_days": 2555, // 7 years
    "compliance_tags": ["SOC2", "GDPR", "21CFR11"]
  },
  "changes": {
    "before": {...}, // Previous state (for update events)
    "after": {...}   // New state (for create/update events)
  },
  "metadata": {
    "bayer_cost_center": "CC-12345",
    "bayer_project_code": "PRJ-67890",
    "application": "AutoGraph",
    "application_version": "3.0.0",
    "bayer_compliance_standard": "v3.2"
  }
}
```

## Event Types

### Authentication Events

#### user.login
```json
{
  "event_type": "user.login",
  "action": {
    "action_type": "login",
    "action_result": "success",
    "action_description": "User successfully logged in via SSO"
  },
  "user": {
    "authentication_method": "sso" | "password" | "mfa",
    "mfa_verified": true | false
  }
}
```

#### user.logout
```json
{
  "event_type": "user.logout",
  "action": {
    "action_type": "logout",
    "action_result": "success",
    "action_description": "User logged out"
  }
}
```

#### user.login_failed
```json
{
  "event_type": "user.login_failed",
  "severity": "WARNING",
  "action": {
    "action_type": "login",
    "action_result": "failure",
    "failure_reason": "Invalid credentials",
    "attempt_count": 3
  }
}
```

### Diagram Events

#### diagram.create
```json
{
  "event_type": "diagram.create",
  "resource": {
    "resource_type": "diagram",
    "resource_id": "uuid",
    "resource_name": "Microservices Architecture",
    "diagram_type": "canvas" | "mermaid" | "note"
  },
  "changes": {
    "after": {
      "title": "Microservices Architecture",
      "type": "canvas",
      "created_at": "2025-12-24T15:30:45.123Z"
    }
  }
}
```

#### diagram.edit
```json
{
  "event_type": "diagram.edit",
  "resource": {
    "resource_type": "diagram",
    "resource_id": "uuid"
  },
  "changes": {
    "before": {
      "title": "Old Title",
      "last_modified": "2025-12-24T14:00:00.000Z"
    },
    "after": {
      "title": "New Title",
      "last_modified": "2025-12-24T15:30:45.123Z"
    }
  }
}
```

#### diagram.delete
```json
{
  "event_type": "diagram.delete",
  "severity": "WARNING",
  "resource": {
    "resource_type": "diagram",
    "resource_id": "uuid"
  },
  "action": {
    "action_type": "delete",
    "action_description": "Diagram moved to trash",
    "soft_delete": true
  }
}
```

#### diagram.share
```json
{
  "event_type": "diagram.share",
  "resource": {
    "resource_type": "diagram",
    "resource_id": "uuid"
  },
  "action": {
    "action_description": "Diagram shared with external user"
  },
  "share_details": {
    "share_type": "public_link" | "email" | "team",
    "permissions": "view" | "edit",
    "shared_with": "external@partner.com",
    "expiration": "2025-12-31T23:59:59.999Z"
  },
  "compliance": {
    "data_classification": "internal",
    "external_share": true,
    "approval_required": true,
    "approval_status": "approved",
    "approver": "manager@bayer.com"
  }
}
```

### Export Events

#### file.export
```json
{
  "event_type": "file.export",
  "resource": {
    "resource_type": "export",
    "resource_id": "uuid"
  },
  "action": {
    "action_description": "Diagram exported as PDF"
  },
  "export_details": {
    "format": "pdf" | "png" | "svg" | "json",
    "resolution": "2x",
    "file_size_bytes": 1048576,
    "includes_sensitive_data": false
  }
}
```

### System Events

#### system.config_change
```json
{
  "event_type": "system.config_change",
  "severity": "WARNING",
  "resource": {
    "resource_type": "system",
    "resource_name": "API Rate Limit Configuration"
  },
  "changes": {
    "before": {"rate_limit": 100},
    "after": {"rate_limit": 200}
  }
}
```

## Log Destinations

### Primary: Bayer Splunk

Logs are sent to Bayer's Splunk instance via HTTP Event Collector (HEC):

```
Endpoint: https://splunk.bayer.com:8088/services/collector
Token: HEC_TOKEN
Source Type: _json
Index: bayer_autograph_audit
```

### Secondary: Azure Sentinel

Logs are also sent to Azure Sentinel for advanced threat detection:

```
Workspace ID: WORKSPACE_ID
Shared Key: SHARED_KEY
Log Type: AutoGraph_Audit_CL
```

### Tertiary: Local File Storage

For disaster recovery, logs are also written locally:

```
Path: /var/log/autograph/audit/
Format: JSON (one log per line)
Rotation: Daily
Retention: 90 days local, then archive to Azure Blob Storage
```

## Log Retention

| Event Type | Retention Period | Compliance Requirement |
|------------|------------------|------------------------|
| Authentication | 7 years | SOC 2, ISO 27001 |
| Data Access | 7 years | SOC 2, GDPR |
| System Changes | 10 years | 21 CFR Part 11, GxP |
| Exports (Sensitive Data) | 10 years | GxP, GDPR |
| User Actions | 7 years | SOC 2 |

## Log Levels

- **INFO**: Normal operations (login, create, update)
- **WARNING**: Potentially suspicious activity (failed login, delete, external share)
- **ERROR**: Errors that don't affect security (service unavailable)
- **CRITICAL**: Security incidents (multiple failed logins, unauthorized access attempts)

## Alerting Rules

### Critical Alerts (Immediate Response)

1. **Multiple Failed Logins**: 5 failed login attempts within 5 minutes
2. **Unauthorized Access Attempt**: User attempts to access resource without permission
3. **Mass Data Export**: User exports more than 100 diagrams within 1 hour
4. **System Config Change**: Any change to security configuration
5. **External Share**: Diagram shared with non-Bayer email domain

### Warning Alerts (Review Within 24 Hours)

1. **After-Hours Access**: User access outside business hours (18:00-08:00 CET)
2. **Unusual Location**: User logs in from unexpected geographic location
3. **VPN Bypass**: User accesses system without VPN connection
4. **Elevated Privilege Use**: Admin actions by non-admin users

## Compliance Queries

### SOC 2 Audit Query (Splunk)

```spl
index=bayer_autograph_audit 
| eval retention_check=if(_time < relative_time(now(), "-7y"), "EXPIRED", "VALID")
| stats count by event_type, retention_check
```

### GDPR Data Access Report

```spl
index=bayer_autograph_audit event_type="diagram.read" OR event_type="file.export"
| search user.email="data_subject@example.com"
| table timestamp, event_type, resource.resource_name, user.ip_address
| sort - timestamp
```

### 21 CFR Part 11 Electronic Signature Report

```spl
index=bayer_autograph_audit compliance.compliance_tags="21CFR11"
| table timestamp, user.email, event_type, resource.resource_name, changes.before, changes.after
| sort - timestamp
```

## Implementation Example (Python)

```python
import json
import logging
from datetime import datetime
from uuid import uuid4
import requests

class BayerAuditLogger:
    """
    Bayer-compliant audit logger
    """
    
    def __init__(self, splunk_hec_url, splunk_token):
        self.splunk_hec_url = splunk_hec_url
        self.splunk_token = splunk_token
        
    def log_event(
        self,
        event_type: str,
        user_id: str,
        user_email: str,
        resource_type: str,
        resource_id: str,
        action_type: str,
        action_result: str,
        **kwargs
    ):
        """
        Log a Bayer-compliant audit event
        """
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_id": str(uuid4()),
            "event_type": event_type,
            "severity": kwargs.get("severity", "INFO"),
            "user": {
                "user_id": user_id,
                "email": user_email,
                "ip_address": kwargs.get("ip_address"),
                "session_id": kwargs.get("session_id")
            },
            "resource": {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "resource_name": kwargs.get("resource_name")
            },
            "action": {
                "action_type": action_type,
                "action_result": action_result,
                "action_description": kwargs.get("action_description")
            },
            "context": {
                "request_id": kwargs.get("request_id"),
                "service": kwargs.get("service"),
                "environment": "production",
                "tenant_id": "bayer"
            },
            "compliance": {
                "data_classification": kwargs.get("data_classification", "internal"),
                "contains_pii": kwargs.get("contains_pii", False),
                "gdpr_applicable": True,
                "retention_period_days": 2555,  # 7 years
                "compliance_tags": ["SOC2", "GDPR"]
            },
            "metadata": {
                "application": "AutoGraph",
                "application_version": "3.0.0",
                "bayer_compliance_standard": "v3.2"
            }
        }
        
        # Send to Splunk
        self._send_to_splunk(event)
        
        # Log locally
        logging.info(json.dumps(event))
        
    def _send_to_splunk(self, event):
        """
        Send event to Bayer Splunk
        """
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
        except Exception as e:
            logging.error(f"Failed to send audit log to Splunk: {e}")

# Usage Example
audit_logger = BayerAuditLogger(
    splunk_hec_url="https://splunk.bayer.com:8088/services/collector",
    splunk_token="YOUR_HEC_TOKEN"
)

# Log a diagram creation
audit_logger.log_event(
    event_type="diagram.create",
    user_id="uuid-123",
    user_email="john.doe@bayer.com",
    resource_type="diagram",
    resource_id="diagram-uuid-456",
    resource_name="Microservices Architecture",
    action_type="create",
    action_result="success",
    action_description="User created a new diagram",
    ip_address="192.168.1.100",
    session_id="session-uuid-789",
    request_id="request-uuid-101112",
    service="diagram-service",
    data_classification="internal"
)
```

## Verification

To verify audit logging is working correctly:

1. **Check Splunk**: Search for `index=bayer_autograph_audit` within 5 minutes of event
2. **Check Local Logs**: `tail -f /var/log/autograph/audit/audit.log`
3. **Check Azure Sentinel**: Query `AutoGraph_Audit_CL` table
4. **Verify Retention**: Ensure logs older than 7 years are archived

## Support

For audit logging questions:
- **Technical Issues**: AutoGraph Support (`autograph-support@bayer.com`)
- **Compliance Questions**: Bayer Compliance Office (`compliance@bayer.com`)
- **Splunk Access**: Bayer IT Security (`itsecurity@bayer.com`)
