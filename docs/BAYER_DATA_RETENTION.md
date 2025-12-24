# Bayer Data Retention Policy Configuration

## Overview

This document defines the configurable data retention policies for AutoGraph v3 to comply with Bayer's regulatory requirements including SOC 2, GDPR, GxP, and 21 CFR Part 11.

## Default Retention Periods

| Data Type | Retention Period | Compliance Requirement | Auto-Archive | Auto-Delete |
|-----------|------------------|------------------------|--------------|-------------|
| Audit Logs | 7 years | SOC 2, ISO 27001 | After 90 days | After 7 years |
| GxP Audit Logs | 10 years | 21 CFR Part 11, GxP | After 90 days | After 10 years |
| User Diagrams | Indefinite* | User data | After 1 year inactive | Never (soft delete only) |
| Deleted Diagrams (Trash) | 30 days | Recovery window | N/A | After 30 days |
| User Accounts (Inactive) | 2 years | Data minimization | N/A | After 2 years |
| Access Tokens | 1 hour (access), 30 days (refresh) | Security | N/A | After expiry |
| Session Data | 24 hours | Security | N/A | After expiry |
| Export Files | 7 days | Temporary storage | N/A | After 7 days |
| Collaboration History | 7 years | Audit trail | After 90 days | After 7 years |
| Version History | Indefinite* | Compliance | After 1 year inactive | Never |

\* Unless user deletes or account is closed

## Configuration

### Environment Variables

```bash
# Data Retention Configuration
RETENTION_AUDIT_LOGS_DAYS=2555          # 7 years
RETENTION_GXP_LOGS_DAYS=3650            # 10 years
RETENTION_DELETED_DIAGRAMS_DAYS=30      # 30 days in trash
RETENTION_INACTIVE_USERS_DAYS=730       # 2 years
RETENTION_EXPORT_FILES_DAYS=7           # 7 days
RETENTION_SESSIONS_HOURS=24             # 24 hours

# Archive Settings
ARCHIVE_AUDIT_LOGS_DAYS=90              # Archive to cold storage after 90 days
ARCHIVE_DIAGRAMS_INACTIVE_DAYS=365      # Archive inactive diagrams after 1 year

# Storage Tiers
STORAGE_HOT_TIER=azure-blob-hot         # Active data
STORAGE_COOL_TIER=azure-blob-cool       # Inactive data (1 year)
STORAGE_ARCHIVE_TIER=azure-blob-archive # Long-term retention (7-10 years)

# Compliance Mode
COMPLIANCE_MODE=bayer                   # bayer, standard, gxp
GDPR_ENABLED=true                       # Enable GDPR compliance features
GXP_ENABLED=true                        # Enable GxP compliance features
```

### Database Configuration

```sql
-- retention_policies table
CREATE TABLE retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_name VARCHAR(255) NOT NULL UNIQUE,
    data_type VARCHAR(100) NOT NULL,
    retention_days INTEGER NOT NULL,
    archive_days INTEGER,
    compliance_requirement VARCHAR(255),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default Bayer policies
INSERT INTO retention_policies (policy_name, data_type, retention_days, archive_days, compliance_requirement) VALUES
('bayer_audit_logs', 'audit_log', 2555, 90, 'SOC2,ISO27001'),
('bayer_gxp_logs', 'gxp_audit_log', 3650, 90, '21CFR11,GxP'),
('bayer_deleted_diagrams', 'deleted_diagram', 30, NULL, 'User Recovery'),
('bayer_inactive_users', 'user_account', 730, NULL, 'GDPR Data Minimization'),
('bayer_export_files', 'export_file', 7, NULL, 'Security'),
('bayer_sessions', 'session', 1, NULL, 'Security');

-- Data retention tracking table
CREATE TABLE data_retention_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL,
    last_accessed_at TIMESTAMP,
    archived_at TIMESTAMP,
    deletion_scheduled_at TIMESTAMP,
    deleted_at TIMESTAMP,
    retention_policy_id UUID REFERENCES retention_policies(id),
    compliance_hold BOOLEAN DEFAULT FALSE,
    hold_reason TEXT,
    INDEX idx_deletion_scheduled (deletion_scheduled_at),
    INDEX idx_resource (resource_type, resource_id)
);
```

## Retention Policy Enforcement

### Automated Cleanup Jobs

#### Daily Cleanup Job (Cron: 0 2 * * *)

```python
#!/usr/bin/env python3
"""
Bayer Data Retention Cleanup Job

Runs daily at 2 AM UTC to enforce data retention policies.
"""

import psycopg2
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enforce_retention_policies():
    """
    Enforce all active retention policies
    """
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Get active retention policies
    cursor.execute("""
        SELECT policy_name, data_type, retention_days, archive_days
        FROM retention_policies
        WHERE enabled = TRUE
    """)
    
    policies = cursor.fetchall()
    
    for policy_name, data_type, retention_days, archive_days in policies:
        logger.info(f"Enforcing policy: {policy_name}")
        
        # Archive old data if archive_days is set
        if archive_days:
            archive_date = datetime.now() - timedelta(days=archive_days)
            archive_data(data_type, archive_date)
        
        # Delete data past retention period
        deletion_date = datetime.now() - timedelta(days=retention_days)
        delete_data(data_type, deletion_date)
    
    conn.commit()
    cursor.close()
    conn.close()

def archive_data(data_type, archive_date):
    """
    Move data to cold storage (Azure Blob Archive tier)
    """
    logger.info(f"Archiving {data_type} older than {archive_date}")
    
    if data_type == 'audit_log':
        # Move audit logs to archive tier
        archive_audit_logs(archive_date)
    elif data_type == 'diagram':
        # Move inactive diagrams to archive tier
        archive_diagrams(archive_date)
    
def delete_data(data_type, deletion_date):
    """
    Permanently delete data past retention period
    """
    logger.info(f"Deleting {data_type} older than {deletion_date}")
    
    if data_type == 'deleted_diagram':
        # Permanently delete diagrams in trash
        delete_trash_diagrams(deletion_date)
    elif data_type == 'user_account':
        # Delete inactive user accounts
        delete_inactive_users(deletion_date)
    elif data_type == 'export_file':
        # Delete temporary export files
        delete_export_files(deletion_date)

if __name__ == "__main__":
    enforce_retention_policies()
```

### Manual Retention Commands

```bash
# Check retention status
python manage.py retention:status

# Enforce retention policies immediately
python manage.py retention:enforce

# Archive specific data type
python manage.py retention:archive --type audit_logs --before 2024-01-01

# Place legal hold on data (prevent deletion)
python manage.py retention:hold --resource-id <uuid> --reason "Litigation Hold"

# Release legal hold
python manage.py retention:release --resource-id <uuid>
```

## GDPR Compliance

### Right to Erasure (Right to be Forgotten)

```python
def gdpr_delete_user_data(user_id: str):
    """
    Delete all user data for GDPR compliance
    """
    # 1. Delete user account
    delete_user_account(user_id)
    
    # 2. Delete or anonymize diagrams
    anonymize_diagrams(user_id)  # Replace user_id with "deleted-user"
    
    # 3. Delete exports
    delete_user_exports(user_id)
    
    # 4. Redact from audit logs (keep action, remove PII)
    redact_audit_logs(user_id)
    
    # 5. Delete sessions
    delete_user_sessions(user_id)
    
    # 6. Notify user
    send_gdpr_deletion_confirmation(user_id)
```

### Data Portability

```python
def gdpr_export_user_data(user_id: str):
    """
    Export all user data in machine-readable format (JSON)
    """
    data = {
        "user_profile": get_user_profile(user_id),
        "diagrams": get_user_diagrams(user_id),
        "exports": get_user_exports(user_id),
        "audit_trail": get_user_audit_trail(user_id),
        "settings": get_user_settings(user_id)
    }
    
    return json.dumps(data, indent=2)
```

## GxP Compliance (21 CFR Part 11)

### Electronic Signature Support

```python
def gxp_sign_record(user_id: str, record_id: str, signature_meaning: str):
    """
    Electronically sign a record per 21 CFR Part 11
    """
    signature = {
        "signer_id": user_id,
        "record_id": record_id,
        "signature_meaning": signature_meaning,  # "Reviewed by", "Approved by", etc.
        "timestamp": datetime.utcnow(),
        "signature_hash": generate_signature_hash(user_id, record_id)
    }
    
    # Record must be locked after signing
    lock_record(record_id)
    
    return signature
```

### Audit Trail Requirements

- All GxP records must have complete audit trail for 10 years
- Audit trail must record: Who, What, When, Why
- Audit trail must be tamper-proof (append-only)
- Audit trail must be easily readable by FDA inspectors

## Legal Hold

### Litigation Hold Process

```python
def place_legal_hold(resource_ids: list, hold_reason: str, requestor: str):
    """
    Place legal hold on data (prevents deletion)
    """
    for resource_id in resource_ids:
        # Mark resource as on hold
        conn.execute("""
            UPDATE data_retention_tracking
            SET compliance_hold = TRUE,
                hold_reason = %s,
                hold_placed_by = %s,
                hold_placed_at = CURRENT_TIMESTAMP
            WHERE resource_id = %s
        """, (hold_reason, requestor, resource_id))
    
    # Notify legal team
    notify_legal_team(resource_ids, hold_reason)
```

## Monitoring and Alerts

### Retention Policy Alerts

```yaml
# Prometheus alerts
- alert: RetentionJobFailed
  expr: retention_job_last_success_timestamp < (time() - 86400)
  annotations:
    summary: "Retention job hasn't run in 24 hours"
    
- alert: StorageQuotaExceeded
  expr: storage_usage_bytes / storage_quota_bytes > 0.9
  annotations:
    summary: "Storage quota 90% full, retention may be needed"

- alert: GxPDataNearExpiry
  expr: gxp_data_retention_days_remaining < 30
  annotations:
    summary: "GxP data approaching 10-year retention limit"
```

### Retention Dashboard

Access at: https://diagrams.bayer.com/admin/retention

Metrics:
- Data volume by type and age
- Storage costs by tier (hot/cool/archive)
- Upcoming deletions (next 30 days)
- Legal holds active
- GDPR requests pending

## Compliance Reports

### SOC 2 Audit Report

```sql
SELECT 
    policy_name,
    data_type,
    COUNT(*) as records,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record,
    retention_days,
    compliance_requirement
FROM data_retention_tracking
JOIN retention_policies ON retention_policy_id = retention_policies.id
GROUP BY policy_name, data_type, retention_days, compliance_requirement;
```

### GDPR Deletion Report

```sql
SELECT 
    resource_type,
    COUNT(*) as deleted_count,
    DATE(deleted_at) as deletion_date,
    deletion_reason
FROM data_retention_tracking
WHERE deleted_at >= CURRENT_DATE - INTERVAL '30 days'
  AND deletion_reason = 'GDPR Right to Erasure'
GROUP BY resource_type, DATE(deleted_at), deletion_reason;
```

## Disaster Recovery

### Backup Retention

- **Daily backups**: 30 days retention
- **Weekly backups**: 12 weeks retention
- **Monthly backups**: 7 years retention
- **Annual backups**: 10 years retention (GxP)

### Backup Storage

- Primary: Azure Blob Storage (geo-redundant)
- Secondary: AWS S3 (cross-cloud redundancy)
- Tertiary: On-premises tape backup (air-gapped)

## Support

For data retention questions:
- **Policy Questions**: Bayer Compliance Office (`compliance@bayer.com`)
- **Technical Issues**: AutoGraph Support (`autograph-support@bayer.com`)
- **Legal Hold**: Bayer Legal (`legal@bayer.com`)
- **GDPR Requests**: Bayer Data Protection Officer (`dpo@bayer.com`)
