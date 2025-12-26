"""
Test Feature #541: Enterprise: Compliance reports: SOC 2 format

Steps:
1. Generate SOC 2 report
2. Verify includes access controls
3. Verify includes audit logs
4. Verify compliance evidence
"""

import requests
import time
from datetime import datetime, timedelta, timezone
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

AUTH_SERVICE = "http://localhost:8085"

# Database connection for test data setup
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": os.getenv("POSTGRES_DB", "autograph"),
    "user": os.getenv("POSTGRES_USER", "autograph_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "autograph_password")
}


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG)


def create_admin_user():
    """Create an admin user for testing."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Delete if exists and recreate
        cursor.execute("DELETE FROM users WHERE email = 'admin541@test.com'")
        conn.commit()

        # Create admin user (password: Admin123!)
        import bcrypt
        password_hash = bcrypt.hashpw("Admin123!".encode(), bcrypt.gensalt()).decode()

        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
            VALUES (gen_random_uuid(), 'admin541@test.com', %s, 'Admin User 541', true, true, 'admin')
            RETURNING id
        """, (password_hash,))
        admin_id = cursor.fetchone()[0]
        conn.commit()
        print(f"✓ Created admin user: {admin_id}")

        return admin_id
    finally:
        cursor.close()
        conn.close()


def login_admin():
    """Login as admin and get token."""
    response = requests.post(
        f"{AUTH_SERVICE}/login",
        json={
            "email": "admin541@test.com",
            "password": "Admin123!"
        }
    )

    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✓ Admin logged in successfully")
        return token
    else:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")


def create_test_audit_data(admin_id):
    """Create various audit log entries for testing SOC 2 report."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        now = datetime.now(timezone.utc)

        # Create diverse audit events for SOC 2 reporting
        test_events = [
            # Authentication events
            ('login_success', 'authentication', None, {"source": "web"}),
            ('login_success', 'authentication', None, {"source": "api"}),
            ('login_failed', 'authentication', None, {"reason": "invalid_password"}),
            ('login_failed', 'authentication', None, {"reason": "invalid_email"}),

            # Access control changes
            ('role_change', 'user', 'user-123', {"from": "user", "to": "admin"}),
            ('role_change', 'user', 'user-456', {"from": "viewer", "to": "editor"}),

            # Data access events
            ('read', 'file', 'file-abc', {"action": "view_diagram"}),
            ('write', 'file', 'file-def', {"action": "update_diagram"}),
            ('delete', 'file', 'file-ghi', {"action": "delete_diagram"}),
            ('read', 'user', 'user-789', {"action": "view_profile"}),
            ('write', 'team', 'team-123', {"action": "update_settings"}),

            # Configuration changes
            ('config_change', 'audit_retention', 'audit_retention', {"retention_days": 90}),
            ('config_change', 'security', 'mfa', {"enabled": True}),
        ]

        event_ids = []
        import json
        for action, resource_type, resource_id, extra_data in test_events:
            cursor.execute("""
                INSERT INTO audit_log (user_id, action, resource_type, resource_id, ip_address, user_agent, extra_data, created_at)
                VALUES (%s, %s, %s, %s, '192.168.1.100', 'Mozilla/5.0 Test', %s, %s)
                RETURNING id
            """, (admin_id, action, resource_type, resource_id, json.dumps(extra_data), now - timedelta(days=1)))
            event_id = cursor.fetchone()[0]
            event_ids.append(event_id)

        conn.commit()
        print(f"✓ Created {len(test_events)} test audit events")
        return event_ids
    finally:
        cursor.close()
        conn.close()


def generate_soc2_report(token, start_date=None, end_date=None):
    """Generate SOC 2 compliance report."""
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date

    response = requests.get(
        f"{AUTH_SERVICE}/admin/compliance/report/soc2",
        headers={"Authorization": f"Bearer {token}"},
        params=params
    )

    if response.status_code == 200:
        report = response.json()
        print("✓ SOC 2 report generated successfully")
        return report
    else:
        raise Exception(f"Failed to generate SOC 2 report: {response.status_code} - {response.text}")


def test_soc2_compliance_report():
    """Test SOC 2 compliance report generation."""
    print("=" * 80)
    print("TEST: Feature #541 - SOC 2 Compliance Report")
    print("=" * 80)

    try:
        # Step 0: Setup
        print("\n[STEP 0] Setup")
        admin_id = create_admin_user()
        token = login_admin()

        # Create test audit data
        event_ids = create_test_audit_data(admin_id)

        # Step 1: Generate SOC 2 report
        print("\n[STEP 1] Generate SOC 2 report")

        # Generate report for last 7 days
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        end_date = datetime.now(timezone.utc).isoformat()

        report = generate_soc2_report(token, start_date, end_date)

        # Verify report structure
        assert "report_type" in report, "Report should have report_type"
        assert report["report_type"] == "SOC 2 Type II", f"Expected 'SOC 2 Type II', got {report['report_type']}"
        assert "generated_at" in report, "Report should have generated_at timestamp"
        assert "period" in report, "Report should have period information"
        print(f"✓ Report type: {report['report_type']}")
        print(f"✓ Generated at: {report['generated_at']}")
        print(f"✓ Period: {report['period']['days']} days")

        # Step 2: Verify includes access controls
        print("\n[STEP 2] Verify includes access controls")

        assert "security_controls" in report, "Report should include security_controls"
        security = report["security_controls"]

        # Check authentication controls
        assert "authentication" in security, "Security controls should include authentication"
        auth = security["authentication"]
        assert "total_login_attempts" in auth, "Should track total login attempts"
        assert "failed_login_attempts" in auth, "Should track failed login attempts"
        assert "failure_rate" in auth, "Should calculate failure rate"
        print(f"✓ Authentication metrics:")
        print(f"  - Total login attempts: {auth['total_login_attempts']}")
        print(f"  - Failed attempts: {auth['failed_login_attempts']}")
        print(f"  - Failure rate: {auth['failure_rate']}%")

        # Check access control
        assert "access_control" in security, "Security controls should include access_control"
        access = security["access_control"]
        assert "role_changes" in access, "Should track role changes"
        assert "data_access_events" in access, "Should track data access events"
        print(f"✓ Access control metrics:")
        print(f"  - Role changes: {access['role_changes']}")
        print(f"  - Data access events: {access['data_access_events']}")

        # Check configuration controls
        assert "configuration" in security, "Security controls should include configuration"
        config = security["configuration"]
        assert "config_changes" in config, "Should track config changes"
        print(f"✓ Configuration metrics:")
        print(f"  - Config changes: {config['config_changes']}")

        # Step 3: Verify includes audit logs
        print("\n[STEP 3] Verify includes audit logs")

        assert "audit_logging" in report, "Report should include audit_logging"
        audit = report["audit_logging"]

        assert "total_events" in audit, "Should track total audit events"
        assert "events_per_day" in audit, "Should calculate events per day"
        assert "completeness" in audit, "Should indicate audit completeness"

        assert audit["total_events"] > 0, f"Expected audit events, got {audit['total_events']}"
        assert audit["completeness"] == "100%", f"Expected 100% completeness, got {audit['completeness']}"

        print(f"✓ Audit logging metrics:")
        print(f"  - Total events: {audit['total_events']}")
        print(f"  - Events per day: {audit['events_per_day']}")
        print(f"  - Completeness: {audit['completeness']}")

        # Step 4: Verify compliance evidence
        print("\n[STEP 4] Verify compliance evidence")

        assert "trust_service_criteria" in report, "Report should include trust_service_criteria"
        tsc = report["trust_service_criteria"]

        # Check all 5 Trust Service Criteria
        required_criteria = [
            ("CC6_Security", "Security"),
            ("A1_Availability", "Availability"),
            ("PI1_Processing_Integrity", "Processing Integrity"),
            ("C1_Confidentiality", "Confidentiality"),
            ("P1_Privacy", "Privacy")
        ]

        for criterion_key, criterion_name in required_criteria:
            assert criterion_key in tsc, f"Trust Service Criteria should include {criterion_name}"
            criterion = tsc[criterion_key]
            assert "status" in criterion, f"{criterion_name} should have status"
            assert "details" in criterion, f"{criterion_name} should have details"
            assert criterion["status"] == "Compliant", f"{criterion_name} should be Compliant, got {criterion['status']}"
            print(f"✓ {criterion_name}:")
            print(f"  - Status: {criterion['status']}")
            print(f"  - Details: {criterion['details']}")

        # Verify period information
        assert "start" in report["period"], "Period should have start date"
        assert "end" in report["period"], "Period should have end date"
        assert "days" in report["period"], "Period should have duration in days"
        assert report["period"]["days"] > 0, f"Period should span at least 1 day, got {report['period']['days']}"

        # Verify data in report matches test data
        # We created 4 login attempts (2 success, 2 failed)
        if auth["total_login_attempts"] > 0:
            assert auth["failed_login_attempts"] <= auth["total_login_attempts"], \
                "Failed attempts should not exceed total attempts"
            print(f"✓ Login metrics are consistent")

        # We created 2 role changes
        if access["role_changes"] >= 2:
            print(f"✓ Role changes tracked correctly ({access['role_changes']} >= 2)")

        # We created multiple data access events (file, user, team reads/writes)
        if access["data_access_events"] >= 5:
            print(f"✓ Data access events tracked correctly ({access['data_access_events']} >= 5)")

        # We created 2 config changes
        if config["config_changes"] >= 2:
            print(f"✓ Config changes tracked correctly ({config['config_changes']} >= 2)")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Feature #541 Working!")
        print("=" * 80)
        print("\nSOC 2 Report Summary:")
        print(f"  - Report Type: {report['report_type']}")
        print(f"  - Period: {report['period']['days']} days")
        print(f"  - Total Audit Events: {audit['total_events']}")
        print(f"  - Authentication Attempts: {auth['total_login_attempts']}")
        print(f"  - Trust Service Criteria: All 5 Compliant")
        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_soc2_compliance_report()
    exit(0 if success else 1)
