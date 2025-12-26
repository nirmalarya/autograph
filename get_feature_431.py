import json

with open('spec/feature_list.json') as f:
    features = json.load(f)

# Feature 431 is at index 430 (0-based)
feature = features[430]
print(json.dumps(feature, indent=2))
