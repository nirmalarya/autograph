#!/usr/bin/env python3
"""Update feature #289 to passing status"""

import json
from datetime import datetime

# Read current feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update feature #289 (index 288)
feature_289 = features[288]
feature_289['passes'] = True
feature_289['validation_reason'] = "Beta drag-and-drop feature implemented with SVG manipulation and position comment injection"
feature_289['validated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
feature_289['validation_method'] = "automated_code_inspection"

# Write updated feature list
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✅ Feature #289 marked as passing")
print(f"   Title: {feature_289.get('description')}")
print(f"   Validation: {feature_289['validation_reason']}")
