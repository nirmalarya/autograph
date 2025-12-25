#!/usr/bin/env python3
import json

# Read feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update features 317-326
for i in range(317, 327):
    features[i]['passes'] = True
    features[i]['validation_script'] = 'validate_features_317_326_ai_advanced.py'

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✅ Updated features 317-326 to passing")
print(f"Total: {len(features)}, Passing: {len([f for f in features if f.get('passes')])}")
