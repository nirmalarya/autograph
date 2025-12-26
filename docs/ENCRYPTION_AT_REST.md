# Encryption at Rest

This document describes the encryption at rest capabilities implemented in Autograph for enterprise compliance.

## Overview

Autograph implements database-level encryption at rest using PostgreSQL's `pgcrypto` extension, providing cryptographic functions to encrypt sensitive data before storing it on disk.

## Features

### 1. Database Encryption (pgcrypto)

The `pgcrypto` extension is automatically enabled during database initialization and provides:

- **Symmetric encryption/decryption**: Using `pgp_sym_encrypt()` and `pgp_sym_decrypt()`
- **Hash functions**: SHA-256, SHA-512, MD5
- **Password hashing**: Using bcrypt, crypt, etc.
- **Random data generation**: For cryptographic purposes

### 2. Encryption Key Management

Encryption keys are managed through environment variables:

- `SECRETS_MASTER_KEY`: Master encryption key for application-level encryption
- Keys should be rotated regularly and stored securely (e.g., HashiCorp Vault, AWS KMS)

### 3. Connection Encryption

While SSL/TLS is optional in development, it should be enabled in production:

```yaml
# Production configuration
POSTGRES_SSL_MODE=require
POSTGRES_SSL_CERT=/path/to/client-cert.pem
POSTGRES_SSL_KEY=/path/to/client-key.pem
POSTGRES_SSL_ROOT_CERT=/path/to/ca-cert.pem
```

## Usage Examples

### Encrypting Data

```sql
-- Encrypt data before storing
INSERT INTO sensitive_table (encrypted_column)
VALUES (pgp_sym_encrypt('sensitive data', 'encryption-key'));
```

### Decrypting Data

```sql
-- Decrypt data when retrieving
SELECT pgp_sym_decrypt(encrypted_column, 'encryption-key') AS decrypted_data
FROM sensitive_table;
```

### Encrypting with Base64 Encoding

```sql
-- Encrypt and encode as base64 for text storage
SELECT encode(
    pgp_sym_encrypt('sensitive data', 'encryption-key'),
    'base64'
) AS encrypted_base64;

-- Decrypt from base64
SELECT pgp_sym_decrypt(
    decode('base64_encrypted_data', 'base64'),
    'encryption-key'
) AS decrypted_data;
```

## Production Recommendations

### 1. Enable SSL/TLS for Database Connections

Update `docker-compose.yml`:

```yaml
postgres:
  command:
    - postgres
    - -c
    - ssl=on
    - -c
    - ssl_cert_file=/etc/ssl/certs/server.crt
    - -c
    - ssl_key_file=/etc/ssl/private/server.key
```

### 2. Use Volume-Level Encryption

For complete encryption at rest, use encrypted volumes:

**Linux (LUKS/dm-crypt):**
```bash
# Create encrypted volume
cryptsetup luksFormat /dev/sdb
cryptsetup open /dev/sdb postgres_encrypted

# Mount encrypted volume
mount /dev/mapper/postgres_encrypted /var/lib/postgresql/data
```

**Docker Volume with Encryption:**
```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: encrypted
      device: /dev/mapper/postgres_encrypted
```

### 3. Key Rotation

Implement regular key rotation:

```sql
-- Rotate encryption keys
UPDATE sensitive_table
SET encrypted_column = pgp_sym_encrypt(
    pgp_sym_decrypt(encrypted_column, 'old-key'),
    'new-key'
);
```

### 4. Use Key Management Services

In production, integrate with enterprise key management:

- **HashiCorp Vault**: Store and rotate encryption keys
- **AWS KMS**: Envelope encryption for data keys
- **Azure Key Vault**: Centralized key management
- **GCP Cloud KMS**: Cloud-native key management

## Security Considerations

1. **Never hardcode encryption keys** - Use environment variables or key management services
2. **Use strong encryption keys** - Minimum 32 bytes, cryptographically random
3. **Enable SSL/TLS** - Encrypt data in transit
4. **Implement key rotation** - Regular rotation of encryption keys
5. **Audit access** - Log all access to encrypted data
6. **Backup encrypted** - Ensure backups are also encrypted

## Compliance

This implementation supports compliance with:

- **GDPR**: Data protection and privacy requirements
- **HIPAA**: Healthcare data encryption requirements
- **PCI DSS**: Payment card data encryption requirements
- **SOC 2**: Security controls for data protection
- **ISO 27001**: Information security management

## Testing

Run the encryption at rest test:

```bash
python3 test_feature_545_encryption_at_rest.py
```

This test verifies:
- pgcrypto extension is enabled
- Encryption/decryption functions work correctly
- Data can be stored encrypted and retrieved
- Connection security is configured

## Monitoring

Monitor encryption health:

```sql
-- Check extension status
SELECT * FROM pg_extension WHERE extname = 'pgcrypto';

-- Check SSL connections
SELECT datname, usename, ssl, client_addr
FROM pg_stat_ssl
JOIN pg_stat_activity USING (pid);

-- Monitor encrypted data usage
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename LIKE '%encrypted%';
```

## Troubleshooting

### pgcrypto Not Available

```sql
-- Enable the extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

### Decryption Failures

Check that:
1. Encryption key matches the one used for encryption
2. Data is properly encoded/decoded (base64, hex, etc.)
3. Data hasn't been corrupted

### Performance Issues

- Consider encrypting only sensitive columns, not entire tables
- Use indexed columns for searching encrypted data
- Implement caching for frequently accessed encrypted data
- Use hardware acceleration for encryption (AES-NI)

## References

- [PostgreSQL pgcrypto Documentation](https://www.postgresql.org/docs/current/pgcrypto.html)
- [PostgreSQL SSL Support](https://www.postgresql.org/docs/current/ssl-tcp.html)
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
