#!/bin/bash

# Setup test users for Feature #444

# User 1
cat > /tmp/user1.json <<'EOF'
{"email":"realtime_user1@example.com","password":"SecurePassword123!","full_name":"RT User 1"}
EOF

# User 2
cat > /tmp/user2.json <<'EOF'
{"email":"realtime_user2@example.com","password":"SecurePassword123!","full_name":"RT User 2"}
EOF

# Register users
curl -s -X POST http://localhost:8080/api/auth/register -H "Content-Type: application/json" -d @/tmp/user1.json
echo ""
curl -s -X POST http://localhost:8080/api/auth/register -H "Content-Type: application/json" -d @/tmp/user2.json
echo ""

# Mark as verified
docker exec autograph-postgres psql -U autograph -d autograph <<'SQL'
UPDATE users SET is_verified = true
WHERE email IN ('realtime_user1@example.com', 'realtime_user2@example.com');

SELECT email, is_verified FROM users
WHERE email IN ('realtime_user1@example.com', 'realtime_user2@example.com');
SQL

rm /tmp/user1.json /tmp/user2.json
