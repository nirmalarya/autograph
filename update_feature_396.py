#!/usr/bin/env python3
"""Update feature #396 to passing status."""
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Feature 396 is at index 395
features[395]['passes'] = True

with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✅ Updated feature #396 (index 395) to passing")
