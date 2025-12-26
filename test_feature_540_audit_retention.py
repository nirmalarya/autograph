"""
Test Feature #540: Enterprise: Audit retention: configurable period

Steps:
1. Set retention: 90 days
2. Verify logs older than 90 days deleted
3. Set: 1 year
4. Verify 1-year retention
"""

import requests
import time
from datetime import datetime, timedelta
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8080"
AUTH_SERVICE = "http://localhost:8085"

# Database connection for direct data manipulation
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
        cursor.execute("DELETE FROM users WHERE email = 'admin540@test.com'")
        conn.commit()

        # Create admin user (password: Admin123!)
        import bcrypt
        password_hash = bcrypt.hashpw("Admin123!".encode(), bcrypt.gensalt()).decode()

        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
            VALUES (gen_random_uuid(), 'admin540@test.com', %s, 'Admin User 540', true, true, 'admin')
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
            "email": "admin540@test.com",
            "password": "Admin123!"
        }
    )

    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✓ Admin logged in successfully")
        return token
    else:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")


def create_test_audit_logs(admin_id):
    """Create audit logs with various timestamps for testing retention."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        now = datetime.utcnow()

        # Create logs at different ages
        test_logs = [
            (now - timedelta(days=100), "old_log_1", "100 days old"),
            (now - timedelta(days=200), "old_log_2", "200 days old"),
            (now - timedelta(days=400), "very_old_log", "400 days old (over 1 year)"),
            (now - timedelta(days=50), "recent_log_1", "50 days old"),
            (now - timedelta(days=10), "recent_log_2", "10 days old"),
            (now - timedelta(days=1), "very_recent_log", "1 day old"),
        ]

        log_ids = []
        for created_at, action, description in test_logs:
            cursor.execute("""
                INSERT INTO audit_log (user_id, action, resource_type, resource_id, ip_address, extra_data, created_at)
                VALUES (%s, %s, 'test', 'test-540', '127.0.0.1', %s, %s)
                RETURNING id
            """, (admin_id, action, f'{{"description": "{description}"}}', created_at))
            log_id = cursor.fetchone()[0]
            log_ids.append((log_id, action, created_at))

        conn.commit()
        print(f"✓ Created {len(test_logs)} test audit logs")
        return log_ids
    finally:
        cursor.close()
        conn.close()


def count_audit_logs_by_age(days_old):
    """Count audit logs older than specified days."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        cursor.execute("""
            SELECT COUNT(*) FROM audit_log
            WHERE (action LIKE 'old_log%%' OR action LIKE 'recent_log%%' OR action LIKE 'very_%%')
            AND created_at < %s
        """, (cutoff_date,))
        count = cursor.fetchone()[0]
        return count
    finally:
        cursor.close()
        conn.close()


def count_recent_audit_logs(days_old):
    """Count audit logs newer than specified days."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        cursor.execute("""
            SELECT COUNT(*) FROM audit_log
            WHERE (action LIKE 'old_log%%' OR action LIKE 'recent_log%%' OR action LIKE 'very_%%')
            AND created_at >= %s
        """, (cutoff_date,))
        count = cursor.fetchone()[0]
        return count
    finally:
        cursor.close()
        conn.close()


def get_retention_config(token):
    """Get current audit retention configuration."""
    response = requests.get(
        f"{AUTH_SERVICE}/admin/config/audit-retention",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        config = response.json()
        print(f"✓ Current retention config: {config}")
        return config
    else:
        raise Exception(f"Failed to get retention config: {response.status_code} - {response.text}")


def set_retention_config(token, retention_days, enabled=True):
    """Set audit retention configuration."""
    response = requests.post(
        f"{AUTH_SERVICE}/admin/config/audit-retention",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "retention_days": retention_days,
            "enabled": enabled
        }
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Set retention to {retention_days} days: {result}")
        return result
    else:
        raise Exception(f"Failed to set retention config: {response.status_code} - {response.text}")


def test_audit_retention():
    """Test audit retention configuration."""
    print("=" * 80)
    print("TEST: Feature #540 - Audit Retention: Configurable Period")
    print("=" * 80)

    try:
        # Step 0: Setup
        print("\n[STEP 0] Setup")
        admin_id = create_admin_user()
        token = login_admin()

        # Create test logs
        log_ids = create_test_audit_logs(admin_id)
        print(f"Created logs: {len(log_ids)} total")

        # Verify logs created
        old_count = count_audit_logs_by_age(90)
        recent_count = count_recent_audit_logs(90)
        print(f"  Logs older than 90 days: {old_count}")
        print(f"  Logs newer than 90 days: {recent_count}")

        # Step 1: Set retention to 90 days
        print("\n[STEP 1] Set retention: 90 days")
        result = set_retention_config(token, 90, enabled=True)
        assert result["config"]["retention_days"] == 90
        assert result["config"]["enabled"] == True
        print("✓ Retention set to 90 days")

        # Step 2: Verify logs older than 90 days deleted
        print("\n[STEP 2] Verify logs older than 90 days deleted")
        time.sleep(1)  # Wait for deletion to complete

        old_count_after = count_audit_logs_by_age(90)
        recent_count_after = count_recent_audit_logs(90)

        print(f"  Logs older than 90 days after cleanup: {old_count_after}")
        print(f"  Logs newer than 90 days after cleanup: {recent_count_after}")

        # Should have deleted logs older than 90 days
        assert old_count_after == 0, f"Expected 0 old logs, found {old_count_after}"
        # Recent logs should still exist
        assert recent_count_after > 0, f"Expected recent logs to exist, found {recent_count_after}"
        print("✓ Old logs deleted, recent logs retained")

        # Step 3: Set retention to 1 year (365 days)
        print("\n[STEP 3] Set retention: 1 year (365 days)")
        result = set_retention_config(token, 365, enabled=True)
        assert result["config"]["retention_days"] == 365
        assert result["config"]["enabled"] == True
        print("✓ Retention set to 365 days")

        # Verify configuration persisted
        config = get_retention_config(token)
        assert config["retention_days"] == 365
        assert config["enabled"] == True
        print("✓ Configuration persisted correctly")

        # Step 4: Verify 1-year retention works
        print("\n[STEP 4] Verify 1-year retention")

        # Create more test logs
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            now = datetime.utcnow()
            # Create a log that's 370 days old (should be deleted)
            cursor.execute("""
                INSERT INTO audit_log (user_id, action, resource_type, resource_id, ip_address, created_at)
                VALUES (%s, 'very_old_test', 'test', 'test-540', '127.0.0.1', %s)
            """, (admin_id, now - timedelta(days=370)))

            # Create a log that's 350 days old (should be kept)
            cursor.execute("""
                INSERT INTO audit_log (user_id, action, resource_type, resource_id, ip_address, created_at)
                VALUES (%s, 'within_year_test', 'test', 'test-540', '127.0.0.1', %s)
            """, (admin_id, now - timedelta(days=350)))
            conn.commit()
            print("  Created test logs for 1-year retention verification")
        finally:
            cursor.close()
            conn.close()

        # Trigger retention cleanup by updating config
        result = set_retention_config(token, 365, enabled=True)
        time.sleep(1)

        # Check that very old log was deleted, but 350-day-old log remains
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM audit_log WHERE action = 'very_old_test'")
            very_old_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM audit_log WHERE action = 'within_year_test'")
            within_year_count = cursor.fetchone()[0]

            assert very_old_count == 0, f"Expected very old log to be deleted, found {very_old_count}"
            assert within_year_count == 1, f"Expected within-year log to exist, found {within_year_count}"
            print("✓ 1-year retention verified: logs > 365 days deleted, logs <= 365 days retained")
        finally:
            cursor.close()
            conn.close()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Feature #540 Working!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_audit_retention()
    exit(0 if success else 1)
