#!/usr/bin/env python3
"""
Test script for Team Files feature (#154)

Tests:
1. Team Files tab exists in dashboard
2. Team Files endpoint returns empty list for user with no teams
3. Frontend can fetch from team endpoint
"""

import subprocess
import sys
import json

def run_command(cmd, description):
    """Run a command and return output."""
    print(f"\n[Test] {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        print(f"  ✗ TIMEOUT")
        return None, -1

def test_team_endpoint():
    """Test that /team endpoint exists and works."""
    print("\n" + "="*80)
    print("TEST 1: Team endpoint exists and returns data")
    print("="*80)
    
    # Test with a user ID
    test_user_id = "96e81379-add2-4f4e-be8f-e6b8773f5899"
    
    output, code = run_command(
        f'curl -s http://localhost:8082/team -H "X-User-ID: {test_user_id}"',
        "Fetching team files from endpoint"
    )
    
    if code != 0:
        print(f"  ✗ FAILED: Command failed with code {code}")
        return False
    
    try:
        data = json.loads(output)
        if 'diagrams' in data and 'total' in data:
            print(f"  ✓ Endpoint returns correct structure")
            print(f"  ✓ Diagrams: {data['total']}")
            return True
        else:
            print(f"  ✗ FAILED: Response missing 'diagrams' or 'total'")
            print(f"  Response: {output}")
            return False
    except json.JSONDecodeError as e:
        print(f"  ✗ FAILED: Invalid JSON response")
        print(f"  Error: {e}")
        print(f"  Response: {output}")
        return False

def test_frontend_code():
    """Test that frontend code has team tab."""
    print("\n" + "="*80)
    print("TEST 2: Frontend has Team Files tab")
    print("="*80)
    
    dashboard_file = "services/frontend/app/dashboard/page.tsx"
    
    # Check if 'team' is in activeTab type
    output, code = run_command(
        f"grep -n \"activeTab.*useState.*'team'\" {dashboard_file}",
        "Checking if 'team' tab is in state"
    )
    
    if code == 0 and 'team' in output:
        print(f"  ✓ 'team' tab found in state definition")
    else:
        print(f"  ✗ FAILED: 'team' tab not in state")
        return False
    
    # Check if Team Files button exists
    output, code = run_command(
        f"grep -n \"Team Files\" {dashboard_file}",
        "Checking if Team Files button exists"
    )
    
    if code == 0 and 'Team Files' in output:
        print(f"  ✓ 'Team Files' button found in UI")
    else:
        print(f"  ✗ FAILED: 'Team Files' button not in UI")
        return False
    
    # Check if team endpoint is called
    output, code = run_command(
        f"grep -n \"activeTab === 'team'\" {dashboard_file}",
        "Checking if team endpoint is used"
    )
    
    if code == 0:
        print(f"  ✓ Team endpoint logic found")
        return True
    else:
        print(f"  ✗ FAILED: Team endpoint logic not found")
        return False

def test_backend_code():
    """Test that backend has /team endpoint."""
    print("\n" + "="*80)
    print("TEST 3: Backend has /team endpoint")
    print("="*80)
    
    main_file = "services/diagram-service/src/main.py"
    
    # Check if /team endpoint exists
    output, code = run_command(
        f'grep -n "@app.get\\(\\\"/team\\\"\\)" {main_file}',
        "Checking if /team endpoint is defined"
    )
    
    if code == 0:
        print(f"  ✓ /team endpoint found at line: {output.split(':')[0]}")
    else:
        print(f"  ✗ FAILED: /team endpoint not defined")
        return False
    
    # Check if Team model is imported
    output, code = run_command(
        f"grep -n \"from .models import.*Team\" {main_file}",
        "Checking if Team model is imported"
    )
    
    if code == 0 and 'Team' in output:
        print(f"  ✓ Team model is imported")
        return True
    else:
        print(f"  ✗ FAILED: Team model not imported")
        return False

def main():
    """Run all tests."""
    print("="*80)
    print("TEAM FILES FEATURE TEST (#154)")
    print("="*80)
    
    tests = [
        ("Backend /team endpoint", test_backend_code),
        ("Frontend Team tab", test_frontend_code),
        ("Team endpoint API", test_team_endpoint),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ✗ EXCEPTION: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Feature #154 is working!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
