"""Update feature_list.json to mark feature #516 as passing."""
import json
from datetime import datetime

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

# Find and update feature 516 (index 516 since we're 0-indexed)
if len(features) > 516:
    feature = features[516]
    if feature.get('description') == 'Export: Quality optimization: compress PNG':
        feature['passes'] = True
        feature['validation_reason'] = 'PNG compression implemented with compress_level and optimize flags'
        feature['validated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        feature['validation_method'] = 'automated_test'

        print(f"✅ Updated feature at index 516:")
        print(f"   Description: {feature['description']}")
        print(f"   Passes: {feature['passes']}")

        # Save the updated features
        with open('spec/feature_list.json', 'w') as f:
            json.dump(features, f, indent=2)

        print("\n✅ feature_list.json updated successfully")

        # Count total passing
        passing = len([f for f in features if f.get('passes', False)])
        total = len(features)
        print(f"\nProgress: {passing}/{total} features ({100*passing/total:.1f}%)")
    else:
        print(f"❌ Feature at index 516 has wrong description: {feature.get('description')}")
        exit(1)
else:
    print(f"❌ Not enough features in list (only {len(features)})")
    exit(1)
