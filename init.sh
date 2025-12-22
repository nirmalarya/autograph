#!/bin/bash
#
# AutoGraph v3 - Development Environment Setup Script
# This script initializes the complete development environment for the AutoGraph v3 project
#

set -e  # Exit on error

echo "=================================================="
echo "AutoGraph v3 - Environment Setup"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker is not installed. Please install Docker Desktop first.${NC}"
    echo "Visit: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}Docker Compose is not available. Please install Docker Compose.${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Node.js is not installed. Please install Node.js 20.x${NC}"
    echo "Visit: https://nodejs.org/"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python 3 is not installed. Please install Python 3.12+${NC}"
    exit 1
fi

echo -e "${BLUE}✓ Prerequisites check passed${NC}"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${BLUE}Creating .env file...${NC}"
    cat > .env << 'EOF'
# AutoGraph v3 Environment Configuration

# Environment
NODE_ENV=development
PYTHON_ENV=development

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=autograph
POSTGRES_USER=autograph
POSTGRES_PASSWORD=autograph_dev_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# MinIO (S3-compatible storage)
MINIO_HOST=localhost
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_BUCKET_DIAGRAMS=diagrams
MINIO_BUCKET_EXPORTS=exports
MINIO_BUCKET_UPLOADS=uploads

# JWT
JWT_SECRET=your-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# API Gateway
API_GATEWAY_PORT=8080

# Microservices Ports
FRONTEND_PORT=3000
AUTH_SERVICE_PORT=8085
DIAGRAM_SERVICE_PORT=8082
AI_SERVICE_PORT=8084
COLLABORATION_SERVICE_PORT=8083
GIT_SERVICE_PORT=8087
EXPORT_SERVICE_PORT=8097
INTEGRATION_HUB_PORT=8099
SVG_RENDERER_PORT=8096

# AI Providers
# Bayer MGA (Primary)
MGA_API_KEY=your-mga-api-key
MGA_ENDPOINT=https://chat.int.bayer.com/api/v2
MGA_MODEL=gpt-4.1

# OpenAI (Fallback)
OPENAI_API_KEY=your-openai-api-key

# Anthropic (Fallback)
ANTHROPIC_API_KEY=your-anthropic-api-key

# Google Gemini (Fallback)
GOOGLE_API_KEY=your-google-api-key

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Rate Limiting
RATE_LIMIT_PER_USER=100
RATE_LIMIT_PER_IP=1000

# Logging
LOG_LEVEL=INFO
EOF
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}⚠ Please update .env with your actual API keys${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

echo ""

# Create directory structure
echo -e "${BLUE}Creating project structure...${NC}"

# Services directories
mkdir -p services/frontend
mkdir -p services/api-gateway/src
mkdir -p services/auth-service/src
mkdir -p services/diagram-service/src
mkdir -p services/ai-service/src
mkdir -p services/collaboration-service/src
mkdir -p services/git-service/src
mkdir -p services/export-service/src
mkdir -p services/integration-hub/src
mkdir -p services/svg-renderer/src

# Shared directories
mkdir -p shared/types
mkdir -p shared/utils

# Infrastructure
mkdir -p infrastructure/docker
mkdir -p infrastructure/kubernetes
mkdir -p infrastructure/terraform

# Testing
mkdir -p tests/e2e
mkdir -p tests/integration
mkdir -p tests/unit

# Documentation
mkdir -p docs

echo -e "${GREEN}✓ Project structure created${NC}"
echo ""

# Check if docker-compose.yml exists
if [ ! -f docker-compose.yml ]; then
    echo -e "${BLUE}Creating docker-compose.yml...${NC}"
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # Infrastructure Services
  postgres:
    image: postgres:16.6
    container_name: autograph-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "${POSTGRES_PORT}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7.4.1-alpine
    container_name: autograph-redis
    ports:
      - "${REDIS_PORT}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  minio:
    image: minio/minio:latest
    container_name: autograph-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    ports:
      - "${MINIO_PORT}:9000"
      - "${MINIO_CONSOLE_PORT}:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  redis_data:
  minio_data:

networks:
  default:
    name: autograph-network
EOF
    echo -e "${GREEN}✓ Created docker-compose.yml${NC}"
else
    echo -e "${GREEN}✓ docker-compose.yml already exists${NC}"
fi

echo ""

# Start infrastructure services
echo -e "${BLUE}Starting infrastructure services (PostgreSQL, Redis, MinIO)...${NC}"
docker-compose up -d

echo ""
echo -e "${BLUE}Waiting for services to be healthy...${NC}"
sleep 10

# Check service health
echo -e "${BLUE}Checking PostgreSQL...${NC}"
until docker exec autograph-postgres pg_isready -U autograph > /dev/null 2>&1; do
    echo "  Waiting for PostgreSQL..."
    sleep 2
done
echo -e "${GREEN}✓ PostgreSQL is ready${NC}"

echo -e "${BLUE}Checking Redis...${NC}"
until docker exec autograph-redis redis-cli ping > /dev/null 2>&1; do
    echo "  Waiting for Redis..."
    sleep 2
done
echo -e "${GREEN}✓ Redis is ready${NC}"

echo -e "${BLUE}Checking MinIO...${NC}"
until curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; do
    echo "  Waiting for MinIO..."
    sleep 2
done
echo -e "${GREEN}✓ MinIO is ready${NC}"

echo ""
echo "=================================================="
echo -e "${GREEN}✓ AutoGraph v3 Environment Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "Infrastructure Services:"
echo "  • PostgreSQL:      http://localhost:5432"
echo "  • Redis:           http://localhost:6379"
echo "  • MinIO API:       http://localhost:9000"
echo "  • MinIO Console:   http://localhost:9001"
echo "    Credentials:     minioadmin / minioadmin"
echo ""
echo "Next Steps:"
echo "  1. Update .env with your API keys (MGA, OpenAI, etc.)"
echo "  2. Initialize database schema:"
echo "     cd services/auth-service && alembic upgrade head"
echo "  3. Start development servers:"
echo "     Frontend:  cd services/frontend && npm install && npm run dev"
echo "     Backend:   cd services/<service-name> && pip install -r requirements.txt && uvicorn src.main:app --reload"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "Happy coding! 🚀"
echo ""
