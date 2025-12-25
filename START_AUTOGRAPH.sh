#!/bin/bash

echo "=========================================="
echo "  🚀 Starting AutoGraph v3.1"
echo "=========================================="
echo ""

cd /Users/nirmalarya/Workspace/autograph

# Step 1: Stop existing services
echo "1. Stopping existing services..."
docker-compose down
echo "   ✅ Stopped"
echo ""

# Step 2: Start all services
echo "2. Starting all services..."
docker-compose up -d
echo "   ✅ Started"
echo ""

# Step 3: Wait for services to initialize
echo "3. Waiting for services to initialize (60 seconds)..."
for i in {60..1}; do
    echo -ne "   ⏳ $i seconds remaining...\r"
    sleep 1
done
echo "   ✅ Services initialized                    "
echo ""

# Step 4: Check service health
echo "4. Checking service health..."
docker-compose ps
echo ""

# Step 5: Count healthy services
healthy_count=$(docker-compose ps | grep -c "healthy" || echo "0")
echo "   Healthy services: $healthy_count"
echo ""

# Step 6: Test accessibility
echo "5. Testing service accessibility..."

if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "   ✅ API Gateway (8080): Accessible"
else
    echo "   ❌ API Gateway (8080): Not accessible"
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "   ✅ Frontend (3000): Accessible"
else
    echo "   ❌ Frontend (3000): Not accessible yet (may still be building)"
fi

echo ""
echo "=========================================="
echo "  🎉 AutoGraph Started!"
echo "=========================================="
echo ""
echo "Access points:"
echo "  - Frontend:    http://localhost:3000"
echo "  - API Gateway: http://localhost:8080"
echo "  - MinIO:       http://localhost:9001"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f frontend"
echo "  docker-compose logs -f auth-service"
echo ""
echo "To check status:"
echo "  docker-compose ps"
echo ""


