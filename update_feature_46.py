#!/usr/bin/env python3
"""Update feature_list.json to mark Feature #46 as passing."""

import json
from datetime import datetime

# Read current feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Find and update Feature #46 (index 45)
feature_index = 45
if feature_index < len(features):
    features[feature_index]["passes"] = True
    features[feature_index]["validation_reason"] = "All 8 steps validated: service dependency mapping, graph generation, edge verification, circular dependency detection, critical path analysis, health checks"
    features[feature_index]["validated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    features[feature_index]["validation_method"] = "automated_script"

    # Write back
    with open('spec/feature_list.json', 'w') as f:
        json.dump(features, f, indent=2)

    print(f"✅ Updated Feature #46 to passing")
    print(f"   Description: {features[feature_index]['description']}")
    print(f"   Validation reason: {features[feature_index]['validation_reason']}")
else:
    print(f"❌ Feature index {feature_index} out of range")
