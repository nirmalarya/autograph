import json

with open('spec/feature_list.json') as f:
    features = json.load(f)

total = len(features)
passing = len([f for f in features if f.get('passes')])

print(f'Progress: {passing}/{total} features')
print(f'Percentage: {passing/total*100:.1f}%')
print(f'Remaining: {total - passing}')
print(f'Complete: {passing == total}')

if passing == total:
    print('\n🎉 ALL FEATURES COMPLETE!')
    print('✅ STOPPING - All work done!')
