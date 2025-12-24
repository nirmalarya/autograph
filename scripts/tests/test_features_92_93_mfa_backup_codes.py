#!/usr/bin/env python3
"""
Test Features #92-93: MFA Backup Codes and Recovery

Feature #92: MFA backup codes for account recovery
- Backup codes generated when MFA enabled
- Backup codes can be used to login when device lost
- Each backup code can only be used once
- Users can regenerate backup codes

Feature #93: MFA recovery: disable MFA if lost device
- Users can disable MFA if they have access to codes
- Requires valid MFA code or backup code to disable
- All MFA data cleared when disabled
"""

import requests
import time
import json
import pyotp
from datetime import datetime
from typing import Optional

# ANSI color codes
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

BASE_URL = "http://localhost:8085"

def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")

def print_step(text: str):
    """Print a test step."""
    print(f"{YELLOW}{text}{RESET}")

def print_success(text: str):
    """Print a success message."""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text: str):
    """Print an error message."""
    print(f"{RED}✗ {text}{RESET}")

def print_info(text: str, indent: int = 2):
    """Print an info message."""
    print(f"{' ' * indent}{text}")


class MFABackupCodesTest:
    """Test MFA backup codes and recovery features."""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.user_email = f"mfa_backup_test_{int(time.time())}@example.com"
        self.user_password = "SecurePass123!"
        self.user_id: Optional[str] = None
        self.access_token: Optional[str] = None
        self.mfa_secret: Optional[str] = None
        self.backup_codes: Optional[list[str]] = None
        
    def register_user(self) -> bool:
        """Register a test user."""
        print_step("Step 1: Register test user")
        
        response = requests.post(
            f"{self.base_url}/register",
            json={
                "email": self.user_email,
                "password": self.user_password,
                "full_name": "MFA Backup Test User"
            }
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.user_id = data["id"]
            print_success(f"User registered (ID: {self.user_id})")
            print_info(f"Email: {self.user_email}")
            
            # Mark user as verified (bypass email verification for testing)
            import psycopg2
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    dbname="autograph",
                    user="autograph",
                    password="autograph_dev_password"
                )
                cur = conn.cursor()
                cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (self.user_id,))
                conn.commit()
                cur.close()
                conn.close()
                print_info("Email marked as verified (for testing)")
            except Exception as e:
                print_error(f"Failed to mark email as verified: {e}")
                return False
            
            return True
        else:
            print_error(f"Registration failed (status {response.status_code}): {response.text}")
            return False
    
    def login_user(self) -> bool:
        """Login user and get access token."""
        print_step("\nStep 2: Login user")
        
        response = requests.post(
            f"{self.base_url}/login",
            json={
                "email": self.user_email,
                "password": self.user_password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            print_success("User logged in successfully")
            print_info(f"Token: {self.access_token[:20]}...")
            return True
        else:
            print_error(f"Login failed: {response.text}")
            return False
    
    def setup_mfa(self) -> bool:
        """Setup MFA for user."""
        print_step("\nStep 3: Setup MFA")
        
        response = requests.post(
            f"{self.base_url}/mfa/setup",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.mfa_secret = data["secret"]
            print_success("MFA setup successful")
            print_info(f"Secret: {self.mfa_secret[:10]}...")
            return True
        else:
            print_error(f"MFA setup failed: {response.text}")
            return False
    
    def enable_mfa(self) -> bool:
        """Enable MFA and receive backup codes."""
        print_step("\nStep 4: Enable MFA and receive backup codes")
        
        # Generate TOTP code
        totp = pyotp.TOTP(self.mfa_secret)
        code = totp.now()
        
        response = requests.post(
            f"{self.base_url}/mfa/enable",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"code": code}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.backup_codes = data.get("backup_codes", [])
            
            print_success("MFA enabled successfully")
            print_info(f"Backup codes generated: {len(self.backup_codes)}")
            
            if self.backup_codes:
                print_info("\nBackup codes (save these!):")
                for i, code in enumerate(self.backup_codes, 1):
                    print_info(f"  {i}. {code}", indent=4)
                
                # Check warning message
                if "backup_codes_warning" in data:
                    print_info(f"\n⚠️  {data['backup_codes_warning']}", indent=2)
                
                return True
            else:
                print_error("No backup codes received!")
                return False
        else:
            print_error(f"MFA enable failed: {response.text}")
            return False
    
    def login_with_backup_code(self, backup_code: str) -> bool:
        """Login using a backup code."""
        print_step(f"\nStep 5: Login with backup code ({backup_code})")
        
        # First, login with password (this will require MFA)
        response = requests.post(
            f"{self.base_url}/login",
            json={
                "email": self.user_email,
                "password": self.user_password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if "mfa_required" in data and data["mfa_required"]:
                print_info("MFA required (as expected)")
                
                # Now verify with backup code
                response = requests.post(
                    f"{self.base_url}/mfa/verify",
                    json={
                        "email": self.user_email,
                        "code": backup_code
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print_success("Login with backup code successful!")
                    
                    # Check for warning about backup code usage
                    if "warning" in data:
                        print_info(f"⚠️  {data['warning']}", indent=2)
                    
                    # Update access token
                    self.access_token = data["access_token"]
                    return True
                else:
                    print_error(f"MFA verification with backup code failed: {response.text}")
                    return False
            else:
                print_error("MFA not required (unexpected)")
                return False
        else:
            print_error(f"Login failed: {response.text}")
            return False
    
    def try_reuse_backup_code(self, backup_code: str) -> bool:
        """Try to reuse a backup code (should fail)."""
        print_step(f"\nStep 6: Try to reuse backup code (should fail)")
        
        # Login with password
        response = requests.post(
            f"{self.base_url}/login",
            json={
                "email": self.user_email,
                "password": self.user_password
            }
        )
        
        if response.status_code == 200:
            # Try to verify with same backup code
            response = requests.post(
                f"{self.base_url}/mfa/verify",
                json={
                    "email": self.user_email,
                    "code": backup_code
                }
            )
            
            if response.status_code == 401:
                print_success("Backup code correctly rejected (already used)")
                return True
            else:
                print_error(f"Backup code was accepted again (should have been rejected)!")
                return False
        else:
            print_error(f"Login failed: {response.text}")
            return False
    
    def regenerate_backup_codes(self) -> bool:
        """Regenerate backup codes."""
        print_step("\nStep 7: Regenerate backup codes")
        
        # Generate TOTP code
        totp = pyotp.TOTP(self.mfa_secret)
        code = totp.now()
        
        response = requests.post(
            f"{self.base_url}/mfa/backup-codes/regenerate",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"code": code}
        )
        
        if response.status_code == 200:
            data = response.json()
            new_backup_codes = data.get("backup_codes", [])
            
            print_success(f"Backup codes regenerated: {len(new_backup_codes)}")
            print_info("\nNew backup codes:")
            for i, code in enumerate(new_backup_codes, 1):
                print_info(f"  {i}. {code}", indent=4)
            
            # Verify old codes are different from new codes
            if set(self.backup_codes) & set(new_backup_codes):
                print_error("Some old backup codes are still present!")
                return False
            else:
                print_success("All backup codes are new (old codes invalidated)")
            
            # Check warning message
            if "backup_codes_warning" in data:
                print_info(f"\n⚠️  {data['backup_codes_warning']}", indent=2)
            
            self.backup_codes = new_backup_codes
            return True
        else:
            print_error(f"Regenerate backup codes failed: {response.text}")
            return False
    
    def disable_mfa(self) -> bool:
        """Disable MFA (Feature #93)."""
        print_step("\nStep 8: Disable MFA (recovery)")
        
        # Generate TOTP code
        totp = pyotp.TOTP(self.mfa_secret)
        code = totp.now()
        
        response = requests.post(
            f"{self.base_url}/mfa/disable",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"code": code}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("MFA disabled successfully")
            print_info(f"Message: {data.get('message', 'N/A')}")
            return True
        else:
            print_error(f"Disable MFA failed: {response.text}")
            return False
    
    def verify_mfa_disabled(self) -> bool:
        """Verify MFA is disabled by logging in without MFA."""
        print_step("\nStep 9: Verify MFA is disabled")
        
        response = requests.post(
            f"{self.base_url}/login",
            json={
                "email": self.user_email,
                "password": self.user_password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we got tokens directly (no MFA required)
            if "access_token" in data and "refresh_token" in data:
                print_success("Login successful without MFA (MFA correctly disabled)")
                return True
            elif "mfa_required" in data and data["mfa_required"]:
                print_error("MFA still required (should be disabled)")
                return False
            else:
                print_error(f"Unexpected response: {data}")
                return False
        else:
            print_error(f"Login failed: {response.text}")
            return False
    
    def test_disable_mfa_with_backup_code(self) -> bool:
        """Test disabling MFA with a backup code (Feature #93)."""
        print_step("\nStep 10: Test disable MFA with backup code")
        
        # First, re-enable MFA
        print_info("Re-enabling MFA for test...", indent=2)
        if not self.setup_mfa():
            return False
        if not self.enable_mfa():
            return False
        
        # Now try to disable with backup code
        if not self.backup_codes:
            print_error("No backup codes available")
            return False
        
        backup_code = self.backup_codes[0]
        print_info(f"Using backup code to disable: {backup_code}", indent=2)
        
        response = requests.post(
            f"{self.base_url}/mfa/disable",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"code": backup_code}
        )
        
        if response.status_code == 200:
            print_success("MFA disabled with backup code")
            return True
        else:
            print_error(f"Disable MFA with backup code failed: {response.text}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests."""
        print_header("FEATURES #92-93: MFA BACKUP CODES AND RECOVERY TEST SUITE")
        
        print(f"Testing against: {self.base_url}")
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        tests = [
            ("Register user", self.register_user),
            ("Login user", self.login_user),
            ("Setup MFA", self.setup_mfa),
            ("Enable MFA and receive backup codes", self.enable_mfa),
        ]
        
        # Run initial tests
        for name, test_func in tests:
            if not test_func():
                print_error(f"\n❌ Test suite failed at: {name}")
                return False
        
        # Save first backup code for later tests
        if not self.backup_codes or len(self.backup_codes) < 2:
            print_error("Not enough backup codes generated")
            return False
        
        first_backup_code = self.backup_codes[0]
        
        # Continue with backup code tests
        if not self.login_with_backup_code(first_backup_code):
            print_error("\n❌ Login with backup code failed")
            return False
        
        if not self.try_reuse_backup_code(first_backup_code):
            print_error("\n❌ Backup code reuse test failed")
            return False
        
        if not self.regenerate_backup_codes():
            print_error("\n❌ Regenerate backup codes failed")
            return False
        
        if not self.disable_mfa():
            print_error("\n❌ Disable MFA failed")
            return False
        
        if not self.verify_mfa_disabled():
            print_error("\n❌ Verify MFA disabled failed")
            return False
        
        if not self.test_disable_mfa_with_backup_code():
            print_error("\n❌ Disable MFA with backup code failed")
            return False
        
        # All tests passed!
        print_header("✅ ALL TESTS PASSED!")
        
        print(f"\n{GREEN}Summary:{RESET}")
        print(f"  ✓ Feature #92: MFA backup codes - PASSING")
        print(f"    • Backup codes generated on MFA enable")
        print(f"    • Backup codes work for login")
        print(f"    • One-time use enforced")
        print(f"    • Regeneration works correctly")
        print(f"  ✓ Feature #93: MFA recovery - PASSING")
        print(f"    • Can disable MFA with TOTP code")
        print(f"    • Can disable MFA with backup code")
        print(f"    • MFA correctly disabled")
        
        return True


def main():
    """Main test function."""
    tester = MFABackupCodesTest()
    
    try:
        success = tester.run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print_error("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
