import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update feature 438 (index 437)
features[437]['passes'] = True
features[437]['validation_reason'] = 'Comment count badge displays and updates correctly'
features[437]['validated_at'] = '2025-12-26 01:56:00'
features[437]['validation_method'] = 'automated_test'

with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✅ Feature #438 marked as passing")
print(f"Total passing: {len([f for f in features if f.get('passes')])} / {len(features)}")
