#!/usr/bin/env python3
"""Generate audit features for v3.1 quality audit."""

import json
from pathlib import Path

def create_audit_features():
    """Create audit features #667-678."""

    # Load existing features
    feature_file = Path("spec/feature_list.json")
    with open(feature_file) as f:
        features = json.load(f)

    print(f"Loaded {len(features)} existing features")

    # Get last feature ID (handle features without IDs)
    last_id = 0
    for f in features:
        if 'id' in f and f['id'] > last_id:
            last_id = f['id']

    print(f"Last feature ID: {last_id}")

    # Audit features (start at 667)
    audit_features = [
        {
            "id": 667,
            "category": "audit",
            "description": "MinIO buckets verified to exist (diagrams, exports, uploads)",
            "steps": [
                "Connect to MinIO container",
                "List all buckets with 'mc ls local/'",
                "Verify 'diagrams' bucket exists",
                "Verify 'exports' bucket exists",
                "Verify 'uploads' bucket exists",
                "If missing, create buckets with 'mc mb local/{bucket}'",
                "Re-verify all 3 buckets exist"
            ],
            "passes": False,
            "test_file": "test_minio_buckets.py",
            "v21_gate": "infrastructure_validation"
        },
        {
            "id": 668,
            "category": "audit",
            "description": "MinIO buckets are accessible (read/write permissions)",
            "steps": [
                "Create test file in diagrams bucket",
                "Read test file from diagrams bucket",
                "Delete test file from diagrams bucket",
                "Repeat for exports bucket",
                "Repeat for uploads bucket",
                "Verify all operations succeed"
            ],
            "passes": False,
            "test_file": "test_minio_access.py",
            "v21_gate": "infrastructure_validation"
        },
        {
            "id": 669,
            "category": "audit",
            "description": "PostgreSQL schema complete (all tables, columns, indexes)",
            "steps": [
                "Connect to PostgreSQL",
                "Query information_schema for all tables",
                "Verify all 12 tables exist",
                "For each table, verify all columns from models.py exist",
                "Verify all indexes exist",
                "Verify all foreign keys exist",
                "Document any missing schema elements"
            ],
            "passes": False,
            "test_file": "test_schema_complete.py",
            "v21_gate": "infrastructure_validation"
        },
        {
            "id": 670,
            "category": "audit",
            "description": "Redis sessions working with correct TTL",
            "steps": [
                "Connect to Redis",
                "Create test session with 24h TTL",
                "Verify session exists",
                "Verify TTL is 86400 seconds",
                "Wait 1 second, verify TTL decrements",
                "Delete test session",
                "Verify session deleted"
            ],
            "passes": False,
            "test_file": "test_redis_sessions.py",
            "v21_gate": "infrastructure_validation"
        },
        {
            "id": 671,
            "category": "audit",
            "description": "test_save_diagram.py EXECUTES and PASSES",
            "steps": [
                "Verify test_save_diagram.py exists",
                "Execute: python3 test_save_diagram.py",
                "Capture output and exit code",
                "Verify exit code is 0 (success)",
                "Verify test actually created user, logged in, created diagram, saved changes",
                "Verify test output shows 'PASS' or '✅'",
                "If test fails, document failure reason"
            ],
            "passes": False,
            "test_file": "verify_test_execution.py",
            "v21_gate": "test_execution"
        },
        {
            "id": 672,
            "category": "audit",
            "description": "test_duplicate_template.py EXECUTES and PASSES",
            "steps": [
                "Verify test_duplicate_template.py exists",
                "Execute: python3 test_duplicate_template.py",
                "Capture output and exit code",
                "Verify exit code is 0 (success)",
                "Verify test actually duplicated a diagram",
                "Verify duplicate has different ID but same content",
                "If test fails, document failure reason"
            ],
            "passes": False,
            "test_file": "verify_test_execution.py",
            "v21_gate": "test_execution"
        },
        {
            "id": 673,
            "category": "audit",
            "description": "test_create_folder.py EXECUTES and PASSES",
            "steps": [
                "Verify test_create_folder.py exists",
                "Execute: python3 test_create_folder.py",
                "Capture output and exit code",
                "Verify exit code is 0 (success)",
                "Verify test created 22 folders successfully",
                "Verify 100% success rate claimed is accurate",
                "If test fails, document failure reason"
            ],
            "passes": False,
            "test_file": "verify_test_execution.py",
            "v21_gate": "test_execution"
        },
        {
            "id": 674,
            "category": "audit",
            "description": "test_quality_gates.py EXECUTES and PASSES",
            "steps": [
                "Verify test_quality_gates.py exists",
                "Execute: python3 test_quality_gates.py",
                "Capture output and exit code",
                "Verify exit code is 0 (success)",
                "Verify test checks service health, schema errors, regressions",
                "Verify all quality checks pass",
                "If test fails, document failure reason"
            ],
            "passes": False,
            "test_file": "verify_test_execution.py",
            "v21_gate": "test_execution"
        },
        {
            "id": 675,
            "category": "audit",
            "description": "Complete user registration → login → create → save workflow works",
            "steps": [
                "Open browser to http://localhost:3000",
                "Register new user with unique email",
                "Verify registration success redirect to login",
                "Login with new user credentials",
                "Verify dashboard loads",
                "Create new diagram",
                "Add shapes to canvas",
                "Click Save",
                "Verify save success message",
                "Reload page",
                "Verify shapes persisted",
                "Document any workflow failures"
            ],
            "passes": False,
            "test_file": "test_e2e_workflow.py",
            "v21_gate": "e2e_testing"
        },
        {
            "id": 676,
            "category": "audit",
            "description": "Complete diagram lifecycle works (create → edit → save → reopen → delete)",
            "steps": [
                "Login to application",
                "Create new diagram",
                "Add 5 shapes with different types",
                "Save diagram",
                "Navigate away (back to dashboard)",
                "Reopen diagram",
                "Verify all 5 shapes present",
                "Edit diagram (add 2 more shapes)",
                "Save again",
                "Delete diagram",
                "Verify diagram deleted from list",
                "Document any lifecycle failures"
            ],
            "passes": False,
            "test_file": "test_diagram_lifecycle.py",
            "v21_gate": "e2e_testing"
        },
        {
            "id": 677,
            "category": "audit",
            "description": "All critical CRUD operations work in browser (not just curl)",
            "steps": [
                "Open browser to AutoGraph",
                "Test CREATE: Create user, team, diagram, folder, comment",
                "Test READ: View dashboard, open diagram, view folder, read comments",
                "Test UPDATE: Edit diagram title, move shapes, update folder name",
                "Test DELETE: Delete diagram, delete folder, delete comment",
                "Verify all operations in browser console (no errors)",
                "Verify all operations in database (data persists)",
                "Document any CRUD failures"
            ],
            "passes": False,
            "test_file": "test_browser_crud.py",
            "v21_gate": "smoke_test"
        },
        {
            "id": 678,
            "category": "audit",
            "description": "All 666 existing features verified via automated smoke test",
            "steps": [
                "Run comprehensive smoke test suite",
                "Sample 10% of features (67 features) randomly",
                "Execute automated tests for sampled features",
                "Verify 100% pass rate",
                "If any feature fails, mark entire audit failed",
                "Document all failures with stack traces",
                "Re-run failed features individually to confirm",
                "Final verification: All 666 features actually work"
            ],
            "passes": False,
            "test_file": "smoke_test_suite.py",
            "v21_gate": "smoke_test"
        }
    ]

    # Add to existing features
    all_features = features + audit_features

    # Save updated feature list
    with open(feature_file, 'w') as f:
        json.dump(all_features, f, indent=2)

    print(f"\n✅ Created {len(audit_features)} audit features (#667-678)")
    print(f"📊 Total features: {len(all_features)}")
    print(f"🎯 v2.1 quality gates tested:")
    print("   - infrastructure_validation")
    print("   - test_execution")
    print("   - e2e_testing")
    print("   - smoke_test")

    # Create baseline for audit
    baseline = {
        "version": "v3.1-audit",
        "base_features": 666,
        "audit_features": 12,
        "total_features": 678,
        "baseline_passing": 666,
        "audit_passing": 0,
        "date": "2024-12-24",
        "purpose": "Quality audit with autonomous-harness v2.1"
    }

    with open("baseline_features-v3.1.txt", 'w') as f:
        f.write("AutoGraph v3.1 Quality Audit Baseline\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Base version: v3.0 (claimed 666/666 features passing)\n")
        f.write(f"Audit version: v3.1 (testing with autonomous-harness v2.1)\n\n")
        f.write(f"Baseline features: {baseline['base_features']} (must remain passing)\n")
        f.write(f"Audit features: {baseline['audit_features']} (testing quality claims)\n")
        f.write(f"Total features: {baseline['total_features']}\n\n")
        f.write("Purpose: Verify v3.0 completion claims with v2.1 harness\n")
        f.write("Expected: v2.1 may find issues v2.0 missed!\n")

    print(f"\n📝 Created baseline_features-v3.1.txt")

if __name__ == "__main__":
    create_audit_features()
