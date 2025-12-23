# AutoGraph v3 - Kubernetes Deployment

This directory contains Kubernetes manifests for deploying AutoGraph v3 to a production Kubernetes cluster.

## Prerequisites

- Kubernetes 1.24+ cluster
- kubectl configured to access the cluster
- NGINX Ingress Controller (for Ingress)
- cert-manager (optional, for TLS certificates)
- Prometheus Operator (optional, for ServiceMonitor)
- StorageClass `standard` available for persistent volumes

## Quick Start

### 1. Create Namespace

```bash
kubectl apply -f namespace.yaml
```

### 2. Create Secrets

**Important:** Replace placeholder values in `secrets.yaml` before applying, or create secrets manually:

```bash
kubectl create secret generic autograph-secrets \
  --from-literal=POSTGRES_PASSWORD='your-secure-password' \
  --from-literal=REDIS_PASSWORD='your-secure-password' \
  --from-literal=MINIO_ROOT_USER='autograph-admin' \
  --from-literal=MINIO_ROOT_PASSWORD='your-secure-password' \
  --from-literal=JWT_SECRET="$(openssl rand -hex 32)" \
  --from-literal=MGA_API_KEY='your-mga-api-key' \
  --from-literal=OPENAI_API_KEY='your-openai-key' \
  --from-literal=ANTHROPIC_API_KEY='your-anthropic-key' \
  --from-literal=GOOGLE_API_KEY='your-google-key' \
  --namespace autograph
```

### 3. Create ConfigMap

```bash
kubectl apply -f configmap.yaml
```

### 4. Deploy Infrastructure Services

```bash
# Create Persistent Volume Claims
kubectl apply -f persistentvolumeclaims.yaml

# Deploy PostgreSQL
kubectl apply -f postgres-deployment.yaml

# Deploy Redis
kubectl apply -f redis-deployment.yaml

# Deploy MinIO
kubectl apply -f minio-deployment.yaml

# Create Infrastructure Services
kubectl apply -f infrastructure-services.yaml

# Wait for infrastructure to be ready
kubectl wait --for=condition=ready pod -l component=postgres -n autograph --timeout=120s
kubectl wait --for=condition=ready pod -l component=redis -n autograph --timeout=120s
kubectl wait --for=condition=ready pod -l component=minio -n autograph --timeout=120s
```

### 5. Initialize Database Schema

```bash
# Port-forward to PostgreSQL
kubectl port-forward -n autograph svc/postgres-service 5432:5432 &

# Run Alembic migrations (from auth-service directory)
cd ../services/auth-service
source venv/bin/activate
alembic upgrade head

# Stop port-forward
pkill -f "port-forward.*postgres"
```

### 6. Deploy Microservices

```bash
# Deploy API Gateway
kubectl apply -f api-gateway-deployment.yaml

# Deploy Auth Service
kubectl apply -f auth-service-deployment.yaml

# Deploy Diagram Service
kubectl apply -f diagram-service-deployment.yaml

# Deploy AI, Collaboration, Git Services
kubectl apply -f ai-collaboration-git-deployments.yaml

# Deploy Export, Integration Hub, SVG Renderer
kubectl apply -f export-integration-svg-deployments.yaml

# Deploy Frontend
kubectl apply -f frontend-deployment.yaml

# Create Microservices Services
kubectl apply -f microservices-services.yaml

# Wait for all services to be ready
kubectl wait --for=condition=ready pod -l app=autograph-v3 -n autograph --timeout=180s
```

### 7. Create Ingress (Optional)

```bash
# Update domain names in ingress.yaml before applying
kubectl apply -f ingress.yaml
```

### 8. Deploy Prometheus ServiceMonitor (Optional)

```bash
# Only if Prometheus Operator is installed
kubectl apply -f servicemonitor.yaml
```

## Verification

### Check All Pods

```bash
kubectl get pods -n autograph
```

Expected output: All pods in `Running` state with 1/1 or 2/2 ready.

### Check All Services

```bash
kubectl get svc -n autograph
```

### Check Resource Limits

```bash
kubectl describe deployment api-gateway -n autograph
```

Verify CPU and memory limits are defined.

### Test Health Endpoints

```bash
# Port-forward to API Gateway
kubectl port-forward -n autograph svc/api-gateway-service 8080:8080

# In another terminal, test health
curl http://localhost:8080/health
```

### Test Metrics Endpoints

```bash
curl http://localhost:8080/metrics
```

### Check Logs

```bash
# API Gateway logs
kubectl logs -n autograph -l component=api-gateway -f

# Auth Service logs
kubectl logs -n autograph -l component=auth-service -f
```

## Rolling Update

To update a service with zero downtime:

```bash
# Update image
kubectl set image deployment/api-gateway \
  api-gateway=autograph/api-gateway:v1.1.0 \
  -n autograph

# Watch rollout
kubectl rollout status deployment/api-gateway -n autograph

# Rollback if needed
kubectl rollout undo deployment/api-gateway -n autograph
```

## Scaling

### Manual Scaling

```bash
# Scale API Gateway to 5 replicas
kubectl scale deployment api-gateway --replicas=5 -n autograph
```

### Horizontal Pod Autoscaling

```bash
kubectl autoscale deployment api-gateway \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n autograph
```

## Troubleshooting

### Pod Not Starting

```bash
# Describe pod for events
kubectl describe pod <pod-name> -n autograph

# Check logs
kubectl logs <pod-name> -n autograph

# Get previous logs (if crashed)
kubectl logs <pod-name> -n autograph --previous
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
kubectl exec -it <api-gateway-pod> -n autograph -- \
  psql postgresql://autograph:password@postgres-service:5432/autograph
```

### Redis Connection Issues

```bash
# Test Redis connection
kubectl exec -it <api-gateway-pod> -n autograph -- \
  redis-cli -h redis-service -p 6379 -a password ping
```

### MinIO Connection Issues

```bash
# Port-forward to MinIO console
kubectl port-forward -n autograph svc/minio-service 9001:9001

# Access at http://localhost:9001
```

## Resource Requirements

### Minimum Cluster Size

- **Nodes:** 3 nodes (for high availability)
- **CPU:** 8 vCPUs total
- **Memory:** 16 GB total
- **Storage:** 40 GB persistent volumes

### Production Recommendations

- **Nodes:** 5+ nodes
- **CPU:** 16+ vCPUs
- **Memory:** 32+ GB
- **Storage:** 100+ GB with fast SSD

## Security Considerations

1. **Secrets Management:** Use Kubernetes Secrets or external secret managers (Vault, AWS Secrets Manager)
2. **Network Policies:** Implement network policies to restrict pod-to-pod communication
3. **RBAC:** Configure Role-Based Access Control for service accounts
4. **Pod Security:** Use Pod Security Standards (restricted)
5. **TLS:** Enable TLS for all external traffic via Ingress
6. **Image Security:** Scan images for vulnerabilities before deployment

## Monitoring

### Prometheus Metrics

All services expose metrics at `/metrics` endpoint:
- Request count, duration, error rate
- Circuit breaker state
- Database connection pool stats
- Redis connection pool stats

### Grafana Dashboards

Import pre-built dashboards for:
- Application overview
- Service performance
- Infrastructure health
- Business metrics

### Logging

All services log to stdout in JSON format. Configure log aggregation with:
- Fluentd/Fluent Bit
- Elasticsearch
- Grafana Loki

## Backup and Restore

### Database Backup

```bash
# Create backup
kubectl exec -n autograph <postgres-pod> -- \
  pg_dump -U autograph autograph > backup.sql

# Restore
kubectl exec -i -n autograph <postgres-pod> -- \
  psql -U autograph autograph < backup.sql
```

### Redis Backup

```bash
# Save snapshot
kubectl exec -n autograph <redis-pod> -- redis-cli -a password SAVE

# Copy snapshot
kubectl cp autograph/<redis-pod>:/data/dump.rdb ./dump.rdb
```

### MinIO Backup

```bash
# Use mc (MinIO Client) to mirror buckets
mc mirror minio-source/diagrams /backup/diagrams
```

## Cost Optimization

1. **Right-size resources:** Monitor actual usage and adjust limits
2. **Use node affinity:** Group similar workloads
3. **Enable cluster autoscaler:** Scale nodes based on demand
4. **Use spot instances:** For non-critical workloads
5. **Optimize storage:** Use appropriate storage classes

## Compliance

- **Audit Logs:** All API calls logged to audit_log table
- **Encryption:** Data encrypted at rest and in transit
- **Data Retention:** Configurable retention policies
- **GDPR:** User data deletion workflows

## Support

For issues or questions:
- Create GitHub issue
- Email: support@autograph.io
- Slack: #autograph-support
