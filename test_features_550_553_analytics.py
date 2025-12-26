#!/usr/bin/env python3
"""
Test script for Features #550-553: Usage Analytics and Cost Allocation

Tests:
- Feature #550: Enterprise: Usage analytics: diagrams created
- Feature #551: Enterprise: Usage analytics: users active
- Feature #552: Enterprise: Usage analytics: storage used
- Feature #553: Enterprise: Cost allocation: track usage by team
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
API_GATEWAY = "https://localhost:8080"

def print_section(title):
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")

def print_test(test_num, description):
    """Print test header."""
    print(f"\n[Test {test_num}] {description}")

def print_success(message):
    """Print success message."""
    print(f"  ✓ {message}")

def print_error(message):
    """Print error message."""
    print(f"  ✗ {message}")

def print_data(label, data, indent=2):
    """Print formatted data."""
    prefix = " " * indent
    if isinstance(data, dict):
        print(f"{prefix}{label}:")
        for key, value in data.items():
            if isinstance(value, dict):
                print_data(f"{key}", value, indent + 2)
            elif isinstance(value, list):
                print(f"{prefix}  {key}: {len(value)} items")
            else:
                print(f"{prefix}  {key}: {value}")
    else:
        print(f"{prefix}{label}: {data}")

def test_diagrams_created_analytics():
    """Test Feature #550: Diagrams created analytics."""
    print_section("Feature #550: Diagrams Created Analytics")

    # Test 1: Get diagrams created analytics (default 30 days)
    print_test(1, "Get diagrams created analytics (30 days)")
    try:
        response = requests.get(f"{API_GATEWAY}/api/admin/analytics/diagrams-created", timeout=10, verify=False)

        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            data = response.json()

            # Check response structure
            assert "success" in data, "Response missing 'success' field"
            assert data["success"] is True, "Success should be True"
            assert "analytics" in data, "Response missing 'analytics' field"

            analytics = data["analytics"]

            # Verify total diagrams count
            assert "total_diagrams" in analytics, "Missing total_diagrams"
            total_diagrams = analytics["total_diagrams"]
            print_success(f"Total diagrams: {total_diagrams}")

            # Verify diagrams per day chart
            assert "diagrams_per_day" in analytics, "Missing diagrams_per_day"
            diagrams_per_day = analytics["diagrams_per_day"]
            print_success(f"Diagrams per day data: {len(diagrams_per_day)} days")

            # Show sample data
            if diagrams_per_day:
                for i, day in enumerate(diagrams_per_day[:5]):
                    print(f"    Day {i+1}: {day['date']} - {day['count']} diagrams")

            # Verify trends
            assert "trend" in analytics, "Missing trend data"
            trend = analytics["trend"]
            assert "direction" in trend, "Missing trend direction"
            assert "percentage" in trend, "Missing trend percentage"

            print_data("Trend", trend)

            print_success("Feature #550 test passed!")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: Get diagrams created analytics (7 days)
    print_test(2, "Get diagrams created analytics (7 days)")
    try:
        response = requests.get(
            f"{API_GATEWAY}/api/admin/analytics/diagrams-created?days=7",
            timeout=10
        )

        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            data = response.json()
            analytics = data["analytics"]

            assert analytics["period_days"] == 7, "Period should be 7 days"
            print_success(f"Period: {analytics['period_days']} days")
            print_success(f"Total diagrams: {analytics['total_diagrams']}")

            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False

def test_users_active_analytics():
    """Test Feature #551: Active users analytics."""
    print_section("Feature #551: Active Users Analytics")

    print_test(1, "Get active users analytics (30 days)")
    try:
        response = requests.get(f"{API_GATEWAY}/api/admin/analytics/users-active", timeout=10, verify=False)

        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            data = response.json()

            assert "success" in data, "Response missing 'success' field"
            assert data["success"] is True, "Success should be True"
            assert "analytics" in data, "Response missing 'analytics' field"

            analytics = data["analytics"]

            # Verify user counts
            assert "total_users" in analytics, "Missing total_users"
            assert "active_users" in analytics, "Missing active_users"

            total_users = analytics["total_users"]
            active_users = analytics["active_users"]

            print_success(f"Total users: {total_users}")
            print_success(f"Active users (30 days): {active_users}")

            if total_users > 0:
                activity_rate = (active_users / total_users) * 100
                print_success(f"Activity rate: {activity_rate:.1f}%")

            # Verify active users per day
            assert "active_users_per_day" in analytics, "Missing active_users_per_day"
            active_users_per_day = analytics["active_users_per_day"]
            print_success(f"Active users per day data: {len(active_users_per_day)} days")

            # Verify trends
            assert "trend" in analytics, "Missing trend data"
            trend = analytics["trend"]
            print_data("Trend", trend)

            print_success("Feature #551 test passed!")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_storage_used_analytics():
    """Test Feature #552: Storage used analytics."""
    print_section("Feature #552: Storage Used Analytics")

    print_test(1, "Get storage usage analytics")
    try:
        response = requests.get(f"{API_GATEWAY}/api/admin/analytics/storage-used", timeout=10, verify=False)

        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            data = response.json()

            assert "success" in data, "Response missing 'success' field"
            assert data["success"] is True, "Success should be True"
            assert "analytics" in data, "Response missing 'analytics' field"

            analytics = data["analytics"]

            # Verify total storage
            assert "total_storage" in analytics, "Missing total_storage"
            total_storage = analytics["total_storage"]

            assert "bytes" in total_storage, "Missing bytes in total_storage"
            assert "mb" in total_storage, "Missing mb in total_storage"
            assert "gb" in total_storage, "Missing gb in total_storage"
            assert "total_files" in total_storage, "Missing total_files"

            print_success(f"Total storage: {total_storage['gb']} GB ({total_storage['mb']} MB)")
            print_success(f"Total files: {total_storage['total_files']}")

            # Verify storage per team
            assert "storage_per_team" in analytics, "Missing storage_per_team"
            storage_per_team = analytics["storage_per_team"]
            print_success(f"Storage per team data: {len(storage_per_team)} teams")

            # Show top teams by storage
            if storage_per_team:
                print("    Top teams by storage:")
                for i, team in enumerate(storage_per_team[:3]):
                    print(f"      {i+1}. {team['team_name']}: {team['storage_mb']} MB ({team['file_count']} files)")

            # Verify storage per file type
            assert "storage_per_type" in analytics, "Missing storage_per_type"
            storage_per_type = analytics["storage_per_type"]
            print_success(f"Storage per type data: {len(storage_per_type)} types")

            # Show file types
            if storage_per_type:
                print("    Storage by file type:")
                for file_type in storage_per_type:
                    print(f"      {file_type['file_type']}: {file_type['storage_mb']} MB ({file_type['file_count']} files)")

            # Verify trends
            assert "trend" in analytics, "Missing trend data"
            trend = analytics["trend"]
            print_data("Trend", trend)

            print_success("Feature #552 test passed!")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_cost_allocation_analytics():
    """Test Feature #553: Cost allocation analytics."""
    print_section("Feature #553: Cost Allocation Analytics")

    print_test(1, "Get cost allocation by team")
    try:
        response = requests.get(f"{API_GATEWAY}/api/admin/analytics/cost-allocation", timeout=10, verify=False)

        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            data = response.json()

            assert "success" in data, "Response missing 'success' field"
            assert data["success"] is True, "Success should be True"
            assert "analytics" in data, "Response missing 'analytics' field"

            analytics = data["analytics"]

            # Verify total metrics
            assert "total_storage_bytes" in analytics, "Missing total_storage_bytes"
            assert "total_storage_mb" in analytics, "Missing total_storage_mb"
            assert "total_files" in analytics, "Missing total_files"

            print_success(f"Total storage: {analytics['total_storage_mb']} MB")
            print_success(f"Total files: {analytics['total_files']}")

            # Verify team usage
            assert "team_usage" in analytics, "Missing team_usage"
            team_usage = analytics["team_usage"]
            print_success(f"Teams analyzed: {len(team_usage)}")

            # Show team metrics and cost allocation
            if team_usage:
                print("\n    Team usage and cost allocation:")
                for i, team in enumerate(team_usage[:5]):
                    print(f"\n      Team {i+1}: {team['team_name']}")
                    print(f"        Members: {team['metrics']['members']}")
                    print(f"        Files: {team['metrics']['files']}")
                    print(f"        Storage: {team['metrics']['storage_mb']} MB")
                    print(f"        Versions: {team['metrics']['versions']}")
                    print(f"        Comments: {team['metrics']['comments']}")
                    print(f"        Views: {team['metrics']['views']}")
                    print(f"        Cost share: {team['cost_allocation']['weighted_cost_share']}%")

            # Verify cost model
            assert "cost_model" in analytics, "Missing cost_model"
            cost_model = analytics["cost_model"]
            print_data("\n  Cost model", cost_model)

            print_success("Feature #553 test passed!")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all analytics tests."""
    print("\n" + "=" * 70)
    print("  USAGE ANALYTICS AND COST ALLOCATION TESTS")
    print("  Features #550-553")
    print("=" * 70)

    results = {
        "Feature #550 (Diagrams created analytics)": test_diagrams_created_analytics(),
        "Feature #551 (Active users analytics)": test_users_active_analytics(),
        "Feature #552 (Storage used analytics)": test_storage_used_analytics(),
        "Feature #553 (Cost allocation analytics)": test_cost_allocation_analytics(),
    }

    # Print summary
    print_section("TEST SUMMARY")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for feature, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {feature}: {status}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n  🎉 ALL ANALYTICS FEATURES WORKING!")
        return 0
    else:
        print("\n  ⚠ Some tests failed")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
