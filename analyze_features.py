#!/usr/bin/env python3
import json

with open('feature_list.json', 'r') as f:
    data = json.load(f)

categories = {}
for f in data:
    cat = f.get('category', 'Unknown')
    if cat not in categories:
        categories[cat] = {'total': 0, 'passing': 0, 'not_passing': []}
    categories[cat]['total'] += 1
    if f.get('passes', False):
        categories[cat]['passing'] += 1
    else:
        categories[cat]['not_passing'].append(f)

print('Categories:')
for cat, stats in sorted(categories.items()):
    pct = (stats['passing'] / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"{cat}: {stats['passing']}/{stats['total']} ({pct:.0f}%)")

print('\n\nCategories with incomplete features:')
for cat, stats in sorted(categories.items(), key=lambda x: len(x[1]['not_passing'])):
    if len(stats['not_passing']) > 0:
        print(f"\n{cat}: {len(stats['not_passing'])} remaining ({stats['passing']}/{stats['total']} - {(stats['passing']/stats['total']*100):.0f}%)")
        for i, f in enumerate(stats['not_passing'][:5], 1):
            desc = f.get('description', 'No description')[:80]
            print(f"  {i}. {desc}")
        if len(stats['not_passing']) > 5:
            print(f"  ... and {len(stats['not_passing']) - 5} more")
