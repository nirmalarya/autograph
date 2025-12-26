#!/usr/bin/env python3
"""Mark Feature #431 as passing."""

import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Feature 431 is at index 430 (0-based)
features[430]['passes'] = True

with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✅ Feature #431 marked as passing")
print(f"Total features: {len(features)}")
print(f"Passing features: {len([f for f in features if f.get('passes')])}")
