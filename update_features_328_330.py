#!/usr/bin/env python3
"""Update features 328-330 (spacing, alignment, readability) as passing."""
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Find and update features
updates = {
    "AI generation: Quality validation: spacing minimum 50px": "Feature #328: Spacing validation with 50px minimum",
    "AI generation: Quality validation: alignment check": "Feature #329: Alignment check for professional diagrams",
    "AI generation: Quality validation: readability score 0-100": "Feature #330: Readability score calculation"
}

count = 0
for feature in features:
    desc = feature.get('description', '')
    if desc in updates:
        if not feature.get('passes'):
            feature['passes'] = True
            count += 1
            print(f"✓ Updated: {desc}")
        else:
            print(f"  Already passing: {desc}")

with open('spec/feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print(f"\n✓ Updated {count} features to passing")
print(f"Total passing: {len([f for f in features if f.get('passes')])}/{len(features)}")
