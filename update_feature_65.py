#!/usr/bin/env python3
"""Update Feature 65 to passing status"""

import json

# Read feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update feature 65 (index 64)
features[64]['passes'] = True

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✓ Feature 65 marked as passing")
print(f"Total passing: {sum(1 for f in features if f.get('passes', False))}/{len(features)}")
