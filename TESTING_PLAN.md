# AutoGraph v3 - Testing Plan

## Session 3 Status: Docker Compose Complete ✅

All services are configured and ready for testing. This document outlines how to test each feature.

## Infrastructure Services (Currently Running ✅)

### PostgreSQL
```bash
docker exec autograph-postgres psql -U autograph -d autograph -c "\dt"
# Expected: 13 tables (12 app tables + alembic_version)
```

### Redis
```bash
docker exec autograph-redis redis-cli ping
# Expected: PONG

docker exec autograph-redis redis-cli SET "test:session" "value" EX 86400
docker exec autograph-redis redis-cli TTL "test:session"
# Expected: 86400 (24 hours)
```

### MinIO
```bash
mc ls local/
# Expected: diagrams/, exports/, uploads/
```

## Microservices Testing

### 1. Start Services Locally (Recommended for Development)

#### Auth Service
```bash
cd services/auth-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8085

# Test:
curl http://localhost:8085/health
```

#### API Gateway
```bash
cd services/api-gateway
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8080

# Test:
curl http://localhost:8080/health
curl http://localhost:8080/health/services
```

#### Frontend
```bash
cd services/frontend
npm run dev

# Visit: http://localhost:3000
```

### 2. Test API Gateway Routing

Once API Gateway and at least one backend service are running:

```bash
# Test auth routing
curl http://localhost:8080/api/auth/health

# Test diagram routing
curl http://localhost:8080/api/diagrams/health

# Test AI routing
curl http://localhost:8080/api/ai/health

# Test 404 for unknown routes
curl http://localhost:8080/api/unknown/route
# Expected: 404 or 503 (service unavailable)
```

### 3. Docker Compose Testing (When Ready)

Build all images (takes 30+ minutes):
```bash
docker-compose build
```

Start all services:
```bash
docker-compose up -d
```

Check status:
```bash
docker-compose ps
docker-compose logs -f
```

Test health checks:
```bash
# API Gateway
curl http://localhost:8080/health
curl http://localhost:8080/health/services

# Frontend
curl http://localhost:3000

# Individual services
curl http://localhost:8085/health  # auth-service
curl http://localhost:8082/health  # diagram-service
curl http://localhost:8084/health  # ai-service
curl http://localhost:8083/health  # collaboration-service
curl http://localhost:8087/health  # git-service
curl http://localhost:8097/health  # export-service
curl http://localhost:8099/health  # integration-hub
curl http://localhost:8096/health  # svg-renderer
```

## Feature Testing Checklist

### Feature #1: Docker Compose ✅ PASSING
- [x] 13 services configured (3 infrastructure + 10 microservices)
- [x] All services have Dockerfiles
- [x] All services have health checks
- [x] Service dependencies defined
- [x] docker-compose.yml validates

### Feature #7: API Gateway Routing (NEXT)
- [ ] Start API Gateway on port 8080
- [ ] Start auth-service on port 8085
- [ ] Test /api/auth/* routes to auth-service
- [ ] Start diagram-service on port 8082
- [ ] Test /api/diagrams/* routes to diagram-service
- [ ] Test all 7 service routes
- [ ] Verify 404 for unknown routes
- [ ] Check /health/services aggregation

### Feature #8: JWT Authentication (FUTURE)
- [ ] Implement JWT token generation
- [ ] Implement password hashing with bcrypt
- [ ] Create /api/auth/register endpoint
- [ ] Create /api/auth/login endpoint
- [ ] Test authentication flow
- [ ] Verify tokens work

### Feature #9: Rate Limiting (FUTURE)
- [ ] Implement rate limiting middleware
- [ ] Test 100 requests/min per user
- [ ] Test 1000 requests/min per IP
- [ ] Verify 429 response when exceeded

## Next Steps

1. **Install Dependencies**: Create virtual environments and install requirements for each service
2. **Start Services**: Start services locally for testing
3. **Test Routing**: Verify API Gateway routes requests correctly
4. **Implement Auth**: Add JWT authentication endpoints
5. **Add Tests**: Write Playwright E2E tests and pytest unit tests
6. **Build Docker**: Build and test Docker images
7. **Deploy**: Deploy to production environment

## Notes

- Python 3.12.7 recommended (Dockerfiles use this version)
- Node.js 20.18.0 for frontend and svg-renderer
- All services use port numbers from .env file
- CORS configured for http://localhost:3000
- Health checks on all services at /health endpoint
