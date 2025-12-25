#!/usr/bin/env python3
"""Analyze current project state for enhancement initialization."""

import json
from pathlib import Path

def analyze_features():
    """Analyze existing feature list."""
    feature_file = Path("spec/feature_list.json")

    if not feature_file.exists():
        print("⚠️ No feature_list.json found!")
        return None

    with open(feature_file) as f:
        features = json.load(f)

    total = len(features)
    passing = len([f for f in features if f.get("passes")])
    failing = total - passing

    # Get last feature ID
    last_id = max(f.get("id", 0) for f in features)

    # Category breakdown
    categories = {}
    for f in features:
        cat = f.get("category", "unknown")
        if cat not in categories:
            categories[cat] = {"total": 0, "passing": 0}
        categories[cat]["total"] += 1
        if f.get("passes"):
            categories[cat]["passing"] += 1

    print("=" * 80)
    print("CURRENT PROJECT STATE ANALYSIS")
    print("=" * 80)
    print(f"\n📊 Feature Statistics:")
    print(f"   Total features: {total}")
    print(f"   ✅ Passing: {passing} ({passing/total*100:.1f}%)")
    print(f"   ❌ Failing: {failing} ({failing/total*100:.1f}%)")
    print(f"   🔢 Last feature ID: {last_id}")
    print(f"   🆕 Next feature starts at: {last_id + 1}")

    print(f"\n📁 Category Breakdown:")
    for cat, stats in sorted(categories.items()):
        pct = stats["passing"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"   {cat:20s}: {stats['passing']:3d}/{stats['total']:3d} ({pct:5.1f}%)")

    return {
        "total": total,
        "passing": passing,
        "failing": failing,
        "last_id": last_id,
        "next_id": last_id + 1,
        "categories": categories
    }

def check_enhancement_spec():
    """Check enhancement specification."""
    spec_file = Path("spec/enhancement_spec.txt")

    if not spec_file.exists():
        print("\n⚠️ No enhancement_spec.txt found!")
        return None

    print("\n" + "=" * 80)
    print("ENHANCEMENT SPECIFICATION")
    print("=" * 80)

    with open(spec_file) as f:
        spec = f.read()

    # Extract key info
    if "v3.1" in spec:
        print("   Target version: v3.1")
    if "v3.0" in spec:
        print("   Base version: v3.0")
    if "bugfix" in spec:
        print("   Mode: BUGFIX")
    if "v2.1" in spec:
        print("   Testing with: autonomous-harness v2.1")

    print("\n   Critical fixes to test:")
    if "MinIO" in spec:
        print("   - MinIO bucket initialization")
    if "Save diagram" in spec:
        print("   - Save diagram functionality")
    if "E2E" in spec:
        print("   - E2E workflow testing")
    if "smoke test" in spec:
        print("   - Smoke test at 100%")

    return spec

def check_existing_plans():
    """Check for existing enhancement plans."""
    plans = list(Path(".").glob("ENHANCEMENT_PLAN*.md"))

    if plans:
        print("\n" + "=" * 80)
        print("EXISTING ENHANCEMENT PLANS")
        print("=" * 80)
        for plan in plans:
            print(f"   📄 {plan.name}")

    baselines = list(Path(".").glob("baseline_features*.txt"))
    if baselines:
        print("\n   Existing baselines:")
        for baseline in baselines:
            print(f"   📄 {baseline.name}")

    return plans, baselines

def main():
    """Main analysis."""
    print("\n🔍 ENHANCEMENT MODE INITIALIZATION - PROJECT ANALYSIS\n")

    # Analyze features
    stats = analyze_features()

    # Check enhancement spec
    spec = check_enhancement_spec()

    # Check existing plans
    plans, baselines = check_existing_plans()

    if stats:
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"   Current state: {stats['passing']}/{stats['total']} features passing")
        print(f"   Next feature ID: {stats['next_id']}")
        print(f"   Mode: Enhancement/Bugfix (v2.1 test)")
        print(f"   Existing plans: {len(plans)}")
        print(f"   Existing baselines: {len(baselines)}")
        print("\n✅ Ready to proceed with enhancement initialization!")
    else:
        print("\n⚠️ Missing critical files - check project structure")

if __name__ == "__main__":
    main()
