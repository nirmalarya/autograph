#!/usr/bin/env python3
import json

# Read feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update features 309-316
for i in range(309, 317):
    features[i]['passes'] = True
    features[i]['validation_script'] = 'validate_features_309_316_ai_generation.py'

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✅ Updated features 309-316 to passing")
print(f"Total: {len(features)}, Passing: {len([f for f in features if f.get('passes')])}")
