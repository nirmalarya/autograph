# Bayer Custom Domain Configuration

This document describes how to configure AutoGraph v3 to run on a custom Bayer domain (e.g., `diagrams.bayer.com`).

## Overview

AutoGraph v3 supports custom domain configuration for white-label deployment. This allows organizations like Bayer to deploy the application under their own domain name with proper SSL/TLS certificates.

## Prerequisites

- Access to Bayer's DNS management system
- SSL/TLS certificate for `diagrams.bayer.com` (or wildcard `*.bayer.com`)
- Kubernetes cluster or cloud infrastructure (AWS, Azure, GCP)
- Admin access to configure load balancers and ingress controllers

## DNS Configuration

### Step 1: Create DNS Record

Add a DNS record in Bayer's DNS management:

```
Type: A or CNAME
Name: diagrams.bayer.com
Value: [Load Balancer IP or Hostname]
TTL: 300 (5 minutes)
```

For AWS:
```
Type: CNAME
Name: diagrams.bayer.com
Value: autograph-lb-xxxxxxxxxx.eu-central-1.elb.amazonaws.com
TTL: 300
```

For Azure:
```
Type: CNAME
Name: diagrams.bayer.com
Value: autograph-lb.westeurope.cloudapp.azure.com
TTL: 300
```

### Step 2: Verify DNS Propagation

```bash
# Check DNS resolution
nslookup diagrams.bayer.com

# Check with specific DNS server
nslookup diagrams.bayer.com 8.8.8.8

# Test with dig
dig diagrams.bayer.com
```

## SSL/TLS Certificate Configuration

### Option 1: Let's Encrypt (Recommended for Kubernetes)

Use cert-manager for automatic certificate issuance and renewal:

```yaml
# cert-manager/issuer.yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: it-security@bayer.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

### Option 2: Bayer-Managed Certificate

If Bayer provides its own certificate:

```yaml
# Create Kubernetes secret with certificate
apiVersion: v1
kind: Secret
metadata:
  name: bayer-tls-cert
  namespace: autograph
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded-certificate>
  tls.key: <base64-encoded-private-key>
```

## Kubernetes Ingress Configuration

### Update Ingress for Custom Domain

Edit `k8s/ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: autograph-ingress
  namespace: autograph
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    # Bayer-specific security headers
    nginx.ingress.kubernetes.io/configuration-snippet: |
      add_header X-Frame-Options "SAMEORIGIN" always;
      add_header X-Content-Type-Options "nosniff" always;
      add_header X-XSS-Protection "1; mode=block" always;
      add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
spec:
  tls:
  - hosts:
    - diagrams.bayer.com
    secretName: bayer-tls-cert  # Or letsencrypt-generated secret
  rules:
  - host: diagrams.bayer.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8080
```

Apply the configuration:

```bash
kubectl apply -f k8s/ingress.yaml
```

## Environment Variable Configuration

Update frontend environment variables to use custom domain:

### Frontend (.env.production)

```bash
# Custom domain configuration
NEXT_PUBLIC_DOMAIN=diagrams.bayer.com
NEXT_PUBLIC_API_URL=https://diagrams.bayer.com/api
NEXT_PUBLIC_WS_URL=wss://diagrams.bayer.com/ws

# Bayer branding
NEXT_PUBLIC_ENABLE_BAYER_BRANDING=true
NEXT_PUBLIC_BAYER_LOGO_URL=/bayer-logo.svg
NEXT_PUBLIC_BAYER_PRIMARY_COLOR=#00A0E3
NEXT_PUBLIC_BAYER_SECONDARY_COLOR=#0066B2
```

### Backend Services

Update all backend services to allow the custom domain:

```python
# CORS configuration
ALLOWED_ORIGINS = [
    "https://diagrams.bayer.com",
    "http://localhost:3000",  # Development only
]

# Cookie domain
COOKIE_DOMAIN = ".bayer.com"
SESSION_COOKIE_DOMAIN = ".bayer.com"
```

## CORS Configuration (API Gateway)

Update `services/api-gateway/src/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://diagrams.bayer.com",
        "http://localhost:3000",  # Dev only
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## SSO Configuration

Update SAML SSO configuration for custom domain:

### Entity ID

```
https://diagrams.bayer.com/saml/metadata
```

### Assertion Consumer Service (ACS) URL

```
https://diagrams.bayer.com/saml/acs
```

### Single Logout Service (SLS) URL

```
https://diagrams.bayer.com/saml/logout
```

## Testing Custom Domain

### 1. Health Check

```bash
curl https://diagrams.bayer.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "timestamp": "2025-12-24T15:00:00Z"
}
```

### 2. SSL Certificate Verification

```bash
# Check certificate details
openssl s_client -connect diagrams.bayer.com:443 -servername diagrams.bayer.com

# Verify certificate expiration
echo | openssl s_client -servername diagrams.bayer.com -connect diagrams.bayer.com:443 2>/dev/null | openssl x509 -noout -dates
```

### 3. Full Application Test

1. Open browser: `https://diagrams.bayer.com`
2. Verify Bayer branding appears
3. Register/login works
4. Create a diagram
5. Check all API calls use HTTPS

### 4. Security Headers Verification

```bash
curl -I https://diagrams.bayer.com
```

Verify headers include:
- `Strict-Transport-Security`
- `X-Frame-Options`
- `X-Content-Type-Options`
- `X-XSS-Protection`

## Monitoring and Maintenance

### Certificate Renewal

If using Let's Encrypt:
- Certificates auto-renew 30 days before expiration
- Monitor cert-manager logs: `kubectl logs -n cert-manager -l app=cert-manager`

If using Bayer certificate:
- Set calendar reminder 60 days before expiration
- Update secret with new certificate
- Restart ingress controller

### DNS Monitoring

Monitor DNS resolution:

```bash
# Cron job for DNS monitoring
*/5 * * * * nslookup diagrams.bayer.com || echo "DNS resolution failed" | mail -s "DNS Alert" it-ops@bayer.com
```

### Application Health Monitoring

```bash
# Kubernetes liveness probe
livenessProbe:
  httpGet:
    path: /health
    port: 3000
    httpHeaders:
    - name: Host
      value: diagrams.bayer.com
  initialDelaySeconds: 30
  periodSeconds: 10
```

## Rollback Procedure

If issues occur:

1. Update DNS to point back to old domain:
   ```bash
   # Revert DNS record
   aws route53 change-resource-record-sets ...
   ```

2. Revert ingress configuration:
   ```bash
   kubectl rollout undo deployment/autograph-ingress
   ```

3. Clear CDN/cache if applicable

## Support Contacts

- **DNS/Network Issues**: Bayer IT Network Team
- **Certificate Issues**: Bayer IT Security Team
- **Application Issues**: AutoGraph Support Team
- **Kubernetes/Infrastructure**: Bayer Cloud Ops Team

## References

- [Kubernetes Ingress Documentation](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Bayer IT Security Standards](https://intranet.bayer.com/it-security)
