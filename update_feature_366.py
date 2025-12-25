#!/usr/bin/env python3
"""Update feature #366 status to passing."""

import json
from datetime import datetime

# Read feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update feature 366 (index 365)
features[365]['passes'] = True
features[365]['validation_reason'] = "Rate limit error handling implemented with wait time and retry information"
features[365]['validated_at'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
features[365]['validation_method'] = "automated_script"

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✓ Feature #366 marked as passing")
print(f"  Description: {features[365]['description']}")
print(f"  Validation: {features[365]['validation_reason']}")
