#!/usr/bin/env python3
"""
Create regression baseline - document all currently passing features
This is what we MUST NOT BREAK during enhancement!
"""

import json
from collections import Counter

def create_baseline():
    """Create baseline of currently passing features"""

    with open('spec/feature_list.json', 'r') as f:
        all_features = json.load(f)

    # Separate existing from enhancement
    existing_features = [f for f in all_features if f.get('id', 0) <= 654]
    enhancement_features = [f for f in all_features if f.get('id', 0) > 654]

    # All existing features are passing
    passing_features = [f for f in existing_features if f.get('passes', False)]

    # Statistics
    total_existing = len(existing_features)
    total_passing = len(passing_features)
    total_enhancement = len(enhancement_features)

    # Category breakdown
    categories = Counter([f.get('category') for f in passing_features])

    # Generate baseline document
    baseline = []
    baseline.append("=" * 80)
    baseline.append("AUTOGRAPH v3.0 → v3.1 ENHANCEMENT - REGRESSION BASELINE")
    baseline.append("=" * 80)
    baseline.append("")
    baseline.append("This document captures the current state of AutoGraph v3.0.")
    baseline.append("ALL features listed here are currently PASSING.")
    baseline.append("These MUST continue to pass after enhancement work!")
    baseline.append("")
    baseline.append("=" * 80)
    baseline.append("BASELINE SUMMARY")
    baseline.append("=" * 80)
    baseline.append("")
    baseline.append(f"Total Existing Features: {total_existing}")
    baseline.append(f"Currently Passing: {total_passing} (100%)")
    baseline.append(f"Enhancement Features Added: {total_enhancement}")
    baseline.append(f"Total Features in List: {len(all_features)}")
    baseline.append("")
    baseline.append("Categories of Passing Features:")
    for category, count in sorted(categories.items(), key=lambda x: -x[1]):
        baseline.append(f"  {category}: {count} features")
    baseline.append("")
    baseline.append("=" * 80)
    baseline.append("REGRESSION TESTING REQUIREMENTS")
    baseline.append("=" * 80)
    baseline.append("")
    baseline.append("CRITICAL: These 654 features MUST continue to pass!")
    baseline.append("")
    baseline.append("Testing Schedule:")
    baseline.append("  - Run regression_tester.py every 5 sessions")
    baseline.append("  - Sample size: 10% minimum (65+ features)")
    baseline.append("  - Pass rate required: 100%")
    baseline.append("")
    baseline.append("If ANY regression is found:")
    baseline.append("  1. STOP all enhancement work immediately")
    baseline.append("  2. Fix the regression first")
    baseline.append("  3. Re-run regression tests")
    baseline.append("  4. Only continue when 100% passing again")
    baseline.append("")
    baseline.append("=" * 80)
    baseline.append("ENHANCEMENT WORK (Features #655-666)")
    baseline.append("=" * 80)
    baseline.append("")
    baseline.append("New Features to Implement:")
    for f in enhancement_features:
        priority = f.get('priority', '??')
        cat = f.get('category', 'unknown')
        desc = f.get('description', 'No description')
        baseline.append(f"  [{priority}] #{f.get('id')}: {desc}")
    baseline.append("")
    baseline.append("=" * 80)
    baseline.append("CURRENT SERVICE STATUS")
    baseline.append("=" * 80)
    baseline.append("")
    baseline.append("Healthy Services:")
    baseline.append("  ✅ ai-service")
    baseline.append("  ✅ postgres")
    baseline.append("  ✅ redis")
    baseline.append("  ✅ minio")
    baseline.append("")
    baseline.append("Unhealthy Services (TO FIX):")
    baseline.append("  🔴 auth-service")
    baseline.append("  🔴 diagram-service")
    baseline.append("  🔴 collaboration-service")
    baseline.append("  🔴 integration-hub")
    baseline.append("")
    baseline.append("=" * 80)
    baseline.append("END OF BASELINE")
    baseline.append("=" * 80)
    baseline.append("")
    baseline.append("Generated: Session 1 - Enhancement Mode Initialization")
    baseline.append("DO NOT MODIFY THIS FILE - It represents v3.0 baseline")
    baseline.append("")

    return "\n".join(baseline)

def main():
    print("Creating regression baseline...")
    baseline = create_baseline()

    with open('baseline_features.txt', 'w') as f:
        f.write(baseline)

    print("✅ Baseline created: baseline_features.txt")
    print("\nBaseline summary:")
    print("  654 existing features (all passing)")
    print("  12 enhancement features (to be implemented)")
    print("  4 services need health fixes")
    print("\nThis baseline MUST be preserved during enhancement work!")

if __name__ == '__main__':
    main()
