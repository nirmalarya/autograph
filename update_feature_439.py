#!/usr/bin/env python3
"""Update feature #439 to passing status."""

import json

# Load feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update feature #439 (index 438)
features[438]["passes"] = True

# Save
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

# Print status
total = len(features)
passing = len([f for f in features if f.get('passes')])
print(f"✅ Feature #439 marked as passing")
print(f"Progress: {passing}/{total} features ({passing/total*100:.1f}%)")
