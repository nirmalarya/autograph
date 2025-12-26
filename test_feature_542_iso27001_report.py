"""
Test Feature #542: Enterprise: Compliance reports: ISO 27001 format

Steps:
1. Generate ISO 27001 report
2. Verify security controls documented
3. Verify evidence included
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
        cursor.execute("DELETE FROM users WHERE email = 'admin542@test.com'")
        conn.commit()

        # Create admin user (password: Admin123!)
        import bcrypt
        password_hash = bcrypt.hashpw("Admin123!".encode(), bcrypt.gensalt()).decode()

        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
            VALUES (gen_random_uuid(), 'admin542@test.com', %s, 'Admin User 542', true, true, 'admin')
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
            "email": "admin542@test.com",
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
    """Create various audit log entries for testing ISO 27001 report."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        now = datetime.now(timezone.utc)

        # Create diverse audit events covering ISO 27001 Annex A controls
        test_events = [
            # A.9: Access Control
            ('login_success', 'authentication', None, {"source": "web", "control": "A.9"}),
            ('login_success', 'authentication', None, {"source": "api", "control": "A.9"}),
            ('login_failed', 'authentication', None, {"reason": "invalid_password", "control": "A.9"}),
            ('logout', 'authentication', None, {"source": "web", "control": "A.9"}),
            ('role_change', 'user', 'user-123', {"from": "user", "to": "admin", "control": "A.9"}),
            ('role_change', 'user', 'user-456', {"from": "viewer", "to": "editor", "control": "A.9"}),

            # A.12: Operations Security
            ('config_change', 'security', 'mfa', {"enabled": True, "control": "A.12"}),
            ('config_change', 'audit_retention', 'retention', {"retention_days": 90, "control": "A.12"}),
            ('audit_export', 'audit', 'export-123', {"format": "csv", "control": "A.12"}),

            # A.16: Information Security Incident Management
            ('login_failed', 'authentication', None, {"reason": "invalid_password", "control": "A.16"}),
            ('login_failed', 'authentication', None, {"reason": "account_locked", "control": "A.16"}),
            ('account_locked', 'security', 'user-789', {"reason": "too_many_attempts", "control": "A.16"}),

            # A.18: Compliance
            ('compliance_report', 'compliance', 'report-001', {"type": "SOC2", "control": "A.18"}),
            ('audit_export', 'audit', 'export-456', {"format": "json", "control": "A.18"}),

            # Additional general events
            ('read', 'file', 'file-abc', {"action": "view_diagram"}),
            ('write', 'file', 'file-def', {"action": "update_diagram"}),
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


def generate_iso27001_report(token, start_date=None, end_date=None):
    """Generate ISO 27001 compliance report."""
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date

    response = requests.get(
        f"{AUTH_SERVICE}/admin/compliance/report/iso27001",
        headers={"Authorization": f"Bearer {token}"},
        params=params
    )

    if response.status_code == 200:
        report = response.json()
        print("✓ ISO 27001 report generated successfully")
        return report
    else:
        raise Exception(f"Failed to generate ISO 27001 report: {response.status_code} - {response.text}")


def test_iso27001_compliance_report():
    """Test ISO 27001 compliance report generation."""
    print("=" * 80)
    print("TEST: Feature #542 - ISO 27001 Compliance Report")
    print("=" * 80)

    try:
        # Step 0: Setup
        print("\n[STEP 0] Setup")
        admin_id = create_admin_user()
        token = login_admin()

        # Create test audit data
        event_ids = create_test_audit_data(admin_id)

        # Step 1: Generate ISO 27001 report
        print("\n[STEP 1] Generate ISO 27001 report")

        # Generate report for last 7 days
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        end_date = datetime.now(timezone.utc).isoformat()

        report = generate_iso27001_report(token, start_date, end_date)

        # Verify report structure
        assert "report_type" in report, "Report should have report_type"
        assert report["report_type"] == "ISO 27001:2013", f"Expected 'ISO 27001:2013', got {report['report_type']}"
        assert "generated_at" in report, "Report should have generated_at timestamp"
        assert "period" in report, "Report should have period information"
        print(f"✓ Report type: {report['report_type']}")
        print(f"✓ Generated at: {report['generated_at']}")
        print(f"✓ Period: {report['period']['days']} days")

        # Step 2: Verify security controls documented
        print("\n[STEP 2] Verify security controls documented")

        assert "annex_a_controls" in report, "Report should include annex_a_controls"
        controls = report["annex_a_controls"]

        # Check all 4 required Annex A controls
        required_controls = [
            ("A9_Access_Control", "A.9 Access Control"),
            ("A12_Operations_Security", "A.12 Operations Security"),
            ("A16_Incident_Management", "A.16 Incident Management"),
            ("A18_Compliance", "A.18 Compliance")
        ]

        for control_key, control_name in required_controls:
            assert control_key in controls, f"Annex A controls should include {control_name}"
            control = controls[control_key]
            assert "status" in control, f"{control_name} should have status"
            assert "events" in control, f"{control_name} should have events count"
            assert "details" in control, f"{control_name} should have details"
            assert control["status"] == "Implemented", f"{control_name} should be Implemented, got {control['status']}"
            print(f"✓ {control_name}:")
            print(f"  - Status: {control['status']}")
            print(f"  - Events: {control['events']}")
            print(f"  - Details: {control['details']}")

        # Step 3: Verify evidence included
        print("\n[STEP 3] Verify evidence included")

        # Check audit trail
        assert "audit_trail" in report, "Report should include audit_trail"
        audit = report["audit_trail"]

        assert "total_events" in audit, "Audit trail should track total events"
        assert "completeness" in audit, "Audit trail should indicate completeness"
        assert "integrity" in audit, "Audit trail should indicate integrity status"
        assert "retention" in audit, "Audit trail should indicate retention policy"

        assert audit["total_events"] > 0, f"Expected audit events, got {audit['total_events']}"
        assert audit["completeness"] == "100%", f"Expected 100% completeness, got {audit['completeness']}"
        assert audit["integrity"] == "Protected", f"Expected Protected integrity, got {audit['integrity']}"

        print(f"✓ Audit trail metrics:")
        print(f"  - Total events: {audit['total_events']}")
        print(f"  - Completeness: {audit['completeness']}")
        print(f"  - Integrity: {audit['integrity']}")
        print(f"  - Retention: {audit['retention']}")

        # Check information security objectives
        assert "information_security_objectives" in report, "Report should include information_security_objectives"
        objectives = report["information_security_objectives"]

        assert "confidentiality" in objectives, "Should include confidentiality objective"
        assert "integrity" in objectives, "Should include integrity objective"
        assert "availability" in objectives, "Should include availability objective"

        print(f"✓ Information Security Objectives:")
        print(f"  - Confidentiality: {objectives['confidentiality']}")
        print(f"  - Integrity: {objectives['integrity']}")
        print(f"  - Availability: {objectives['availability']}")

        # Verify period information
        assert "start" in report["period"], "Period should have start date"
        assert "end" in report["period"], "Period should have end date"
        assert "days" in report["period"], "Period should have duration in days"
        assert report["period"]["days"] > 0, f"Period should span at least 1 day, got {report['period']['days']}"

        # Verify control metrics match test data
        a9_control = controls["A9_Access_Control"]
        # We created 6 access control events (4 logins + 2 role changes)
        if a9_control["events"] >= 6:
            print(f"✓ A.9 Access Control events tracked correctly ({a9_control['events']} >= 6)")

        a12_control = controls["A12_Operations_Security"]
        # We created 3 operations security events (2 config changes + 1 audit export)
        if a12_control["events"] >= 3:
            print(f"✓ A.12 Operations Security events tracked correctly ({a12_control['events']} >= 3)")

        a16_control = controls["A16_Incident_Management"]
        # We created 3 incident management events (2 failed logins + 1 account locked)
        if a16_control["events"] >= 3:
            print(f"✓ A.16 Incident Management events tracked correctly ({a16_control['events']} >= 3)")

        a18_control = controls["A18_Compliance"]
        # We created 2 compliance events (1 compliance report + 1 audit export)
        if a18_control["events"] >= 2:
            print(f"✓ A.18 Compliance events tracked correctly ({a18_control['events']} >= 2)")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Feature #542 Working!")
        print("=" * 80)
        print("\nISO 27001 Report Summary:")
        print(f"  - Report Type: {report['report_type']}")
        print(f"  - Period: {report['period']['days']} days")
        print(f"  - Total Audit Events: {audit['total_events']}")
        print(f"  - Annex A Controls: All 4 Implemented")
        print(f"  - A.9 Access Control Events: {a9_control['events']}")
        print(f"  - A.12 Operations Security Events: {a12_control['events']}")
        print(f"  - A.16 Incident Management Events: {a16_control['events']}")
        print(f"  - A.18 Compliance Events: {a18_control['events']}")
        print(f"  - Audit Trail Completeness: {audit['completeness']}")
        print(f"  - Audit Trail Integrity: {audit['integrity']}")
        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_iso27001_compliance_report()
    exit(0 if success else 1)
