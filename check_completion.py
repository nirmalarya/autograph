#!/usr/bin/env python3
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

total = len(features)
passing = len([f for f in features if f.get('passes')])

print(f'Progress: {passing}/{total} features')
print(f'Complete: {passing == total}')

if passing == total:
    print(f'🎉 ALL FEATURES COMPLETE ({total}/{total})!')
    print('✅ STOPPING - All work done!')
