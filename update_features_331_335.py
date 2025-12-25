#!/usr/bin/env python3
"""Update features 331-335 (auto-retry, refinement, context) as passing."""
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Features to update
updates = {
    "AI generation: Auto-retry: regenerate if quality < 80": "Feature #331: Auto-retry with quality threshold",
    "AI generation: Iterative refinement: 'Add caching layer'": "Feature #332: Refinement - Add component",
    "AI generation: Iterative refinement: 'Make database bigger'": "Feature #333: Refinement - Modify size",
    "AI generation: Iterative refinement: 'Change colors to blue'": "Feature #334: Refinement - Change colors",
    "AI generation: Context awareness: remember previous diagrams in session": "Feature #335: Session context awareness"
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
