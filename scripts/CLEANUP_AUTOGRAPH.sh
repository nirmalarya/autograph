#!/bin/bash
# Clean up AutoGraph v3 file organization for GitHub release

set -e

echo "🧹 Cleaning up AutoGraph v3 file organization..."

# Create directories
mkdir -p .sessions
mkdir -p scripts/tests
mkdir -p scripts/debug
mkdir -p scripts/verify
mkdir -p scripts/utils
mkdir -p docs/sessions
mkdir -p docs/features
mkdir -p docs/planning

# Move session files
echo "Moving session files..."
find . -maxdepth 1 -name "SESSION_*.md" -exec mv {} .sessions/ \; 2>/dev/null || true
find . -maxdepth 1 -name "NEXT_SESSION_*.md" -exec mv {} .sessions/ \; 2>/dev/null || true

# Move test files
echo "Moving test files..."
find . -maxdepth 1 -name "test_*.py" -exec mv {} scripts/tests/ \; 2>/dev/null || true
find . -maxdepth 1 -name "test_*.html" -exec mv {} scripts/tests/ \; 2>/dev/null || true
find . -maxdepth 1 -name "manual_*.py" -exec mv {} scripts/tests/ \; 2>/dev/null || true

# Move debug scripts
echo "Moving debug scripts..."
find . -maxdepth 1 -name "debug_*.py" -exec mv {} scripts/debug/ \; 2>/dev/null || true
find . -maxdepth 1 -name "analyze_*.py" -exec mv {} scripts/debug/ \; 2>/dev/null || true
find . -maxdepth 1 -name "check_*.py" -exec mv {} scripts/debug/ \; 2>/dev/null || true
find . -maxdepth 1 -name "count_*.py" -exec mv {} scripts/debug/ \; 2>/dev/null || true

# Move verify scripts
echo "Moving verify scripts..."
find . -maxdepth 1 -name "verify_*.py" -exec mv {} scripts/verify/ \; 2>/dev/null || true
find . -maxdepth 1 -name "cleanup_*.py" -exec mv {} scripts/verify/ \; 2>/dev/null || true
find . -maxdepth 1 -name "clear_*.py" -exec mv {} scripts/verify/ \; 2>/dev/null || true
find . -maxdepth 1 -name "create_*.py" -exec mv {} scripts/utils/ \; 2>/dev/null || true

# Move documentation
echo "Moving documentation..."
find . -maxdepth 1 -name "*_VERIFICATION.md" -exec mv {} docs/sessions/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*_COMPLETE.md" -exec mv {} docs/sessions/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*_SUMMARY.md" -exec mv {} docs/sessions/ \; 2>/dev/null || true
find . -maxdepth 1 -name "FEATURE_*.md" -exec mv {} docs/features/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*_PLAN.md" -exec mv {} docs/planning/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*_SETUP.md" -exec mv {} docs/planning/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*_STRATEGY.md" -exec mv {} docs/planning/ \; 2>/dev/null || true
find . -maxdepth 1 -name "CONFIGURATION.md" -exec mv {} docs/planning/ \; 2>/dev/null || true

# Count remaining
echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Files in root now:"
ls -1 | wc -l

echo ""
echo "Essential files only (should be < 30):"
ls -1

