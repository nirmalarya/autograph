#!/bin/bash
set -e

echo "================================================================================"
echo "TESTING DIAGRAM AUDIT LOGGING"
echo "================================================================================"

# Step 1: Register a test user
echo ""
echo "[Step 1] Registering test user..."
TIMESTAMP=$(date +%s)
EMAIL="diagtest${TIMESTAMP}@test.com"

REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8085/register \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${EMAIL}\",
    \"password\": \"TestPass123!\",
    \"full_name\": \"Diagram Test User\"
  }")

echo "$REGISTER_RESPONSE" | python3 -m json.tool
USER_ID=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")

if [ -z "$USER_ID" ]; then
  echo "❌ Failed to register user"
  exit 1
fi

echo "✅ User registered: $USER_ID"

# Step 2: Login and get token
echo ""
echo "[Step 2] Logging in..."
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8085/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${EMAIL}&password=TestPass123!")

TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to login"
  echo "$TOKEN_RESPONSE"
  exit 1
fi

echo "✅ Login successful, token: ${TOKEN:0:30}..."

# Step 3: Check audit log for login
echo ""
echo "[Step 3] Checking login audit log..."
docker exec autograph-postgres psql -U autograph -d autograph -c \
  "SELECT action, resource_type, created_at FROM audit_log WHERE user_id = '${USER_ID}' AND action LIKE '%login%' ORDER BY created_at DESC LIMIT 1;"

# Step 4: Create a diagram
echo ""
echo "[Step 4] Creating a diagram..."
CREATE_RESPONSE=$(curl -s -X POST http://localhost:8082/\
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-User-ID: ${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Audit Test Diagram",
    "file_type": "canvas",
    "canvas_data": {"shapes": [], "version": "1.0"}
  }')

DIAGRAM_ID=$(echo "$CREATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")

if [ -z "$DIAGRAM_ID" ]; then
  echo "❌ Failed to create diagram"
  echo "$CREATE_RESPONSE"
  exit 1
fi

echo "✅ Diagram created: $DIAGRAM_ID"

# Step 5: Check audit log for diagram creation
echo ""
echo "[Step 5] Checking diagram creation audit log..."
sleep 1
docker exec autograph-postgres psql -U autograph -d autograph -c \
  "SELECT action, resource_type, resource_id, created_at FROM audit_log WHERE user_id = '${USER_ID}' AND action = 'create_diagram' ORDER BY created_at DESC LIMIT 1;"

# Step 6: Update the diagram
echo ""
echo "[Step 6] Updating diagram..."
UPDATE_RESPONSE=$(curl -s -X PUT http://localhost:8082/${DIAGRAM_ID} \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-User-ID: ${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Audit Test Diagram - Updated",
    "canvas_data": {"shapes": [{"type": "rect"}], "version": "1.1"}
  }')

echo "✅ Diagram updated"

# Step 7: Check audit log for diagram update
echo ""
echo "[Step 7] Checking diagram update audit log..."
sleep 1
docker exec autograph-postgres psql -U autograph -d autograph -c \
  "SELECT action, resource_type, resource_id, created_at FROM audit_log WHERE user_id = '${USER_ID}' AND action = 'update_diagram' ORDER BY created_at DESC LIMIT 1;"

# Step 8: Delete the diagram
echo ""
echo "[Step 8] Deleting diagram..."
DELETE_RESPONSE=$(curl -s -X DELETE http://localhost:8082/${DIAGRAM_ID} \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-User-ID: ${USER_ID}")

echo "✅ Diagram deleted"

# Step 9: Check audit log for diagram deletion
echo ""
echo "[Step 9] Checking diagram deletion audit log..."
sleep 1
docker exec autograph-postgres psql -U autograph -d autograph -c \
  "SELECT action, resource_type, resource_id, created_at FROM audit_log WHERE user_id = '${USER_ID}' AND action LIKE 'delete_diagram%' ORDER BY created_at DESC LIMIT 1;"

# Step 10: Show all audit logs for this user
echo ""
echo "[Step 10] All audit logs for test user:"
docker exec autograph-postgres psql -U autograph -d autograph -c \
  "SELECT action, resource_type, resource_id, TO_CHAR(created_at, 'HH24:MI:SS') as time FROM audit_log WHERE user_id = '${USER_ID}' ORDER BY created_at;"

echo ""
echo "================================================================================"
echo "TEST COMPLETE"
echo "================================================================================"
