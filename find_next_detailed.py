#!/usr/bin/env python3
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Find first 5 failing features
count = 0
for i, feature in enumerate(features):
    if not feature.get('passes', False):
        if count == 0:
            print(f"=== NEXT FEATURE TO IMPLEMENT ===\n")
        count += 1
        print(f"Feature #{i+1}")
        print(f"Description: {feature.get('description', 'N/A')}")
        print(f"Category: {feature.get('category', 'N/A')}")
        if 'steps' in feature and feature['steps']:
            print(f"Steps: {len(feature['steps'])} steps defined")
        print()

        if count >= 5:
            break

print(f"\nTotal failing features: {len([f for f in features if not f.get('passes', False)])}")
