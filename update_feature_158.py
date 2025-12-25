import json

# Read feature list
with open('spec/feature_list.json') as f:
    features = json.load(f)

# Update feature #158 (index 157)
if len(features) > 157:
    features[157]['passes'] = True
    print(f"Updated feature #158: {features[157].get('description')}")
    print(f"Now passes: {features[157]['passes']}")
else:
    print(f"Error: Feature list only has {len(features)} features")
    exit(1)

# Write back
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("Feature list updated successfully!")
