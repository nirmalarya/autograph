#!/bin/bash
# Trivy Container Image Scanning Script - All Services
# Scans all Autograph service images for vulnerabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Summary file
SUMMARY_FILE="$RESULTS_DIR/scan_summary.json"
echo "{" > "$SUMMARY_FILE"
echo '  "scan_date": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",' >> "$SUMMARY_FILE"
echo '  "services": [' >> "$SUMMARY_FILE"

# Summary variables
TOTAL_SERVICES=0
SERVICES_WITH_CRITICAL=0
SERVICES_WITH_HIGH=0
SERVICES_CLEAN=0
FIRST_SERVICE=true

echo "Scanning ${#SERVICES[@]} service images..."
echo ""

# Scan each service
for SERVICE in "${SERVICES[@]}"; do
    TOTAL_SERVICES=$((TOTAL_SERVICES + 1))
    IMAGE_NAME="autograph-${SERVICE}:latest"

    echo "-------------------------------------------"
    echo -e "${BLUE}Scanning: $IMAGE_NAME${NC}"
    echo "-------------------------------------------"

    # Check if image exists
    if ! docker images | grep -q "autograph-${SERVICE}"; then
        echo -e "${RED}✗ Image not found: $IMAGE_NAME${NC}"
        echo ""
        continue
    fi

    # Add comma for JSON array (except first element)
    if [ "$FIRST_SERVICE" = true ]; then
        FIRST_SERVICE=false
    else
        echo "," >> "$SUMMARY_FILE"
    fi

    # Run Trivy scan with JSON output
    docker run --rm \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v "$PWD/$RESULTS_DIR:/results" \
        -e TRIVY_INSECURE=true \
        aquasec/trivy:latest image \
        --format json \
        --output "/results/${SERVICE}_scan.json" \
        --severity CRITICAL,HIGH,MEDIUM,LOW \
        "$IMAGE_NAME" 2>&1 | grep -v "INFO" | grep -v "WARN" || true

    echo ""
    echo "Generating report for $SERVICE..."

    # Parse JSON results
    if [ -f "$RESULTS_DIR/${SERVICE}_scan.json" ]; then
        # Count vulnerabilities by severity
        CRITICAL=$(grep -o '"Severity":"CRITICAL"' "$RESULTS_DIR/${SERVICE}_scan.json" | wc -l | tr -d ' ' || echo "0")
        HIGH=$(grep -o '"Severity":"HIGH"' "$RESULTS_DIR/${SERVICE}_scan.json" | wc -l | tr -d ' ' || echo "0")
        MEDIUM=$(grep -o '"Severity":"MEDIUM"' "$RESULTS_DIR/${SERVICE}_scan.json" | wc -l | tr -d ' ' || echo "0")
        LOW=$(grep -o '"Severity":"LOW"' "$RESULTS_DIR/${SERVICE}_scan.json" | wc -l | tr -d ' ' || echo "0")

        # Add to summary JSON
        echo '    {' >> "$SUMMARY_FILE"
        echo "      \"service\": \"$SERVICE\"," >> "$SUMMARY_FILE"
        echo "      \"image\": \"$IMAGE_NAME\"," >> "$SUMMARY_FILE"
        echo "      \"vulnerabilities\": {" >> "$SUMMARY_FILE"
        echo "        \"critical\": $CRITICAL," >> "$SUMMARY_FILE"
        echo "        \"high\": $HIGH," >> "$SUMMARY_FILE"
        echo "        \"medium\": $MEDIUM," >> "$SUMMARY_FILE"
        echo "        \"low\": $LOW" >> "$SUMMARY_FILE"
        echo "      }" >> "$SUMMARY_FILE"
        echo -n '    }' >> "$SUMMARY_FILE"

        # Print results
        echo "Results for $SERVICE:"
        echo -e "  CRITICAL: ${RED}$CRITICAL${NC}"
        echo -e "  HIGH: ${YELLOW}$HIGH${NC}"
        echo -e "  MEDIUM: $MEDIUM"
        echo -e "  LOW: $LOW"

        # Track status
        if [ "$CRITICAL" -gt 0 ]; then
            echo -e "${RED}✗ CRITICAL vulnerabilities found${NC}"
            SERVICES_WITH_CRITICAL=$((SERVICES_WITH_CRITICAL + 1))
        elif [ "$HIGH" -gt 0 ]; then
            echo -e "${YELLOW}⚠ HIGH vulnerabilities found${NC}"
            SERVICES_WITH_HIGH=$((SERVICES_WITH_HIGH + 1))
        else
            echo -e "${GREEN}✓ No critical or high vulnerabilities${NC}"
            SERVICES_CLEAN=$((SERVICES_CLEAN + 1))
        fi
    fi

    echo ""
done

# Close JSON
echo "" >> "$SUMMARY_FILE"
echo '  ],' >> "$SUMMARY_FILE"
echo '  "summary": {' >> "$SUMMARY_FILE"
echo "    \"total_services\": $TOTAL_SERVICES," >> "$SUMMARY_FILE"
echo "    \"services_with_critical\": $SERVICES_WITH_CRITICAL," >> "$SUMMARY_FILE"
echo "    \"services_with_high\": $SERVICES_WITH_HIGH," >> "$SUMMARY_FILE"
echo "    \"services_clean\": $SERVICES_CLEAN" >> "$SUMMARY_FILE"
echo '  }' >> "$SUMMARY_FILE"
echo '}' >> "$SUMMARY_FILE"

# Print summary
echo "=========================================="
echo "SCAN SUMMARY"
echo "=========================================="
echo "Total services scanned: $TOTAL_SERVICES"
echo -e "Services with CRITICAL: ${RED}$SERVICES_WITH_CRITICAL${NC}"
echo -e "Services with HIGH: ${YELLOW}$SERVICES_WITH_HIGH${NC}"
echo -e "Services clean (no CRITICAL/HIGH): ${GREEN}$SERVICES_CLEAN${NC}"
echo ""
echo "Detailed results saved to: $RESULTS_DIR/"
echo "Summary JSON: $SUMMARY_FILE"
echo "=========================================="

echo -e "${GREEN}✓ Scan complete!${NC}"
echo ""
echo "Note: Vulnerabilities found are primarily in base OS packages."
echo "Consider using minimal base images (alpine, distroless) to reduce attack surface."
