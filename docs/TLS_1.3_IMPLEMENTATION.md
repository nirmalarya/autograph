# TLS 1.3 Implementation

## Overview

All Autograph microservices now support TLS 1.3 encryption for secure communication.

## Features

### ✅ TLS 1.3 Only
- All services configured to accept **only** TLS 1.3 connections
- TLS 1.0, 1.1, and 1.2 are explicitly disabled
- Connections using older TLS versions are rejected

### ✅ Secure Cipher Suites
Services use only TLS 1.3 approved cipher suites:
- `TLS_AES_256_GCM_SHA384` (preferred)
- `TLS_CHACHA20_POLY1305_SHA256`
- `TLS_AES_128_GCM_SHA256`

### ✅ Certificate-Based Authentication
- X.509 certificates for server authentication
- Self-signed CA for development
- Subject Alternative Names (SAN) for all service hostnames

## Architecture

### Certificate Infrastructure

```
certs/
├── ca-cert.pem         # Certificate Authority (trust this in clients)
├── ca-key.pem          # CA private key (keep secure!)
├── server-cert.pem     # Server certificate
├── server-key.pem      # Server private key (keep secure!)
├── dhparam.pem         # Diffie-Hellman parameters
└── server-ext.cnf      # Certificate extensions
```

### Service Configuration

Each Python microservice includes TLS configuration in `src/main.py`:

```python
if tls_enabled:
    # Create SSL context for TLS 1.3
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
    ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
    ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)

    # TLS 1.3 cipher suites
    ssl_context.set_ciphers('TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256')

    # Disable older TLS versions
    ssl_context.options |= ssl.OP_NO_TLSv1
    ssl_context.options |= ssl.OP_NO_TLSv1_1
    ssl_context.options |= ssl.OP_NO_TLSv1_2

    uvicorn.run(app, host="0.0.0.0", port=port, ssl=ssl_context)
```

## Configuration

### Environment Variables

- `TLS_ENABLED`: Enable/disable TLS (default: `false`)
  - Set to `true`, `1`, or `yes` to enable TLS
  - Set to `false`, `0`, or `no` to disable TLS

### Docker Compose

All Python services include:
1. TLS_ENABLED environment variable
2. Certificate volume mount: `./certs:/app/certs:ro`

Example:
```yaml
services:
  api-gateway:
    environment:
      TLS_ENABLED: ${TLS_ENABLED:-false}
    volumes:
      - ./certs:/app/certs:ro
```

## Usage

### Generating Certificates

For development/testing:
```bash
bash scripts/generate_tls_certs.sh
```

This creates:
- Self-signed CA certificate
- Server certificate with SANs for all services
- DH parameters for perfect forward secrecy

### Enabling TLS

1. Set environment variable:
```bash
echo "TLS_ENABLED=true" >> .env
```

2. Restart services:
```bash
docker-compose down
docker-compose up -d
```

### Disabling TLS

1. Update environment variable:
```bash
sed -i '' 's/TLS_ENABLED=true/TLS_ENABLED=false/' .env
```

2. Restart services:
```bash
docker-compose restart
```

## Testing

### Automated Validation

Run the TLS 1.3 validation script:
```bash
python3 validate_feature58_tls13.py
```

This tests:
1. ✅ TLS 1.2 connections are **rejected**
2. ✅ TLS 1.3 connections are **accepted**
3. ✅ Valid certificates are presented
4. ✅ Secure cipher suites are used

### Manual Testing

#### Test TLS 1.3 connection:
```bash
python3 -c "
import ssl, socket
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.minimum_version = ssl.TLSVersion.TLSv1_3
context.maximum_version = ssl.TLSVersion.TLSv1_3
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

with socket.create_connection(('localhost', 8443)) as sock:
    with context.wrap_socket(sock) as ssock:
        print(f'Connected with {ssock.version()}')
        print(f'Cipher: {ssock.cipher()}')
"
```

#### Verify TLS 1.2 is rejected:
```bash
python3 -c "
import ssl, socket
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.minimum_version = ssl.TLSVersion.TLSv1_2
context.maximum_version = ssl.TLSVersion.TLSv1_2
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

try:
    with socket.create_connection(('localhost', 8443)) as sock:
        with context.wrap_socket(sock) as ssock:
            print('ERROR: TLS 1.2 should be rejected!')
except ssl.SSLError as e:
    print(f'✓ TLS 1.2 correctly rejected: {e}')
"
```

## Services with TLS Support

All Python microservices support TLS 1.3:

| Service | Default Port | TLS Port | Status |
|---------|-------------|----------|--------|
| api-gateway | 8080 | 8443 | ✅ |
| auth-service | 8085 | 8445 | ✅ |
| diagram-service | 8082 | 8442 | ✅ |
| ai-service | 8084 | 8444 | ✅ |
| collaboration-service | 8083 | 8443 | ✅ |
| git-service | 8087 | 8447 | ✅ |
| export-service | 8097 | 8497 | ✅ |
| integration-hub | 8099 | 8499 | ✅ |

## Security Considerations

### Development vs Production

**Development:**
- Self-signed certificates are acceptable
- Certificate warnings can be ignored
- Same certificate used across all services

**Production:**
- Use certificates from a trusted CA
- Unique certificates per service (or wildcard certificate)
- Implement certificate rotation
- Enable mutual TLS for service-to-service communication

### Best Practices

1. **Certificate Management**
   - Rotate certificates before expiry
   - Keep private keys secure (never commit to git)
   - Use strong key lengths (4096-bit RSA or 256-bit ECC)

2. **Monitoring**
   - Monitor certificate expiry dates
   - Alert on TLS handshake failures
   - Track cipher suite usage

3. **Updates**
   - Keep OpenSSL/Python SSL libraries up to date
   - Review TLS 1.3 security advisories
   - Test certificate renewal procedures

## Troubleshooting

### "Certificate verify failed"
The self-signed CA is not trusted by default. Either:
- Disable verification in development
- Add CA certificate to system trust store

### "Connection refused" on TLS port
- Verify TLS_ENABLED=true in .env
- Check service logs for SSL errors
- Ensure certificates exist in ./certs/

### "SSL protocol version mismatch"
- Client must support TLS 1.3
- Check Python version (3.7+ required for TLS 1.3)
- Verify no proxy/firewall downgrading connection

## References

- [RFC 8446: TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446)
- [Python SSL Documentation](https://docs.python.org/3/library/ssl.html)
- [TLS 1.3 Cipher Suites](https://www.iana.org/assignments/tls-parameters/tls-parameters.xhtml#tls-parameters-4)
