#!/usr/bin/env python3
"""Update feature #394 as passing"""
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update feature #394 (0-indexed as 393)
features[393]['passes'] = True

with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✓ Feature #394 marked as passing")
print(f"Progress: {len([f for f in features if f.get('passes')])} / {len(features)} features passing")
