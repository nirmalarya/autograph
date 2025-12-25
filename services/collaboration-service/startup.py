#!/usr/bin/env python3
"""Startup script for collaboration-service with TLS support."""
import os
import ssl
import uvicorn
from pathlib import Path

# Import the FastAPI app
from src.main import app

if __name__ == "__main__":
    port = int(os.getenv("COLLABORATION_SERVICE_PORT", "8083"))
    tls_enabled = os.getenv("TLS_ENABLED", "false").lower() in ("true", "1", "yes")

    if tls_enabled:
        # Configure TLS 1.3
        cert_dir = Path("/app/certs")
        cert_file = str(cert_dir / "server-cert.pem")
        key_file = str(cert_dir / "server-key.pem")

        # Create SSL context for TLS 1.3
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
        ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)

        # Security options (TLS 1.3 ciphers are enabled by default)
        ssl_context.options |= ssl.OP_NO_TLSv1
        ssl_context.options |= ssl.OP_NO_TLSv1_1
        ssl_context.options |= ssl.OP_NO_TLSv1_2
        ssl_context.options |= ssl.OP_NO_COMPRESSION

        print(f"Starting collaboration-service with TLS 1.3 on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, ssl=ssl_context)
    else:
        print(f"Starting collaboration-service without TLS on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
