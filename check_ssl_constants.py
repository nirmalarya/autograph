#!/usr/bin/env python3
import ssl

print(f"PROTOCOL_TLS_SERVER = {ssl.PROTOCOL_TLS_SERVER}")
print(f"PROTOCOL_TLS = {ssl.PROTOCOL_TLS}")

# Check if we can monkey-patch the SSL context creation
# The real solution: uvicorn creates SSL context in the server, we need to
# override it AFTER creation but BEFORE the server starts listening

print("\n" + "="*80)
print("The problem:")
print("="*80)
print("""
Uvicorn creates its SSL context internally from ssl_keyfile, ssl_certfile, and
ssl_version parameters. But it doesn't set minimum_version or maximum_version,
so it allows TLS version negotiation.

Solution: We need to monkey-patch or hook into the server creation to modify
the SSL context after uvicorn creates it but before it binds to the socket.
""")

print("\n" + "="*80)
print("Better approach:")
print("="*80)
print("""
Instead of using uvicorn.run() or uvicorn.Server(), we should:
1. Create the SSL context ourselves with TLS 1.3 enforcement
2. Create a raw socket with that SSL context
3. Use hypercorn or another ASGI server that supports custom SSL contexts
4. OR: Modify uvicorn's server implementation to accept an SSL context

For now, let's try to directly access and modify the server's SSL context.
""")
