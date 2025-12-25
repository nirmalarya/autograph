# GDPR Compliance Documentation

## Overview

This document outlines how Autograph v3 complies with the General Data Protection Regulation (GDPR) requirements.

## GDPR Rights Implementation

### Article 15: Right to Access (Data Export)

**Endpoint:** `GET /gdpr/export`

Users can request a complete export of all their personal data in JSON format.

**Exported Data Includes:**
- Personal information (email, name, preferences)
- Files and diagrams
- Comments and collaboration data
- Team memberships
- API keys and access tokens (metadata only)
- Audit logs
- Consent records
- Usage metrics

**Usage:**
```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:8085/gdpr/export
```

### Article 17: Right to be Forgotten (Data Deletion)

**Endpoints:**
- `POST /gdpr/deletion/request` - Request data deletion
- `POST /gdpr/deletion/verify` - Verify deletion request
- `POST /gdpr/deletion/execute/{request_id}` - Execute deletion (admin only)

**Deletion Process:**
1. User requests deletion with optional reason
2. System generates verification token
3. User verifies request using token
4. Admin executes deletion
5. All user data is permanently deleted except:
   - Audit logs (anonymized for legal compliance)

**Data Deleted:**
- User account and credentials
- All files, diagrams, and versions
- Comments and reactions
- Team memberships and owned teams
- API keys and tokens
- Usage metrics
- Consents
- Git connections

**Usage:**
```bash
# Request deletion
curl -X POST -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"reason": "No longer need the account"}' \
     http://localhost:8085/gdpr/deletion/request

# Verify deletion
curl -X POST -H "Content-Type: application/json" \
     -d '{"verification_token": "<token>"}' \
     http://localhost:8085/gdpr/deletion/verify
```

### Consent Management

**Endpoints:**
- `POST /gdpr/consent` - Record consent
- `POST /gdpr/consent/withdraw` - Withdraw consent
- `GET /gdpr/consent` - Get user consents

**Consent Types:**
- `data_processing` - Essential data processing
- `marketing` - Marketing communications
- `analytics` - Usage analytics
- `cookies` - Cookie usage
- `third_party` - Third-party data sharing

**Usage:**
```bash
# Record consent
curl -X POST -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"consent_type": "marketing", "consent_given": true, "consent_version": "1.0"}' \
     http://localhost:8085/gdpr/consent

# Withdraw consent
curl -X POST -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"consent_type": "marketing"}' \
     http://localhost:8085/gdpr/consent/withdraw
```

## Article 30: Data Processing Activities

**Endpoint:** `GET /gdpr/processing-activities` (Admin only)

Maintains a record of all data processing activities as required by GDPR Article 30.

**Processing Activities Include:**
1. **User Authentication and Authorization**
   - Legal Basis: Contract
   - Data: Email, password hash, session tokens
   - Retention: Account duration + 30 days

2. **Diagram and File Storage**
   - Legal Basis: Contract
   - Data: File content, metadata, versions
   - Retention: Account duration or until user deletes

3. **Collaboration and Comments**
   - Legal Basis: Contract
   - Data: Comments, mentions, reactions
   - Retention: Duration of associated file

4. **Usage Analytics**
   - Legal Basis: Legitimate Interest
   - Data: Usage metrics, timestamps
   - Retention: 12 months

5. **Audit Logging and Security**
   - Legal Basis: Legal Obligation
   - Data: Action logs, IP addresses
   - Retention: 7 years

6. **Marketing Communications**
   - Legal Basis: Consent
   - Data: Email, name, preferences
   - Retention: Until consent withdrawn

## Article 33/34: Data Breach Notification

**Endpoint:** `POST /gdpr/breach/log` (Admin only)

System for logging and tracking data breaches with automatic notification requirements.

**Breach Logging Includes:**
- Breach type and severity
- Affected users count
- Data categories affected
- Detection and containment timestamps
- DPA notification status (72-hour requirement)
- User notification status

**Usage:**
```bash
curl -X POST -H "Authorization: Bearer <admin_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "breach_type": "unauthorized_access",
       "severity": "high",
       "description": "Unauthorized access attempt detected",
       "affected_users_count": 0,
       "affected_data_categories": [],
       "detected_at": "2024-01-01T00:00:00Z",
       "reported_by": "Security Team"
     }' \
     http://localhost:8085/gdpr/breach/log
```

## Data Minimization Principles

Autograph implements data minimization through:

1. **Password Security**: Passwords never stored in plain text (bcrypt hashing)
2. **Session Management**: Tokens have expiration (60 minutes for access, 30 days for refresh)
3. **Audit Log Anonymization**: After user deletion, audit logs are anonymized
4. **Data Retention**: Each data type has defined retention period
5. **Minimal Collection**: Only collect data necessary for service provision

## Cross-Border Data Transfers

For services that transfer data outside the EU:

1. **Email Services**: Standard Contractual Clauses (SCCs) in place
2. **Cloud Storage**: Data stored within EU region by default
3. **Documentation**: Third-country transfers documented in processing activities
4. **Safeguards**: All transfers protected with appropriate safeguards

## Security Measures

GDPR-compliant security measures:

1. **Encryption in Transit**: TLS 1.3
2. **Encryption at Rest**: Database and file storage encryption
3. **Access Control**: Role-based access control (RBAC)
4. **Audit Logging**: Comprehensive activity logging
5. **Pseudonymization**: User IDs used instead of email where possible
6. **Regular Security Assessments**: Vulnerability scanning and penetration testing

## Data Retention Policies

| Data Type | Retention Period | Legal Basis |
|-----------|-----------------|-------------|
| User Account | Account duration + 30 days | Contract |
| Files/Diagrams | Until user deletes or account closed | Contract |
| Comments | File duration or account duration | Contract |
| Audit Logs | 7 years (anonymized after deletion) | Legal Obligation |
| Usage Metrics | 12 months | Legitimate Interest |
| Marketing Consent | Until consent withdrawn | Consent |
| Session Tokens | 60 minutes (access) / 30 days (refresh) | Contract |

## Data Protection Officer (DPO)

**Contact:** dpo@autograph.example.com

Responsible for:
- Monitoring GDPR compliance
- Advising on data protection obligations
- Cooperating with supervisory authorities
- Acting as contact point for data subjects

## User Rights Summary

| Right | Article | Implementation |
|-------|---------|----------------|
| Right to Access | Art. 15 | Data export endpoint |
| Right to Rectification | Art. 16 | Profile update endpoints |
| Right to Erasure | Art. 17 | Data deletion workflow |
| Right to Restrict Processing | Art. 18 | Account deactivation |
| Right to Data Portability | Art. 20 | JSON export format |
| Right to Object | Art. 21 | Consent withdrawal |
| Automated Decision Making | Art. 22 | No automated profiling |

## Compliance Monitoring

Regular compliance checks include:

1. **Data Export Testing**: Verify complete data export
2. **Deletion Testing**: Verify complete data removal
3. **Consent Auditing**: Review consent records
4. **Processing Activities Review**: Quarterly review
5. **Security Assessments**: Continuous monitoring
6. **Breach Response Drills**: Quarterly testing

## Response Times

- **Data Export**: Within 48 hours
- **Data Deletion**: Within 30 days of verification
- **Consent Withdrawal**: Immediate (processing stops within 24 hours)
- **Data Breach Notification to DPA**: Within 72 hours
- **Data Breach Notification to Users**: Within 72 hours (if high risk)

## Compliance Validation

Run the GDPR compliance validation script:

```bash
python3 validate_feature63_gdpr_compliance.py
```

This tests all GDPR requirements and generates a compliance score.

## Legal Disclaimers

This documentation describes technical implementation of GDPR requirements. For legal advice on GDPR compliance, consult with qualified legal professionals. GDPR compliance requires both technical and organizational measures.

## Updates

This document is updated whenever:
- New data processing activities are added
- Retention policies change
- Legal requirements are updated
- Security measures are enhanced

**Last Updated:** 2024-12-25
**Version:** 1.0
