#!/usr/bin/env python3
"""Create startup.py scripts for all Python services."""
from pathlib import Path

STARTUP_SCRIPT_TEMPLATE = '''#!/usr/bin/env python3
"""Startup script for {service_name} with TLS support."""
import os
import ssl
import uvicorn
from pathlib import Path

# Import the FastAPI app
from src.main import app

if __name__ == "__main__":
    port = int(os.getenv("{port_env}", "{default_port}"))
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

        print(f"Starting {service_name} with TLS 1.3 on port {{port}}")
        uvicorn.run(app, host="0.0.0.0", port=port, ssl=ssl_context)
    else:
        print(f"Starting {service_name} without TLS on port {{port}}")
        uvicorn.run(app, host="0.0.0.0", port=port)
'''

services = [
    {"name": "api-gateway", "port_env": "API_GATEWAY_PORT", "default_port": "8080"},
    {"name": "auth-service", "port_env": "AUTH_SERVICE_PORT", "default_port": "8085"},
    {"name": "diagram-service", "port_env": "DIAGRAM_SERVICE_PORT", "default_port": "8082"},
    {"name": "ai-service", "port_env": "AI_SERVICE_PORT", "default_port": "8084"},
    {"name": "collaboration-service", "port_env": "COLLABORATION_SERVICE_PORT", "default_port": "8083"},
    {"name": "git-service", "port_env": "GIT_SERVICE_PORT", "default_port": "8087"},
    {"name": "export-service", "port_env": "EXPORT_SERVICE_PORT", "default_port": "8097"},
    {"name": "integration-hub", "port_env": "INTEGRATION_HUB_PORT", "default_port": "8099"},
]

for service in services:
    service_dir = Path(f"services/{service['name']}")
    if not service_dir.exists():
        print(f"❌ {service['name']}: directory not found")
        continue

    startup_file = service_dir / "startup.py"
    content = STARTUP_SCRIPT_TEMPLATE.format(
        service_name=service["name"],
        port_env=service["port_env"],
        default_port=service["default_port"]
    )

    startup_file.write_text(content)
    print(f"✅ {service['name']}: created startup.py")

print("\n✓ All startup scripts created")
