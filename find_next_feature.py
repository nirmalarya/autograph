#!/usr/bin/env python3
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Find first failing feature
for feature in features:
    if not feature.get('passes', False):
        print(f"Next feature to implement:")
        print(f"ID: {feature.get('id', 'N/A')}")
        print(f"Title: {feature.get('title', 'N/A')}")
        print(f"Description: {feature.get('description', 'N/A')}")
        print(f"Category: {feature.get('category', 'N/A')}")
        break
