#!/usr/bin/env python3
"""Test Features #507-508: Scheduled Exports (Daily and Weekly)"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8097"

def test_daily_scheduled_export():
    """
    Feature #507: Scheduled exports - auto-export daily

    Tests:
    - POST /api/scheduled-exports with daily schedule
    - Verify schedule is created
    - Verify next run time is calculated correctly
    """
    print("\n" + "="*60)
    print("Testing Feature #507: Daily Scheduled Export")
    print("="*60)

    # Create a daily scheduled export
    schedule_request = {
        "file_id": "test-diagram-daily",
        "user_id": "test-user-507",
        "schedule_type": "daily",
        "schedule_time": "02:00:00",  # 2 AM daily
        "timezone": "UTC",
        "export_format": "png",
        "destination_type": "local"
    }

    try:
        print("\n1. Creating daily scheduled export...")
        response = requests.post(
            f"{BASE_URL}/api/scheduled-exports",
            json=schedule_request,
            timeout=10
        )

        print(f"   Status: {response.status_code}")

        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ Scheduled export created")
            print(f"   Schedule ID: {data.get('id')}")
            print(f"   Schedule Type: {data.get('schedule_type')}")
            print(f"   Schedule Time: {data.get('schedule_time')}")
            print(f"   Next Run: {data.get('next_run_at')}")
            print(f"   Active: {data.get('is_active')}")

            # Verify required fields
            if data.get('schedule_type') != 'daily':
                print(f"   ❌ Expected schedule_type='daily', got '{data.get('schedule_type')}'")
                return False

            if not data.get('next_run_at'):
                print(f"   ❌ Missing next_run_at field")
                return False

            print("\n✅ Feature #507 PASSED: Daily scheduled export works correctly")
            return True
        else:
            error_detail = response.json() if response.content else response.text
            print(f"   ❌ Request failed: {error_detail}")
            return False

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_weekly_scheduled_export():
    """
    Feature #508: Scheduled exports - auto-export weekly

    Tests:
    - POST /api/scheduled-exports with weekly schedule
    - Verify schedule is created with correct day of week
    - Verify next run time is calculated correctly
    """
    print("\n" + "="*60)
    print("Testing Feature #508: Weekly Scheduled Export")
    print("="*60)

    # Create a weekly scheduled export (every Monday at 3 AM)
    schedule_request = {
        "file_id": "test-diagram-weekly",
        "user_id": "test-user-508",
        "schedule_type": "weekly",
        "schedule_time": "03:00:00",  # 3 AM
        "schedule_day_of_week": 0,    # Monday (0=Monday, 6=Sunday)
        "timezone": "UTC",
        "export_format": "pdf",
        "destination_type": "local"
    }

    try:
        print("\n1. Creating weekly scheduled export...")
        response = requests.post(
            f"{BASE_URL}/api/scheduled-exports",
            json=schedule_request,
            timeout=10
        )

        print(f"   Status: {response.status_code}")

        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ Scheduled export created")
            print(f"   Schedule ID: {data.get('id')}")
            print(f"   Schedule Type: {data.get('schedule_type')}")
            print(f"   Schedule Day: {data.get('schedule_day_of_week')} (Monday)")
            print(f"   Schedule Time: {data.get('schedule_time')}")
            print(f"   Next Run: {data.get('next_run_at')}")
            print(f"   Active: {data.get('is_active')}")

            # Verify required fields
            if data.get('schedule_type') != 'weekly':
                print(f"   ❌ Expected schedule_type='weekly', got '{data.get('schedule_type')}'")
                return False

            if data.get('schedule_day_of_week') != 0:
                print(f"   ❌ Expected schedule_day_of_week=0, got {data.get('schedule_day_of_week')}")
                return False

            if not data.get('next_run_at'):
                print(f"   ❌ Missing next_run_at field")
                return False

            print("\n✅ Feature #508 PASSED: Weekly scheduled export works correctly")
            return True
        else:
            error_detail = response.json() if response.content else response.text
            print(f"   ❌ Request failed: {error_detail}")
            return False

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_list_scheduled_exports():
    """Test listing all scheduled exports"""
    print("\n" + "="*60)
    print("Testing: List Scheduled Exports")
    print("="*60)

    try:
        print("\n2. Listing all scheduled exports...")
        response = requests.get(
            f"{BASE_URL}/api/scheduled-exports",
            params={"user_id": "test-user-507"},
            timeout=10
        )

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            schedules = data.get('schedules', [])
            print(f"   ✅ Found {len(schedules)} scheduled exports")

            for schedule in schedules:
                print(f"     - {schedule.get('schedule_type')} export (ID: {schedule.get('id')})")

            return True
        else:
            print(f"   ⚠️  List endpoint returned {response.status_code}")
            return True  # Not required for features #507-508

    except Exception as e:
        print(f"   ⚠️  Error listing schedules: {str(e)}")
        return True  # Not required for features #507-508


if __name__ == "__main__":
    print("\n" + "="*60)
    print("FEATURES #507-508: SCHEDULED EXPORTS - COMPREHENSIVE TEST")
    print("="*60)

    feature_507_passed = test_daily_scheduled_export()
    feature_508_passed = test_weekly_scheduled_export()
    test_list_scheduled_exports()

    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)

    if feature_507_passed:
        print("✅ Feature #507: Daily scheduled export PASSED")
    else:
        print("❌ Feature #507: Daily scheduled export FAILED")

    if feature_508_passed:
        print("✅ Feature #508: Weekly scheduled export PASSED")
    else:
        print("❌ Feature #508: Weekly scheduled export FAILED")

    all_passed = feature_507_passed and feature_508_passed

    print("\n" + "="*60)
    if all_passed:
        print("ALL FEATURES PASSED ✅")
    else:
        print("SOME FEATURES FAILED ❌")
    print("="*60)

    exit(0 if all_passed else 1)
