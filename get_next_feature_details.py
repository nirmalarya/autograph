#!/usr/bin/env python3
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Find first failing feature
for i, feature in enumerate(features, 1):
    if not feature.get('passes', False):
        print(f"\n🎯 NEXT FEATURE: #{i}")
        print(json.dumps(feature, indent=2))
        break
