#!/usr/bin/env python3
"""Update Dockerfiles to use startup.py for TLS support."""
from pathlib import Path
import re

services = [
    "api-gateway",
    "auth-service",
    "diagram-service",
    "ai-service",
    "collaboration-service",
    "git-service",
    "export-service",
    "integration-hub",
]

for service_name in services:
    dockerfile_path = Path(f"services/{service_name}/Dockerfile")

    if not dockerfile_path.exists():
        print(f"❌ {service_name}: Dockerfile not found")
        continue

    content = dockerfile_path.read_text()

    # Check if already updated
    if "startup.py" in content:
        print(f"⏭️  {service_name}: already updated")
        continue

    # Add COPY startup.py before the EXPOSE directive
    if "COPY src/ ./src/" in content and "COPY startup.py" not in content:
        content = content.replace(
            "# Copy application code\nCOPY src/ ./src/",
            "# Copy application code\nCOPY src/ ./src/\nCOPY startup.py ."
        )

    # Replace CMD line to use startup.py
    # Match pattern like: CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8084"]
    cmd_pattern = r'CMD \["uvicorn",\s*"src\.main:app",.*?\]'
    if re.search(cmd_pattern, content):
        content = re.sub(cmd_pattern, 'CMD ["python", "startup.py"]', content)

    dockerfile_path.write_text(content)
    print(f"✅ {service_name}: Dockerfile updated")

print("\n✓ All Dockerfiles updated")
