#!/usr/bin/env python3
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

total = len(features)
passing = len([f for f in features if f.get('passes')])
remaining = total - passing

print(f'Progress: {passing}/{total} features')
print(f'Remaining: {remaining} features')
print(f'Completion: {passing/total*100:.1f}%')

if passing == total:
    print('\n🎉 ALL FEATURES COMPLETE!')
    print('✅ STOPPING - All work done!')
else:
    print(f'\n➡️ Continue working: {remaining} features to go')
