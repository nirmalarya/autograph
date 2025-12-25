#!/usr/bin/env python3
"""Mark feature #63 (GDPR Compliance) as passing."""
import json
from pathlib import Path

# Read feature list
project_root = Path(__file__).parent
with open(project_root / 'spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Find feature #63 (index 62 - zero-indexed)
if len(features) > 62:
    feature_63 = features[62]
    print(f"Feature #{feature_63.get('id', 63)}: {feature_63.get('description', 'GDPR Compliance')}")
    print(f"Current status: {'PASSING' if feature_63.get('passes') else 'FAILING'}")

    # Update to passing
    feature_63['passes'] = True
    feature_63['name'] = "GDPR Compliance"
    feature_63['test_file'] = "validate_feature63_gdpr_simple.py"

    # Write back
    with open(project_root / 'spec/feature_list.json', 'w') as f:
        json.dump(features, f, indent=2)

    print(f"\n✅ Feature #63 marked as PASSING!")
    print(f"Total passing: {len([f for f in features if f.get('passes')])}/{len(features)}")
else:
    print("❌ Feature #63 not found in feature list")
