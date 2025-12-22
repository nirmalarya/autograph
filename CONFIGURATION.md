# AutoGraph v3 - Configuration Guide

## Overview

AutoGraph v3 supports environment-based configuration for local development, Docker Compose, and Kubernetes deployments. Configuration is loaded from environment-specific `.env` files and can be overridden by OS environment variables.

## Configuration Files

- `.env.local` - Local development (localhost connections)
- `.env.docker` - Docker Compose (Docker network hostnames)
- `.env.kubernetes` - Kubernetes (service discovery, secrets from environment)
- `.env` - Base configuration (fallback values)

## Usage

### Programmatic Configuration

```python
from shared.python.config import get_config

# Load configuration for current environment
config = get_config()  # Uses ENV environment variable or defaults to 'local'

# Or specify environment explicitly
config = get_config("docker")

# Access configuration
postgres_host = config.get('POSTGRES_HOST')
database_url = config.database_url  # Automatically constructed
redis_url = config.redis_url

# Check environment
if config.is_local:
    print("Running in local development")
elif config.is_docker:
    print("Running in Docker")
elif config.is_kubernetes:
    print("Running in Kubernetes")
```

### Configuration Properties

```python
# Basic getters
config.get('KEY', 'default')          # Get string value
config.get_int('PORT', 8080)          # Get integer value
config.get_bool('DEBUG', False)       # Get boolean value

# Computed properties
config.database_url                    # PostgreSQL connection URL
config.redis_url                       # Redis connection URL
config.env                             # Current environment name
config.is_local                        # True if ENV=local
config.is_docker                       # True if ENV=docker
config.is_kubernetes                   # True if ENV=kubernetes
config.is_production                   # True if docker or kubernetes
```

## Environment Priority

Configuration is loaded in this order (highest to lowest priority):

1. **OS Environment Variables** - Highest priority
2. **Environment-specific .env file** - `.env.{ENV}`
3. **Base .env file** - Lowest priority (fallback values)

Example:
```bash
# Set environment variable (takes precedence)
export POSTGRES_HOST=custom-host

# Start service
python main.py

# POSTGRES_HOST will be "custom-host" regardless of .env files
```

## Local Development

Set `ENV=local` or leave unset (defaults to local):

```bash
export ENV=local
python main.py
```

Configuration:
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- MinIO: `localhost:9000`
- Services connect to localhost

## Docker Compose

Set `ENV=docker`:

```bash
export ENV=docker
python main.py
```

Or in `docker-compose.yml`:
```yaml
services:
  api-gateway:
    environment:
      - ENV=docker
```

Configuration:
- PostgreSQL: `postgres:5432` (Docker service name)
- Redis: `redis:6379`
- MinIO: `minio:9000`
- Services connect via Docker network

## Kubernetes

Set `ENV=kubernetes`:

```bash
export ENV=kubernetes
python main.py
```

Or in Kubernetes deployment:
```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: api-gateway
        env:
        - name: ENV
          value: "kubernetes"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: jwt-secret
              key: secret
```

Configuration:
- PostgreSQL: `postgres-service.autograph.svc.cluster.local:5432`
- Redis: `redis-service.autograph.svc.cluster.local:6379`
- MinIO: `minio-service.autograph.svc.cluster.local:9000`
- Secrets loaded from Kubernetes Secrets via environment variables
- Services connect via Kubernetes service discovery

## Secrets Management

### Local Development
Secrets in `.env.local` file (not committed to git):
```env
JWT_SECRET=dev-secret-key
POSTGRES_PASSWORD=dev-password
```

### Docker Compose
Secrets in `.env.docker` or Docker secrets:
```yaml
services:
  api-gateway:
    environment:
      - JWT_SECRET=${JWT_SECRET}
    secrets:
      - jwt_secret
```

### Kubernetes
Secrets from Kubernetes Secrets:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: autograph-secrets
type: Opaque
data:
  jwt-secret: <base64-encoded-secret>
  postgres-password: <base64-encoded-password>
```

Then reference in deployment:
```yaml
env:
- name: JWT_SECRET
  valueFrom:
    secretKeyRef:
      name: autograph-secrets
      key: jwt-secret
```

## Validation

Configuration is validated on startup. Required variables:
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `REDIS_HOST`
- `REDIS_PORT`
- `JWT_SECRET`

If any required variable is missing, the service will fail to start with a clear error message.

## Adding New Configuration

1. Add to all `.env.{environment}` files
2. Document in this guide
3. If required, add to `_validate_required()` in `config.py`

Example:
```python
# In config.py
def _validate_required(self):
    required = [
        # ... existing ...
        "NEW_REQUIRED_VAR",
    ]
```

## Troubleshooting

### "Missing required configuration variables"
- Check that the correct `.env.{ENV}` file exists
- Verify required variables are set
- Check `ENV` environment variable is correct

### Configuration not loading
- Check file path (must be in project root)
- Verify `.env` file format (KEY=value, no spaces)
- Check for syntax errors in .env file

### Environment variables not overriding
- Ensure environment variable is set BEFORE importing config
- Check variable name matches exactly (case-sensitive)
- Verify using `echo $VARIABLE_NAME`

## Best Practices

1. **Never commit secrets** - Add `.env.local` to `.gitignore`
2. **Use environment variables for secrets in production** - Not .env files
3. **Validate configuration on startup** - Fail fast with clear errors
4. **Document all configuration variables** - In this guide and .env files
5. **Use environment-specific defaults** - Reduce configuration burden
6. **Test all environments** - Local, Docker, and Kubernetes

## Examples

### Start service locally
```bash
ENV=local python services/api-gateway/src/main.py
```

### Start service in Docker
```bash
docker-compose up
# ENV=docker is set in docker-compose.yml
```

### Deploy to Kubernetes
```bash
kubectl apply -f k8s/
# ENV=kubernetes is set in deployment.yaml
# Secrets are loaded from Kubernetes Secrets
```
