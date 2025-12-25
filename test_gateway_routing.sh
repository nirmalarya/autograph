#!/bin/bash
# Test API Gateway routing to all microservices

echo "==================================================================="
echo "API GATEWAY ROUTING TEST"
echo "==================================================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

GATEWAY_URL="http://localhost:8080"
PASSED=0
FAILED=0

# Test function
test_route() {
    local service_name=$1
    local route=$2
    local expected_service=$3

    echo "Testing: $service_name"
    echo "  Route: $route"

    # Make request and capture HTTP status
    response=$(curl -s -w "\n%{http_code}" "$GATEWAY_URL$route" 2>/dev/null)
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)

    # Check if we got a response (200 OK or 401 Unauthorized means routing worked)
    # 404 would mean route doesn't exist, 502/503 means service is down
    if [[ "$http_code" == "200" ]] || [[ "$http_code" == "401" ]]; then
        echo -e "  ${GREEN}✓ PASS${NC} - HTTP $http_code (route exists and reached service)"

        # For 200 responses, try to verify the service name in response
        if [[ "$http_code" == "200" ]] && [[ "$body" == *"$expected_service"* ]]; then
            echo "  ${GREEN}✓${NC} Service verified: $expected_service"
        fi

        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}✗ FAIL${NC} - HTTP $http_code"
        echo "  Response: $body"
        FAILED=$((FAILED + 1))
    fi

    echo ""
}

# Test all service routes
echo "1. AUTHENTICATION SERVICE"
test_route "Auth Service Health" "/api/auth/health" "auth-service"

echo "2. DIAGRAM SERVICE"
test_route "Diagram Service Health" "/api/diagrams/health" "diagram-service"

echo "3. AI SERVICE"
test_route "AI Service Health" "/api/ai/health" "ai-service"

echo "4. COLLABORATION SERVICE"
test_route "Collaboration Service Health" "/api/collaboration/health" "collaboration-service"

echo "5. GIT SERVICE"
test_route "Git Service Health" "/api/git/health" "git-service"

echo "6. EXPORT SERVICE"
test_route "Export Service Health" "/api/export/health" "export-service"

echo "7. INTEGRATION HUB"
test_route "Integration Hub Health" "/api/integrations/health" "integration-hub"

echo "==================================================================="
echo "8. TEST INVALID ROUTE (should return 404 or 401)"
echo "==================================================================="
response=$(curl -s -w "\n%{http_code}" "$GATEWAY_URL/api/nonexistent/route" 2>/dev/null)
http_code=$(echo "$response" | tail -n 1)

if [[ "$http_code" == "404" ]] || [[ "$http_code" == "401" ]]; then
    echo -e "${GREEN}✓ PASS${NC} - Unknown route returned HTTP $http_code"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} - Expected 404 or 401, got HTTP $http_code"
    FAILED=$((FAILED + 1))
fi
echo ""

echo "==================================================================="
echo "TEST SUMMARY"
echo "==================================================================="
echo "Total tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED - API Gateway routing is working correctly!${NC}"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED - Check the output above${NC}"
    exit 1
fi
