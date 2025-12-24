"""
Test License Management Features (#550-554)

Tests for:
- Seat count tracking
- Utilization tracking
- Quota limits per plan tier
- Quota usage tracking
- Configurable quota limits
"""
import requests
import json
import sys
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Configuration
API_BASE = "http://localhost:8080"
AUTH_SERVICE = "http://localhost:8085"

def print_test_header(test_name: str):
    """Print a formatted test header."""
    print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{test_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")

def print_success(message: str):
    """Print a success message."""
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")

def print_error(message: str):
    """Print an error message."""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")

def print_info(message: str):
    """Print an info message."""
    print(f"{Fore.YELLOW}ℹ {message}{Style.RESET_ALL}")

def get_admin_token():
    """Get admin authentication token."""
    try:
        # Try to get existing admin user
        response = requests.post(f"{AUTH_SERVICE}/login", json={
            "email": "admin@autograph.com",
            "password": "Admin123!@#"
        })
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            print_success("Admin login successful")
            return token
        
        # If admin doesn't exist, create one
        print_info("Creating admin user...")
        
        # First, register a regular user
        register_response = requests.post(f"{AUTH_SERVICE}/register", json={
            "email": "admin@autograph.com",
            "password": "Admin123!@#",
            "full_name": "Admin User"
        })
        
        if register_response.status_code not in [200, 201]:
            print_error(f"Admin registration failed: {register_response.text}")
            return None
        
        # Login with the new user
        login_response = requests.post(f"{AUTH_SERVICE}/login", json={
            "email": "admin@autograph.com",
            "password": "Admin123!@#"
        })
        
        if login_response.status_code != 200:
            print_error(f"Admin login failed: {login_response.text}")
            return None
        
        token = login_response.json()["access_token"]
        
        # Update user to admin role via database
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="autograph",
            user="autograph",
            password="autograph123"
        )
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = 'admin' WHERE email = 'admin@autograph.com'")
        conn.commit()
        cursor.close()
        conn.close()
        
        print_success("Admin user created and promoted")
        return token
        
    except Exception as e:
        print_error(f"Error getting admin token: {str(e)}")
        return None


def test_seat_count_tracking():
    """Test Feature #550: License management: seat count tracking."""
    print_test_header("TEST #550: SEAT COUNT TRACKING")
    
    try:
        # Get admin token
        token = get_admin_token()
        if not token:
            print_error("Failed to get admin token")
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: Get all teams seat count
        print_info("Test 1: Get all teams seat count summary...")
        response = requests.get(
            f"{AUTH_SERVICE}/admin/license/seat-count",
            headers=headers
        )
        
        if response.status_code != 200:
            print_error(f"Failed to get seat count: {response.status_code}")
            print_error(response.text)
            return False
        
        data = response.json()
        print_success("Retrieved seat count summary")
        print_info(f"Total teams: {data['summary']['total_teams']}")
        print_info(f"Total seats: {data['summary']['total_seats']}")
        print_info(f"Used seats: {data['summary']['used_seats']}")
        print_info(f"Available seats: {data['summary']['available_seats']}")
        print_info(f"Overall utilization: {data['summary']['overall_utilization_percentage']}%")
        
        # Test 2: Get specific team seat count (if teams exist)
        if data['teams']:
            team_id = data['teams'][0]['team_id']
            print_info(f"\nTest 2: Get specific team seat count (team_id: {team_id})...")
            
            response = requests.get(
                f"{AUTH_SERVICE}/admin/license/seat-count?team_id={team_id}",
                headers=headers
            )
            
            if response.status_code != 200:
                print_error(f"Failed to get team seat count: {response.status_code}")
                return False
            
            team_data = response.json()
            print_success(f"Retrieved seat count for team: {team_data['team_name']}")
            print_info(f"Plan: {team_data['plan']}")
            print_info(f"Total seats: {team_data['total_seats']}")
            print_info(f"Used seats: {team_data['used_seats']}")
            print_info(f"Available seats: {team_data['available_seats']}")
            print_info(f"Utilization: {team_data['utilization_percentage']}%")
        else:
            print_info("No teams found, skipping specific team test")
        
        print_success("\n✓ TEST #550 PASSED: Seat count tracking working correctly")
        return True
        
    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_utilization_tracking():
    """Test Feature #551: License management: utilization tracking."""
    print_test_header("TEST #551: UTILIZATION TRACKING")
    
    try:
        # Get admin token
        token = get_admin_token()
        if not token:
            print_error("Failed to get admin token")
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: Get 30-day utilization
        print_info("Test 1: Get 30-day utilization metrics...")
        response = requests.get(
            f"{AUTH_SERVICE}/admin/license/utilization?days=30",
            headers=headers
        )
        
        if response.status_code != 200:
            print_error(f"Failed to get utilization: {response.status_code}")
            print_error(response.text)
            return False
        
        data = response.json()
        print_success("Retrieved utilization metrics")
        print_info(f"Period: {data['period_days']} days")
        print_info(f"Total users: {data['overall_metrics']['total_users']}")
        print_info(f"Active users: {data['overall_metrics']['active_users']}")
        print_info(f"User utilization: {data['overall_metrics']['user_utilization_percentage']}%")
        print_info(f"Diagrams created: {data['activity_metrics']['diagrams_created']}")
        print_info(f"AI generations: {data['activity_metrics']['ai_generations']}")
        print_info(f"Exports: {data['activity_metrics']['exports']}")
        
        # Test 2: Get 7-day utilization
        print_info("\nTest 2: Get 7-day utilization metrics...")
        response = requests.get(
            f"{AUTH_SERVICE}/admin/license/utilization?days=7",
            headers=headers
        )
        
        if response.status_code != 200:
            print_error(f"Failed to get 7-day utilization: {response.status_code}")
            return False
        
        data_7d = response.json()
        print_success("Retrieved 7-day utilization metrics")
        print_info(f"Active users (7d): {data_7d['overall_metrics']['active_users']}")
        print_info(f"Diagrams created (7d): {data_7d['activity_metrics']['diagrams_created']}")
        
        print_success("\n✓ TEST #551 PASSED: Utilization tracking working correctly")
        return True
        
    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_quota_limits():
    """Test Feature #552-554: Quota management: limits per plan tier."""
    print_test_header("TEST #552-554: QUOTA MANAGEMENT")
    
    try:
        # Get admin token
        token = get_admin_token()
        if not token:
            print_error("Failed to get admin token")
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: Get all quota limits
        print_info("Test 1: Get quota limits for all plans...")
        response = requests.get(
            f"{AUTH_SERVICE}/admin/quota/limits",
            headers=headers
        )
        
        if response.status_code != 200:
            print_error(f"Failed to get quota limits: {response.status_code}")
            print_error(response.text)
            return False
        
        data = response.json()
        print_success("Retrieved quota limits for all plans")
        
        for plan_name, limits in data['plans'].items():
            print_info(f"\n{plan_name.upper()} Plan:")
            print_info(f"  Max diagrams: {limits['max_diagrams']}")
            print_info(f"  Max storage: {limits['max_storage_mb']} MB")
            print_info(f"  Max team members: {limits['max_team_members']}")
            print_info(f"  Max AI generations/month: {limits['max_ai_generations_per_month']}")
            print_info(f"  Max exports/month: {limits['max_exports_per_month']}")
        
        # Test 2: Get specific plan limits
        print_info("\nTest 2: Get quota limits for Pro plan...")
        response = requests.get(
            f"{AUTH_SERVICE}/admin/quota/limits?plan=pro",
            headers=headers
        )
        
        if response.status_code != 200:
            print_error(f"Failed to get Pro plan limits: {response.status_code}")
            return False
        
        pro_limits = response.json()
        print_success("Retrieved Pro plan limits")
        print_info(f"Max diagrams: {pro_limits['max_diagrams']}")
        print_info(f"Max AI generations/month: {pro_limits['max_ai_generations_per_month']}")
        
        # Test 3: Set custom quota limits
        print_info("\nTest 3: Set custom quota limits for Free plan...")
        custom_limits = {
            "plan": "free",
            "max_diagrams": 15,  # Increase from 10 to 15
            "max_storage_mb": 150,
            "max_team_members": 5,
            "max_ai_generations_per_month": 60,
            "max_exports_per_month": 30
        }
        
        response = requests.post(
            f"{AUTH_SERVICE}/admin/quota/set-limits?plan=free",
            headers=headers,
            json=custom_limits
        )
        
        if response.status_code != 200:
            print_error(f"Failed to set quota limits: {response.status_code}")
            print_error(response.text)
            return False
        
        result = response.json()
        print_success("Custom quota limits set successfully")
        print_info(f"Updated Free plan limits: {result['limits']}")
        
        # Test 4: Get quota usage (if users exist)
        print_info("\nTest 4: Get quota usage...")
        
        # Get current user info
        me_response = requests.get(f"{AUTH_SERVICE}/me", headers=headers)
        if me_response.status_code == 200:
            user_data = me_response.json()
            user_id = user_data['id']
            
            response = requests.get(
                f"{AUTH_SERVICE}/admin/quota/usage?user_id={user_id}",
                headers=headers
            )
            
            if response.status_code != 200:
                print_error(f"Failed to get quota usage: {response.status_code}")
                return False
            
            usage = response.json()
            print_success(f"Retrieved quota usage for user: {usage['email']}")
            print_info(f"Plan: {usage['plan']}")
            print_info(f"Diagrams: {usage['usage']['diagrams']}")
            print_info(f"AI generations this month: {usage['usage']['ai_generations_this_month']}")
            print_info(f"Exports this month: {usage['usage']['exports_this_month']}")
        else:
            print_info("Could not get current user, skipping usage test")
        
        print_success("\n✓ TEST #552-554 PASSED: Quota management working correctly")
        return True
        
    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all license management tests."""
    print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}LICENSE MANAGEMENT TESTS - Features #550-554{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
    
    results = []
    
    # Test #550: Seat count tracking
    results.append(("Feature #550: Seat Count Tracking", test_seat_count_tracking()))
    
    # Test #551: Utilization tracking
    results.append(("Feature #551: Utilization Tracking", test_utilization_tracking()))
    
    # Test #552-554: Quota management
    results.append(("Features #552-554: Quota Management", test_quota_limits()))
    
    # Print summary
    print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}TEST SUMMARY{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print(f"{Fore.GREEN}✓ {test_name}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ {test_name}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}Results: {passed}/{total} tests passed{Style.RESET_ALL}")
    
    if passed == total:
        print(f"\n{Fore.GREEN}🎉 All license management tests passed!{Style.RESET_ALL}\n")
        return 0
    else:
        print(f"\n{Fore.RED}Some tests failed. Please review the output above.{Style.RESET_ALL}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
