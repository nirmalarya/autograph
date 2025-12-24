#!/usr/bin/env python3
"""
Test Enterprise Analytics Features

Tests:
- Enterprise: Usage analytics: diagrams created
- Enterprise: Usage analytics: users active
- Enterprise: Usage analytics: storage used
- Enterprise: Cost allocation: track usage by team
"""

import requests
import json

DIAGRAM_SERVICE_URL = "http://localhost:8082"

def test_diagrams_created_analytics():
    """Test: Usage analytics - diagrams created"""
    print("=" * 80)
    print("TEST: Diagrams Created Analytics")
    print("=" * 80)
    
    response = requests.get(f"{DIAGRAM_SERVICE_URL}/api/analytics/diagrams-created")
    
    if response.status_code != 200:
        print(f"\n✗ FAIL: Status code {response.status_code}")
        return False
    
    data = response.json()
    
    print(f"\nDiagrams Created (Last 30 Days):")
    print(f"  Total diagrams created: {data.get('total_diagrams_created', 0)}")
    print(f"  Average per day: {data.get('average_per_day', 0):.2f}")
    print(f"  Days with data: {len(data.get('daily_counts', []))}")
    
    # Show recent days
    daily_counts = data.get('daily_counts', [])
    if daily_counts:
        print(f"\nRecent days:")
        for day in daily_counts[-5:]:
            print(f"    {day['date']}: {day['count']} diagrams")
    
    has_data = 'total_diagrams_created' in data and 'daily_counts' in data
    
    if has_data:
        print("\n✓ PASS: Diagrams created analytics working")
        return True
    else:
        print("\n✗ FAIL: Missing required data")
        return False

def test_users_active_analytics():
    """Test: Usage analytics - users active"""
    print("\n" + "=" * 80)
    print("TEST: Active Users Analytics")
    print("=" * 80)
    
    response = requests.get(f"{DIAGRAM_SERVICE_URL}/api/analytics/users-active")
    
    if response.status_code != 200:
        print(f"\n✗ FAIL: Status code {response.status_code}")
        return False
    
    data = response.json()
    
    print(f"\nActive Users (Last 30 Days):")
    print(f"  Unique active users: {data.get('unique_active_users', 0)}")
    print(f"  Average daily active: {data.get('average_daily_active', 0):.2f}")
    print(f"  Days with data: {len(data.get('daily_active_users', []))}")
    
    # Show recent days
    daily_active = data.get('daily_active_users', [])
    if daily_active:
        print(f"\nRecent days:")
        for day in daily_active[-5:]:
            print(f"    {day['date']}: {day['active_users']} users")
    
    has_data = 'unique_active_users' in data and 'daily_active_users' in data
    
    if has_data:
        print("\n✓ PASS: Active users analytics working")
        return True
    else:
        print("\n✗ FAIL: Missing required data")
        return False

def test_storage_used_analytics():
    """Test: Usage analytics - storage used"""
    print("\n" + "=" * 80)
    print("TEST: Storage Used Analytics")
    print("=" * 80)
    
    response = requests.get(f"{DIAGRAM_SERVICE_URL}/api/analytics/storage-used")
    
    if response.status_code != 200:
        print(f"\n✗ FAIL: Status code {response.status_code}")
        return False
    
    data = response.json()
    
    total_storage = data.get('total_storage', {})
    
    print(f"\nStorage Usage:")
    print(f"  Total: {total_storage.get('mb', 0):.2f} MB ({total_storage.get('gb', 0):.3f} GB)")
    print(f"  Raw bytes: {total_storage.get('bytes', 0):,}")
    
    by_type = data.get('by_type', [])
    if by_type:
        print(f"\nStorage by diagram type:")
        for item in by_type:
            print(f"    {item['type']:10s}: {item['diagram_count']:4d} diagrams, {item['storage_mb']:.2f} MB")
    
    top_users = data.get('top_users', [])
    if top_users:
        print(f"\nTop users by storage (top 5):")
        for i, user in enumerate(top_users[:5], 1):
            print(f"    {i}. {user['email']:30s}: {user['diagram_count']:3d} diagrams, {user['storage_mb']:.2f} MB")
    
    has_data = 'total_storage' in data and 'by_type' in data
    
    if has_data:
        print("\n✓ PASS: Storage used analytics working")
        return True
    else:
        print("\n✗ FAIL: Missing required data")
        return False

def test_cost_allocation():
    """Test: Cost allocation by team"""
    print("\n" + "=" * 80)
    print("TEST: Cost Allocation Analytics")
    print("=" * 80)
    
    response = requests.get(f"{DIAGRAM_SERVICE_URL}/api/analytics/cost-allocation")
    
    if response.status_code != 200:
        print(f"\n✗ FAIL: Status code {response.status_code}")
        return False
    
    data = response.json()
    
    cost_model = data.get('cost_model', {})
    totals = data.get('totals', {})
    teams = data.get('teams', [])
    
    print(f"\nCost Model:")
    print(f"  Per user: ${cost_model.get('per_user', 0):.2f}")
    print(f"  Per diagram: ${cost_model.get('per_diagram', 0):.2f}")
    print(f"  Per GB storage: ${cost_model.get('per_gb_storage', 0):.2f}")
    print(f"  Currency: {cost_model.get('currency', 'USD')}")
    
    print(f"\nTotal Usage:")
    print(f"  Teams: {totals.get('teams', 0)}")
    print(f"  Users: {totals.get('users', 0)}")
    print(f"  Diagrams: {totals.get('diagrams', 0)}")
    print(f"  Storage: {totals.get('storage_gb', 0):.3f} GB")
    print(f"  Total cost: ${totals.get('total_cost', 0):.2f}")
    
    if teams:
        print(f"\nTeam Breakdown (top 5):")
        for i, team in enumerate(teams[:5], 1):
            metrics = team.get('metrics', {})
            costs = team.get('costs', {})
            print(f"    {i}. {team['team_name']}:")
            print(f"       Users: {metrics.get('users', 0)}, Diagrams: {metrics.get('diagrams', 0)}")
            print(f"       Cost: ${costs.get('total_cost', 0):.2f}")
    elif totals.get('teams', 0) == 0:
        print(f"\n  No team data available (this is okay for systems without teams)")
    
    has_data = 'cost_model' in data and 'totals' in data
    
    if has_data:
        print("\n✓ PASS: Cost allocation analytics working")
        return True
    else:
        print("\n✗ FAIL: Missing required data")
        return False

def test_overview():
    """Test the comprehensive overview endpoint"""
    print("\n" + "=" * 80)
    print("TEST: Analytics Overview (Comprehensive)")
    print("=" * 80)
    
    response = requests.get(f"{DIAGRAM_SERVICE_URL}/api/analytics/overview")
    
    if response.status_code != 200:
        print(f"\n✗ FAIL: Status code {response.status_code}")
        return False
    
    data = response.json()
    
    diagrams = data.get('diagrams', {})
    users = data.get('users', {})
    storage = data.get('storage', {})
    
    print(f"\nOverview:")
    print(f"  Diagrams:")
    print(f"    Total: {diagrams.get('total', 0)}")
    print(f"    Last 30 days: {diagrams.get('last_30_days', 0)}")
    print(f"  Users:")
    print(f"    Total: {users.get('total', 0)}")
    print(f"    Active (30 days): {users.get('active_last_30_days', 0)}")
    print(f"  Storage:")
    print(f"    Total: {storage.get('total_mb', 0):.2f} MB")
    
    has_data = 'diagrams' in data and 'users' in data and 'storage' in data
    
    if has_data:
        print("\n✓ PASS: Overview analytics working")
        return True
    else:
        print("\n✗ FAIL: Missing required data")
        return False

def main():
    """Run all tests"""
    print("\n")
    print("=" * 80)
    print("ENTERPRISE ANALYTICS TEST SUITE")
    print("=" * 80)
    print()
    
    tests = [
        ("Diagrams Created Analytics", test_diagrams_created_analytics),
        ("Active Users Analytics", test_users_active_analytics),
        ("Storage Used Analytics", test_storage_used_analytics),
        ("Cost Allocation Analytics", test_cost_allocation),
        ("Overview Analytics", test_overview),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ FAIL: {name} - Exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passing ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All enterprise analytics features are working!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} feature(s) need attention")
        return 1

if __name__ == "__main__":
    exit(main())
