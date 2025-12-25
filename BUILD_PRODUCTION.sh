#!/bin/bash
#
# AutoGraph v3.1 - Production Build Script
# Builds all Docker images with proper SSL certificate handling
#

set -e

echo "=========================================="
echo "  🏗️  Building AutoGraph v3.1 Images"
echo "=========================================="
echo ""

cd /Users/nirmalarya/Workspace/autograph

# Check for .env
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Run ./scripts/init.sh first"
    exit 1
fi

# Stop existing containers
echo "1. Stopping existing containers..."
docker-compose down
echo "   ✅ Stopped"
echo ""

# Clean up old images (optional - uncomment if needed)
# echo "2. Removing old images..."
# docker images | grep autograph | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true
# echo "   ✅ Cleaned"
# echo ""

# Build all images
echo "2. Building all service images..."
echo "   (This may take 10-15 minutes on first build)"
echo ""

# Set build context timeout
export DOCKER_BUILDKIT=1
export COMPOSE_HTTP_TIMEOUT=300
export DOCKER_CLIENT_TIMEOUT=300

# Build with progress
docker-compose build --progress=plain 2>&1 | tee build.log

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All images built successfully!"
    echo ""
    
    # Start services
    echo "3. Starting all services..."
    docker-compose up -d
    echo "   ✅ Started"
    echo ""
    
    # Wait for health checks
    echo "4. Waiting for services to become healthy (60 seconds)..."
    sleep 60
    echo ""
    
    # Show status
    echo "5. Service Status:"
    docker-compose ps
    echo ""
    
    # Count healthy
    healthy=$(docker-compose ps | grep -c "healthy" || echo "0")
    total=$(docker-compose ps | grep -c "Up" || echo "0")
    echo "Healthy: $healthy/$total services"
    echo ""
    
    if [ "$healthy" -ge "8" ]; then
        echo "🎉 AutoGraph is ready!"
        echo ""
        echo "Access:"
        echo "  - Frontend:    http://localhost:3000"
        echo "  - API Gateway: http://localhost:8080"
        echo "  - MinIO Console: http://localhost:9001"
        echo ""
    else
        echo "⚠️  Some services are not healthy yet."
        echo "   Check logs: docker-compose logs <service-name>"
        echo ""
    fi
else
    echo ""
    echo "❌ Build failed!"
    echo "   Check build.log for details"
    echo ""
    exit 1
fi


