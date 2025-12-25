#!/usr/bin/env python3
"""Update features 336-340 (templates and domain-specific) as passing."""
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Features to update
updates = {
    "AI generation: Template-based generation: use reference library": "Feature #336: Template library",
    "AI generation: Domain-specific: fintech architecture patterns": "Feature #337: Fintech templates",
    "AI generation: Domain-specific: healthcare architecture": "Feature #338: Healthcare templates",
    "AI generation: Domain-specific: e-commerce architecture": "Feature #339: E-commerce templates",
    "AI generation: Domain-specific: DevOps pipeline": "Feature #340: DevOps templates"
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
