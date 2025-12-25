#!/usr/bin/env python3
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

feature = features[47]  # Feature #48 is at index 47
print("=== FEATURE #48 DETAILS ===\n")
print(json.dumps(feature, indent=2))
