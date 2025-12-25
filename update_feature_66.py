#!/usr/bin/env python3
"""Update feature list to mark feature 66 as passing."""

import json

# Read the feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update feature 66 (index 65)
features[65]['passes'] = True

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✅ Feature 66 marked as passing")
print(f"Progress: {len([f for f in features if f.get('passes')])}/{len(features)} features")
