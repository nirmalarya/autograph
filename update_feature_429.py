#!/usr/bin/env python3
"""Update feature #429 to passing status."""
import json

# Load feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Find and update feature #429
for i, feature in enumerate(features):
    feature_id = feature.get('id', i + 1)
    if feature_id == 429:
        feature['passes'] = True
        print(f"✅ Updated feature #429 to passing")
        print(f"   Description: {feature['description']}")
        break

# Save updated list
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

# Show progress
total = len(features)
passing = len([f for f in features if f.get('passes')])
print(f"\n📊 Progress: {passing}/{total} features passing ({passing/total*100:.1f}%)")
