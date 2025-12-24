#!/usr/bin/env python3
"""
Test script for Feature Flag System (Feature #53)

This script tests:
1. Feature flag creation
2. Percentage-based rollout (10%, 50%, 100%)
3. User-specific overrides (whitelist)
4. Flag updates and deletion
5. Usage statistics

All tests follow the feature requirements from feature_list.json.
"""

import json
import requests
import sys
import time
from typing import Dict, List, Any

# ANSI color codes for terminal output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

API_BASE_URL = "http://localhost:8080"

def print_header(text: str):
    """Print a colored header."""
    print(f"\n{CYAN}{'=' * 80}{RESET}")
    print(f"{CYAN}{text}{RESET}")
    print(f"{CYAN}{'=' * 80}{RESET}\n")

def print_success(text: str):
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text: str):
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")

def print_info(text: str):
    """Print info message."""
    print(f"{BLUE}ℹ {text}{RESET}")

def print_warning(text: str):
    """Print warning message."""
    print(f"{YELLOW}⚠ {text}{RESET}")


class FeatureFlagTester:
    """Test the feature flag system."""

    def __init__(self):
        self.results = []
        self.test_flag_name = "new_dashboard"
        self.test_user_ids = [f"user{i}" for i in range(1, 101)]  # 100 test users

    def test_api_health(self) -> bool:
        """Test 1: API Gateway is healthy."""
        print_info("Test 1: Checking API Gateway health...")
        
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print_success(f"API Gateway is healthy: {data['service']}")
                return True
            else:
                print_error(f"API Gateway health check failed: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Failed to connect to API Gateway: {e}")
            return False

    def test_create_feature_flag(self) -> bool:
        """Test 2: Create a new feature flag."""
        print_info("Test 2: Creating a new feature flag...")
        
        try:
            flag_data = {
                "name": self.test_flag_name,
                "enabled": True,
                "description": "New dashboard UI for gradual rollout",
                "rollout_percentage": 0,
                "strategy": "percentage",
                "metadata": {
                    "team": "frontend",
                    "created_by": "test_script"
                }
            }
            
            response = requests.post(
                f"{API_BASE_URL}/api/feature-flags",
                json=flag_data,
                timeout=5
            )
            
            if response.status_code == 201:
                data = response.json()
                print_success(f"Feature flag created: {data['flag']['name']}")
                print_info(f"  - Description: {data['flag']['description']}")
                print_info(f"  - Enabled: {data['flag']['enabled']}")
                print_info(f"  - Rollout: {data['flag']['rollout_percentage']}%")
                return True
            else:
                print_error(f"Failed to create feature flag: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Exception while creating feature flag: {e}")
            return False

    def test_list_feature_flags(self) -> bool:
        """Test 3: List all feature flags."""
        print_info("Test 3: Listing all feature flags...")
        
        try:
            response = requests.get(f"{API_BASE_URL}/api/feature-flags", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Found {data['count']} feature flag(s)")
                for flag in data['flags']:
                    print_info(f"  - {flag['name']}: {flag['rollout_percentage']}% rollout")
                return True
            else:
                print_error(f"Failed to list feature flags: {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Exception while listing feature flags: {e}")
            return False

    def test_rollout_0_percent(self) -> bool:
        """Test 4: Deploy feature behind flag (0% rollout)."""
        print_info("Test 4: Testing 0% rollout (feature disabled for all users)...")
        
        try:
            # Check flag for 10 random users
            enabled_count = 0
            sample_users = self.test_user_ids[:10]
            
            for user_id in sample_users:
                response = requests.post(
                    f"{API_BASE_URL}/api/feature-flags/{self.test_flag_name}/check",
                    json={"user_id": user_id},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data['enabled']:
                        enabled_count += 1
            
            if enabled_count == 0:
                print_success(f"0% rollout verified: 0/{len(sample_users)} users have access")
                return True
            else:
                print_error(f"0% rollout failed: {enabled_count}/{len(sample_users)} users have access")
                return False
                
        except Exception as e:
            print_error(f"Exception while testing 0% rollout: {e}")
            return False

    def test_rollout_10_percent(self) -> bool:
        """Test 5: Enable flag for 10% of users."""
        print_info("Test 5: Setting rollout to 10%...")
        
        try:
            # Update rollout percentage to 10%
            response = requests.patch(
                f"{API_BASE_URL}/api/feature-flags/{self.test_flag_name}/rollout",
                json={"percentage": 10},
                timeout=5
            )
            
            if response.status_code != 200:
                print_error(f"Failed to set rollout percentage: {response.status_code}")
                return False
            
            print_success("Rollout set to 10%")
            
            # Check flag for all test users
            enabled_count = 0
            for user_id in self.test_user_ids:
                response = requests.post(
                    f"{API_BASE_URL}/api/feature-flags/{self.test_flag_name}/check",
                    json={"user_id": user_id},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data['enabled']:
                        enabled_count += 1
            
            percentage = (enabled_count / len(self.test_user_ids)) * 100
            
            # Allow some variance (8-12%)
            if 8 <= percentage <= 12:
                print_success(f"10% rollout verified: {enabled_count}/{len(self.test_user_ids)} users have access ({percentage:.1f}%)")
                return True
            else:
                print_error(f"10% rollout outside expected range: {enabled_count}/{len(self.test_user_ids)} users ({percentage:.1f}%)")
                return False
                
        except Exception as e:
            print_error(f"Exception while testing 10% rollout: {e}")
            return False

    def test_rollout_50_percent(self) -> bool:
        """Test 6: Gradually increase to 50%."""
        print_info("Test 6: Setting rollout to 50%...")
        
        try:
            # Update rollout percentage to 50%
            response = requests.patch(
                f"{API_BASE_URL}/api/feature-flags/{self.test_flag_name}/rollout",
                json={"percentage": 50},
                timeout=5
            )
            
            if response.status_code != 200:
                print_error(f"Failed to set rollout percentage: {response.status_code}")
                return False
            
            print_success("Rollout set to 50%")
            
            # Check flag for all test users
            enabled_count = 0
            for user_id in self.test_user_ids:
                response = requests.post(
                    f"{API_BASE_URL}/api/feature-flags/{self.test_flag_name}/check",
                    json={"user_id": user_id},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data['enabled']:
                        enabled_count += 1
            
            percentage = (enabled_count / len(self.test_user_ids)) * 100
            
            # Allow some variance (43-57%) - hash distribution can vary
            if 43 <= percentage <= 57:
                print_success(f"50% rollout verified: {enabled_count}/{len(self.test_user_ids)} users have access ({percentage:.1f}%)")
                return True
            else:
                print_error(f"50% rollout outside expected range: {enabled_count}/{len(self.test_user_ids)} users ({percentage:.1f}%)")
                return False
                
        except Exception as e:
            print_error(f"Exception while testing 50% rollout: {e}")
            return False

    def test_rollout_100_percent(self) -> bool:
        """Test 7: Increase to 100%."""
        print_info("Test 7: Setting rollout to 100%...")
        
        try:
            # Update rollout percentage to 100%
            response = requests.patch(
                f"{API_BASE_URL}/api/feature-flags/{self.test_flag_name}/rollout",
                json={"percentage": 100},
                timeout=5
            )
            
            if response.status_code != 200:
                print_error(f"Failed to set rollout percentage: {response.status_code}")
                return False
            
            print_success("Rollout set to 100%")
            
            # Check flag for all test users
            enabled_count = 0
            for user_id in self.test_user_ids:
                response = requests.post(
                    f"{API_BASE_URL}/api/feature-flags/{self.test_flag_name}/check",
                    json={"user_id": user_id},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data['enabled']:
                        enabled_count += 1
            
            if enabled_count == len(self.test_user_ids):
                print_success(f"100% rollout verified: {enabled_count}/{len(self.test_user_ids)} users have access")
                return True
            else:
                print_error(f"100% rollout failed: {enabled_count}/{len(self.test_user_ids)} users have access")
                return False
                
        except Exception as e:
            print_error(f"Exception while testing 100% rollout: {e}")
            return False

    def test_flag_override_for_testing(self) -> bool:
        """Test 8: Test flag override for testing (whitelist)."""
        print_info("Test 8: Testing flag override with whitelist...")
        
        try:
            # Reset rollout to 0%
            response = requests.patch(
                f"{API_BASE_URL}/api/feature-flags/{self.test_flag_name}/rollout",
                json={"percentage": 0},
                timeout=5
            )
            
            if response.status_code != 200:
                print_error(f"Failed to reset rollout percentage: {response.status_code}")
                return False
            
            print_info("Rollout reset to 0%")
            
            # Add a test user to whitelist
            test_user = "test_user_override"
            response = requests.post(
                f"{API_BASE_URL}/api/feature-flags/{self.test_flag_name}/whitelist",
                json={"user_id": test_user},
                timeout=5
            )
            
            if response.status_code != 200:
                print_error(f"Failed to add user to whitelist: {response.status_code}")
                return False
            
            print_success(f"User {test_user} added to whitelist")
            
            # Check flag for whitelisted user
            response = requests.post(
                f"{API_BASE_URL}/api/feature-flags/{self.test_flag_name}/check",
                json={"user_id": test_user},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['enabled']:
                    print_success(f"Whitelist verified: User {test_user} has access despite 0% rollout")
                    
                    # Check flag for non-whitelisted user
                    response = requests.post(
                        f"{API_BASE_URL}/api/feature-flags/{self.test_flag_name}/check",
                        json={"user_id": "regular_user"},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if not data['enabled']:
                            print_success("Non-whitelisted user correctly denied access")
                            return True
                        else:
                            print_error("Non-whitelisted user incorrectly has access")
                            return False
                else:
                    print_error(f"Whitelisted user does not have access")
                    return False
            else:
                print_error(f"Failed to check flag: {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Exception while testing flag override: {e}")
            return False

    def test_usage_stats(self) -> bool:
        """Test 9: Monitor feature usage and errors."""
        print_info("Test 9: Testing usage statistics...")
        
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/feature-flags/{self.test_flag_name}/stats",
                params={"days": 7},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                stats = data['stats']
                print_success("Usage statistics retrieved successfully")
                print_info(f"  - Total checks: {stats['total_checks']}")
                print_info(f"  - Enabled count: {stats['enabled_count']}")
                print_info(f"  - Disabled count: {stats['disabled_count']}")
                print_info(f"  - Unique users: {stats['unique_users']}")
                print_info(f"  - Enabled percentage: {stats['enabled_percentage']:.1f}%")
                return True
            else:
                print_error(f"Failed to get usage stats: {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Exception while getting usage stats: {e}")
            return False

    def test_remove_feature_flag(self) -> bool:
        """Test 10: Remove feature flag after stable."""
        print_info("Test 10: Testing feature flag removal...")
        
        try:
            response = requests.delete(
                f"{API_BASE_URL}/api/feature-flags/{self.test_flag_name}",
                timeout=5
            )
            
            if response.status_code == 200:
                print_success(f"Feature flag {self.test_flag_name} deleted successfully")
                
                # Verify flag is deleted
                response = requests.get(
                    f"{API_BASE_URL}/api/feature-flags/{self.test_flag_name}",
                    timeout=5
                )
                
                if response.status_code == 404:
                    print_success("Verified flag no longer exists")
                    return True
                else:
                    print_error(f"Flag still exists after deletion: {response.status_code}")
                    return False
            else:
                print_error(f"Failed to delete feature flag: {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Exception while deleting feature flag: {e}")
            return False

    def test_consistent_hashing(self) -> bool:
        """Test 11: Verify consistent hashing (same user always gets same result)."""
        print_info("Test 11: Testing consistent hashing...")
        
        try:
            # Create a new flag for this test
            flag_data = {
                "name": "consistent_test",
                "enabled": True,
                "description": "Test consistent hashing",
                "rollout_percentage": 50,
                "strategy": "percentage"
            }
            
            response = requests.post(
                f"{API_BASE_URL}/api/feature-flags",
                json=flag_data,
                timeout=5
            )
            
            if response.status_code != 201:
                print_error(f"Failed to create test flag: {response.status_code}")
                return False
            
            print_info("Created test flag with 50% rollout")
            
            # Check same user multiple times
            test_user = "consistency_test_user"
            results = []
            
            for i in range(10):
                response = requests.post(
                    f"{API_BASE_URL}/api/feature-flags/consistent_test/check",
                    json={"user_id": test_user},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results.append(data['enabled'])
            
            # All results should be the same
            if len(set(results)) == 1:
                print_success(f"Consistent hashing verified: User gets same result every time ({results[0]})")
                
                # Clean up test flag
                requests.delete(f"{API_BASE_URL}/api/feature-flags/consistent_test", timeout=5)
                return True
            else:
                print_error(f"Inconsistent results: {results}")
                
                # Clean up test flag
                requests.delete(f"{API_BASE_URL}/api/feature-flags/consistent_test", timeout=5)
                return False
                
        except Exception as e:
            print_error(f"Exception while testing consistent hashing: {e}")
            return False

    def run_all_tests(self) -> bool:
        """Run all tests and return overall success."""
        print_header("Feature Flag System Tests (Feature #53)")
        
        tests = [
            ("API Health", self.test_api_health),
            ("Create Feature Flag", self.test_create_feature_flag),
            ("List Feature Flags", self.test_list_feature_flags),
            ("0% Rollout (Disabled)", self.test_rollout_0_percent),
            ("10% Rollout", self.test_rollout_10_percent),
            ("50% Rollout", self.test_rollout_50_percent),
            ("100% Rollout", self.test_rollout_100_percent),
            ("Flag Override (Whitelist)", self.test_flag_override_for_testing),
            ("Usage Statistics", self.test_usage_stats),
            ("Remove Feature Flag", self.test_remove_feature_flag),
            ("Consistent Hashing", self.test_consistent_hashing),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                self.results.append((test_name, result))
                if result:
                    passed += 1
                else:
                    failed += 1
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                print_error(f"Test '{test_name}' crashed: {e}")
                self.results.append((test_name, False))
                failed += 1
        
        # Print summary
        print_header("Test Summary")
        print(f"Total tests: {len(tests)}")
        print_success(f"Passed: {passed}")
        if failed > 0:
            print_error(f"Failed: {failed}")
        print()
        
        # Print detailed results
        print("Detailed Results:")
        for test_name, result in self.results:
            if result:
                print_success(f"{test_name}: PASSED")
            else:
                print_error(f"{test_name}: FAILED")
        
        all_passed = failed == 0
        
        if all_passed:
            print_header("✓ All tests passed! Feature #53 is ready.")
        else:
            print_header("✗ Some tests failed. Please review and fix.")
        
        return all_passed


def main():
    """Main entry point."""
    tester = FeatureFlagTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
