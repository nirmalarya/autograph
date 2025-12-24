#!/usr/bin/env python3
import json

with open('feature_list.json', 'r') as f:
    data = json.load(f)

# Find all not passing features
not_passing = []
for i, f in enumerate(data):
    if not f.get('passes', False):
        not_passing.append((i, f))

print(f"Total features: {len(data)}")
print(f"Passing: {sum(1 for f in data if f.get('passes', False))}")
print(f"Not passing: {len(not_passing)}")

# Show first 20 not passing features
print("\n\nFirst 20 not passing features:")
for idx, (i, f) in enumerate(not_passing[:20], 1):
    desc = f.get('description', 'No description')
    cat = f.get('category', 'Unknown')
    print(f"\n{idx}. Feature #{i} ({cat})")
    print(f"   Description: {desc}")
    if 'steps' in f and len(f['steps']) > 0:
        print(f"   First step: {f['steps'][0][:100]}")
