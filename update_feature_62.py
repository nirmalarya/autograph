#!/usr/bin/env python3
import json

# Read feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update feature #62
features[61]['passes'] = True

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✅ Updated feature #62 to passing")

# Show progress
total = len(features)
passing = len([f for f in features if f.get('passes')])
print(f"Progress: {passing}/{total} features passing")
