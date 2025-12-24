"""
Test API Rate Limiting and Webhook Management Features (#555-556)

Tests for:
- API rate limiting per plan
- Webhook management
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
        response = requests.post(f"{AUTH_SERVICE}/login", json={
            "email": "admin@autograph.com",
            "password": "Admin123!@#"
        })
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            print_success("Admin login successful")
            return token
        else:
            print_error(f"Admin login failed: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Error getting admin token: {str(e)}")
        return None


def test_rate_limiting_config():
    """Test Feature #555: API rate limiting per plan."""
    print_test_header("TEST #555: API RATE LIMITING PER PLAN")
    
    try:
        # Get admin token
        token = get_admin_token()
        if not token:
            print_error("Failed to get admin token")
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: Get all rate limit configurations
        print_info("Test 1: Get rate limit configs for all plans...")
        response = requests.get(
            f"{AUTH_SERVICE}/admin/rate-limit/config",
            headers=headers
        )
        
        if response.status_code != 200:
            print_error(f"Failed to get rate limit config: {response.status_code}")
            print_error(response.text)
            return False
        
        data = response.json()
        print_success("Retrieved rate limit configurations")
        
        for plan_name, config in data['plans'].items():
            print_info(f"\n{plan_name.upper()} Plan:")
            print_info(f"  Requests/hour: {config['requests_per_hour']}")
            print_info(f"  Requests/day: {config['requests_per_day']}")
            print_info(f"  Burst limit: {config['burst_limit']}")
        
        # Verify free plan limits
        free_config = data['plans']['free']
        if free_config['requests_per_hour'] != 100:
            print_error(f"Free plan should have 100 req/hour, got {free_config['requests_per_hour']}")
            return False
        print_success("Free plan limits correct (100 req/hour)")
        
        # Verify pro plan limits
        pro_config = data['plans']['pro']
        if pro_config['requests_per_hour'] != 1000:
            print_error(f"Pro plan should have 1000 req/hour, got {pro_config['requests_per_hour']}")
            return False
        print_success("Pro plan limits correct (1000 req/hour)")
        
        # Verify enterprise plan limits (unlimited)
        enterprise_config = data['plans']['enterprise']
        if enterprise_config['requests_per_hour'] != -1:
            print_error(f"Enterprise plan should be unlimited (-1), got {enterprise_config['requests_per_hour']}")
            return False
        print_success("Enterprise plan limits correct (unlimited)")
        
        # Test 2: Get specific plan config
        print_info("\nTest 2: Get Free plan rate limit config...")
        response = requests.get(
            f"{AUTH_SERVICE}/admin/rate-limit/config?plan=free",
            headers=headers
        )
        
        if response.status_code != 200:
            print_error(f"Failed to get Free plan config: {response.status_code}")
            return False
        
        free_data = response.json()
        print_success(f"Retrieved Free plan config")
        print_info(f"Requests/hour: {free_data['requests_per_hour']}")
        
        # Test 3: Set custom rate limit config
        print_info("\nTest 3: Set custom rate limits for Free plan...")
        custom_config = {
            "plan": "free",
            "requests_per_hour": 150,  # Increase from 100 to 150
            "requests_per_day": 1500,
            "burst_limit": 15
        }
        
        response = requests.post(
            f"{AUTH_SERVICE}/admin/rate-limit/config?plan=free",
            headers=headers,
            json=custom_config
        )
        
        if response.status_code != 200:
            print_error(f"Failed to set rate limit config: {response.status_code}")
            print_error(response.text)
            return False
        
        result = response.json()
        print_success("Custom rate limits set successfully")
        print_info(f"Updated config: {result['config']}")
        
        # Verify the update
        response = requests.get(
            f"{AUTH_SERVICE}/admin/rate-limit/config?plan=free",
            headers=headers
        )
        
        if response.status_code != 200:
            print_error("Failed to verify updated config")
            return False
        
        updated_data = response.json()
        if updated_data['requests_per_hour'] != 150:
            print_error(f"Config not updated correctly. Expected 150, got {updated_data['requests_per_hour']}")
            return False
        
        print_success("Verified rate limit update")
        
        print_success("\n✓ TEST #555 PASSED: Rate limiting per plan working correctly")
        return True
        
    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_webhook_management():
    """Test Feature #556: Webhook management."""
    print_test_header("TEST #556: WEBHOOK MANAGEMENT")
    
    try:
        # Get admin token
        token = get_admin_token()
        if not token:
            print_error("Failed to get admin token")
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: List webhooks (should be empty initially)
        print_info("Test 1: List webhooks...")
        response = requests.get(
            f"{AUTH_SERVICE}/webhooks",
            headers=headers
        )
        
        if response.status_code != 200:
            print_error(f"Failed to list webhooks: {response.status_code}")
            print_error(response.text)
            return False
        
        data = response.json()
        print_success(f"Listed webhooks: {data['count']} found")
        
        # Test 2: Create a webhook
        print_info("\nTest 2: Create webhook for diagram.created event...")
        webhook_data = {
            "url": "https://webhook.site/test-autograph",
            "events": ["diagram.created", "diagram.updated"],
            "description": "Test webhook for diagram events",
            "is_active": True
        }
        
        response = requests.post(
            f"{AUTH_SERVICE}/webhooks",
            headers=headers,
            json=webhook_data
        )
        
        if response.status_code != 200:
            print_error(f"Failed to create webhook: {response.status_code}")
            print_error(response.text)
            return False
        
        webhook_result = response.json()
        webhook_id = webhook_result['webhook']['id']
        print_success(f"Webhook created with ID: {webhook_id}")
        print_info(f"URL: {webhook_result['webhook']['url']}")
        print_info(f"Events: {webhook_result['webhook']['events']}")
        
        # Test 3: Get webhook by ID
        print_info("\nTest 3: Get webhook by ID...")
        response = requests.get(
            f"{AUTH_SERVICE}/webhooks/{webhook_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            print_error(f"Failed to get webhook: {response.status_code}")
            return False
        
        webhook = response.json()
        print_success(f"Retrieved webhook: {webhook['url']}")
        
        # Test 4: Update webhook
        print_info("\nTest 4: Update webhook...")
        update_data = {
            "is_active": False,
            "description": "Updated test webhook (disabled)"
        }
        
        response = requests.put(
            f"{AUTH_SERVICE}/webhooks/{webhook_id}",
            headers=headers,
            json=update_data
        )
        
        if response.status_code != 200:
            print_error(f"Failed to update webhook: {response.status_code}")
            return False
        
        updated_webhook = response.json()['webhook']
        print_success("Webhook updated successfully")
        print_info(f"Active: {updated_webhook['is_active']}")
        print_info(f"Description: {updated_webhook['description']}")
        
        # Test 5: Test webhook (send test event)
        print_info("\nTest 5: Test webhook (send test event)...")
        response = requests.post(
            f"{AUTH_SERVICE}/webhooks/{webhook_id}/test",
            headers=headers
        )
        
        if response.status_code != 200:
            print_error(f"Failed to test webhook: {response.status_code}")
            return False
        
        test_result = response.json()
        print_success("Webhook test completed")
        print_info(f"Success: {test_result['success']}")
        if 'status_code' in test_result:
            print_info(f"Response status: {test_result['status_code']}")
        if 'error' in test_result:
            print_info(f"Error (expected for test URL): {test_result['error'][:100]}")
        
        # Test 6: List webhooks again (should show 1)
        print_info("\nTest 6: List webhooks again...")
        response = requests.get(
            f"{AUTH_SERVICE}/webhooks",
            headers=headers
        )
        
        if response.status_code != 200:
            print_error("Failed to list webhooks")
            return False
        
        data = response.json()
        if data['count'] < 1:
            print_error(f"Expected at least 1 webhook, got {data['count']}")
            return False
        
        print_success(f"Found {data['count']} webhook(s)")
        
        # Test 7: Delete webhook
        print_info("\nTest 7: Delete webhook...")
        response = requests.delete(
            f"{AUTH_SERVICE}/webhooks/{webhook_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            print_error(f"Failed to delete webhook: {response.status_code}")
            return False
        
        print_success("Webhook deleted successfully")
        
        # Verify deletion
        response = requests.get(
            f"{AUTH_SERVICE}/webhooks/{webhook_id}",
            headers=headers
        )
        
        if response.status_code != 404:
            print_error("Webhook should be deleted (404), but still accessible")
            return False
        
        print_success("Verified webhook deletion (404)")
        
        print_success("\n✓ TEST #556 PASSED: Webhook management working correctly")
        return True
        
    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all rate limiting and webhook tests."""
    print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}RATE LIMITING & WEBHOOK TESTS - Features #555-556{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
    
    results = []
    
    # Test #555: API rate limiting per plan
    results.append(("Feature #555: API Rate Limiting Per Plan", test_rate_limiting_config()))
    
    # Test #556: Webhook management
    results.append(("Feature #556: Webhook Management", test_webhook_management()))
    
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
        print(f"\n{Fore.GREEN}🎉 All rate limiting and webhook tests passed!{Style.RESET_ALL}\n")
        return 0
    else:
        print(f"\n{Fore.RED}Some tests failed. Please review the output above.{Style.RESET_ALL}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
