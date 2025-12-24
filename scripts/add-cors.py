#!/usr/bin/env python3
"""Add CORS middleware to all FastAPI services."""

import os
import re

CORS_CODE = """
# CORS Middleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""

def add_cors_to_service(service_path):
    """Add CORS middleware if not present."""
    main_py = os.path.join(service_path, "src", "main.py")
    
    if not os.path.exists(main_py):
        return False
    
    with open(main_py, 'r') as f:
        content = f.read()
    
    # Check if CORS already added
    if "CORSMiddleware" in content:
        print(f"✓ {service_path}: CORS already configured")
        return False
    
    # Find app = FastAPI() line
    app_match = re.search(r'app = FastAPI\([^)]*\)', content)
    if not app_match:
        print(f"✗ {service_path}: Could not find FastAPI app")
        return False
    
    # Insert CORS after app creation
    insert_pos = app_match.end()
    new_content = content[:insert_pos] + "\n" + CORS_CODE + content[insert_pos:]
    
    with open(main_py, 'w') as f:
        f.write(new_content)
    
    print(f"✅ {service_path}: CORS added!")
    return True

# Find all services
services_dir = "services"
for service in os.listdir(services_dir):
    service_path = os.path.join(services_dir, service)
    if os.path.isdir(service_path):
        add_cors_to_service(service_path)

print("\n✅ CORS configuration complete!")

