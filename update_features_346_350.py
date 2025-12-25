#!/usr/bin/env python3
"""Update features 346-350 (history, regenerate, settings) as passing."""
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Features to update
updates = {
    "AI generation: Generation history: view past generations": "Feature #346: Generation history",
    "AI generation: Regenerate: try generation again with same prompt": "Feature #347: Regenerate",
    "AI generation: Generation settings: temperature control": "Feature #348: Temperature control",
    "AI generation: Generation settings: max tokens limit": "Feature #349: Max tokens limit",
    "AI generation: Prompt templates: pre-defined prompts": "Feature #350: Prompt templates"
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
