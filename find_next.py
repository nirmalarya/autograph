#!/usr/bin/env python3
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Find first failing feature
for i, feature in enumerate(features):
    if not feature.get('passes', False):
        print(f"Next feature to implement:")
        print(f"ID: {feature.get('id', i+1)}")
        print(f"Name: {feature.get('name', 'N/A')}")
        print(f"Description: {feature.get('description', 'N/A')}")
        print(f"Category: {feature.get('category', 'core')}")
        print(f"\nFull feature details:")
        print(json.dumps(feature, indent=2))
        break
