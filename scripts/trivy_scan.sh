#!/bin/bash
# Trivy Container Image Scanning Script
# Scans all Autograph service images for vulnerabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Trivy Container Image Scanning"
echo "=========================================="
echo ""

# List of services to scan
SERVICES=(
    "api-gateway"
    "auth-service"
    "diagram-service"
    "collaboration-service"
    "ai-service"
    "git-service"
    "export-service"
    "integration-hub"
)

# Create results directory
RESULTS_DIR="./trivy_results"
mkdir -p "$RESULTS_DIR"

# Summary variables
TOTAL_SERVICES=0
SERVICES_WITH_CRITICAL=0
SERVICES_WITH_HIGH=0
SERVICES_CLEAN=0

echo "Scanning ${#SERVICES[@]} service images..."
echo ""

# Scan each service
for SERVICE in "${SERVICES[@]}"; do
    TOTAL_SERVICES=$((TOTAL_SERVICES + 1))
    IMAGE_NAME="autograph-${SERVICE}:latest"

    echo "-------------------------------------------"
    echo "Scanning: $IMAGE_NAME"
    echo "-------------------------------------------"

    # Check if image exists
    if ! docker images | grep -q "autograph-${SERVICE}"; then
        echo -e "${RED}✗ Image not found: $IMAGE_NAME${NC}"
        echo ""
        continue
    fi

    # Run Trivy scan using Docker
    # Output both to terminal and JSON file
    docker run --rm \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v "$PWD/$RESULTS_DIR:/results" \
        aquasec/trivy:latest image \
        --format json \
        --output "/results/${SERVICE}_scan.json" \
        --severity CRITICAL,HIGH,MEDIUM,LOW \
        "$IMAGE_NAME" || true

    # Also generate human-readable report
    docker run --rm \
        -v /var/run/docker.sock:/var/run/docker.sock \
        aquasec/trivy:latest image \
        --severity CRITICAL,HIGH \
        "$IMAGE_NAME" | tee "$RESULTS_DIR/${SERVICE}_report.txt"

    # Parse results
    if [ -f "$RESULTS_DIR/${SERVICE}_scan.json" ]; then
        CRITICAL=$(cat "$RESULTS_DIR/${SERVICE}_scan.json" | grep -o '"Severity":"CRITICAL"' | wc -l || echo 0)
        HIGH=$(cat "$RESULTS_DIR/${SERVICE}_scan.json" | grep -o '"Severity":"HIGH"' | wc -l || echo 0)

        if [ "$CRITICAL" -gt 0 ]; then
            echo -e "${RED}✗ CRITICAL vulnerabilities found: $CRITICAL${NC}"
            SERVICES_WITH_CRITICAL=$((SERVICES_WITH_CRITICAL + 1))
        elif [ "$HIGH" -gt 0 ]; then
            echo -e "${YELLOW}⚠ HIGH vulnerabilities found: $HIGH${NC}"
            SERVICES_WITH_HIGH=$((SERVICES_WITH_HIGH + 1))
        else
            echo -e "${GREEN}✓ No critical or high vulnerabilities${NC}"
            SERVICES_CLEAN=$((SERVICES_CLEAN + 1))
        fi
    fi

    echo ""
done

# Print summary
echo "=========================================="
echo "SCAN SUMMARY"
echo "=========================================="
echo "Total services scanned: $TOTAL_SERVICES"
echo -e "Services with CRITICAL: ${RED}$SERVICES_WITH_CRITICAL${NC}"
echo -e "Services with HIGH: ${YELLOW}$SERVICES_WITH_HIGH${NC}"
echo -e "Services clean: ${GREEN}$SERVICES_CLEAN${NC}"
echo ""
echo "Detailed results saved to: $RESULTS_DIR/"
echo "=========================================="

# Exit with error if critical vulnerabilities found
if [ "$SERVICES_WITH_CRITICAL" -gt 0 ]; then
    echo -e "${RED}ERROR: Critical vulnerabilities detected!${NC}"
    exit 1
fi

echo -e "${GREEN}Scan complete!${NC}"
