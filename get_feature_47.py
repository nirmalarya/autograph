#!/usr/bin/env python3
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

feature = features[46]  # Feature #47 is at index 46
print("=== FEATURE #47 DETAILS ===\n")
print(json.dumps(feature, indent=2))
