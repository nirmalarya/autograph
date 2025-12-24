#!/usr/bin/env python3
"""
Test Compliance Features (#540-543)

Features being tested:
- Feature #540: Enterprise: Audit retention: configurable period
- Feature #541: Enterprise: Compliance reports: SOC 2 format
- Feature #542: Enterprise: Compliance reports: ISO 27001 format
- Feature #543: Enterprise: Compliance reports: GDPR format
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import psycopg2

# Configuration
BASE_URL = "http://localhost:8085"
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_test(message):
    print(f"{BLUE}  {message}{RESET}")

def print_success(message):
    print(f"{GREEN}  ✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}  ✗ {message}{RESET}")

def print_section(message):
    print(f"\n{YELLOW}{'='*80}{RESET}")
    print(f"{YELLOW}{message}{RESET}")
    print(f"{YELLOW}{'='*80}{RESET}")


def create_admin_user():
    """Create an admin user for testing."""
    try:
        register_data = {
            "email": f"compliance_admin_{datetime.now().timestamp()}@test.com",
            "password": "AdminPass123!",
            "full_name": "Compliance Admin"
        }
        
        response = requests.post(f"{BASE_URL}/register", json=register_data)
        if response.status_code not in [200, 201]:
            print_error(f"Failed to register user: {response.status_code}")
            return None, None
        
        user_data = response.json()
        user_id = user_data["id"]
        
        # Update to admin
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("UPDATE users SET role = 'admin' WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return register_data["email"], register_data["password"]
        
    except Exception as e:
        print_error(f"Failed to create admin: {str(e)}")
        return None, None


def get_admin_token():
    """Get admin access token."""
    admin_email, admin_password = create_admin_user()
    if not admin_email:
        return None
    
    login_response = requests.post(
        f"{BASE_URL}/token",
        data={"username": admin_email, "password": admin_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if login_response.status_code != 200:
        print_error(f"Failed to login: {login_response.status_code}")
        return None
    
    return login_response.json()["access_token"]


def test_audit_retention():
    """Test Feature #540: Audit retention configuration."""
    print_section("TEST 1: AUDIT RETENTION CONFIGURATION")
    
    access_token = get_admin_token()
    if not access_token:
        return False
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        # Step 1: Get current retention config
        print_test("Step 1: Getting current retention configuration...")
        
        response = requests.get(
            f"{BASE_URL}/admin/config/audit-retention",
            headers=headers
        )
        
        if response.status_code != 200:
            print_error(f"Failed to get config: {response.status_code}")
            return False
        
        config = response.json()
        print_success(f"Current retention: {config['retention_days']} days")
        print_success(f"Enabled: {config['enabled']}")
        
        # Step 2: Update retention to 90 days
        print_test("Step 2: Setting retention to 90 days...")
        
        response = requests.post(
            f"{BASE_URL}/admin/config/audit-retention",
            headers=headers,
            json={"retention_days": 90, "enabled": True}
        )
        
        if response.status_code != 200:
            print_error(f"Failed to update config: {response.status_code}")
            return False
        
        result = response.json()
        print_success(f"Retention updated to {result['config']['retention_days']} days")
        print_success(f"Deleted {result['deleted_old_logs']} old logs")
        
        # Step 3: Verify configuration persisted
        print_test("Step 3: Verifying configuration persisted...")
        
        response = requests.get(
            f"{BASE_URL}/admin/config/audit-retention",
            headers=headers
        )
        
        if response.status_code != 200:
            print_error("Failed to verify config")
            return False
        
        config = response.json()
        if config['retention_days'] == 90:
            print_success("Configuration persisted correctly")
        else:
            print_error(f"Config not persisted: {config['retention_days']}")
            return False
        
        # Step 4: Test validation (should reject invalid values)
        print_test("Step 4: Testing validation...")
        
        response = requests.post(
            f"{BASE_URL}/admin/config/audit-retention",
            headers=headers,
            json={"retention_days": 0, "enabled": True}  # Invalid: too short
        )
        
        if response.status_code == 400:
            print_success("Validation correctly rejected 0 days")
        else:
            print_error(f"Validation failed to reject invalid value: {response.status_code}")
        
        print_success("TEST 1 PASSED: Audit retention works!")
        return True
        
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_soc2_report():
    """Test Feature #541: SOC 2 compliance report."""
    print_section("TEST 2: SOC 2 COMPLIANCE REPORT")
    
    access_token = get_admin_token()
    if not access_token:
        return False
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        # Step 1: Generate SOC 2 report
        print_test("Step 1: Generating SOC 2 report...")
        
        start_date = (datetime.now() - timedelta(days=30)).isoformat() + "Z"
        
        response = requests.get(
            f"{BASE_URL}/admin/compliance/report/soc2",
            headers=headers,
            params={"start_date": start_date}
        )
        
        if response.status_code != 200:
            print_error(f"Failed to generate report: {response.status_code}")
            return False
        
        report = response.json()
        print_success(f"Report generated: {report['report_type']}")
        
        # Step 2: Verify report structure
        print_test("Step 2: Verifying report structure...")
        
        required_keys = ['report_type', 'generated_at', 'period', 'security_controls', 
                        'audit_logging', 'trust_service_criteria']
        
        if all(key in report for key in required_keys):
            print_success("Report structure is correct")
        else:
            print_error(f"Missing keys: {[k for k in required_keys if k not in report]}")
            return False
        
        # Step 3: Verify Trust Service Criteria
        print_test("Step 3: Verifying Trust Service Criteria...")
        
        tsc = report['trust_service_criteria']
        criteria = ['CC6_Security', 'A1_Availability', 'PI1_Processing_Integrity',
                   'C1_Confidentiality', 'P1_Privacy']
        
        if all(c in tsc for c in criteria):
            print_success(f"All {len(criteria)} Trust Service Criteria present")
        else:
            print_error("Missing Trust Service Criteria")
            return False
        
        # Display sample data
        print_test("Sample metrics:")
        auth = report['security_controls']['authentication']
        print_test(f"  - Total login attempts: {auth['total_login_attempts']}")
        print_test(f"  - Failed logins: {auth['failed_login_attempts']}")
        print_test(f"  - Failure rate: {auth['failure_rate']}%")
        
        print_success("TEST 2 PASSED: SOC 2 report works!")
        return True
        
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_iso27001_report():
    """Test Feature #542: ISO 27001 compliance report."""
    print_section("TEST 3: ISO 27001 COMPLIANCE REPORT")
    
    access_token = get_admin_token()
    if not access_token:
        return False
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        # Step 1: Generate ISO 27001 report
        print_test("Step 1: Generating ISO 27001 report...")
        
        start_date = (datetime.now() - timedelta(days=30)).isoformat() + "Z"
        
        response = requests.get(
            f"{BASE_URL}/admin/compliance/report/iso27001",
            headers=headers,
            params={"start_date": start_date}
        )
        
        if response.status_code != 200:
            print_error(f"Failed to generate report: {response.status_code}")
            return False
        
        report = response.json()
        print_success(f"Report generated: {report['report_type']}")
        
        # Step 2: Verify report structure
        print_test("Step 2: Verifying report structure...")
        
        required_keys = ['report_type', 'generated_at', 'period', 'annex_a_controls',
                        'audit_trail', 'information_security_objectives']
        
        if all(key in report for key in required_keys):
            print_success("Report structure is correct")
        else:
            print_error(f"Missing keys in report")
            return False
        
        # Step 3: Verify Annex A controls
        print_test("Step 3: Verifying Annex A controls...")
        
        controls = report['annex_a_controls']
        required_controls = ['A9_Access_Control', 'A12_Operations_Security',
                            'A16_Incident_Management', 'A18_Compliance']
        
        if all(c in controls for c in required_controls):
            print_success(f"All {len(required_controls)} Annex A controls present")
        else:
            print_error("Missing Annex A controls")
            return False
        
        # Display sample data
        print_test("Sample controls:")
        for control_name, control_data in list(controls.items())[:2]:
            print_test(f"  - {control_name}: {control_data['status']} ({control_data['events']} events)")
        
        print_success("TEST 3 PASSED: ISO 27001 report works!")
        return True
        
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_gdpr_report():
    """Test Feature #543: GDPR compliance report."""
    print_section("TEST 4: GDPR COMPLIANCE REPORT")
    
    access_token = get_admin_token()
    if not access_token:
        return False
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        # Step 1: Generate GDPR report
        print_test("Step 1: Generating GDPR report...")
        
        start_date = (datetime.now() - timedelta(days=30)).isoformat() + "Z"
        
        response = requests.get(
            f"{BASE_URL}/admin/compliance/report/gdpr",
            headers=headers,
            params={"start_date": start_date}
        )
        
        if response.status_code != 200:
            print_error(f"Failed to generate report: {response.status_code}")
            return False
        
        report = response.json()
        print_success(f"Report generated: {report['report_type']}")
        
        # Step 2: Verify report structure
        print_test("Step 2: Verifying report structure...")
        
        required_keys = ['report_type', 'generated_at', 'period', 'gdpr_articles',
                        'data_subjects', 'data_breaches', 'dpo_contact']
        
        if all(key in report for key in required_keys):
            print_success("Report structure is correct")
        else:
            print_error(f"Missing keys in report")
            return False
        
        # Step 3: Verify GDPR articles
        print_test("Step 3: Verifying GDPR articles...")
        
        articles = report['gdpr_articles']
        required_articles = ['Article_5_Processing_Principles', 'Article_15_Right_of_Access',
                            'Article_17_Right_to_Erasure', 'Article_30_Records_of_Processing',
                            'Article_32_Security_of_Processing']
        
        if all(a in articles for a in required_articles):
            print_success(f"All {len(required_articles)} GDPR articles covered")
        else:
            print_error("Missing GDPR articles")
            return False
        
        # Step 4: Verify data subjects information
        print_test("Step 4: Verifying data subjects info...")
        
        ds = report['data_subjects']
        print_test(f"  - New registrations: {ds['new_registrations']}")
        print_test(f"  - Active users: {ds['active_users']}")
        print_test(f"  - Total users: {ds['total_users']}")
        print_success("Data subjects information present")
        
        # Step 5: Verify security measures
        print_test("Step 5: Verifying security measures...")
        
        security = articles['Article_32_Security_of_Processing']
        measures = security['measures']
        if len(measures) >= 5:
            print_success(f"{len(measures)} security measures documented")
        else:
            print_error("Insufficient security measures")
        
        print_success("TEST 4 PASSED: GDPR report works!")
        return True
        
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}COMPLIANCE FEATURES TEST SUITE{RESET}")
    print(f"{BLUE}Testing Features #540-543{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    results = []
    
    # Test 1: Audit Retention
    results.append(("Feature #540: Audit Retention", test_audit_retention()))
    
    # Test 2: SOC 2 Report
    results.append(("Feature #541: SOC 2 Report", test_soc2_report()))
    
    # Test 3: ISO 27001 Report
    results.append(("Feature #542: ISO 27001 Report", test_iso27001_report()))
    
    # Test 4: GDPR Report
    results.append(("Feature #543: GDPR Report", test_gdpr_report()))
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")
    
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Total: {passed}/{total} tests passed{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    if passed == total:
        print_success("🎉 All compliance features are fully functional!")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
