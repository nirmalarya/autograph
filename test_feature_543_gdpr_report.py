"""
Test Feature #543: Enterprise: Compliance reports: GDPR format

Steps:
1. Generate GDPR report
2. Verify data processing activities
3. Verify consent tracking
4. Verify data retention policies
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
        cursor.execute("DELETE FROM users WHERE email = 'admin543@test.com'")
        conn.commit()

        # Create admin user (password: Admin123!)
        import bcrypt
        password_hash = bcrypt.hashpw("Admin123!".encode(), bcrypt.gensalt()).decode()

        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
            VALUES (gen_random_uuid(), 'admin543@test.com', %s, 'Admin User 543', true, true, 'admin')
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
            "email": "admin543@test.com",
            "password": "Admin123!"
        }
    )

    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✓ Admin logged in successfully")
        return token
    else:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")


def create_test_gdpr_data(admin_id):
    """Create various audit log entries for testing GDPR report."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        now = datetime.now(timezone.utc)

        # Create diverse audit events covering GDPR articles
        test_events = [
            # Article 5: Data processing principles
            ('register', 'user', 'user-001', {"consent_given": True, "article": "Article 5"}),
            ('register', 'user', 'user-002', {"consent_given": True, "article": "Article 5"}),
            ('register', 'user', 'user-003', {"consent_given": True, "article": "Article 5"}),

            # Article 15: Right of access
            ('read', 'user', 'user-001', {"action": "data_export", "article": "Article 15"}),
            ('read', 'user', 'user-002', {"action": "view_profile", "article": "Article 15"}),
            ('read', 'user', 'user-003', {"action": "data_export", "article": "Article 15"}),
            ('read', 'user', 'user-004', {"action": "view_profile", "article": "Article 15"}),

            # Article 17: Right to erasure
            ('delete_user', 'user', 'user-005', {"reason": "user_request", "article": "Article 17"}),
            ('delete_file', 'file', 'file-001', {"reason": "user_request", "article": "Article 17"}),

            # Article 30: Records of processing activities
            ('write', 'file', 'file-002', {"action": "create_diagram", "article": "Article 30"}),
            ('update', 'file', 'file-003', {"action": "edit_diagram", "article": "Article 30"}),
            ('write', 'comment', 'comment-001', {"action": "create_comment", "article": "Article 30"}),

            # Article 32: Security of processing
            ('login_success', 'authentication', None, {"source": "web", "article": "Article 32"}),
            ('login_success', 'authentication', None, {"source": "api", "article": "Article 32"}),
            ('login_failed', 'authentication', None, {"reason": "invalid_password", "article": "Article 32"}),
            ('config_change', 'security', 'encryption', {"enabled": True, "article": "Article 32"}),

            # Additional processing activities
            ('write', 'file', 'file-004', {"action": "create_canvas"}),
            ('update', 'file', 'file-005', {"action": "update_canvas"}),
            ('read', 'file', 'file-006', {"action": "view_canvas"}),
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
        print(f"✓ Created {len(test_events)} test GDPR audit events")
        return event_ids
    finally:
        cursor.close()
        conn.close()


def generate_gdpr_report(token, start_date=None, end_date=None):
    """Generate GDPR compliance report."""
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date

    response = requests.get(
        f"{AUTH_SERVICE}/admin/compliance/report/gdpr",
        headers={"Authorization": f"Bearer {token}"},
        params=params
    )

    if response.status_code == 200:
        report = response.json()
        print("✓ GDPR report generated successfully")
        return report
    else:
        raise Exception(f"Failed to generate GDPR report: {response.status_code} - {response.text}")


def test_gdpr_compliance_report():
    """Test GDPR compliance report generation."""
    print("=" * 80)
    print("TEST: Feature #543 - GDPR Compliance Report")
    print("=" * 80)

    try:
        # Step 0: Setup
        print("\n[STEP 0] Setup")
        admin_id = create_admin_user()
        token = login_admin()

        # Create test GDPR data
        event_ids = create_test_gdpr_data(admin_id)

        # Step 1: Generate GDPR report
        print("\n[STEP 1] Generate GDPR report")

        # Generate report for last 7 days
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        end_date = datetime.now(timezone.utc).isoformat()

        report = generate_gdpr_report(token, start_date, end_date)

        # Verify report structure
        assert "report_type" in report, "Report should have report_type"
        assert report["report_type"] == "GDPR Compliance Report", f"Expected 'GDPR Compliance Report', got {report['report_type']}"
        assert "generated_at" in report, "Report should have generated_at timestamp"
        assert "period" in report, "Report should have period information"
        print(f"✓ Report type: {report['report_type']}")
        print(f"✓ Generated at: {report['generated_at']}")
        print(f"✓ Period: {report['period']['days']} days")

        # Step 2: Verify data processing activities
        print("\n[STEP 2] Verify data processing activities")

        assert "gdpr_articles" in report, "Report should include gdpr_articles"
        articles = report["gdpr_articles"]

        # Check Article 30: Records of processing activities
        assert "Article_30_Records_of_Processing" in articles, "Should include Article 30"
        article_30 = articles["Article_30_Records_of_Processing"]

        assert "status" in article_30, "Article 30 should have status"
        assert "processing_activities" in article_30, "Article 30 should have processing_activities count"
        assert "details" in article_30, "Article 30 should have details"

        assert article_30["status"] == "Compliant", f"Article 30 should be Compliant, got {article_30['status']}"
        assert article_30["processing_activities"] > 0, f"Expected processing activities, got {article_30['processing_activities']}"

        print(f"✓ Article 30 - Records of Processing:")
        print(f"  - Status: {article_30['status']}")
        print(f"  - Processing Activities: {article_30['processing_activities']}")
        print(f"  - Details: {article_30['details']}")

        # Step 3: Verify consent tracking
        print("\n[STEP 3] Verify consent tracking")

        # Check Article 5: Data processing principles (includes consent)
        assert "Article_5_Processing_Principles" in articles, "Should include Article 5"
        article_5 = articles["Article_5_Processing_Principles"]

        assert "status" in article_5, "Article 5 should have status"
        assert "lawfulness" in article_5, "Article 5 should document lawfulness"
        assert "purpose_limitation" in article_5, "Article 5 should document purpose limitation"
        assert "data_minimization" in article_5, "Article 5 should document data minimization"
        assert "accuracy" in article_5, "Article 5 should document accuracy"
        assert "storage_limitation" in article_5, "Article 5 should document storage limitation"
        assert "integrity_confidentiality" in article_5, "Article 5 should document integrity/confidentiality"

        assert article_5["status"] == "Compliant", f"Article 5 should be Compliant, got {article_5['status']}"

        print(f"✓ Article 5 - Processing Principles:")
        print(f"  - Status: {article_5['status']}")
        print(f"  - Lawfulness: {article_5['lawfulness']}")
        print(f"  - Purpose Limitation: {article_5['purpose_limitation']}")
        print(f"  - Data Minimization: {article_5['data_minimization']}")
        print(f"  - Accuracy: {article_5['accuracy']}")
        print(f"  - Storage Limitation: {article_5['storage_limitation']}")
        print(f"  - Integrity/Confidentiality: {article_5['integrity_confidentiality']}")

        # Check Article 15: Right of access
        assert "Article_15_Right_of_Access" in articles, "Should include Article 15"
        article_15 = articles["Article_15_Right_of_Access"]

        assert "status" in article_15, "Article 15 should have status"
        assert "data_access_requests" in article_15, "Article 15 should track data access requests"
        assert article_15["status"] == "Compliant", f"Article 15 should be Compliant, got {article_15['status']}"

        print(f"✓ Article 15 - Right of Access:")
        print(f"  - Status: {article_15['status']}")
        print(f"  - Data Access Requests: {article_15['data_access_requests']}")

        # Step 4: Verify data retention policies
        print("\n[STEP 4] Verify data retention policies")

        # Check Article 17: Right to erasure
        assert "Article_17_Right_to_Erasure" in articles, "Should include Article 17"
        article_17 = articles["Article_17_Right_to_Erasure"]

        assert "status" in article_17, "Article 17 should have status"
        assert "deletion_requests" in article_17, "Article 17 should track deletion requests"
        assert article_17["status"] == "Compliant", f"Article 17 should be Compliant, got {article_17['status']}"

        print(f"✓ Article 17 - Right to Erasure:")
        print(f"  - Status: {article_17['status']}")
        print(f"  - Deletion Requests: {article_17['deletion_requests']}")

        # Check Article 32: Security of processing
        assert "Article_32_Security_of_Processing" in articles, "Should include Article 32"
        article_32 = articles["Article_32_Security_of_Processing"]

        assert "status" in article_32, "Article 32 should have status"
        assert "security_events" in article_32, "Article 32 should track security events"
        assert "measures" in article_32, "Article 32 should list security measures"
        assert article_32["status"] == "Compliant", f"Article 32 should be Compliant, got {article_32['status']}"
        assert isinstance(article_32["measures"], list), "Security measures should be a list"
        assert len(article_32["measures"]) > 0, "Should have at least one security measure"

        print(f"✓ Article 32 - Security of Processing:")
        print(f"  - Status: {article_32['status']}")
        print(f"  - Security Events: {article_32['security_events']}")
        print(f"  - Security Measures:")
        for measure in article_32["measures"]:
            print(f"    • {measure}")

        # Verify data subjects section
        assert "data_subjects" in report, "Report should include data_subjects"
        data_subjects = report["data_subjects"]

        assert "new_registrations" in data_subjects, "Should track new registrations"
        assert "active_users" in data_subjects, "Should track active users"
        assert "total_users" in data_subjects, "Should track total users"

        print(f"\n✓ Data Subjects:")
        print(f"  - New Registrations (period): {data_subjects['new_registrations']}")
        print(f"  - Active Users: {data_subjects['active_users']}")
        print(f"  - Total Users: {data_subjects['total_users']}")

        # Verify data breaches section
        assert "data_breaches" in report, "Report should include data_breaches"
        data_breaches = report["data_breaches"]

        assert "count" in data_breaches, "Should track breach count"
        assert "details" in data_breaches, "Should provide breach details"

        print(f"\n✓ Data Breaches:")
        print(f"  - Count: {data_breaches['count']}")
        print(f"  - Details: {data_breaches['details']}")

        # Verify DPO contact
        assert "dpo_contact" in report, "Report should include dpo_contact"
        dpo = report["dpo_contact"]

        assert "email" in dpo, "Should provide DPO email"

        print(f"\n✓ DPO Contact:")
        print(f"  - Email: {dpo['email']}")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Feature #543 Working!")
        print("=" * 80)
        print("\nGDPR Report Summary:")
        print(f"  - Report Type: {report['report_type']}")
        print(f"  - Period: {report['period']['days']} days")
        print(f"  - GDPR Articles: 5 articles covered")
        print(f"  - Article 5 (Processing Principles): {article_5['status']}")
        print(f"  - Article 15 (Right of Access): {article_15['status']}")
        print(f"  - Article 17 (Right to Erasure): {article_17['status']}")
        print(f"  - Article 30 (Processing Records): {article_30['status']}")
        print(f"  - Article 32 (Security): {article_32['status']}")
        print(f"  - Processing Activities: {article_30['processing_activities']}")
        print(f"  - Data Access Requests: {article_15['data_access_requests']}")
        print(f"  - Deletion Requests: {article_17['deletion_requests']}")
        print(f"  - Security Events: {article_32['security_events']}")
        print(f"  - Total Users: {data_subjects['total_users']}")
        print(f"  - Data Breaches: {data_breaches['count']}")
        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_gdpr_compliance_report()
    exit(0 if success else 1)
