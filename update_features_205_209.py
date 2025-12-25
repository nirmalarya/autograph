#!/usr/bin/env python3
"""Mark features 205-209 as passing in feature_list.json."""
import json

# Read feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update features 205-209 (indices 204-208)
features_to_update = [204, 205, 206, 207, 208]

for idx in features_to_update:
    if idx < len(features):
        features[idx]['passes'] = True
        title = features[idx].get('title', features[idx].get('description', 'Unknown'))
        print(f"✅ Marked feature {idx+1} as passing: {title}")

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print(f"\n✅ Updated feature_list.json")
print(f"Total passing: {len([f for f in features if f.get('passes')])}/{len(features)}")
