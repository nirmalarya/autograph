#!/usr/bin/env python3
"""
Test Feature #548: Enterprise: Key management: rotate encryption keys

This test verifies that encryption keys can be rotated safely:
1. Rotate database encryption key
2. Verify data re-encrypted
3. Verify no data loss
4. Test access after rotation
"""
import requests
import psycopg2
import os
import sys
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

# Test configuration
API_BASE_URL = "https://localhost:8080"
DATABASE_URL = os.getenv("DATABASE_URL")

# Disable SSL warnings for self-signed certificates
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test_generate_encryption_key():
    """Test: Generate a new encryption key"""
    print("\n1. Testing encryption key generation...")

    response = requests.post(
        f"{API_BASE_URL}/api/admin/encryption/generate-key",
        verify=False
    )

    assert response.status_code == 200, f"Key generation failed: {response.status_code}"

    data = response.json()
    assert data["success"], "Key generation did not succeed"
    assert "new_key" in data, "New key not returned"
    assert len(data["new_key"]) > 0, "New key is empty"

    print(f"✓ Generated new encryption key: {data['new_key'][:20]}...")

    return data["new_key"]


def test_verify_encryption_key(encryption_key: str, should_be_valid: bool = True):
    """Test: Verify encryption key validity"""
    print(f"\n2. Testing encryption key verification (should be {'valid' if should_be_valid else 'invalid'})...")

    response = requests.post(
        f"{API_BASE_URL}/api/admin/encryption/verify",
        json={
            "encryption_key": encryption_key,
            "test_data": "test-data-for-verification"
        },
        verify=False
    )

    assert response.status_code == 200, f"Verification request failed: {response.status_code}"

    data = response.json()
    assert data["success"], "Verification request did not succeed"

    if should_be_valid:
        assert data["valid"], f"Key should be valid but got: {data['message']}"
        print(f"✓ Encryption key is valid: {data['message']}")
    else:
        assert not data["valid"], f"Key should be invalid but got: {data['message']}"
        print(f"✓ Encryption key is invalid (as expected): {data['message']}")


def test_database_encryption_direct():
    """Test: Direct database encryption/decryption using pgcrypto"""
    print("\n3. Testing direct database encryption...")

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # Test pgcrypto is available
        cursor.execute("SELECT COUNT(*) FROM pg_extension WHERE extname = 'pgcrypto';")
        result = cursor.fetchone()[0]
        assert result == 1, "pgcrypto extension is not installed"
        print("✓ pgcrypto extension is installed")

        # Test encryption/decryption
        test_data = "sensitive-test-data"
        test_key = "test-encryption-key-123"

        cursor.execute("""
            SELECT pgp_sym_decrypt(
                pgp_sym_encrypt(%s, %s),
                %s
            )
        """, (test_data, test_key, test_key))

        decrypted = cursor.fetchone()[0].tobytes().decode('utf-8')
        assert decrypted == test_data, f"Encryption/decryption failed: expected '{test_data}', got '{decrypted}'"

        print(f"✓ Database encryption/decryption works correctly")

    finally:
        cursor.close()
        conn.close()


def test_key_rotation_with_data():
    """Test: Key rotation with actual encrypted data"""
    print("\n4. Testing key rotation with encrypted data...")

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # Create a test table with encrypted data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_encrypted_data (
                id SERIAL PRIMARY KEY,
                encrypted_value BYTEA,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Insert test data encrypted with old key
        old_key = "old-encryption-key-123"
        test_values = ["secret-value-1", "secret-value-2", "secret-value-3"]

        for value in test_values:
            cursor.execute("""
                INSERT INTO test_encrypted_data (encrypted_value)
                VALUES (pgp_sym_encrypt(%s, %s))
            """, (value, old_key))

        conn.commit()
        print(f"✓ Inserted {len(test_values)} encrypted test records")

        # Verify we can decrypt with old key
        cursor.execute("""
            SELECT id, pgp_sym_decrypt(encrypted_value, %s) AS decrypted
            FROM test_encrypted_data
            ORDER BY id
        """, (old_key,))

        old_results = [(row[0], row[1].tobytes().decode('utf-8')) for row in cursor.fetchall()]
        assert len(old_results) == len(test_values), "Not all records retrieved"
        print(f"✓ Successfully decrypted {len(old_results)} records with old key")

        # Perform key rotation
        new_key = "new-encryption-key-456"

        cursor.execute("""
            UPDATE test_encrypted_data
            SET encrypted_value = pgp_sym_encrypt(
                pgp_sym_decrypt(encrypted_value, %s),
                %s
            )
        """, (old_key, new_key))

        conn.commit()
        print(f"✓ Rotated encryption keys for {cursor.rowcount} records")

        # Verify we can decrypt with new key
        cursor.execute("""
            SELECT id, pgp_sym_decrypt(encrypted_value, %s) AS decrypted
            FROM test_encrypted_data
            ORDER BY id
        """, (new_key,))

        new_results = [(row[0], row[1].tobytes().decode('utf-8')) for row in cursor.fetchall()]
        assert len(new_results) == len(test_values), "Not all records retrieved after rotation"

        # Verify no data loss
        for i, (old_id, old_value) in enumerate(old_results):
            new_id, new_value = new_results[i]
            assert old_id == new_id, f"Record ID mismatch after rotation"
            assert old_value == new_value, f"Data loss detected: '{old_value}' != '{new_value}'"

        print(f"✓ No data loss - all {len(new_results)} records match after rotation")

        # Verify old key no longer works
        try:
            cursor.execute("""
                SELECT pgp_sym_decrypt(encrypted_value, %s)
                FROM test_encrypted_data
                LIMIT 1
            """, (old_key,))
            cursor.fetchone()
            assert False, "Old key should not work after rotation"
        except psycopg2.Error:
            print("✓ Old key correctly fails after rotation")

        # Clean up test table
        cursor.execute("DROP TABLE test_encrypted_data")
        conn.commit()
        print("✓ Cleaned up test table")

    except Exception as e:
        conn.rollback()
        # Try to clean up even if test failed
        try:
            cursor.execute("DROP TABLE IF EXISTS test_encrypted_data")
            conn.commit()
        except:
            pass
        raise

    finally:
        cursor.close()
        conn.close()


def test_secrets_manager_key_rotation():
    """Test: SecretsManager key rotation"""
    print("\n5. Testing SecretsManager key rotation...")

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared', 'python'))
    from secrets_manager import SecretsManager

    # Generate two keys for testing
    old_master_key = Fernet.generate_key().decode()
    new_master_key = Fernet.generate_key().decode()

    # Create secrets manager with old key
    sm_old = SecretsManager(master_key=old_master_key)

    # Store some test secrets
    test_secrets = {
        "test_api_key": "sk-test-12345",
        "test_password": "SuperSecret123!",
        "test_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    }

    for name, value in test_secrets.items():
        sm_old.set_secret(name, value)

    print(f"✓ Stored {len(test_secrets)} secrets with old key")

    # Simulate rotation by loading with old key and saving with new key
    all_secrets = {name: sm_old.get_secret(name) for name in sm_old.list_secrets()}

    # Create new secrets manager with new key
    sm_new = SecretsManager(master_key=new_master_key)

    for name, value in all_secrets.items():
        sm_new.set_secret(name, value)

    print(f"✓ Re-encrypted {len(all_secrets)} secrets with new key")

    # Verify no data loss
    for name, original_value in test_secrets.items():
        rotated_value = sm_new.get_secret(name)
        assert rotated_value == original_value, f"Data loss in secret '{name}': '{original_value}' != '{rotated_value}'"

    print(f"✓ No data loss - all {len(test_secrets)} secrets match after rotation")


def test_api_key_rotation_endpoint():
    """Test: Full key rotation via API endpoint"""
    print("\n6. Testing full key rotation via API endpoint...")

    # Generate keys for testing
    old_db_key = "test-old-db-key-123"
    new_db_key = "test-new-db-key-456"
    old_master_key = Fernet.generate_key().decode()
    new_master_key = Fernet.generate_key().decode()

    response = requests.post(
        f"{API_BASE_URL}/api/admin/encryption/rotate-keys",
        json={
            "old_db_key": old_db_key,
            "new_db_key": new_db_key,
            "old_master_key": old_master_key,
            "new_master_key": new_master_key
        },
        verify=False
    )

    assert response.status_code == 200, f"Key rotation API failed: {response.status_code} - {response.text}"

    data = response.json()
    assert data["success"], f"Key rotation failed: {data.get('message', 'Unknown error')}"

    print(f"✓ API key rotation completed successfully")
    print(f"  - Database tables rotated: {data['result']['database']['tables_rotated']}")
    print(f"  - Database rows rotated: {data['result']['database']['rows_rotated']}")
    print(f"  - Secrets rotated: {data['result']['secrets_manager']['secrets_rotated']}")

    # Verify the new database key works
    test_verify_encryption_key(new_db_key, should_be_valid=True)


def run_all_tests():
    """Run all key rotation tests"""
    print("=" * 70)
    print("Feature #548: Enterprise: Key management: rotate encryption keys")
    print("=" * 70)

    try:
        # Test 1: Generate encryption key
        new_key = test_generate_encryption_key()

        # Test 2: Verify encryption key
        test_verify_encryption_key(new_key, should_be_valid=True)

        # Test 3: Direct database encryption
        test_database_encryption_direct()

        # Test 4: Key rotation with data
        test_key_rotation_with_data()

        # Test 5: SecretsManager rotation
        test_secrets_manager_key_rotation()

        # Test 6: Full API rotation
        test_api_key_rotation_endpoint()

        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED - Feature #548 is working correctly!")
        print("=" * 70)

        return True

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
