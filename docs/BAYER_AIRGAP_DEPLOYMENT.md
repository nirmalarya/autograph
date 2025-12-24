# AutoGraph v3: On-Premises Air-Gapped Deployment Guide

## Overview

This guide describes how to deploy AutoGraph v3 in an air-gapped (disconnected) on-premises environment where there is no internet connectivity. This deployment model is suitable for:

- High-security Bayer facilities
- Research laboratories with sensitive data
- Manufacturing plants with OT networks
- Regulatory compliance requirements (21 CFR Part 11, GxP)

## Air-Gapped Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Air-Gapped Environment                    │
│                   (No Internet Connectivity)                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐  │
│  │   User       │──────│   Internal   │──────│ AutoGraph │  │
│  │ Workstation  │      │   Firewall   │      │  Cluster  │  │
│  └──────────────┘      └──────────────┘      └───────────┘  │
│                                                      │        │
│                        ┌─────────────────────────────┘        │
│                        │                                      │
│  ┌──────────────┬──────┴────┬──────────────┬──────────────┐  │
│  │  PostgreSQL  │   Redis   │    MinIO     │  Services    │  │
│  │   Database   │   Cache   │   Storage    │  (8 nodes)   │  │
│  └──────────────┴───────────┴──────────────┴──────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │             Offline Package Repository                   │ │
│  │  (Docker registry, npm/pip mirrors, OS packages)        │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Hardware Requirements

#### Minimum Configuration (Small deployment, < 50 users)

- **Application Nodes**: 3 servers
  - CPU: 8 cores
  - RAM: 32 GB
  - Disk: 500 GB SSD
  
- **Database Server**: 1 server
  - CPU: 16 cores
  - RAM: 64 GB
  - Disk: 2 TB SSD (RAID 10)
  
- **Storage Server**: 1 server
  - CPU: 4 cores
  - RAM: 16 GB
  - Disk: 10 TB HDD (RAID 6)

#### Recommended Configuration (Medium deployment, 50-500 users)

- **Application Nodes**: 6 servers
  - CPU: 16 cores
  - RAM: 64 GB
  - Disk: 1 TB NVMe SSD
  
- **Database Cluster**: 3 servers
  - CPU: 32 cores
  - RAM: 128 GB
  - Disk: 4 TB NVMe SSD (RAID 10)
  
- **Storage Cluster**: 3 servers
  - CPU: 8 cores
  - RAM: 32 GB
  - Disk: 20 TB SAS HDD (RAID 6)

### Software Requirements

- **Operating System**: RHEL 8/9, Ubuntu 22.04 LTS, or SLES 15
- **Container Runtime**: Docker 24.0+ or containerd 1.7+
- **Orchestration**: Kubernetes 1.28+ or Docker Swarm
- **Load Balancer**: HAProxy 2.8+ or NGINX Plus
- **Monitoring**: Prometheus + Grafana (bundled)

### Network Requirements

- Internal network: 10 Gbps minimum
- DNS server (internal)
- NTP server (internal) for time synchronization
- Backup network (1 Gbps) for data replication

## Installation Process

### Phase 1: Prepare Installation Media

On a machine with internet access, download all required packages:

```bash
#!/bin/bash
# Download AutoGraph air-gapped installation bundle

# 1. Clone repository
git clone --depth 1 https://github.com/bayer/autograph-v3.git
cd autograph-v3

# 2. Download Docker images
./scripts/airgap/pull-images.sh

# 3. Download OS packages
./scripts/airgap/download-packages.sh --os rhel8

# 4. Download npm/pip dependencies
./scripts/airgap/download-dependencies.sh

# 5. Create installation bundle
./scripts/airgap/create-bundle.sh

# Result: autograph-v3-airgap-bundle-20251224.tar.gz (approx 15 GB)
```

Transfer the bundle to air-gapped environment via:
- USB drive (encrypted)
- Secure file transfer (during maintenance window)
- Physical media (DVD)

### Phase 2: Setup Internal Package Repositories

On the air-gapped network, set up local package mirrors:

```bash
# Extract installation bundle
tar -xzf autograph-v3-airgap-bundle-20251224.tar.gz
cd autograph-v3-airgap

# 1. Setup Docker Registry
./setup-registry.sh
# Registry will be available at: registry.internal.bayer.com:5000

# 2. Setup NPM Registry (Verdaccio)
./setup-npm-registry.sh
# NPM registry: npm.internal.bayer.com

# 3. Setup PyPI Mirror (devpi)
./setup-pypi-mirror.sh
# PyPI mirror: pypi.internal.bayer.com

# 4. Setup OS Package Repository
./setup-yum-repo.sh   # For RHEL
# or
./setup-apt-repo.sh   # For Ubuntu
```

### Phase 3: Deploy Kubernetes Cluster

```bash
# 1. Initialize master node
sudo kubeadm init --pod-network-cidr=10.244.0.0/16 \
  --image-repository=registry.internal.bayer.com:5000

# 2. Install CNI plugin (Calico or Flannel)
kubectl apply -f airgap/calico-airgap.yaml

# 3. Join worker nodes
# On each worker node:
sudo kubeadm join <master-ip>:6443 --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash>

# 4. Verify cluster
kubectl get nodes
# All nodes should show "Ready"
```

### Phase 4: Deploy Infrastructure Services

```bash
# 1. Create namespace
kubectl create namespace autograph

# 2. Deploy PostgreSQL
kubectl apply -f k8s/airgap/postgresql.yaml

# 3. Deploy Redis
kubectl apply -f k8s/airgap/redis.yaml

# 4. Deploy MinIO
kubectl apply -f k8s/airgap/minio.yaml

# 5. Verify infrastructure
kubectl get pods -n autograph
# All pods should show "Running"
```

### Phase 5: Initialize Database

```bash
# 1. Copy database schema to PostgreSQL pod
kubectl cp database/schema.sql autograph/postgresql-0:/tmp/

# 2. Initialize database
kubectl exec -n autograph postgresql-0 -- psql -U autograph -d autograph -f /tmp/schema.sql

# 3. Run migrations
kubectl exec -n autograph postgresql-0 -- python manage.py migrate

# 4. Create initial admin user
kubectl exec -n autograph postgresql-0 -- python manage.py createsuperuser \
  --email admin@bayer.com --password <secure-password>
```

### Phase 6: Deploy AutoGraph Services

```bash
# 1. Create ConfigMaps
kubectl create configmap autograph-config \
  --from-file=config/production.yaml \
  -n autograph

# 2. Create Secrets
kubectl create secret generic autograph-secrets \
  --from-literal=database-password=<db-password> \
  --from-literal=jwt-secret=<jwt-secret> \
  --from-literal=minio-access-key=<minio-key> \
  --from-literal=minio-secret-key=<minio-secret> \
  -n autograph

# 3. Deploy services
kubectl apply -f k8s/airgap/frontend.yaml
kubectl apply -f k8s/airgap/api-gateway.yaml
kubectl apply -f k8s/airgap/auth-service.yaml
kubectl apply -f k8s/airgap/diagram-service.yaml
kubectl apply -f k8s/airgap/collaboration-service.yaml
kubectl apply -f k8s/airgap/ai-service.yaml
kubectl apply -f k8s/airgap/export-service.yaml
kubectl apply -f k8s/airgap/git-service.yaml

# 4. Deploy ingress
kubectl apply -f k8s/airgap/ingress.yaml

# 5. Verify deployment
kubectl get pods -n autograph
# All pods should show "Running"
```

## Configuration

### Environment Variables (Air-Gapped)

```bash
# No external API access
EXTERNAL_API_ENABLED=false

# Local service endpoints
POSTGRES_HOST=postgresql.autograph.svc.cluster.local
REDIS_HOST=redis.autograph.svc.cluster.local
MINIO_HOST=minio.autograph.svc.cluster.local

# AI Service Configuration (Offline mode)
AI_PROVIDER=offline  # No external LLM calls
AI_OFFLINE_MODELS_PATH=/models/llama2-7b

# No telemetry or analytics
TELEMETRY_ENABLED=false
ANALYTICS_ENABLED=false

# Local time server
NTP_SERVER=ntp.internal.bayer.com

# Local DNS
DNS_SERVER=dns.internal.bayer.com
```

### SSL/TLS Certificates

For air-gapped deployment, use internal CA:

```bash
# 1. Generate internal CA
./scripts/generate-ca.sh

# 2. Generate server certificates
./scripts/generate-cert.sh --domain autograph.internal.bayer.com

# 3. Deploy certificates
kubectl create secret tls autograph-tls \
  --cert=certs/server.crt \
  --key=certs/server.key \
  -n autograph

# 4. Distribute CA certificate to all user workstations
# Users must import ca.crt to their trust store
```

## AI Services (Offline Mode)

Since air-gapped environments have no internet access, AI features require local models:

### Option 1: Disable AI Features

```yaml
# config/airgap.yaml
ai:
  enabled: false
```

### Option 2: Deploy Local LLM

```bash
# 1. Download Llama 2 model (on internet-connected machine)
wget https://huggingface.co/meta-llama/Llama-2-7b/resolve/main/model.safetensors

# 2. Transfer to air-gapped environment

# 3. Deploy local LLM server
kubectl apply -f k8s/airgap/llm-server.yaml

# 4. Configure AI service to use local LLM
AI_PROVIDER=local
AI_LOCAL_ENDPOINT=http://llm-server.autograph.svc.cluster.local:8000
```

## Updates and Maintenance

### Updating AutoGraph

```bash
# 1. Download new version (on internet-connected machine)
git pull origin main
./scripts/airgap/create-bundle.sh --version 3.1.0

# 2. Transfer new bundle to air-gapped environment

# 3. Extract and upload images
tar -xzf autograph-v3-airgap-bundle-20251225.tar.gz
./scripts/upload-images.sh --registry registry.internal.bayer.com:5000

# 4. Update deployment
kubectl set image deployment/frontend \
  frontend=registry.internal.bayer.com:5000/autograph/frontend:3.1.0 \
  -n autograph

# 5. Rolling update
kubectl rollout status deployment/frontend -n autograph
```

### Patching Security Vulnerabilities

```bash
# 1. Download security patches (on internet-connected machine)
./scripts/airgap/download-security-patches.sh

# 2. Transfer patches to air-gapped environment

# 3. Apply patches
./scripts/apply-patches.sh

# 4. Restart affected services
kubectl rollout restart deployment/api-gateway -n autograph
```

## Backup and Disaster Recovery

### Backup Strategy

```bash
# 1. Backup database (daily)
kubectl exec -n autograph postgresql-0 -- \
  pg_dump -U autograph autograph > backup-$(date +%Y%m%d).sql

# 2. Backup MinIO data (daily)
mc mirror minio-local/diagrams /backup/minio/diagrams

# 3. Backup Kubernetes manifests (weekly)
kubectl get all -n autograph -o yaml > k8s-backup-$(date +%Y%m%d).yaml

# 4. Store backups on separate storage (tape, NAS, secondary datacenter)
```

### Disaster Recovery

```bash
# 1. Restore database
kubectl exec -n autograph postgresql-0 -- \
  psql -U autograph autograph < backup-20251224.sql

# 2. Restore MinIO data
mc mirror /backup/minio/diagrams minio-local/diagrams

# 3. Verify data integrity
./scripts/verify-data-integrity.sh
```

## Monitoring (Offline)

Deploy on-premises monitoring stack:

```bash
# 1. Deploy Prometheus
kubectl apply -f k8s/airgap/prometheus.yaml

# 2. Deploy Grafana
kubectl apply -f k8s/airgap/grafana.yaml

# 3. Deploy Alertmanager
kubectl apply -f k8s/airgap/alertmanager.yaml

# 4. Access Grafana
kubectl port-forward -n autograph svc/grafana 3001:3000
# Open: http://localhost:3001 (admin/admin)
```

## Compliance

### Audit Logging

In air-gapped environments, logs are stored locally:

```bash
# Configure local log storage
LOG_RETENTION_DAYS=2555  # 7 years for SOC2
LOG_STORAGE_PATH=/var/log/autograph
LOG_ARCHIVE_ENABLED=true
LOG_ARCHIVE_PATH=/backup/logs
```

### GxP Validation

For pharmaceutical environments requiring 21 CFR Part 11:

```bash
# Enable GxP mode
GXP_ENABLED=true
GXP_VALIDATION_LEVEL=strict
GXP_AUDIT_RETENTION_DAYS=3650  # 10 years
GXP_ELECTRONIC_SIGNATURES=true
```

## Troubleshooting

### Cannot Pull Docker Images

**Problem**: Image pull fails

**Solution**: Verify local registry

```bash
# Test registry connectivity
curl https://registry.internal.bayer.com:5000/v2/_catalog

# Re-upload images if needed
./scripts/upload-images.sh
```

### Time Synchronization Issues

**Problem**: Certificate validation fails due to time mismatch

**Solution**: Configure NTP

```bash
# On all nodes
sudo systemctl enable chronyd
sudo systemctl start chronyd

# Verify time sync
chronyc tracking
```

### Services Cannot Resolve DNS

**Problem**: Services fail with "host not found" errors

**Solution**: Configure CoreDNS

```yaml
# Edit CoreDNS config
kubectl edit configmap coredns -n kube-system

# Add forwarding to internal DNS
forward . dns.internal.bayer.com
```

## Support

For air-gapped deployment support:
- **Installation**: autograph-onprem@bayer.com
- **Updates**: autograph-airgap@bayer.com
- **Security**: itsecurity@bayer.com

## Appendix

### Bill of Materials (BOM)

Complete list of packages included in air-gapped bundle:

```
Docker Images (15 GB):
- autograph/frontend:3.0.0
- autograph/api-gateway:3.0.0
- autograph/auth-service:3.0.0
- autograph/diagram-service:3.0.0
- autograph/collaboration-service:3.0.0
- autograph/ai-service:3.0.0
- autograph/export-service:3.0.0
- autograph/git-service:3.0.0
- autograph/svg-renderer:3.0.0
- postgres:16.6
- redis:7.4.1
- minio/minio:latest
- nginx:1.25
- prometheus/prometheus:latest
- grafana/grafana:latest

OS Packages (2 GB):
- kubernetes-1.28.x
- docker-ce-24.0.x
- haproxy-2.8.x
- (see full list in packages.txt)

Application Dependencies (1 GB):
- NPM packages (3000+)
- Python packages (500+)
- (see full list in dependencies.txt)
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-24  
**Classification**: Bayer Internal  
**Approved By**: Bayer IT Security Team
