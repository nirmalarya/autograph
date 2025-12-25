#!/usr/bin/env python3
import json

# Read feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update feature #61 (index 60)
features[60]['passes'] = True

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✓ Feature #61 marked as passing")

# Show stats
total = len(features)
passing = len([f for f in features if f.get('passes')])
print(f"Progress: {passing}/{total} features passing")
