# Blue-Green Deployment for AutoGraph v3

## Overview

Blue-green deployment is a release management strategy that reduces downtime and risk by running two identical production environments called Blue and Green.

## Architecture

- **Blue Environment**: Currently active production environment
- **Green Environment**: New version deployment target
- **Active Service**: Routes traffic to either blue or green

## Key Benefits

1. **Zero Downtime**: Switch traffic instantly between environments
2. **Easy Rollback**: Keep previous version running for instant rollback
3. **Testing in Production**: Test new version with real infrastructure
4. **Gradual Migration**: Support canary deployments (10%, 50%, 100%)

## Deployment Workflow

### Step 1: Deploy to Blue (Initial)
```bash
./blue-green-deploy.sh init
```

This creates:
- Blue deployment (active, 2 replicas)
- Green deployment (inactive, 0 replicas)
- Services for routing traffic

### Step 2: Deploy New Version to Green
```bash
./blue-green-deploy.sh deploy v1.1.0
```

This automatically:
1. Detects blue is active
2. Deploys v1.1.0 to green
3. Scales green to 2 replicas
4. Runs smoke tests
5. Asks for confirmation to switch traffic

### Step 3: Switch Traffic (Canary - Optional)
```bash
./blue-green-deploy.sh switch green 10
```

Route 10% traffic to green for testing (requires Ingress with canary support).

### Step 4: Full Switch
```bash
./blue-green-deploy.sh switch green 100
```

Route all traffic to green environment.

### Step 5: Cleanup (Optional)
```bash
./blue-green-deploy.sh cleanup blue
```

Scale down blue environment to save resources (after confirming green is stable).

## Rollback

If issues detected:
```bash
./blue-green-deploy.sh rollback
```

Instantly switches traffic back to previous environment.

## Monitoring

Check deployment status:
```bash
./blue-green-deploy.sh status
```

Shows:
- Active environment
- Blue deployment status (replicas, version)
- Green deployment status
- Service configuration

## Commands Reference

| Command | Description |
|---------|-------------|
| `init` | Initialize blue-green deployment infrastructure |
| `status` | Show current deployment status |
| `deploy <version>` | Deploy new version (automated workflow) |
| `switch <env> [%]` | Switch traffic to environment (optional canary) |
| `rollback` | Rollback to previous environment |
| `cleanup <env>` | Scale down inactive environment |

## Advanced Features

### Canary Deployments

For gradual rollout with NGINX Ingress:

1. Deploy to green: `./blue-green-deploy.sh deploy v1.1.0`
2. Route 10% traffic: `./blue-green-deploy.sh switch green 10`
3. Monitor metrics (error rate, latency)
4. Increase gradually: 25%, 50%, 75%
5. Full switch: `./blue-green-deploy.sh switch green 100`

### Smoke Tests

The deployment script automatically runs smoke tests:
- Health endpoint check
- HTTP 200 response validation
- Basic functionality verification

### Health Checks

Both deployments have:
- Liveness probe: `/health` endpoint (30s delay, 10s period)
- Readiness probe: `/health` endpoint (10s delay, 5s period)

### Resource Management

Each deployment:
- Requests: 250m CPU, 256Mi memory
- Limits: 1000m CPU, 512Mi memory
- 2 replicas for high availability

## Troubleshooting

### Deployment Stuck
```bash
kubectl describe deployment api-gateway-green -n autograph
kubectl logs -l deployment=green -n autograph
```

### Smoke Tests Failing
```bash
kubectl port-forward -n autograph svc/api-gateway-green-service 8080:8080
curl http://localhost:8080/health
```

### Rollback Not Working
```bash
# Manually switch to previous environment
kubectl patch service api-gateway-service-active -n autograph \
  -p '{"spec":{"selector":{"deployment":"blue"}}}'
```

## Best Practices

1. **Always run smoke tests** before switching traffic
2. **Monitor metrics** during and after switch
3. **Keep previous environment** for at least 1 hour
4. **Have rollback plan** ready
5. **Test rollback** procedure regularly
6. **Automate** the process in CI/CD
7. **Document** each deployment with version and changes

## CI/CD Integration

Example GitLab CI:

```yaml
deploy_production:
  stage: deploy
  script:
    - kubectl config use-context production
    - ./k8s/blue-green-deploy.sh deploy $CI_COMMIT_TAG
  only:
    - tags
  when: manual
```

## Comparison with Rolling Update

| Feature | Blue-Green | Rolling Update |
|---------|------------|----------------|
| Downtime | Zero | Zero |
| Rollback Speed | Instant | Slow |
| Resource Usage | 2x (during switch) | 1.5x (during update) |
| Testing | Full environment | Gradual pods |
| Complexity | Higher | Lower |

## When to Use

**Use Blue-Green when:**
- Zero downtime is critical
- Instant rollback is required
- Testing new version in production environment
- Major version changes

**Use Rolling Update when:**
- Resource constraints (can't run 2 environments)
- Minor updates (patches, config changes)
- Gradual rollout is acceptable

## Related Features

- Feature #52: Canary Deployment
- Feature #53: Feature Flags
- Feature #54: Load Balancing
- Feature #55: Auto-scaling

## References

- [Martin Fowler - BlueGreenDeployment](https://martinfowler.com/bliki/BlueGreenDeployment.html)
- [Kubernetes Deployment Strategies](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
