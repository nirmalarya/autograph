#!/usr/bin/env python3
"""Update features 341-347 (analytics and tracking) as passing."""
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Features to update
updates = {
    "AI generation: Token usage tracking: log tokens per generation": "Feature #341: Token usage tracking",
    "AI generation: Token usage: estimate cost per generation": "Feature #342: Cost estimation",
    "AI generation: Provider comparison: track quality metrics": "Feature #343: Provider comparison",
    "AI generation: Model selection: choose specific models": "Feature #344: Model selection",
    "AI generation: Cost optimization: suggest cheaper models for simple diagrams": "Feature #345: Cost optimization"
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
