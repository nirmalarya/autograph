#!/usr/bin/env python3
"""
Test MinIO Bucket Backup and Restore System

Tests all aspects of Feature #49: MinIO bucket backup and restore
"""

import requests
import time
import sys
from datetime import datetime
import json

# Test configuration
API_BASE = "http://localhost:8080"
TEST_BUCKET = "diagrams"  # Use existing bucket for testing

# ANSI color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_section(title):
    """Print a section header"""
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}{title}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")

def print_test(test_name):
    """Print test name"""
    print(f"{BOLD}Testing: {test_name}{RESET}")

def print_success(message):
    """Print success message"""
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    """Print error message"""
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    """Print info message"""
    print(f"{YELLOW}ℹ {message}{RESET}")

def print_result(response):
    """Print API response result"""
    print(f"  Status: {response.status_code}")
    try:
        data = response.json()
        print(f"  Response: {json.dumps(data, indent=2)[:500]}")
    except:
        print(f"  Response: {response.text[:200]}")

class TestResults:
    """Track test results"""
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
    
    def add(self, name, passed, error=None):
        self.tests.append({
            'name': name,
            'passed': passed,
            'error': error
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        """Print test summary"""
        print_section("TEST SUMMARY")
        print(f"\nTotal tests: {len(self.tests)}")
        print(f"{GREEN}Passed: {self.passed}{RESET}")
        print(f"{RED}Failed: {self.failed}{RESET}")
        
        if self.failed > 0:
            print(f"\n{BOLD}Failed tests:{RESET}")
            for test in self.tests:
                if not test['passed']:
                    print(f"{RED}  ✗ {test['name']}: {test['error']}{RESET}")
        
        print(f"\n{BOLD}Overall: ", end='')
        if self.failed == 0:
            print(f"{GREEN}ALL TESTS PASSED ✓{RESET}")
            return True
        else:
            print(f"{RED}SOME TESTS FAILED ✗{RESET}")
            return False

results = TestResults()

def test_api_health():
    """Test 1: Verify API Gateway is healthy"""
    print_test("API Gateway Health Check")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        print_result(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                print_success("API Gateway is healthy")
                results.add("API Gateway Health", True)
                return True
        
        print_error("API Gateway not healthy")
        results.add("API Gateway Health", False, "Unhealthy response")
        return False
        
    except Exception as e:
        print_error(f"Failed to connect to API Gateway: {e}")
        results.add("API Gateway Health", False, str(e))
        return False

def test_list_buckets():
    """Test 2: List all MinIO buckets"""
    print_test("List MinIO Buckets")
    
    try:
        response = requests.get(f"{API_BASE}/api/admin/minio/buckets", timeout=10)
        print_result(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'buckets' in data:
                bucket_count = len(data['buckets'])
                print_success(f"Listed {bucket_count} buckets")
                print_info(f"Buckets: {', '.join(data['buckets'])}")
                results.add("List MinIO Buckets", True)
                return data['buckets']
        
        print_error("Failed to list buckets")
        results.add("List MinIO Buckets", False, f"Status {response.status_code}")
        return []
        
    except Exception as e:
        print_error(f"Failed to list buckets: {e}")
        results.add("List MinIO Buckets", False, str(e))
        return []

def test_list_backups():
    """Test 3: List existing bucket backups"""
    print_test("List MinIO Bucket Backups")
    
    try:
        response = requests.get(f"{API_BASE}/api/admin/minio/backup/list", timeout=10)
        print_result(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                backup_count = data.get('count', 0)
                print_success(f"Listed {backup_count} backups")
                if backup_count > 0:
                    print_info("Existing backups:")
                    for backup in data.get('backups', []):
                        print(f"  - {backup.get('backup_name')} ({backup.get('size_mb')} MB)")
                results.add("List Bucket Backups", True)
                return data.get('backups', [])
        
        print_error("Failed to list backups")
        results.add("List Bucket Backups", False, f"Status {response.status_code}")
        return []
        
    except Exception as e:
        print_error(f"Failed to list backups: {e}")
        results.add("List Bucket Backups", False, str(e))
        return []

def test_create_backup(bucket_name):
    """Test 4: Create a backup of a MinIO bucket"""
    print_test(f"Create Backup of '{bucket_name}' Bucket")
    
    backup_name = f"test-backup-{int(time.time())}"  # Use hyphen instead of underscore
    print_info(f"Backup name: {backup_name}")
    
    try:
        params = {
            'bucket_name': bucket_name,
            'backup_name': backup_name,
            'include_versions': False
        }
        
        print_info("Creating backup... (this may take a while)")
        response = requests.post(
            f"{API_BASE}/api/admin/minio/backup/create",
            params=params,
            timeout=300  # 5 minute timeout
        )
        print_result(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                backup = data.get('backup', {})
                print_success(f"Backup created: {backup.get('backup_name')}")
                print_info(f"  Objects: {backup.get('object_count', 0)}")
                print_info(f"  Size: {backup.get('archive_size_mb', 0)} MB")
                print_info(f"  Archive: {backup.get('archive_path', 'N/A')}")
                results.add("Create Bucket Backup", True)
                return backup_name
        
        print_error("Failed to create backup")
        results.add("Create Bucket Backup", False, f"Status {response.status_code}")
        return None
        
    except Exception as e:
        print_error(f"Failed to create backup: {e}")
        results.add("Create Bucket Backup", False, str(e))
        return None

def test_verify_backup_exists(backup_name):
    """Test 5: Verify backup appears in list"""
    print_test(f"Verify Backup '{backup_name}' Exists")
    
    try:
        response = requests.get(f"{API_BASE}/api/admin/minio/backup/list", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            backups = data.get('backups', [])
            
            # Check if our backup exists
            backup_found = any(b.get('backup_name') == backup_name for b in backups)
            
            if backup_found:
                print_success(f"Backup '{backup_name}' found in list")
                results.add("Verify Backup Exists", True)
                return True
            else:
                print_error(f"Backup '{backup_name}' not found in list")
                results.add("Verify Backup Exists", False, "Backup not in list")
                return False
        
        print_error("Failed to list backups")
        results.add("Verify Backup Exists", False, f"Status {response.status_code}")
        return False
        
    except Exception as e:
        print_error(f"Failed to verify backup: {e}")
        results.add("Verify Backup Exists", False, str(e))
        return False

def test_restore_backup(backup_name, target_bucket=None):
    """Test 6: Restore a backup"""
    print_test(f"Restore Backup '{backup_name}'")
    
    if not target_bucket:
        target_bucket = f"test-restore-{int(time.time())}"  # Use hyphen instead of underscore
    
    print_info(f"Target bucket: {target_bucket}")
    
    try:
        params = {
            'backup_name': backup_name,
            'target_bucket': target_bucket,
            'overwrite': True
        }
        
        print_info("Restoring backup... (this may take a while)")
        response = requests.post(
            f"{API_BASE}/api/admin/minio/backup/restore",
            params=params,
            timeout=300  # 5 minute timeout
        )
        print_result(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                restore = data.get('restore', {})
                print_success(f"Backup restored to '{restore.get('target_bucket')}'")
                print_info(f"  Uploaded: {restore.get('uploaded_count', 0)} objects")
                print_info(f"  Size: {restore.get('total_size_mb', 0)} MB")
                results.add("Restore Bucket Backup", True)
                return target_bucket
        
        print_error("Failed to restore backup")
        results.add("Restore Bucket Backup", False, f"Status {response.status_code}")
        return None
        
    except Exception as e:
        print_error(f"Failed to restore backup: {e}")
        results.add("Restore Bucket Backup", False, str(e))
        return None

def test_delete_backup(backup_name):
    """Test 7: Delete a backup"""
    print_test(f"Delete Backup '{backup_name}'")
    
    try:
        params = {
            'delete_local': True
        }
        
        response = requests.delete(
            f"{API_BASE}/api/admin/minio/backup/{backup_name}",
            params=params,
            timeout=30
        )
        print_result(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                results_data = data.get('results', {})
                print_success(f"Backup deleted")
                print_info(f"  MinIO: {'✓' if results_data.get('minio_deleted') else '✗'}")
                print_info(f"  Local: {'✓' if results_data.get('local_deleted') else '✗'}")
                results.add("Delete Bucket Backup", True)
                return True
        
        print_error("Failed to delete backup")
        results.add("Delete Bucket Backup", False, f"Status {response.status_code}")
        return False
        
    except Exception as e:
        print_error(f"Failed to delete backup: {e}")
        results.add("Delete Bucket Backup", False, str(e))
        return False

def test_verify_backup_deleted(backup_name):
    """Test 8: Verify backup was deleted"""
    print_test(f"Verify Backup '{backup_name}' Deleted")
    
    try:
        response = requests.get(f"{API_BASE}/api/admin/minio/backup/list", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            backups = data.get('backups', [])
            
            # Check if our backup still exists
            backup_found = any(b.get('backup_name') == backup_name for b in backups)
            
            if not backup_found:
                print_success(f"Backup '{backup_name}' successfully deleted")
                results.add("Verify Backup Deleted", True)
                return True
            else:
                print_error(f"Backup '{backup_name}' still exists")
                results.add("Verify Backup Deleted", False, "Backup still in list")
                return False
        
        print_error("Failed to list backups")
        results.add("Verify Backup Deleted", False, f"Status {response.status_code}")
        return False
        
    except Exception as e:
        print_error(f"Failed to verify deletion: {e}")
        results.add("Verify Backup Deleted", False, str(e))
        return False

def main():
    """Run all tests"""
    print_section("MinIO BUCKET BACKUP AND RESTORE TEST SUITE")
    print(f"Testing Feature #49: Backup and restore for MinIO buckets")
    print(f"API Base URL: {API_BASE}")
    print(f"Test Bucket: {TEST_BUCKET}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: API Health Check
    print_section("TEST 1: API HEALTH CHECK")
    if not test_api_health():
        print_error("API Gateway is not healthy. Aborting tests.")
        sys.exit(1)
    
    # Test 2: List MinIO Buckets
    print_section("TEST 2: LIST MINIO BUCKETS")
    buckets = test_list_buckets()
    
    if TEST_BUCKET not in buckets:
        print_error(f"Test bucket '{TEST_BUCKET}' not found. Available buckets: {buckets}")
        print_info("You may need to create the test bucket or update TEST_BUCKET variable")
        # Continue anyway - backup will fail gracefully
    
    # Test 3: List Existing Backups
    print_section("TEST 3: LIST EXISTING BACKUPS")
    existing_backups = test_list_backups()
    
    # Test 4: Create Backup
    print_section("TEST 4: CREATE BUCKET BACKUP")
    backup_name = test_create_backup(TEST_BUCKET)
    
    if not backup_name:
        print_error("Failed to create backup. Skipping remaining tests.")
        results.print_summary()
        sys.exit(1)
    
    # Wait a moment for backup to be fully written
    time.sleep(2)
    
    # Test 5: Verify Backup Exists
    print_section("TEST 5: VERIFY BACKUP EXISTS")
    test_verify_backup_exists(backup_name)
    
    # Test 6: Restore Backup
    print_section("TEST 6: RESTORE BUCKET BACKUP")
    restored_bucket = test_restore_backup(backup_name)
    
    # Test 7: Delete Backup
    print_section("TEST 7: DELETE BUCKET BACKUP")
    test_delete_backup(backup_name)
    
    # Test 8: Verify Backup Deleted
    print_section("TEST 8: VERIFY BACKUP DELETED")
    test_verify_backup_deleted(backup_name)
    
    # Print summary
    success = results.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
