#!/usr/bin/env python3
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

feature = features[45]  # Feature #46 is at index 45
print("=== FEATURE #46 DETAILS ===\n")
print(json.dumps(feature, indent=2))
