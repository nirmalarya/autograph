#!/bin/bash

# Start Load Balanced AutoGraph v3 Services
# This script starts services with multiple instances for load balancing tests

set -e

echo "=============================================="
echo "Starting AutoGraph v3 with Load Balancer"
echo "=============================================="

# Check if .env exists
if [ ! -f .env.docker ]; then
    echo "ERROR: .env.docker file not found!"
    exit 1
fi

# Stop existing services if any
echo ""
echo "Stopping existing services..."
docker-compose down 2>/dev/null || true

# Build services that need rebuilding
echo ""
echo "Building diagram-service..."
docker-compose -f docker-compose.lb.yml build diagram-service-1 diagram-service-2 diagram-service-3

echo ""
echo "Starting infrastructure services (PostgreSQL, Redis, MinIO)..."
docker-compose -f docker-compose.lb.yml up -d postgres redis minio

echo ""
echo "Waiting for infrastructure to be healthy..."
sleep 10

echo ""
echo "Starting microservice instances..."
# Start all instances in parallel
docker-compose -f docker-compose.lb.yml up -d \
    diagram-service-1 diagram-service-2 diagram-service-3 \
    collaboration-service-1 collaboration-service-2 \
    ai-service-1 ai-service-2 \
    auth-service-1 auth-service-2 \
    export-service-1 export-service-2 \
    git-service-1 git-service-2 \
    integration-hub-1 integration-hub-2

echo ""
echo "Waiting for microservices to start..."
sleep 15

echo ""
echo "Starting load balancer..."
docker-compose -f docker-compose.lb.yml up -d load-balancer

echo ""
echo "Waiting for load balancer to be healthy..."
sleep 5

echo ""
echo "Starting API Gateway..."
docker-compose -f docker-compose.lb.yml up -d api-gateway

echo ""
echo "=============================================="
echo "Load Balanced AutoGraph v3 Started!"
echo "=============================================="
echo ""
echo "Services:"
echo "  - Load Balancer: http://localhost:8090"
echo "  - API Gateway: http://localhost:8080"
echo "  - Diagram Service: 3 instances (via load balancer)"
echo "  - Collaboration Service: 2 instances (via load balancer)"
echo "  - AI Service: 2 instances (via load balancer)"
echo ""
echo "Check status with: docker-compose -f docker-compose.lb.yml ps"
echo "View logs with: docker-compose -f docker-compose.lb.yml logs -f <service>"
echo ""

# Show container status
echo "Container Status:"
docker-compose -f docker-compose.lb.yml ps
