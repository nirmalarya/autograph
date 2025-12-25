#!/usr/bin/env python3
"""Quick regression check - verify baseline features still pass."""

import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Count baseline features (not enhancement/bugfix)
baseline_features = [f for f in features if f.get('category') not in ['enhancement', 'bugfix']]
baseline_passing = [f for f in baseline_features if f.get('passes', False)]

total_baseline = len(baseline_features)
passing_baseline = len(baseline_passing)

print(f"Baseline Features: {passing_baseline}/{total_baseline} passing")

if passing_baseline == total_baseline:
    print("✅ No regressions - all baseline features still passing")
    exit(0)
else:
    print(f"❌ REGRESSION DETECTED: {total_baseline - passing_baseline} baseline features failing")

    # Show failing features
    failing = [f for f in baseline_features if not f.get('passes', False)]
    print("\nFailing baseline features:")
    for f in failing[:10]:  # Show first 10
        print(f"  - Feature {f.get('id', '?')}: {f.get('description', 'N/A')}")

    exit(1)
