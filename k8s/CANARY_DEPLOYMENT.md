# Canary Deployment System

## Overview

The AutoGraph v3 canary deployment system provides zero-downtime deployments with gradual traffic rollout and automatic rollback on errors.

## Architecture

- **Stable Deployment**: Production version serving main traffic
- **Canary Deployment**: New version receiving gradual traffic
- **NGINX Ingress**: Traffic splitting between stable and canary
- **Prometheus**: Metrics collection for monitoring
- **Automatic Rollback**: Triggers on error rate or latency thresholds

## Traffic Rollout Stages

The automated deployment follows these stages:

1. **5%** - Initial canary with minimal traffic
2. **25%** - Quarter of traffic to canary
3. **50%** - Half of traffic to canary
4. **100%** - All traffic to canary

Each stage monitors:
- Error rate (threshold: 5%)
- P95 latency (threshold: 1000ms)
- Duration: 60s per stage

Automatic rollback if thresholds exceeded.

## Commands

### Initialize Canary Deployment

```bash
./k8s/canary-deploy.sh init
```

Creates stable and canary deployments with traffic splitting infrastructure.

### Check Deployment Status

```bash
./k8s/canary-deploy.sh status
```

Shows current deployment state, replica counts, and traffic distribution.

### Deploy New Version (Automated)

```bash
./k8s/canary-deploy.sh deploy v1.2.0
```

Automated gradual rollout with monitoring:
1. Deploys new version to canary
2. Routes 5% traffic
3. Monitors metrics for 60s
4. Increases to 25%, monitors
5. Increases to 50%, monitors
6. Increases to 100%, monitors
7. Prompts to promote to stable

### Set Traffic Percentage (Manual)

```bash
./k8s/canary-deploy.sh traffic 25
```

Manually set canary traffic percentage (0-100).

### Promote Canary to Stable

```bash
./k8s/canary-deploy.sh promote
```

Updates stable deployment with canary version and routes all traffic to stable.

### Rollback Canary

```bash
./k8s/canary-deploy.sh rollback
```

Instant rollback by routing all traffic to stable (< 1 minute).

### Monitor Canary Metrics

```bash
./k8s/canary-deploy.sh monitor
```

Continuously monitor canary metrics.

### Cleanup Canary

```bash
./k8s/canary-deploy.sh cleanup
```

Scale down canary deployment and reset traffic to 0%.

## Monitoring

### Manual Monitoring

```bash
python3 monitor_canary.py --duration 60
```

Monitor for 60 seconds with default thresholds.

### Custom Thresholds

```bash
python3 monitor_canary.py \
  --error-threshold 10 \
  --latency-threshold 2000 \
  --duration 120
```

### Automatic Rollback

```bash
python3 monitor_canary.py --auto-rollback --alert-on-error
```

Automatically trigger rollback if thresholds exceeded.

## Metrics

The system monitors:

- **Error Rate**: HTTP 5xx errors as percentage of total requests
- **P95 Latency**: 95th percentile response time in milliseconds
- **Request Rate**: Requests per second
- **Pod Health**: Liveness and readiness probes

## Rollback

Rollback is instant (< 1 minute) because it only changes the Ingress selector, not pods:

```bash
# Instant traffic switch
kubectl patch ingress api-gateway-ingress-canary -n autograph \
  -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"0"}}}'
```

## Best Practices

1. **Always monitor each stage** - Don't skip monitoring windows
2. **Test in staging first** - Validate deployment process
3. **Set appropriate thresholds** - Based on your SLAs
4. **Keep canary small initially** - Start with 5% traffic
5. **Have rollback ready** - Know the rollback command
6. **Monitor during business hours** - Easy to get help if needed
7. **Document versions** - Track what's deployed where

## Troubleshooting

### Canary pods not starting

```bash
kubectl get pods -n autograph -l version=canary
kubectl describe pod <pod-name> -n autograph
kubectl logs <pod-name> -n autograph
```

### Traffic not splitting

```bash
kubectl get ingress api-gateway-ingress-canary -n autograph -o yaml
```

Check canary annotations are present and weight is > 0.

### Metrics not available

```bash
kubectl get servicemonitor -n autograph
kubectl logs -n monitoring prometheus-0
```

## CI/CD Integration

### GitLab CI Example

```yaml
deploy_canary:
  stage: deploy
  script:
    - ./k8s/canary-deploy.sh deploy $CI_COMMIT_TAG
  only:
    - tags
  when: manual
```

### GitHub Actions Example

```yaml
- name: Deploy Canary
  run: |
    ./k8s/canary-deploy.sh deploy ${{ github.ref_name }}
```

## Comparison with Blue-Green

| Feature | Canary | Blue-Green |
|---------|--------|------------|
| Traffic Rollout | Gradual (5%, 25%, 50%, 100%) | All-or-nothing |
| Resource Usage | 1.5x (stable + small canary) | 2x (full blue + green) |
| Blast Radius | Small (5% initially) | Large (100% on switch) |
| Rollback Speed | Instant | Instant |
| Monitoring | Continuous during rollout | After full switch |
| Risk | Lower | Medium |
| Complexity | Higher | Medium |
| Best For | High-risk changes, large systems | Database migrations, full environment testing |

## Related Features

- Feature #51: Blue-Green Deployment
- Feature #53: Feature Flags
- Feature #54: Load Balancing
- Feature #55: Auto-scaling

## References

- [NGINX Ingress Canary Documentation](https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/annotations/#canary)
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Progressive Delivery](https://www.weave.works/blog/what-is-progressive-delivery-all-about)
