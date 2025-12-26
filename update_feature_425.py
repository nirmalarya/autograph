#!/usr/bin/env python3
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Mark feature #425 as passing
features[425]['passes'] = True

with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✅ Feature #425 marked as passing")
print(f"Total passing: {len([f for f in features if f.get('passes')])}/{len(features)}")
