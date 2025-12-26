import json

# Load feature list
with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Mark feature #517 as passing
features[517]['passes'] = True

# Save
with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print("✅ Feature #517 marked as passing")
print(f"Total passing: {len([f for f in features if f.get('passes')])}/{len(features)}")
