#!/usr/bin/env python3
import json

with open('spec/feature_list.json') as f:
    features = json.load(f)

total = len(features)
passing = len([x for x in features if x.get('passes')])
failing = [f for f in features if not f.get('passes')]

print(f'Progress: {passing}/{total} features ({passing*100//total}%)')
print(f'Remaining: {total-passing}')
print()

if passing == total:
    print('🎉 ALL FEATURES COMPLETE!')
    print('✅ STOPPING - All work done!')
else:
    print('Next 5 failing features:')
    for i, f in enumerate(failing[:5], 1):
        feature_num = f.get('feature_number', f.get('number', 'unknown'))
        name = f.get('name', f.get('description', 'Unknown'))
        print(f'{i}. Feature {feature_num}: {name}')
