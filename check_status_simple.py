import json

with open('spec/feature_list.json') as f:
    features = json.load(f)

total = len(features)
passing = len([f for f in features if f.get('passes')])
remaining = total - passing

print(f'Progress: {passing}/{total} features')
print(f'Remaining: {remaining} features')

if remaining == 0:
    print('🎉 ALL FEATURES COMPLETE!')
else:
    print(f'Still working... {remaining} to go')
