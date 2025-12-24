#!/usr/bin/env python3
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

total = len(features)
passing = len([f for f in features if f.get('passes')])
failing = total - passing
last_id = max([f.get('id', 0) for f in features])

print(f"Total features: {total}")
print(f"Passing: {passing}")
print(f"Failing: {failing}")
print(f"Last feature ID: {last_id}")
print(f"Pass rate: {passing/total*100:.1f}%")

# Category breakdown
from collections import Counter
categories = Counter([f.get('category', 'unknown') for f in features])
print("\nFeatures by category:")
for cat, count in sorted(categories.items()):
    cat_passing = len([f for f in features if f.get('category') == cat and f.get('passes')])
    print(f"  {cat}: {cat_passing}/{count} passing")
