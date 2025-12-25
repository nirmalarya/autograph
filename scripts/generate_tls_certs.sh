#!/bin/bash
# Generate TLS 1.3 certificates for development

set -e

CERT_DIR="./certs"
mkdir -p "$CERT_DIR"

echo "🔐 Generating TLS 1.3 certificates for development..."

# Generate CA key and certificate
echo "1. Generating Certificate Authority (CA)..."
openssl genrsa -out "$CERT_DIR/ca-key.pem" 4096
openssl req -new -x509 -days 365 -key "$CERT_DIR/ca-key.pem" \
    -out "$CERT_DIR/ca-cert.pem" \
    -subj "/C=US/ST=CA/L=San Francisco/O=Autograph/OU=Dev/CN=Autograph CA"

# Generate server key
echo "2. Generating server private key..."
openssl genrsa -out "$CERT_DIR/server-key.pem" 4096

# Create certificate signing request
echo "3. Creating certificate signing request..."
openssl req -new -key "$CERT_DIR/server-key.pem" \
    -out "$CERT_DIR/server-csr.pem" \
    -subj "/C=US/ST=CA/L=San Francisco/O=Autograph/OU=Services/CN=localhost"

# Create extensions file for SAN (Subject Alternative Names)
cat > "$CERT_DIR/server-ext.cnf" <<EOF
subjectAltName = @alt_names
extendedKeyUsage = serverAuth

[alt_names]
DNS.1 = localhost
DNS.2 = api-gateway
DNS.3 = auth-service
DNS.4 = diagram-service
DNS.5 = ai-service
DNS.6 = collaboration-service
DNS.7 = git-service
DNS.8 = export-service
DNS.9 = integration-hub
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# Sign the server certificate with CA
echo "4. Signing server certificate..."
openssl x509 -req -days 365 \
    -in "$CERT_DIR/server-csr.pem" \
    -CA "$CERT_DIR/ca-cert.pem" \
    -CAkey "$CERT_DIR/ca-key.pem" \
    -CAcreateserial \
    -out "$CERT_DIR/server-cert.pem" \
    -extfile "$CERT_DIR/server-ext.cnf"

# Generate DH parameters for perfect forward secrecy
echo "5. Generating Diffie-Hellman parameters (this may take a while)..."
openssl dhparam -out "$CERT_DIR/dhparam.pem" 2048

# Set proper permissions
echo "6. Setting certificate permissions..."
chmod 600 "$CERT_DIR"/*.pem
chmod 644 "$CERT_DIR/ca-cert.pem" "$CERT_DIR/server-cert.pem"

echo "✅ TLS certificates generated successfully in $CERT_DIR/"
echo ""
echo "Generated files:"
echo "  - ca-cert.pem        (CA certificate - trust this in clients)"
echo "  - ca-key.pem         (CA private key - keep secure)"
echo "  - server-cert.pem    (Server certificate)"
echo "  - server-key.pem     (Server private key - keep secure)"
echo "  - dhparam.pem        (DH parameters for PFS)"
echo ""
echo "To trust the CA certificate on macOS:"
echo "  sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain $CERT_DIR/ca-cert.pem"
echo ""
echo "To trust the CA certificate on Linux:"
echo "  sudo cp $CERT_DIR/ca-cert.pem /usr/local/share/ca-certificates/autograph-ca.crt"
echo "  sudo update-ca-certificates"
