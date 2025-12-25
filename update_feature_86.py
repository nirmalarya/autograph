#!/usr/bin/env python3
"""Update feature #86 to mark it as passing."""

import json

# Read feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Find and update feature #86
for i, feature in enumerate(features):
    if feature.get('description') == "SAML group mapping: SSO groups map to AutoGraph roles":
        print(f"Found feature #86 at index {i}")
        print(f"Current status: passes={feature.get('passes')}")
        feature['passes'] = True
        print(f"Updated status: passes={feature.get('passes')}")
        break

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("\n✅ Feature #86 marked as passing")

# Count passing features
passing = len([f for f in features if f.get('passes')])
total = len(features)
print(f"\nProgress: {passing}/{total} features passing ({passing/total*100:.1f}%)")
