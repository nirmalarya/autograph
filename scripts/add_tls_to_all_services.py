#!/usr/bin/env python3
"""
Add TLS 1.3 support to all Python microservices
"""
import re
from pathlib import Path

TLS_TEMPLATE = '''if __name__ == "__main__":
    import uvicorn
    import ssl
    from pathlib import Path

    port = int(os.getenv("{PORT_VAR}", "{DEFAULT_PORT}"))
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
        ssl_context.set_ciphers('TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256')

        # Security options
        ssl_context.options |= ssl.OP_NO_TLSv1
        ssl_context.options |= ssl.OP_NO_TLSv1_1
        ssl_context.options |= ssl.OP_NO_TLSv1_2
        ssl_context.options |= ssl.OP_NO_COMPRESSION

        logger.info(f"Starting {SERVICE_NAME} with TLS 1.3 on port {{port}}")
        uvicorn.run(app, host="0.0.0.0", port=port, ssl=ssl_context)
    else:
        logger.info(f"Starting {SERVICE_NAME} without TLS on port {{port}}")
        uvicorn.run(app, host="0.0.0.0", port=port)'''

# Service configurations
SERVICES = {
    "auth-service": ("AUTH_SERVICE_PORT", "8085"),
    "diagram-service": ("DIAGRAM_SERVICE_PORT", "8082"),
    "ai-service": ("AI_SERVICE_PORT", "8084"),
    "collaboration-service": ("COLLABORATION_SERVICE_PORT", "8083"),
    "git-service": ("GIT_SERVICE_PORT", "8087"),
    "export-service": ("EXPORT_SERVICE_PORT", "8097"),
    "integration-hub": ("INTEGRATION_HUB_PORT", "8099"),
}


def update_service(service_name: str, port_var: str, default_port: str):
    """Update a service's main.py to support TLS"""
    main_file = Path(f"services/{service_name}/src/main.py")

    if not main_file.exists():
        print(f"  ✗ {service_name}: main.py not found")
        return False

    # Read the file
    content = main_file.read_text()

    # Find the current if __name__ == "__main__" block
    pattern = r'if __name__ == "__main__":\s+import uvicorn\s+uvicorn\.run\([^)]+\)'

    if not re.search(pattern, content):
        print(f"  ✗ {service_name}: Could not find uvicorn.run pattern")
        return False

    # Create the new TLS-enabled code
    tls_code = TLS_TEMPLATE.format(
        PORT_VAR=port_var,
        DEFAULT_PORT=default_port,
        SERVICE_NAME=service_name
    )

    # Replace the old code with new TLS-enabled code
    new_content = re.sub(pattern, tls_code, content)

    # Backup the original
    backup_file = main_file.with_suffix('.py.tls_backup')
    main_file.rename(backup_file)

    # Write the new content
    main_file.write_text(new_content)

    print(f"  ✓ {service_name}: Updated with TLS support")
    print(f"    Backup: {backup_file}")
    return True


def main():
    print("=" * 80)
    print("Adding TLS 1.3 Support to All Services")
    print("=" * 80)
    print()

    success_count = 0
    for service_name, (port_var, default_port) in SERVICES.items():
        print(f"Processing {service_name}...")
        if update_service(service_name, port_var, default_port):
            success_count += 1

    print()
    print(f"Updated {success_count}/{len(SERVICES)} services")
    print()
    print("Note: API Gateway was already updated manually")


if __name__ == "__main__":
    main()
