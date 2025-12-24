# Bayer Pre-Approved Architecture Templates

This directory contains pre-approved architecture templates that comply with Bayer IT Security Standards v3.2.

## Overview

These templates are designed to help Bayer teams quickly create compliant architecture diagrams for:
- Internal applications and services
- External partner integrations
- Data processing pipelines
- API architectures

All templates have been reviewed and approved by:
- Bayer IT Security Team
- Bayer Enterprise Architecture Team
- Bayer Compliance Office

## Available Templates

### 1. Bayer Microservices Architecture
**File:** `bayer-microservices-architecture.json`  
**Compliance Level:** SOC 2 Type II  
**Use Cases:**
- Enterprise web applications
- Mobile application backends
- Internal APIs
- Service-to-service communication

**Key Features:**
- API Gateway (Kong or Azure APIM)
- Service Mesh (Istio) for mTLS
- Azure AD B2C authentication
- Distributed tracing and observability
- Network segmentation and security

### 2. Bayer Secure API Architecture
**File:** `bayer-api-security.json`  
**Compliance Level:** SOC 2 Type II  
**Use Cases:**
- Public-facing APIs
- Partner integrations
- Third-party access
- Mobile API backends

**Key Features:**
- OAuth 2.0 with PKCE
- JWT-based authentication
- Rate limiting (100 req/min per user)
- Comprehensive audit logging
- CORS and security headers

### 3. Bayer Data Processing Pipeline
**File:** `bayer-data-pipeline.json`  
**Compliance Level:** GxP (21 CFR Part 11)  
**Use Cases:**
- Laboratory data processing
- Clinical trial data
- Manufacturing data
- Supply chain analytics

**Key Features:**
- End-to-end encryption (AES-256)
- PII data masking
- Data quality validation
- Azure Purview for data lineage
- 10-year audit log retention

## Using Templates in AutoGraph

### Via UI

1. Open AutoGraph v3
2. Click "New Diagram" → "From Template"
3. Filter by "Bayer Approved" tag
4. Select desired template
5. Customize for your specific use case

### Via API

```bash
curl https://diagrams.bayer.com/api/templates/bayer-microservices-architecture \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Via Command Palette

1. Press `Cmd+K` (Mac) or `Ctrl+K` (Windows/Linux)
2. Type "template"
3. Select "Create from Bayer Template"
4. Choose template from list

## Compliance Standards

### SOC 2 Type II Requirements

All SOC 2 templates include:
- ✅ Access control mechanisms
- ✅ Encryption at rest (AES-256)
- ✅ Encryption in transit (TLS 1.3)
- ✅ Comprehensive audit logging
- ✅ Change management procedures
- ✅ Incident response workflows

### GxP Requirements

All GxP templates include:
- ✅ 21 CFR Part 11 compliance
- ✅ Electronic signature support
- ✅ Immutable audit trails
- ✅ Data integrity (ALCOA+)
- ✅ 10-year data retention
- ✅ Validation documentation

### GDPR Requirements

All templates with PII handling include:
- ✅ Data minimization
- ✅ Purpose limitation
- ✅ Right to erasure
- ✅ Data portability
- ✅ Consent management
- ✅ EU data residency

## Customization Guidelines

When customizing templates:

1. **Do Not Remove:**
   - Security controls (authentication, encryption)
   - Audit logging mechanisms
   - Network security components

2. **Required Changes:**
   - Replace example service names with actual services
   - Update database names and schemas
   - Customize API endpoints
   - Add environment-specific details

3. **Optional Additions:**
   - Additional services as needed
   - Custom business logic components
   - Environment-specific integrations

4. **Approval Required For:**
   - Removing security components
   - Changing encryption standards
   - Modifying authentication flows
   - External internet access

## Approval Process for Custom Templates

If you need a custom template not covered here:

1. Create diagram in AutoGraph
2. Export as JSON
3. Submit to Bayer Enterprise Architecture team: `ea@bayer.com`
4. Include:
   - Business justification
   - Security assessment
   - Compliance requirements
   - Data classification level

Typical approval timeline: 2-3 weeks

## Security Standards Reference

### Encryption Standards
- **At Rest:** AES-256
- **In Transit:** TLS 1.3
- **Key Management:** Azure Key Vault or AWS KMS

### Authentication Standards
- **Primary:** Azure AD B2C (Bayer SSO)
- **Protocols:** OAuth 2.0, SAML 2.0, OpenID Connect
- **MFA:** Required for production access

### Network Standards
- **VPN:** Required for internal resources
- **Private Link:** Preferred for Azure resources
- **IP Whitelisting:** Bayer corporate IP ranges only

### Logging Standards
- **Retention:** 7 years minimum (10 years for GxP)
- **SIEM:** Splunk or Azure Sentinel
- **Types:** Access, audit, security events, change logs

## Support and Questions

- **Template Questions:** Contact Enterprise Architecture team (`ea@bayer.com`)
- **Security Questions:** Contact IT Security team (`itsecurity@bayer.com`)
- **Compliance Questions:** Contact Compliance Office (`compliance@bayer.com`)
- **AutoGraph Support:** Contact AutoGraph support (`autograph-support@bayer.com`)

## Version History

- **v1.0** (2025-12-24): Initial release with 3 templates
  - Microservices Architecture
  - Secure API Architecture
  - Data Processing Pipeline

## Related Documentation

- [Bayer IT Security Standards v3.2](https://intranet.bayer.com/it-security/standards)
- [Bayer Enterprise Architecture Guidelines](https://intranet.bayer.com/ea/guidelines)
- [GxP Compliance Guide](https://intranet.bayer.com/compliance/gxp)
- [GDPR Implementation Guide](https://intranet.bayer.com/compliance/gdpr)
