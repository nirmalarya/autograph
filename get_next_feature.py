import json

with open('spec/feature_list.json') as f:
    features = json.load(f)

# Find first failing feature
for idx, feature in enumerate(features):
    if not feature.get('passes'):
        print(f"Feature Index: {idx}")
        print(f"Feature Number: {idx + 1}")
        print(json.dumps(feature, indent=2))
        break
