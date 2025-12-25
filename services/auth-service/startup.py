#!/usr/bin/env python3
"""Startup script for auth-service with TLS support."""
import os
import ssl
import uvicorn
from pathlib import Path

# Import the FastAPI app
from src.main import app

if __name__ == "__main__":
    # Internal port should always be 8085 to match healthcheck
    port = 8085
    tls_enabled = os.getenv("TLS_ENABLED", "false").lower() in ("true", "1", "yes")

    if tls_enabled:
        # Configure TLS 1.3
        cert_dir = Path("/app/certs")
        cert_file = str(cert_dir / "server-cert.pem")
        key_file = str(cert_dir / "server-key.pem")

        print(f"Starting auth-service with TLS 1.3 ONLY on port {port}")

        # Create uvicorn config WITH ssl_keyfile/ssl_certfile
        # This ensures is_ssl=True and triggers SSL context creation
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=port,
            ssl_keyfile=key_file,
            ssl_certfile=cert_file,
        )

        # Load the config - this creates config.ssl with default SSL context
        config.load()

        # NOW replace config.ssl with our TLS 1.3-only context
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
        ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)
        ssl_context.options |= ssl.OP_NO_COMPRESSION

        # Replace the SSL context
        config.ssl = ssl_context

        # Create and run server with our custom SSL context
        server = uvicorn.Server(config)
        server.run()
    else:
        print(f"Starting auth-service without TLS on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
