"""
Test Feature #554: Enterprise: License management: seat count enforcement

Test scenario:
1. Configure 100 seats
2. Add 100 users
3. Attempt to add 101st user
4. Verify blocked with "License limit reached"
"""
import requests
import json
import sys
from colorama import init, Fore, Style
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize colorama
init(autoreset=True)

# Configuration
AUTH_SERVICE = "https://localhost:8085"

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
        # Try to login with existing admin
        response = requests.post(f"{AUTH_SERVICE}/login", json={
            "email": "admin@autograph.com",
            "password": "Admin123!@#"
        }, verify=False)

        if response.status_code == 200:
            token = response.json()["access_token"]
            print_success("Admin login successful")
            return token

        print_info("Admin doesn't exist, creating...")

        # Register admin user
        register_response = requests.post(f"{AUTH_SERVICE}/register", json={
            "email": "admin@autograph.com",
            "password": "Admin123!@#",
            "full_name": "Admin User"
        }, verify=False)

        if register_response.status_code not in [200, 201]:
            print_error(f"Admin registration failed: {register_response.text}")
            return None

        # Login
        login_response = requests.post(f"{AUTH_SERVICE}/login", json={
            "email": "admin@autograph.com",
            "password": "Admin123!@#"
        }, verify=False)

        if login_response.status_code != 200:
            print_error(f"Admin login failed: {login_response.text}")
            return None

        token = login_response.json()["access_token"]

        # Promote to admin and verify email via database
        import subprocess
        subprocess.run([
            "docker", "exec", "autograph-postgres",
            "psql", "-U", "autograph", "-d", "autograph",
            "-c", "UPDATE users SET role = 'admin', is_verified = true WHERE email = 'admin@autograph.com'"
        ], check=True, capture_output=True)

        print_success("Admin user created and promoted")
        return token

    except Exception as e:
        print_error(f"Error getting admin token: {str(e)}")
        return None


def cleanup_test_users():
    """Clean up test users from previous runs."""
    try:
        import subprocess

        # Delete test users (keep admin)
        result = subprocess.run([
            "docker", "exec", "autograph-postgres",
            "psql", "-U", "autograph", "-d", "autograph",
            "-c",
            "DELETE FROM users WHERE email LIKE 'testuser554_%@example.com';"
        ], capture_output=True, text=True)

        # Don't fail if cleanup fails (table might be empty)
        print_info("Cleaned up test users from previous runs (if any)")
        return True

    except Exception as e:
        # Don't fail the test if cleanup fails
        print_info(f"Cleanup warning: {str(e)}")
        return True


def get_current_user_count():
    """Get the current number of users in the system."""
    try:
        import subprocess
        result = subprocess.run([
            "docker", "exec", "autograph-postgres",
            "psql", "-U", "autograph", "-d", "autograph",
            "-t", "-c", "SELECT COUNT(*) FROM users"
        ], check=True, capture_output=True, text=True)

        count = int(result.stdout.strip())
        return count
    except Exception as e:
        print_error(f"Error getting user count: {str(e)}")
        return 0


def test_seat_limit_enforcement():
    """Test Feature #554: Seat limit enforcement."""
    print_test_header("TEST #554: SEAT LIMIT ENFORCEMENT")

    try:
        # Step 0: Clean up test users
        print_info("Step 0: Cleaning up test users from previous runs...")
        if not cleanup_test_users():
            return False

        # Get admin token
        token = get_admin_token()
        if not token:
            print_error("Failed to get admin token")
            return False

        headers = {"Authorization": f"Bearer {token}"}

        # Get current user count
        initial_count = get_current_user_count()
        print_info(f"Current user count: {initial_count}")

        # Step 1: Configure 100 seats total (current users + 5 more)
        # This allows us to test the limit without creating 100 users
        seat_limit = initial_count + 5
        print_info(f"\nStep 1: Configure {seat_limit} seats...")

        response = requests.post(
            f"{AUTH_SERVICE}/admin/config/license",
            headers=headers,
            json={"max_seats": seat_limit},
            verify=False
        )

        if response.status_code != 200:
            print_error(f"Failed to configure license: {response.status_code}")
            print_error(response.text)
            return False

        print_success(f"License configured with {seat_limit} seats")

        # Verify configuration
        config_response = requests.get(
            f"{AUTH_SERVICE}/admin/config/license",
            headers=headers,
            verify=False
        )

        if config_response.status_code != 200:
            print_error("Failed to verify license configuration")
            return False

        config = config_response.json()
        if config.get("max_seats") != seat_limit:
            print_error(f"License not configured correctly: {config}")
            return False

        print_success(f"License configuration verified: {seat_limit} seats")

        # Step 2: Add users up to the limit
        print_info(f"\nStep 2: Adding {5} users (up to the limit)...")

        users_to_add = 5
        successful_registrations = 0

        for i in range(users_to_add):
            email = f"testuser554_{i}@example.com"

            # Register user (no auth header needed for registration)
            reg_response = requests.post(f"{AUTH_SERVICE}/register", json={
                "email": email,
                "password": "TestUser123!@#",
                "full_name": f"Test User {i}"
            }, verify=False)

            if reg_response.status_code in [200, 201]:
                successful_registrations += 1
                print_success(f"  Registered user {i+1}/{users_to_add}: {email}")
            else:
                print_error(f"  Failed to register user {i+1}: {reg_response.text}")
                # Continue to see if we hit the limit

        print_info(f"Successfully registered {successful_registrations}/{users_to_add} users")

        # Verify we're at the limit
        current_count = get_current_user_count()
        print_info(f"Current user count: {current_count}, Limit: {seat_limit}")

        # Step 3: Attempt to add the (limit + 1)th user
        print_info(f"\nStep 3: Attempting to add user beyond the limit...")

        over_limit_email = f"testuser554_overlimit@example.com"
        over_limit_response = requests.post(f"{AUTH_SERVICE}/register", json={
            "email": over_limit_email,
            "password": "TestUser123!@#",
            "full_name": "Over Limit User"
        }, verify=False)

        # Step 4: Verify blocked with "License limit reached"
        print_info("Step 4: Verifying rejection...")

        if over_limit_response.status_code == 403:
            error_detail = over_limit_response.json().get("detail", "")

            if error_detail == "License limit reached":
                print_success("✓ Registration correctly blocked!")
                print_success(f"✓ Error message correct: '{error_detail}'")
                print_success("\n✓ TEST #554 PASSED: Seat limit enforcement working correctly!")

                # Clean up
                cleanup_test_users()

                return True
            else:
                print_error(f"Wrong error message: '{error_detail}'")
                print_error(f"Expected: 'License limit reached'")
                return False
        else:
            print_error(f"Registration not blocked! Status: {over_limit_response.status_code}")
            print_error(f"Response: {over_limit_response.text}")
            return False

    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the seat limit enforcement test."""
    print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}LICENSE MANAGEMENT TEST - Feature #554{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")

    result = test_seat_limit_enforcement()

    # Print summary
    print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}TEST SUMMARY{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")

    if result:
        print(f"{Fore.GREEN}✓ Feature #554: Seat Limit Enforcement{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}🎉 Test passed!{Style.RESET_ALL}\n")
        return 0
    else:
        print(f"{Fore.RED}✗ Feature #554: Seat Limit Enforcement{Style.RESET_ALL}")
        print(f"\n{Fore.RED}Test failed. Please review the output above.{Style.RESET_ALL}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
