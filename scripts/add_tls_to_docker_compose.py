#!/usr/bin/env python3
"""
Add TLS support to all Python services in docker-compose.yml
"""
import yaml
from pathlib import Path


def update_docker_compose():
    """Add TLS_ENABLED environment variable and certs volume to all Python services"""

    compose_file = Path("docker-compose.yml")

    # Read the file as text (to preserve formatting)
    content = compose_file.read_text()

    # Services to update (Python microservices)
    python_services = [
        "diagram-service",
        "ai-service",
        "collaboration-service",
        "git-service",
        "export-service",
        "integration-hub",
        "api-gateway",
    ]

    print("=" * 80)
    print("Adding TLS Support to Docker Compose")
    print("=" * 80)
    print()

    updated_count = 0

    for service in python_services:
        print(f"Processing {service}...")

        # Find the service in the content
        service_start = content.find(f"  {service}:")
        if service_start == -1:
            print(f"  ✗ Service not found in docker-compose.yml")
            continue

        # Find the environment section for this service
        env_start = content.find("environment:", service_start)
        if env_start == -1:
            print(f"  ✗ No environment section found")
            continue

        # Find the end of the environment section (next top-level key)
        next_section = content.find("\n    ports:", env_start)
        if next_section == -1:
            next_section = content.find("\n    depends_on:", env_start)

        if next_section == -1:
            print(f"  ✗ Could not determine end of environment section")
            continue

        # Check if TLS_ENABLED already exists
        env_section = content[env_start:next_section]
        if "TLS_ENABLED" in env_section:
            print(f"  ✓ TLS_ENABLED already present")
        else:
            # Add TLS_ENABLED before the ports/depends_on section
            tls_env = "\n      TLS_ENABLED: ${TLS_ENABLED:-false}"
            content = content[:next_section] + tls_env + content[next_section:]
            print(f"  ✓ Added TLS_ENABLED environment variable")

        # Now add volumes section if it doesn't exist
        # Find the service section again (content may have changed)
        service_start = content.find(f"  {service}:")
        service_end = content.find("\n  ", service_start + 1)
        if service_end == -1:
            service_end = len(content)

        service_section = content[service_start:service_end]

        if "volumes:" in service_section and "./certs:/app/certs" in service_section:
            print(f"  ✓ Certs volume already mounted")
        else:
            # Find where to add volumes (after ports, before depends_on)
            ports_end = content.find("\n    depends_on:", service_start)
            if ports_end == -1:
                ports_end = content.find("\n    healthcheck:", service_start)

            if ports_end != -1:
                if "volumes:" not in service_section:
                    volumes_section = "\n    volumes:\n    - ./certs:/app/certs:ro"
                    content = content[:ports_end] + volumes_section + content[ports_end:]
                    print(f"  ✓ Added certs volume mount")
                else:
                    # Volumes section exists, add certs mount
                    volumes_start = content.find("volumes:", service_start)
                    volumes_end = content.find("\n    ", volumes_start + 1)
                    certs_mount = "\n    - ./certs:/app/certs:ro"
                    content = content[:volumes_end] + certs_mount + content[volumes_end:]
                    print(f"  ✓ Added certs to existing volumes")

        updated_count += 1
        print()

    # Write the updated content
    compose_file.write_text(content)

    print(f"Updated {updated_count}/{len(python_services)} services")
    print()
    print("✓ docker-compose.yml updated successfully")
    print()
    print("Note: auth-service was already updated manually")


if __name__ == "__main__":
    update_docker_compose()
