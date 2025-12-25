#!/usr/bin/env python3
import json

with open('spec/feature_list.json') as f:
    features = json.load(f)

failing = [f for f in features if not f.get('passes')]

if failing:
    feature = failing[0]
    print('=== NEXT FAILING FEATURE ===')
    print(json.dumps(feature, indent=2))
else:
    print('No failing features!')
