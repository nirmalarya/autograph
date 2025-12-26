import json

with open('spec/feature_list.json') as f:
    features = json.load(f)

# Find next failing feature
for i, feature in enumerate(features, 1):
    if not feature.get('passes', False):
        print(f"\n{'='*60}")
        print(f"NEXT FEATURE: #{i}")
        print(f"{'='*60}")
        print(f"ID: {feature.get('id', i)}")
        print(f"Name: {feature.get('name', 'N/A')}")
        print(f"Category: {feature.get('category', 'N/A')}")
        print(f"Description: {feature.get('description', 'N/A')}")
        print(f"Passes: {feature.get('passes', False)}")
        print(f"{'='*60}\n")
        break
else:
    print("🎉 All features passing!")
