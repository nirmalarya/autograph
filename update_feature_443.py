#!/usr/bin/env python3
"""Update feature #443 to passing status."""

import json
from datetime import datetime

# Read feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update feature #443 (index 442)
if len(features) > 442:
    features[442]['passes'] = True
    features[442]['validated_at'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    features[442]['validation_method'] = 'automated'

    print(f"Updated feature #443: {features[442]['description']}")
    print(f"Status: passes = {features[442]['passes']}")
else:
    print(f"Error: Feature list only has {len(features)} features")
    exit(1)

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("\n✅ Feature #443 marked as passing in feature_list.json")
