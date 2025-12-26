#!/usr/bin/env python3
"""Update feature #519 to passing status."""

import json

# Read feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Find and update feature #519 (index 518)
if len(features) > 518:
    feature = features[518]
    if 'PDF file size' in feature.get('description', ''):
        features[518]['passes'] = True
        features[518]['test_file'] = 'test_pdf_optimization_feature519.py'
        print(f"✓ Updated feature at index 518")
        print(f"  Description: {feature['description']}")
        print(f"  Status: passing")
    else:
        print(f"❌ Feature at index 518 doesn't match expected description")
        print(f"   Found: {feature.get('description', 'N/A')}")
else:
    print(f"❌ Feature list has only {len(features)} features")

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("\n✅ Feature list updated successfully")
