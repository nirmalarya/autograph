#!/usr/bin/env python3
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Find the first failing feature
for idx, feature in enumerate(features):
    if not feature.get('passes'):
        print('='*60)
        print(f'FEATURE #{idx + 1} (array index {idx})')
        print('='*60)
        for key, value in feature.items():
            if key != 'test_code':
                print(f'{key}: {value}')
        print('='*60)
        break
