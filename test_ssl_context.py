#!/usr/bin/env python3
"""Test if we can set SSL context on uvicorn Config"""
import uvicorn.config
import ssl
import os

# Create a dummy config
config = uvicorn.config.Config(
    "fake:app",
    ssl_keyfile="/tmp/test.pem",
    ssl_certfile="/tmp/test.pem"
)

print(f"Config type: {type(config)}")
print(f"Has 'ssl' attribute: {hasattr(config, 'ssl')}")

# Check all attributes
ssl_attrs = [attr for attr in dir(config) if not attr.startswith('_')]
print(f"\nAll Config attributes: {ssl_attrs}")

# Try to load ssl
try:
    config.load()
    print(f"\nAfter load(), has 'ssl' attribute: {hasattr(config, 'ssl')}")
    if hasattr(config, 'ssl'):
        print(f"SSL attribute type: {type(config.ssl)}")
except Exception as e:
    print(f"Error during load(): {e}")
