#!/bin/bash
# Start all microservices

echo "Starting AutoGraph v3 microservices..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Load environment
source .env 2>/dev/null || true

# Start API Gateway
echo "Starting API Gateway on port ${API_GATEWAY_PORT:-8080}..."
(cd services/api-gateway && python3.12 src/main.py > ../../logs/api-gateway.log 2>&1) &

# Start Auth Service
echo "Starting Auth Service on port ${AUTH_SERVICE_PORT:-8085}..."
(cd services/auth-service && python3.12 src/main.py > ../../logs/auth-service.log 2>&1) &

# Start Diagram Service
echo "Starting Diagram Service on port ${DIAGRAM_SERVICE_PORT:-8082}..."
(cd services/diagram-service && python3.12 -m src.main > ../../logs/diagram-service.log 2>&1) &

# Start AI Service
echo "Starting AI Service on port ${AI_SERVICE_PORT:-8084}..."
(cd services/ai-service && python3.12 src/main.py > ../../logs/ai-service.log 2>&1) &

# Start Collaboration Service
echo "Starting Collaboration Service on port ${COLLABORATION_SERVICE_PORT:-8083}..."
(cd services/collaboration-service && python3.12 src/main.py > ../../logs/collaboration-service.log 2>&1) &

# Start Git Service
echo "Starting Git Service on port ${GIT_SERVICE_PORT:-8087}..."
(cd services/git-service && python3.12 src/main.py > ../../logs/git-service.log 2>&1) &

# Start Export Service
echo "Starting Export Service on port ${EXPORT_SERVICE_PORT:-8097}..."
(cd services/export-service && python3.12 src/main.py > ../../logs/export-service.log 2>&1) &

# Start Integration Hub
echo "Starting Integration Hub on port ${INTEGRATION_HUB_PORT:-8099}..."
(cd services/integration-hub && python3.12 src/main.py > ../../logs/integration-hub.log 2>&1) &

echo ""
echo "Waiting for services to start..."
sleep 5

echo ""
echo "✓ All services started!"
echo ""
echo "Services:"
echo "  • API Gateway:          http://localhost:${API_GATEWAY_PORT:-8080}/health"
echo "  • Auth Service:         http://localhost:${AUTH_SERVICE_PORT:-8085}/health"
echo "  • Diagram Service:      http://localhost:${DIAGRAM_SERVICE_PORT:-8082}/health"
echo "  • AI Service:           http://localhost:${AI_SERVICE_PORT:-8084}/health"
echo "  • Collaboration:        http://localhost:${COLLABORATION_SERVICE_PORT:-8083}/health"
echo "  • Git Service:          http://localhost:${GIT_SERVICE_PORT:-8087}/health"
echo "  • Export Service:       http://localhost:${EXPORT_SERVICE_PORT:-8097}/health"
echo "  • Integration Hub:      http://localhost:${INTEGRATION_HUB_PORT:-8099}/health"
echo ""
echo "Check all services: http://localhost:${API_GATEWAY_PORT:-8080}/health/services"
echo ""
echo "To stop services: pkill -f 'python3 src/main.py'"
