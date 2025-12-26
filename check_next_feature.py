#!/usr/bin/env python3
import json

with open('spec/feature_list.json', 'r') as f:
    features = json.load(f)

total = len(features)
passing = len([f for f in features if f.get('passes')])

print(f'Progress: {passing}/{total} features')
print(f'Percentage: {passing*100/total:.1f}%')
print()

failing = [f for f in features if not f.get('passes')]
if failing:
    next_feature = failing[0]
    print(f'Next failing feature: Feature #{next_feature.get("feature_id", "N/A")}')
    print(f'Name: {next_feature.get("name", "N/A")}')
    print(f'Category: {next_feature.get("category", "baseline")}')
    print(f'Description: {next_feature.get("description", "N/A")[:100]}...')
else:
    print('🎉 ALL FEATURES COMPLETE!')
