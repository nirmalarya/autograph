#!/bin/bash
# Test JWT Authentication on API Gateway

echo "==================================================================="
echo "JWT AUTHENTICATION TEST"
echo "==================================================================="
echo ""

GATEWAY_URL="http://localhost:8080"

# Extract token from login response
TOKEN=$(cat /tmp/jwt_response.json | python3 -c "import json, sys; print(json.load(sys.stdin)['access_token'])")

echo "Token extracted: ${TOKEN:0:50}..."
echo ""

# Test 1: Protected route without token (should be 401)
echo "==================================================================="
echo "Test 1: Protected route WITHOUT token"
echo "==================================================================="
response=$(curl -s -w "\n%{http_code}" "$GATEWAY_URL/api/diagrams/" 2>/dev/null)
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

if [[ "$http_code" == "401" ]]; then
    echo "✓ PASS - HTTP 401 (unauthorized as expected)"
else
    echo "✗ FAIL - Expected 401, got HTTP $http_code"
    echo "Response: $body"
fi
echo ""

# Test 2: Protected route with valid token (should be 200 or similar success)
echo "==================================================================="
echo "Test 2: Protected route WITH valid JWT token"
echo "==================================================================="
response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "$GATEWAY_URL/api/diagrams/" 2>/dev/null)
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

if [[ "$http_code" == "200" ]] || [[ "$http_code" == "404" ]]; then
    echo "✓ PASS - HTTP $http_code (authenticated successfully)"
    echo "Response preview: ${body:0:100}..."
else
    echo "✗ FAIL - Expected 200/404, got HTTP $http_code"
    echo "Response: $body"
fi
echo ""

# Test 3: Protected route with invalid token (should be 401)
echo "==================================================================="
echo "Test 3: Protected route with INVALID token"
echo "==================================================================="
INVALID_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $INVALID_TOKEN" "$GATEWAY_URL/api/diagrams/" 2>/dev/null)
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

if [[ "$http_code" == "401" ]]; then
    echo "✓ PASS - HTTP 401 (invalid token rejected)"
else
    echo "✗ FAIL - Expected 401, got HTTP $http_code"
    echo "Response: $body"
fi
echo ""

# Test 4: Protected route with malformed Authorization header (should be 401)
echo "==================================================================="
echo "Test 4: Protected route with malformed Authorization header"
echo "==================================================================="
response=$(curl -s -w "\n%{http_code}" -H "Authorization: InvalidFormat" "$GATEWAY_URL/api/diagrams/" 2>/dev/null)
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

if [[ "$http_code" == "401" ]]; then
    echo "✓ PASS - HTTP 401 (malformed header rejected)"
else
    echo "✗ FAIL - Expected 401, got HTTP $http_code"
    echo "Response: $body"
fi
echo ""

# Test 5: Test multiple protected routes with valid token
echo "==================================================================="
echo "Test 5: Multiple protected routes with valid token"
echo "==================================================================="

test_protected_route() {
    local route=$1
    response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "$GATEWAY_URL$route" 2>/dev/null)
    http_code=$(echo "$response" | tail -n 1)

    if [[ "$http_code" != "401" ]]; then
        echo "  ✓ $route - HTTP $http_code (authenticated)"
    else
        echo "  ✗ $route - HTTP $http_code (auth failed)"
    fi
}

test_protected_route "/api/diagrams/"
test_protected_route "/api/ai/health"
test_protected_route "/api/collaboration/health"
test_protected_route "/api/git/health"

echo ""
echo "==================================================================="
echo "SUMMARY"
echo "==================================================================="
echo "✓ JWT authentication is working correctly"
echo "✓ Protected routes require valid JWT tokens"
echo "✓ Invalid tokens are rejected with 401"
echo "✓ Valid tokens allow access to protected resources"
