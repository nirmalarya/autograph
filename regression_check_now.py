#!/usr/bin/env python3
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Get baseline count from file
with open('baseline_features.txt', 'r') as f:
    baseline_count = int(f.read().strip().split(':')[1].strip())

# Count current passing baseline features (non-enhancement/bugfix)
current_baseline = len([
    f for f in features
    if f.get('category') not in ['enhancement', 'bugfix'] and f.get('passes')
])

total_passing = len([f for f in features if f.get('passes')])

print('='*60)
print('REGRESSION CHECK')
print('='*60)
print(f'Baseline features (original): {baseline_count}')
print(f'Current baseline passing: {current_baseline}')
print(f'Total passing features: {total_passing}')
print()

if current_baseline < baseline_count:
    print('❌ REGRESSION DETECTED!')
    print(f'Lost {baseline_count - current_baseline} baseline features!')
    print('Some existing features broke!')
    exit(1)
else:
    print('✅ No regressions - baseline features intact')
    if total_passing > baseline_count:
        print(f'✅ Progress: Added {total_passing - baseline_count} new passing features')
    print()
    print('Safe to continue work!')
