# AutoGraph v3: BYOC (Bring Your Own Cloud) Deployment Guide for Bayer

## Overview

This guide describes how to deploy AutoGraph v3 in Bayer's own cloud accounts (AWS or Azure) for maximum control, compliance, and data sovereignty.

**BYOC Benefits:**
- Bayer owns and controls all infrastructure
- Data never leaves Bayer's cloud environment
- Full visibility into costs and usage
- Compliance with Bayer data residency requirements
- Integration with existing Bayer cloud services

## Supported Cloud Providers

- **Amazon Web Services (AWS)** - Recommended for global deployments
- **Microsoft Azure** - Recommended for Europe, integrated with Azure AD
- **Google Cloud Platform (GCP)** - Available on request

## Prerequisites

### AWS Account Setup

```
AWS Account: Bayer Production
Account ID: 123456789012
Region: eu-central-1 (Frankfurt) - Primary
         eu-west-1 (Ireland) - DR
Admin Role: arn:aws:iam::123456789012:role/BayerCloudAdmin
```

### Azure Subscription Setup

```
Subscription: Bayer Production
Subscription ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Resource Group: autograph-prod-rg
Location: West Europe - Primary
          North Europe - DR
Admin: cloudadmin@bayer.com
```

### Required Permissions

**AWS IAM Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:*",
        "ec2:*",
        "rds:*",
        "elasticache:*",
        "s3:*",
        "cloudwatch:*",
        "logs:*",
        "iam:CreateRole",
        "iam:AttachRolePolicy"
      ],
      "Resource": "*"
    }
  ]
}
```

**Azure RBAC Role:**
- Owner or Contributor role on subscription
- Or custom role with permissions for:
  - AKS, Virtual Machines, Databases, Storage, Networking, Monitoring

## Architecture

### AWS Deployment Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Bayer AWS Account                            │
│                   (eu-central-1)                                │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               VPC (10.0.0.0/16)                          │  │
│  │                                                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐     │  │
│  │  │  Public     │  │  Private    │  │  Database    │     │  │
│  │  │  Subnet     │  │  Subnet     │  │  Subnet      │     │  │
│  │  │  (10.0.1.0) │  │  (10.0.2.0) │  │  (10.0.3.0)  │     │  │
│  │  └─────────────┘  └─────────────┘  └──────────────┘     │  │
│  │        │                 │                   │           │  │
│  │  [ALB/NLB]         [EKS Cluster]      [RDS Postgres]    │  │
│  │     ↓                    ↓                   ↓           │  │
│  │  Internet          AutoGraph          [ElastiCache]     │  │
│  │   Gateway           Services            Redis          │  │
│  │                          ↓                               │  │
│  │                     [S3 Buckets]                        │  │
│  │                  (diagrams, exports)                    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            Shared Services                             │    │
│  │  - CloudWatch (Logging & Monitoring)                   │    │
│  │  - AWS Secrets Manager                                 │    │
│  │  - AWS KMS (Encryption Keys)                           │    │
│  │  - AWS WAF (Web Application Firewall)                  │    │
│  │  - AWS Shield (DDoS Protection)                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Azure Deployment Architecture

```
┌────────────────────────────────────────────────────────────────┐
│              Bayer Azure Subscription                           │
│                 (West Europe)                                   │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Resource Group: autograph-prod-rg                │  │
│  │                                                            │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │  VNet (10.0.0.0/16)                                 │ │  │
│  │  │                                                       │ │  │
│  │  │  ┌──────────┐  ┌────────────┐  ┌──────────────┐    │ │  │
│  │  │  │  Public  │  │  Private   │  │  Database    │    │ │  │
│  │  │  │  Subnet  │  │  Subnet    │  │  Subnet      │    │ │  │
│  │  │  └──────────┘  └────────────┘  └──────────────┘    │ │  │
│  │  │       │              │                  │           │ │  │
│  │  │  [App Gw]      [AKS Cluster]    [Azure DB PG]      │ │  │
│  │  │       ↓              ↓                  ↓           │ │  │
│  │  │   Internet      AutoGraph        [Azure Cache]     │ │  │
│  │  │                  Services          Redis           │ │  │
│  │  │                      ↓                              │ │  │
│  │  │              [Azure Blob Storage]                  │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            Shared Services                             │    │
│  │  - Azure Monitor (Logging & Monitoring)                │    │
│  │  - Azure Key Vault (Secrets & Keys)                    │    │
│  │  - Azure Front Door (WAF & CDN)                        │    │
│  │  - Azure Sentinel (SIEM)                               │    │
│  │  - Azure AD (Authentication)                           │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Methods

### Method 1: Terraform (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/bayer/autograph-v3-infrastructure.git
cd autograph-v3-infrastructure/terraform

# 2. Configure Bayer AWS/Azure credentials
export AWS_PROFILE=bayer-production
# or
az login --tenant bayer.onmicrosoft.com

# 3. Initialize Terraform
terraform init

# 4. Create terraform.tfvars for Bayer
cat > terraform.tfvars <<EOF
environment = "production"
region = "eu-central-1"  # AWS
# or location = "westeurope"  # Azure

bayer_account_id = "123456789012"
bayer_vpc_cidr = "10.0.0.0/16"
bayer_data_residency = "eu"

# Cluster configuration
cluster_name = "autograph-prod"
node_count = 6
node_instance_type = "t3.2xlarge"  # AWS
# or node_vm_size = "Standard_D8s_v3"  # Azure

# Database configuration
db_instance_class = "db.r6g.2xlarge"  # AWS
db_multi_az = true
db_backup_retention_days = 30

# Storage configuration
storage_class = "S3_INTELLIGENT_TIERING"  # AWS
storage_replication = "ZRS"  # Azure (Zone-Redundant)

# Bayer-specific tags
tags = {
  Environment = "Production"
  CostCenter = "CC-12345"
  Project = "AutoGraph"
  Owner = "cloudops@bayer.com"
  Compliance = "SOC2,GDPR,GxP"
}
EOF

# 5. Plan deployment
terraform plan -out=plan.tfplan

# 6. Apply (deploy infrastructure)
terraform apply plan.tfplan

# Output will include:
# - Cluster endpoint
# - Database endpoint
# - Load balancer DNS
# - S3 bucket names
```

### Method 2: CloudFormation (AWS) / ARM Templates (Azure)

```bash
# AWS CloudFormation
aws cloudformation create-stack \
  --stack-name autograph-prod \
  --template-body file://cloudformation/autograph-complete.yaml \
  --parameters file://parameters-bayer.json \
  --capabilities CAPABILITY_IAM

# Azure ARM Template
az deployment group create \
  --resource-group autograph-prod-rg \
  --template-file arm/autograph-complete.json \
  --parameters @parameters-bayer.json
```

### Method 3: Manual Deployment

See detailed manual deployment guide in MANUAL_DEPLOYMENT.md

## Post-Deployment Configuration

### 1. Configure DNS

**AWS Route 53:**
```bash
# Create hosted zone
aws route53 create-hosted-zone \
  --name diagrams.bayer.com \
  --caller-reference $(date +%s)

# Create A record pointing to load balancer
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789ABC \
  --change-batch file://route53-record.json
```

**Azure DNS:**
```bash
# Create DNS zone
az network dns zone create \
  --resource-group autograph-prod-rg \
  --name diagrams.bayer.com

# Create A record
az network dns record-set a add-record \
  --resource-group autograph-prod-rg \
  --zone-name diagrams.bayer.com \
  --record-set-name @ \
  --ipv4-address <load-balancer-ip>
```

### 2. Configure SSL/TLS

**AWS Certificate Manager:**
```bash
# Request certificate
aws acm request-certificate \
  --domain-name diagrams.bayer.com \
  --subject-alternative-names *.diagrams.bayer.com \
  --validation-method DNS

# Verify domain ownership via DNS
```

**Azure Key Vault:**
```bash
# Import Bayer certificate
az keyvault certificate import \
  --vault-name autograph-keyvault \
  --name diagrams-bayer-com \
  --file bayer-wildcard.pfx
```

### 3. Integrate with Bayer Azure AD

```bash
# Register application in Azure AD
az ad app create \
  --display-name "AutoGraph Production" \
  --homepage "https://diagrams.bayer.com" \
  --reply-urls "https://diagrams.bayer.com/auth/callback"

# Configure SSO
# Update auth-service configuration with:
AZURE_AD_TENANT_ID=<bayer-tenant-id>
AZURE_AD_CLIENT_ID=<app-client-id>
AZURE_AD_CLIENT_SECRET=<app-secret>
```

### 4. Configure Logging

**AWS CloudWatch:**
```bash
# Create log group
aws logs create-log-group --log-group-name /autograph/prod

# Configure log retention
aws logs put-retention-policy \
  --log-group-name /autograph/prod \
  --retention-in-days 2555  # 7 years
```

**Azure Monitor:**
```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group autograph-prod-rg \
  --workspace-name autograph-logs \
  --retention-time 2555  # 7 years
```

## Cost Management

### AWS Cost Breakdown (Estimated Monthly)

| Service | Configuration | Monthly Cost (EUR) |
|---------|--------------|-------------------|
| EKS Cluster | 6 t3.2xlarge nodes | €900 |
| RDS PostgreSQL | db.r6g.2xlarge, Multi-AZ | €1,200 |
| ElastiCache Redis | cache.r6g.large | €300 |
| S3 Storage | 10 TB | €230 |
| Data Transfer | 5 TB/month | €450 |
| CloudWatch Logs | 500 GB | €250 |
| Load Balancer | ALB | €25 |
| **Total** | | **€3,355/month** |

### Azure Cost Breakdown (Estimated Monthly)

| Service | Configuration | Monthly Cost (EUR) |
|---------|--------------|-------------------|
| AKS Cluster | 6 Standard_D8s_v3 nodes | €1,100 |
| Azure DB PostgreSQL | 16 vCores, HA | €1,500 |
| Azure Cache Redis | P2 Premium | €400 |
| Blob Storage | 10 TB, Hot tier | €200 |
| Data Transfer | 5 TB/month | €500 |
| Azure Monitor | 500 GB | €300 |
| Application Gateway | Standard_v2 | €150 |
| **Total** | | **€4,150/month** |

### Cost Optimization

```bash
# 1. Enable auto-scaling
kubectl autoscale deployment frontend \
  --min=3 --max=10 --cpu-percent=70

# 2. Use Spot/Reserved Instances
# AWS Spot Instances: 70% savings
# Azure Spot VMs: 80% savings

# 3. Use storage lifecycle policies
# Move inactive data to archive tier after 90 days

# 4. Enable compression
# Reduce S3/Blob storage by 60%

# Expected savings: 40-50% reduction
```

## Security Hardening

### 1. Network Security

**AWS Security Groups:**
```bash
# Allow only Bayer corporate IPs
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 10.0.0.0/8  # Bayer internal
```

**Azure Network Security Groups:**
```bash
# Create NSG rule
az network nsg rule create \
  --resource-group autograph-prod-rg \
  --nsg-name autograph-nsg \
  --name AllowBayerCorporate \
  --priority 100 \
  --source-address-prefixes 10.0.0.0/8 \
  --destination-port-ranges 443 \
  --access Allow
```

### 2. Encryption

**AWS:**
- EBS encryption with KMS (all volumes)
- S3 encryption at rest (SSE-KMS)
- RDS encryption with KMS
- TLS 1.3 in transit

**Azure:**
- Managed disk encryption
- Blob Storage encryption (Microsoft-managed keys)
- Azure Database encryption
- TLS 1.3 in transit

### 3. IAM/RBAC

```bash
# AWS - Least privilege IAM policies
# Azure - RBAC with custom roles

# Example: Database admin role (no production data access)
az role definition create --role-definition '{
  "Name": "AutoGraph Database Admin",
  "Description": "Can manage database but not access data",
  "Actions": [
    "Microsoft.DBforPostgreSQL/servers/configurations/write",
    "Microsoft.DBforPostgreSQL/servers/restart/action"
  ],
  "NotActions": [
    "Microsoft.DBforPostgreSQL/servers/databases/read"
  ]
}'
```

## Monitoring and Alerts

### CloudWatch Alarms (AWS)

```bash
# High CPU alert
aws cloudwatch put-metric-alarm \
  --alarm-name autograph-high-cpu \
  --alarm-description "AutoGraph CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EKS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:eu-central-1:123456789012:bayer-ops-alerts
```

### Azure Monitor Alerts

```bash
# Create action group
az monitor action-group create \
  --name bayer-ops-alerts \
  --resource-group autograph-prod-rg \
  --short-name BayerOps \
  --email-receiver name=ops email=cloudops@bayer.com

# Create alert rule
az monitor metrics alert create \
  --name autograph-high-cpu \
  --resource-group autograph-prod-rg \
  --scopes /subscriptions/.../resourceGroups/autograph-prod-rg/providers/Microsoft.Compute/virtualMachines/autograph-vm-1 \
  --condition "avg Percentage CPU > 80" \
  --action bayer-ops-alerts
```

## Backup and DR

### Backup Strategy

**AWS:**
```bash
# RDS automated backups
aws rds modify-db-instance \
  --db-instance-identifier autograph-prod \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00"

# S3 versioning and lifecycle
aws s3api put-bucket-versioning \
  --bucket autograph-diagrams \
  --versioning-configuration Status=Enabled
```

**Azure:**
```bash
# Azure Database backup
az postgres server update \
  --resource-group autograph-prod-rg \
  --name autograph-postgres \
  --backup-retention 30

# Blob soft delete
az storage account blob-service-properties update \
  --account-name autographstorage \
  --enable-delete-retention true \
  --delete-retention-days 30
```

### Disaster Recovery (Cross-Region)

```bash
# AWS - Setup DR in eu-west-1 (Ireland)
terraform apply -var="region=eu-west-1" -var="environment=dr"

# Azure - Setup DR in North Europe
az group create --name autograph-dr-rg --location northeurope
terraform apply -var="location=northeurope" -var="environment=dr"

# Configure replication
# RTO: 4 hours
# RPO: 15 minutes
```

## Compliance

### SOC 2 Requirements

- ✅ Encryption at rest and in transit
- ✅ Access logging (CloudTrail/Activity Log)
- ✅ Multi-factor authentication
- ✅ Backup and disaster recovery
- ✅ Network segmentation

### GDPR Requirements

- ✅ Data residency (EU regions only)
- ✅ Right to erasure
- ✅ Data portability
- ✅ Breach notification (via Azure Sentinel/CloudWatch)

### GxP Requirements

- ✅ 10-year data retention
- ✅ Audit trail
- ✅ Electronic signatures
- ✅ Change control

## Support

| Issue | Contact |
|-------|---------|
| AWS Issues | aws-support@bayer.com |
| Azure Issues | azure-support@bayer.com |
| AutoGraph Issues | autograph-support@bayer.com |
| Cost Optimization | cloudfinops@bayer.com |
| Security | itsecurity@bayer.com |

## Appendix

### Terraform Modules

- `modules/aws/eks` - EKS cluster
- `modules/aws/rds` - PostgreSQL database
- `modules/aws/s3` - S3 buckets
- `modules/azure/aks` - AKS cluster
- `modules/azure/postgres` - Azure Database
- `modules/azure/storage` - Blob storage

### Cost Calculator

Use online calculator:
- AWS: https://calculator.aws
- Azure: https://azure.microsoft.com/pricing/calculator

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-24  
**Classification**: Bayer Confidential  
**Approved By**: Bayer Cloud Architecture Team
