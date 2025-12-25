#!/usr/bin/env python3
import json

# Read feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update feature 308
features[308]['passes'] = True
features[308]['validation_script'] = 'validate_feature_308_multi_cursor.py'

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✅ Updated feature 308 to passing")
print(f"Total: {len(features)}, Passing: {len([f for f in features if f.get('passes')])}")
