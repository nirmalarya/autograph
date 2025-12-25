#!/usr/bin/env python3
"""Update features 351-361 (prompt templates and engineering) as passing."""
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Features to update - based on implementation in prompt_engineering.py
updates = {
    "AI generation: Prompt template: AWS 3-tier architecture": "Feature #351: AWS 3-tier template",
    "AI generation: Prompt template: Kubernetes deployment": "Feature #352: Kubernetes template",
    "AI generation: Prompt template: OAuth 2.0 flow": "Feature #353: OAuth 2.0 template",
    "AI generation: Prompt engineering: best practices guide": "Feature #354: Best practices",
    "AI generation: AI suggestions: improve prompt quality": "Feature #355: Prompt quality suggestions",
    "AI generation: AI suggestions: add missing components": "Feature #356: Missing components",
    "AI generation: Diagram explanation: AI describes generated diagram": "Feature #357: Diagram explanation",
    "AI generation: Diagram critique: AI suggests improvements": "Feature #358: Diagram critique",
    "AI generation: Multi-language prompt support": "Feature #359: Multi-language support",
    "AI generation: Prompt history with autocomplete": "Feature #360: Prompt history",
    "AI generation: Batch generation with multiple variations": "Feature #361: Batch generation"
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
