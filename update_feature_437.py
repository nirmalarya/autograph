import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Update feature 437 (index 436)
features[436]['passes'] = True
features[436]['validation_reason'] = 'Comment flagging and moderation system working correctly'
features[436]['validated_at'] = '2025-12-26 01:50:00'
features[436]['validation_method'] = 'automated_test'

with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✅ Feature #437 marked as passing")
print(f"Total passing: {len([f for f in features if f.get('passes')])} / {len(features)}")
