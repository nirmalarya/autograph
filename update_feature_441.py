#!/usr/bin/env python3
import json

# Load feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Find and update feature 441 (index 440)
feature_index = 440

if feature_index < len(features):
    features[feature_index]['passes'] = True
    print(f"Updated feature #{feature_index + 1}: {features[feature_index]['description']}")
    print(f"Status: passes = {features[feature_index]['passes']}")
else:
    print(f"Feature index {feature_index} not found")
    exit(1)

# Save updated feature list
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

# Count passing features
passing = len([f for f in features if f.get('passes')])
total = len(features)

print(f"\nTotal passing features: {passing}/{total} ({passing*100/total:.1f}%)")
