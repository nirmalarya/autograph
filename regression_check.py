#!/usr/bin/env python3
"""
Regression Check Script
Ensures baseline features remain passing after changes
"""

import json

# Read baseline
with open('baseline_features.txt', 'r') as f:
    baseline_text = f.read().strip()
    baseline_count = int(baseline_text.split()[-1])

# Read current feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Count baseline features (all features that are not enhancement/bugfix)
baseline_passing = len([
    f for f in features
    if f.get('category') not in ['enhancement', 'bugfix'] and f.get('passes')
])

total_passing = len([f for f in features if f.get('passes')])

print("=" * 60)
print("REGRESSION CHECK")
print("=" * 60)
print(f"Baseline expected: {baseline_count}")
print(f"Baseline current:  {baseline_passing}")
print(f"Total passing:     {total_passing}/{len(features)}")
print()

if baseline_passing < baseline_count:
    print("❌ REGRESSION DETECTED!")
    print(f"Lost {baseline_count - baseline_passing} baseline features")
    exit(1)
elif baseline_passing > baseline_count:
    print(f"✅ Gained {baseline_passing - baseline_count} baseline features")
    print("✅ No regressions detected")
    # Update baseline
    with open('baseline_features.txt', 'w') as f:
        f.write(f"Baseline: {baseline_passing}\n")
    print(f"✅ Updated baseline to {baseline_passing}")
else:
    print("✅ Baseline features intact")
    print("✅ No regressions detected")

print("=" * 60)
