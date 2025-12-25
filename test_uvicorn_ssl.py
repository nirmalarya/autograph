#!/usr/bin/env python3
"""Test uvicorn SSL configuration"""
import uvicorn
import ssl

# Check what parameters uvicorn.run accepts
import inspect
sig = inspect.signature(uvicorn.run)
print("uvicorn.run parameters:")
for param_name, param in sig.parameters.items():
    if 'ssl' in param_name.lower():
        print(f"  {param_name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'Any'}")

print("\n" + "="*80)
print("Recommended approach for TLS 1.3:")
print("="*80)
print("""
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)

# Option 1: Pass ssl_context directly to uvicorn.run()
uvicorn.run(app, host="0.0.0.0", port=8080, ssl=ssl_context)

# Option 2: Use ssl_keyfile and ssl_certfile (but this doesn't allow TLS version control)
uvicorn.run(app, host="0.0.0.0", port=8080, ssl_keyfile=key_file, ssl_certfile=cert_file)
""")
