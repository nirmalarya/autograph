#!/usr/bin/env python3
"""Update features 359-361 (multi-language, history, batch) as passing."""
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Find features by partial match (since exact descriptions might differ)
count = 0
for feature in features:
    desc = feature.get('description', '').lower()

    # Multi-language support
    if 'multi-language' in desc and 'prompt' in desc and not feature.get('passes'):
        feature['passes'] = True
        count += 1
        print(f"✓ Updated: {feature.get('description')}")

    # Prompt history with autocomplete
    elif 'prompt history' in desc and 'autocomplete' in desc and not feature.get('passes'):
        feature['passes'] = True
        count += 1
        print(f"✓ Updated: {feature.get('description')}")

    # Batch generation
    elif 'batch generation' in desc and 'variation' in desc and not feature.get('passes'):
        feature['passes'] = True
        count += 1
        print(f"✓ Updated: {feature.get('description')}")

with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print(f"\n✓ Updated {count} features to passing")
print(f"Total passing: {len([f for f in features if f.get('passes')])}/{len(features)}")
