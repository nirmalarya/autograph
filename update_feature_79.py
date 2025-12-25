#!/usr/bin/env python3
"""Update feature #79 to passing."""

import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Find and update feature #79
for i, feature in enumerate(features):
    if i == 78:  # Feature #79 is at index 78 (0-based)
        feature['passes'] = True
        feature['id'] = 79
        print(f"Updated Feature #79:")
        print(f"  Description: {feature.get('description', 'N/A')}")
        print(f"  Passes: {feature['passes']}")
        break

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("\n✅ Feature #79 marked as passing in feature_list.json")

# Update baseline count
passing = len([f for f in features if f.get('passes', False)])
with open('baseline_features.txt', 'w') as f:
    f.write(f"Baseline: {passing}\n")

print(f"✅ Updated baseline_features.txt: {passing} features passing")
