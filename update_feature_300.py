#!/usr/bin/env python3
"""Update feature #300 to passing status"""

import json

# Read feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update feature at index 300
if len(features) > 300:
    features[300]['passes'] = True
    print(f"Updated feature at index 300:")
    print(f"  Description: {features[300].get('description', 'N/A')}")
    print(f"  Passes: {features[300]['passes']}")

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("\n✅ Feature list updated successfully!")

# Show progress
total = len(features)
passing = len([f for f in features if f.get('passes')])
print(f"\nProgress: {passing}/{total} features ({(passing/total)*100:.1f}%)")
