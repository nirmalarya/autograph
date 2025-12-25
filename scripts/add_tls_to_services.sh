#!/bin/bash
# Add TLS 1.3 configuration to all Python services

set -e

echo "Adding TLS 1.3 configuration to all services..."

SERVICES=(
    "auth-service"
    "diagram-service"
    "ai-service"
    "collaboration-service"
    "git-service"
    "export-service"
    "integration-hub"
)

TLS_CODE='if __name__ == "__main__":
    import uvicorn
    import ssl
    from pathlib import Path

    port = int(os.getenv("SERVICE_PORT", "8000"))
    tls_enabled = os.getenv("TLS_ENABLED", "false").lower() in ("true", "1", "yes")

    if tls_enabled:
        # Configure TLS 1.3
        cert_dir = Path(__file__).parent.parent.parent.parent / "certs"
        cert_file = str(cert_dir / "server-cert.pem")
        key_file = str(cert_dir / "server-key.pem")

        # Create SSL context for TLS 1.3
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
        ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)

        # TLS 1.3 cipher suites
        ssl_context.set_ciphers('"'"'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256'"'"')

        # Security options
        ssl_context.options |= ssl.OP_NO_TLSv1
        ssl_context.options |= ssl.OP_NO_TLSv1_1
        ssl_context.options |= ssl.OP_NO_TLSv1_2
        ssl_context.options |= ssl.OP_NO_COMPRESSION

        logger.info(f"Starting service with TLS 1.3 on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, ssl=ssl_context)
    else:
        logger.info(f"Starting service without TLS on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)'

for service in "${SERVICES[@]}"; do
    main_file="services/$service/src/main.py"

    if [ -f "$main_file" ]; then
        echo "Processing $service..."

        # Create backup
        cp "$main_file" "$main_file.backup"

        # This would require manual editing for each service
        # as the port environment variable names differ
        echo "  - Backup created: $main_file.backup"
        echo "  - Manual update required for proper port variable"
    else
        echo "  - Skipping $service (main.py not found)"
    fi
done

echo ""
echo "✓ Backups created. Manual updates required for each service."
echo "  Use the TLS_CODE pattern above to update each service's __main__ block."
