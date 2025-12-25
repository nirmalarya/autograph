#!/usr/bin/env python3
"""Update features #305, #306, #307 to passing status"""

import json

# Read feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update features
updated = []
for idx in [305, 306, 307]:
    if len(features) > idx:
        features[idx]['passes'] = True
        updated.append(idx)
        print(f"✅ Updated feature #{idx}:")
        print(f"   Description: {features[idx].get('description', 'N/A')}")

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print(f"\n✅ Feature list updated successfully! ({len(updated)} features)")

# Show progress
total = len(features)
passing = len([f for f in features if f.get('passes')])
print(f"\nProgress: {passing}/{total} features ({(passing/total)*100:.1f}%)")
print(f"Remaining: {total - passing} features")
