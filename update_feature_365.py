#!/usr/bin/env python3
"""Mark Feature #365 as passing."""

import json

# Read feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Feature #365 is at index 364 (0-indexed)
features[364]['passes'] = True

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✅ Feature #365 marked as passing")

# Count progress
total = len(features)
passing = len([f for f in features if f.get('passes')])
print(f"Progress: {passing}/{total} ({passing*100//total}%)")
