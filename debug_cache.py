#!/usr/bin/env python3
import requests

# Clear cache
requests.post('http://localhost:8084/api/ai/cache/clear')

# Make first request with specific diagram_type
r1 = requests.post('http://localhost:8084/api/ai/generate', json={
    'prompt': 'web server to database',
    'diagram_type': 'architecture'
})
result1 = r1.json()
print(f"Request diagram_type: 'architecture'")
print(f"Response diagram_type: '{result1.get('diagram_type')}'")
print(f"Tokens: {result1.get('tokens_used')}")

# Make second request with same params
r2 = requests.post('http://localhost:8084/api/ai/generate', json={
    'prompt': 'web server to database',
    'diagram_type': 'architecture'
})
result2 = r2.json()
print(f"\nSecond request:")
print(f"Response diagram_type: '{result2.get('diagram_type')}'")
print(f"Tokens: {result2.get('tokens_used')}")
print(f"Cached: {'[CACHED]' in result2.get('explanation', '')}")

# Check what's in cache
stats = requests.get('http://localhost:8084/api/ai/cache/stats').json()
entries = stats.get('cache_statistics', {}).get('entries', [])
if entries:
    print(f"\nCache entry:")
    print(f"  diagram_type in cache: '{entries[0].get('diagram_type')}'")
    print(f"  hits: {entries[0].get('cache_hits')}")
