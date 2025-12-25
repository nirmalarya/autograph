#!/usr/bin/env python3
"""
Test Quality Assessment Framework
Analyzes existing tests and categorizes them as good/partial/bad
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple

class TestAssessor:
    def __init__(self, test_dir: str = "scripts/tests"):
        self.test_dir = Path(test_dir)
        self.good_tests = []
        self.partial_tests = []
        self.bad_tests = []
        self.assessment_notes = {}

    def assess_test_quality(self, test_file: Path) -> Tuple[str, str]:
        """
        Assess test quality based on criteria.
        Returns: (category, reason)

        Categories:
        - good: Complete workflow, real browser/API, persistence check
        - partial: Incomplete but useful
        - bad: Mocked everything, broken, or doesn't test real feature
        """
        try:
            content = test_file.read_text()
        except Exception as e:
            return "bad", f"Cannot read file: {e}"

        # Count quality indicators
        score = 0
        indicators = []

        # GOOD indicators
        if "puppeteer" in content.lower() or "playwright" in content.lower():
            score += 3
            indicators.append("✅ Uses real browser")

        if re.search(r"requests\.(get|post|put|delete)", content):
            score += 2
            indicators.append("✅ Real API calls")

        if "assert" in content or "assertEqual" in content:
            score += 1
            indicators.append("✅ Has assertions")

        if re.search(r"(reload|restart|persistence|database)", content, re.IGNORECASE):
            score += 2
            indicators.append("✅ Checks persistence")

        if re.search(r"(error|exception|fail|invalid)", content, re.IGNORECASE):
            score += 1
            indicators.append("✅ Tests error cases")

        if "sys.exit(0)" in content and "sys.exit(1)" in content:
            score += 1
            indicators.append("✅ Proper exit codes")

        # BAD indicators
        if "mock" in content.lower() or "patch" in content.lower():
            score -= 2
            indicators.append("⚠️ Uses mocking")

        if "# TODO" in content or "# FIXME" in content:
            score -= 1
            indicators.append("⚠️ Has TODOs")

        if len(content) < 500:
            score -= 2
            indicators.append("⚠️ Very short test")

        # Categorize based on score
        if score >= 6:
            category = "good"
            reason = "Comprehensive test: " + ", ".join(indicators)
        elif score >= 3:
            category = "partial"
            reason = "Partial test: " + ", ".join(indicators)
        else:
            category = "bad"
            reason = "Needs work: " + ", ".join(indicators)

        return category, reason

    def assess_all_tests(self) -> Dict:
        """Assess all tests in the test directory"""
        test_files = sorted(self.test_dir.glob("test_*.py"))

        print(f"Found {len(test_files)} test files in {self.test_dir}")

        for test_file in test_files:
            category, reason = self.assess_test_quality(test_file)

            test_info = {
                "file": test_file.name,
                "path": str(test_file),
                "reason": reason
            }

            if category == "good":
                self.good_tests.append(test_info)
            elif category == "partial":
                self.partial_tests.append(test_info)
            else:
                self.bad_tests.append(test_info)

        return {
            "good": self.good_tests,
            "partial": self.partial_tests,
            "bad": self.bad_tests,
            "summary": {
                "total": len(test_files),
                "good": len(self.good_tests),
                "partial": len(self.partial_tests),
                "bad": len(self.bad_tests)
            }
        }

    def save_categorization(self, output_dir: str = "."):
        """Save categorization to files"""
        output_path = Path(output_dir)

        # Save good tests
        with open(output_path / "good_tests.txt", "w") as f:
            f.write(f"# Good Quality Tests ({len(self.good_tests)})\n")
            f.write("# Can use as-is, ready to run\n\n")
            for test in self.good_tests:
                f.write(f"{test['file']}\n")
                f.write(f"  Path: {test['path']}\n")
                f.write(f"  Reason: {test['reason']}\n\n")

        # Save partial tests
        with open(output_path / "partial_tests.txt", "w") as f:
            f.write(f"# Partial Quality Tests ({len(self.partial_tests)})\n")
            f.write("# Need enhancement\n\n")
            for test in self.partial_tests:
                f.write(f"{test['file']}\n")
                f.write(f"  Path: {test['path']}\n")
                f.write(f"  Reason: {test['reason']}\n\n")

        # Save bad tests
        with open(output_path / "bad_tests.txt", "w") as f:
            f.write(f"# Low Quality Tests ({len(self.bad_tests)})\n")
            f.write("# Need rewrite\n\n")
            for test in self.bad_tests:
                f.write(f"{test['file']}\n")
                f.write(f"  Path: {test['path']}\n")
                f.write(f"  Reason: {test['reason']}\n\n")

        print(f"\n✅ Saved categorization files:")
        print(f"   - good_tests.txt ({len(self.good_tests)} tests)")
        print(f"   - partial_tests.txt ({len(self.partial_tests)} tests)")
        print(f"   - bad_tests.txt ({len(self.bad_tests)} tests)")

    def generate_report(self) -> str:
        """Generate assessment report"""
        total = len(self.good_tests) + len(self.partial_tests) + len(self.bad_tests)

        report = f"""
# Test Quality Assessment Report

## Summary
- **Total Tests Reviewed**: {total}
- **Good Tests**: {len(self.good_tests)} ({len(self.good_tests)/total*100:.1f}%)
- **Partial Tests**: {len(self.partial_tests)} ({len(self.partial_tests)/total*100:.1f}%)
- **Bad Tests**: {len(self.bad_tests)} ({len(self.bad_tests)/total*100:.1f}%)

## Assessment Criteria

### Good Test ✅
- Tests complete user workflow
- Uses real browser (Puppeteer/Playwright) for UI features
- Uses real API calls (not mocks)
- Verifies data persistence (reload/restart)
- Tests error cases
- Has clear assertions
- Exits with proper codes (0 on pass, 1 on fail)

### Partial Test ⚠️
- Tests feature but incomplete
- Missing browser testing
- Missing persistence check
- Only happy path
- Needs enhancement

### Bad Test ❌
- Mocks everything
- Doesn't test real feature
- Broken/doesn't run
- Wrong assertions
- Needs rewrite

## Recommended Next Steps

1. **Phase 2: Run Good Tests** ({len(self.good_tests)} tests)
   - Execute each good test
   - Fix any failures
   - Mark features as passing

2. **Phase 3: Enhance Partial Tests** ({len(self.partial_tests)} tests)
   - Add browser testing where needed
   - Add persistence verification
   - Add error case testing

3. **Phase 4: Rewrite Bad Tests** ({len(self.bad_tests)} tests)
   - Create new comprehensive tests
   - Follow v2.1 testing standards

4. **Phase 5: Create Missing Tests** (TBD)
   - Identify features without tests
   - Write new comprehensive tests

## Files Generated
- `good_tests.txt` - Ready to run
- `partial_tests.txt` - Need enhancement
- `bad_tests.txt` - Need rewrite
"""
        return report


if __name__ == "__main__":
    print("🔍 Starting Test Quality Assessment...")
    print("=" * 60)

    assessor = TestAssessor()
    results = assessor.assess_all_tests()

    print("\n📊 Assessment Results:")
    print(f"   Good:    {results['summary']['good']} tests")
    print(f"   Partial: {results['summary']['partial']} tests")
    print(f"   Bad:     {results['summary']['bad']} tests")
    print(f"   Total:   {results['summary']['total']} tests")

    assessor.save_categorization()

    report = assessor.generate_report()
    with open("test_assessment_report.md", "w") as f:
        f.write(report)

    print("\n📝 Generated: test_assessment_report.md")
    print("\n✅ Assessment complete!")
