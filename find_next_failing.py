import json

with open('spec/feature_list.json') as f:
    features = json.load(f)

# Find first failing feature
for feature in features:
    if not feature.get('passes'):
        print(f"Next feature to implement:")
        print(f"ID: {feature.get('id')}")
        print(f"Title: {feature.get('title')}")
        print(f"Description: {feature.get('description', 'N/A')}")
        print(f"Category: {feature.get('category', 'N/A')}")
        break
