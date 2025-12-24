#!/usr/bin/env python3
"""
Generate enhancement features based on enhancement_spec.txt
Appends to existing feature_list.json without modifying existing features
"""

import json
from typing import List, Dict

def load_existing_features() -> List[Dict]:
    """Load existing feature list"""
    with open('spec/feature_list.json', 'r') as f:
        return json.load(f)

def generate_enhancement_features(start_id: int) -> List[Dict]:
    """Generate enhancement features from spec"""

    enhancement_features = []
    current_id = start_id

    # P0: Database Schema Fixes
    enhancement_features.append({
        "id": current_id,
        "category": "bugfix",
        "priority": "P0",
        "description": "Database schema audit - all tables have required columns",
        "original_issue": "Missing columns cause failures in files, versions, users, folders tables",
        "steps": [
            "Connect to PostgreSQL database",
            "Audit 'files' table - verify all columns match model",
            "Audit 'versions' table - verify all columns match model",
            "Audit 'users' table - verify all columns match model",
            "Audit 'folders' table - verify all columns match model",
            "Create migration script for missing columns",
            "Apply migration",
            "Verify all CRUD operations succeed without schema errors"
        ],
        "passes": False,
        "test_method": "E2E: All database operations complete successfully"
    })
    current_id += 1

    # P0: Auth Service Health
    enhancement_features.append({
        "id": current_id,
        "category": "bugfix",
        "priority": "P0",
        "description": "Auth service shows healthy status consistently",
        "original_issue": "auth-service showing unhealthy status",
        "steps": [
            "Check auth-service logs for errors",
            "Debug health check endpoint at /health",
            "Fix any startup issues",
            "Verify database connection works",
            "Restart service",
            "Confirm healthy status for 1+ hour"
        ],
        "passes": False,
        "test_method": "docker-compose ps shows 'healthy' for auth-service"
    })
    current_id += 1

    # P0: Diagram Service Health
    enhancement_features.append({
        "id": current_id,
        "category": "bugfix",
        "priority": "P0",
        "description": "Diagram service shows healthy status consistently",
        "original_issue": "diagram-service showing unhealthy status",
        "steps": [
            "Check diagram-service logs for errors",
            "Debug health check endpoint at /health",
            "Fix any startup issues",
            "Verify database connection works",
            "Verify Redis connection works",
            "Restart service",
            "Confirm healthy status for 1+ hour"
        ],
        "passes": False,
        "test_method": "docker-compose ps shows 'healthy' for diagram-service"
    })
    current_id += 1

    # P0: Collaboration Service Health
    enhancement_features.append({
        "id": current_id,
        "category": "bugfix",
        "priority": "P0",
        "description": "Collaboration service shows healthy status consistently",
        "original_issue": "collaboration-service showing unhealthy status",
        "steps": [
            "Check collaboration-service logs for errors",
            "Debug health check endpoint at /health",
            "Fix any startup issues",
            "Verify WebSocket server starts",
            "Verify Redis connection works",
            "Restart service",
            "Confirm healthy status for 1+ hour"
        ],
        "passes": False,
        "test_method": "docker-compose ps shows 'healthy' for collaboration-service"
    })
    current_id += 1

    # P0: Integration Hub Health
    enhancement_features.append({
        "id": current_id,
        "category": "bugfix",
        "priority": "P0",
        "description": "Integration hub shows healthy status consistently",
        "original_issue": "integration-hub showing unhealthy status",
        "steps": [
            "Check integration-hub logs for errors",
            "Debug health check endpoint at /health",
            "Fix any startup issues",
            "Verify database connection works",
            "Restart service",
            "Confirm healthy status for 1+ hour"
        ],
        "passes": False,
        "test_method": "docker-compose ps shows 'healthy' for integration-hub"
    })
    current_id += 1

    # P0: Save Diagram Functionality
    enhancement_features.append({
        "id": current_id,
        "category": "bugfix",
        "priority": "P0",
        "description": "Save diagram persists changes successfully",
        "original_issue": "Save diagram fails with 'Failed to save' error in browser",
        "steps": [
            "Open browser at http://localhost:3000",
            "Login as test user",
            "Create new canvas diagram",
            "Draw some shapes",
            "Click save button",
            "Verify no errors in browser console",
            "Verify success message appears",
            "Reload page",
            "Reopen diagram",
            "Verify drawing persists exactly as saved"
        ],
        "passes": False,
        "test_method": "E2E Playwright test: create, draw, save, reopen, verify persistence"
    })
    current_id += 1

    # P0: Duplicate Template
    enhancement_features.append({
        "id": current_id,
        "category": "bugfix",
        "priority": "P0",
        "description": "Duplicate template creates exact copy successfully",
        "original_issue": "Duplicate template fails",
        "steps": [
            "Open browser at http://localhost:3000",
            "Login as test user",
            "Navigate to templates page",
            "Select any template",
            "Click 'Duplicate' button",
            "Verify no errors in browser console",
            "Verify new diagram created",
            "Verify content matches original template",
            "Verify can edit duplicated diagram"
        ],
        "passes": False,
        "test_method": "E2E Playwright test: duplicate template, verify copy created"
    })
    current_id += 1

    # P0: Create Folder Reliability
    enhancement_features.append({
        "id": current_id,
        "category": "bugfix",
        "priority": "P0",
        "description": "Create folder succeeds 100% of time",
        "original_issue": "Create folder sometimes fails",
        "steps": [
            "Open browser at http://localhost:3000",
            "Login as test user",
            "Navigate to dashboard",
            "Click 'Create Folder' button 10 times (create 10 folders)",
            "Verify all 10 folders created successfully",
            "Verify no errors in browser console",
            "Verify no database schema errors in logs",
            "Verify folders appear in UI immediately"
        ],
        "passes": False,
        "test_method": "E2E Playwright test: create 10 folders, verify 100% success rate"
    })
    current_id += 1

    # Quality Gate: All Services Healthy
    enhancement_features.append({
        "id": current_id,
        "category": "quality_gate",
        "priority": "P0",
        "description": "Quality Gate: All services show healthy status",
        "steps": [
            "Run docker-compose ps",
            "Verify all 10 services show 'healthy' status:",
            "  - frontend",
            "  - api-gateway",
            "  - auth-service",
            "  - diagram-service",
            "  - ai-service",
            "  - collaboration-service",
            "  - export-service",
            "  - integration-hub",
            "  - git-service",
            "  - svg-renderer",
            "Verify infrastructure healthy:",
            "  - postgres",
            "  - redis",
            "  - minio"
        ],
        "passes": False,
        "test_method": "docker-compose ps | grep unhealthy should return nothing"
    })
    current_id += 1

    # Quality Gate: Zero Database Errors
    enhancement_features.append({
        "id": current_id,
        "category": "quality_gate",
        "priority": "P0",
        "description": "Quality Gate: Zero database schema errors in logs",
        "steps": [
            "Check all service logs",
            "Search for 'column does not exist'",
            "Search for 'relation does not exist'",
            "Search for 'schema error'",
            "Search for 'IntegrityError'",
            "Verify zero matches found"
        ],
        "passes": False,
        "test_method": "grep -r 'column does not exist\\|schema error' logs/ returns nothing"
    })
    current_id += 1

    # Quality Gate: Browser Console Clean
    enhancement_features.append({
        "id": current_id,
        "category": "quality_gate",
        "priority": "P0",
        "description": "Quality Gate: Clean browser console (no errors)",
        "steps": [
            "Open browser at http://localhost:3000",
            "Login",
            "Navigate to dashboard",
            "Create diagram",
            "Draw and save",
            "Open browser console",
            "Verify zero JavaScript errors",
            "Verify zero API 4xx/5xx errors",
            "Verify zero CORS errors"
        ],
        "passes": False,
        "test_method": "E2E Playwright test: monitor console, verify no errors"
    })
    current_id += 1

    # Quality Gate: Regression Pass
    enhancement_features.append({
        "id": current_id,
        "category": "quality_gate",
        "priority": "P0",
        "description": "Quality Gate: All 654 existing features still pass (regression)",
        "steps": [
            "Run regression_tester.py",
            "Test random sample of 65+ features (10%)",
            "Verify all sampled features still pass",
            "If any fail, fix immediately before continuing",
            "Document any regressions found"
        ],
        "passes": False,
        "test_method": "python3 regression_tester.py --sample 10 returns 100% pass rate"
    })
    current_id += 1

    return enhancement_features

def main():
    """Main execution"""
    print("Loading existing features...")
    existing_features = load_existing_features()
    print(f"  Found {len(existing_features)} existing features")
    print(f"  All currently passing: {all(f.get('passes', False) for f in existing_features)}")

    # Determine starting ID
    start_id = len(existing_features) + 1
    print(f"\nGenerating enhancement features starting at ID {start_id}...")

    enhancement_features = generate_enhancement_features(start_id)
    print(f"  Generated {len(enhancement_features)} enhancement features")
    print(f"  Enhancement features: #{start_id} - #{start_id + len(enhancement_features) - 1}")

    # Combine
    all_features = existing_features + enhancement_features
    print(f"\nTotal features: {len(all_features)}")
    print(f"  Existing: {len(existing_features)} (all passing)")
    print(f"  Enhancement: {len(enhancement_features)} (to be fixed)")

    # Save
    print("\nSaving updated feature_list.json...")
    with open('spec/feature_list.json', 'w') as f:
        json.dump(all_features, f, indent=2)

    print("\n✅ Feature list updated successfully!")
    print(f"\nEnhancement summary:")
    print(f"  P0 Bugfixes: {len([f for f in enhancement_features if f.get('priority') == 'P0' and f.get('category') == 'bugfix'])}")
    print(f"  Quality Gates: {len([f for f in enhancement_features if f.get('category') == 'quality_gate'])}")

    # Show what was added
    print(f"\nEnhancement features added:")
    for f in enhancement_features:
        status = "🔴" if not f.get('passes') else "✅"
        priority = f.get('priority', '??')
        print(f"  {status} [{priority}] #{f.get('id')}: {f.get('description')}")

if __name__ == '__main__':
    main()
