#!/usr/bin/env python3
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

total = len(features)
passing = len([f for f in features if f.get('passes')])

print(f'Progress: {passing}/{total} features ({passing*100/total:.1f}%)')
print()

failing = [f for f in features if not f.get('passes')]
if failing:
    next_feature = failing[0]
    print('='*60)
    print('NEXT FEATURE TO IMPLEMENT')
    print('='*60)
    for key, value in next_feature.items():
        if key != 'test_code':
            print(f'{key}: {value}')
    print('='*60)
else:
    print('🎉 ALL FEATURES COMPLETE!')
