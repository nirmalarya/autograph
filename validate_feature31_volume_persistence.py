#!/usr/bin/env python3
"""
Feature 31: Docker volumes persist data across container restarts
Validates that PostgreSQL, Redis, and MinIO data persists when containers are restarted
"""

import subprocess
import time
import psycopg2
import redis
from minio import Minio
from minio.error import S3Error
import sys
import os
from io import BytesIO

def run_command(cmd, description):
    """Run a shell command and return output"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"❌ Failed: {result.stderr}")
            return False, result.stderr
        print(f"✅ Success")
        return True, result.stdout
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout")
        return False, "Command timed out"
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, str(e)

def wait_for_service(service_name, max_retries=30):
    """Wait for a service to be healthy"""
    print(f"\n⏳ Waiting for {service_name} to be healthy...")
    for i in range(max_retries):
        try:
            result = subprocess.run(
                f"docker-compose ps {service_name} | grep healthy",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✅ {service_name} is healthy")
                return True
        except:
            pass
        time.sleep(2)
    print(f"❌ {service_name} failed to become healthy")
    return False

def test_postgres_persistence():
    """Test PostgreSQL data persistence across container restarts"""
    print("\n" + "="*80)
    print("TEST 1: PostgreSQL Data Persistence")
    print("="*80)

    test_table = "volume_test_table"
    test_data = "persistence_test_data_12345"

    try:
        # Connect to PostgreSQL
        print("\n📊 Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database=os.getenv("POSTGRES_DB", "autograph"),
            user=os.getenv("POSTGRES_USER", "autograph"),
            password=os.getenv("POSTGRES_PASSWORD", "autograph_dev_password")
        )
        conn.autocommit = True
        cursor = conn.cursor()
        print("✅ Connected to PostgreSQL")

        # Create test table and insert data
        print(f"\n📝 Creating test table '{test_table}' and inserting data...")
        cursor.execute(f"DROP TABLE IF EXISTS {test_table}")
        cursor.execute(f"CREATE TABLE {test_table} (id SERIAL PRIMARY KEY, data TEXT)")
        cursor.execute(f"INSERT INTO {test_table} (data) VALUES (%s)", (test_data,))
        cursor.execute(f"SELECT data FROM {test_table} WHERE id = 1")
        result = cursor.fetchone()
        print(f"✅ Data inserted: {result[0]}")

        cursor.close()
        conn.close()

        # Stop PostgreSQL container
        print("\n🛑 Stopping PostgreSQL container...")
        success, _ = run_command("docker-compose stop postgres", "Stopping postgres")
        if not success:
            return False
        time.sleep(3)

        # Remove PostgreSQL container (but keep volume)
        print("\n🗑️  Removing PostgreSQL container (volume preserved)...")
        success, _ = run_command("docker-compose rm -f postgres", "Removing postgres container")
        if not success:
            return False
        time.sleep(2)

        # Start new PostgreSQL container with same volume
        print("\n🚀 Starting new PostgreSQL container with same volume...")
        success, _ = run_command("docker-compose up -d postgres", "Starting postgres")
        if not success:
            return False

        # Wait for PostgreSQL to be healthy
        if not wait_for_service("postgres"):
            return False

        time.sleep(5)  # Extra time for full initialization

        # Connect and verify data still exists
        print("\n🔍 Connecting to new container and verifying data...")
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database=os.getenv("POSTGRES_DB", "autograph"),
            user=os.getenv("POSTGRES_USER", "autograph"),
            password=os.getenv("POSTGRES_PASSWORD", "autograph_dev_password")
        )
        cursor = conn.cursor()

        cursor.execute(f"SELECT data FROM {test_table} WHERE id = 1")
        result = cursor.fetchone()

        if result and result[0] == test_data:
            print(f"✅ Data persisted correctly: {result[0]}")
            print("✅ PostgreSQL volume persistence: PASSED")

            # Cleanup
            cursor.execute(f"DROP TABLE {test_table}")
            cursor.close()
            conn.close()
            return True
        else:
            print(f"❌ Data not found or incorrect")
            cursor.close()
            conn.close()
            return False

    except Exception as e:
        print(f"❌ PostgreSQL test failed: {e}")
        return False

def test_redis_persistence():
    """Test Redis data persistence across container restarts"""
    print("\n" + "="*80)
    print("TEST 2: Redis Data Persistence")
    print("="*80)

    test_key = "volume_test_key"
    test_value = "persistence_test_value_67890"

    try:
        # Connect to Redis
        print("\n📊 Connecting to Redis...")
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✅ Connected to Redis")

        # Set test data (no expiry for persistence test)
        print(f"\n📝 Setting test key '{test_key}' with value...")
        r.set(test_key, test_value)
        result = r.get(test_key)
        print(f"✅ Data set: {result}")

        # Ensure Redis saves to disk
        print("\n💾 Forcing Redis to save to disk...")
        r.save()
        print("✅ Data saved to disk")

        # Stop Redis container
        print("\n🛑 Stopping Redis container...")
        success, _ = run_command("docker-compose stop redis", "Stopping redis")
        if not success:
            return False
        time.sleep(3)

        # Remove Redis container (but keep volume)
        print("\n🗑️  Removing Redis container (volume preserved)...")
        success, _ = run_command("docker-compose rm -f redis", "Removing redis container")
        if not success:
            return False
        time.sleep(2)

        # Start new Redis container with same volume
        print("\n🚀 Starting new Redis container with same volume...")
        success, _ = run_command("docker-compose up -d redis", "Starting redis")
        if not success:
            return False

        # Wait for Redis to be healthy
        if not wait_for_service("redis"):
            return False

        time.sleep(3)

        # Connect and verify data still exists
        print("\n🔍 Connecting to new container and verifying data...")
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()

        result = r.get(test_key)

        if result == test_value:
            print(f"✅ Data persisted correctly: {result}")
            print("✅ Redis volume persistence: PASSED")

            # Cleanup
            r.delete(test_key)
            return True
        else:
            print(f"❌ Data not found or incorrect: {result}")
            return False

    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        return False

def test_minio_persistence():
    """Test MinIO data persistence across container restarts"""
    print("\n" + "="*80)
    print("TEST 3: MinIO Data Persistence")
    print("="*80)

    test_bucket = "volume-test-bucket"
    test_object = "test-object.txt"
    test_content = b"persistence_test_content_abcdef"

    try:
        # Connect to MinIO
        print("\n📊 Connecting to MinIO...")
        client = Minio(
            "localhost:9000",
            access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
            secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
            secure=False
        )
        print("✅ Connected to MinIO")

        # Create bucket and upload object
        print(f"\n📝 Creating bucket '{test_bucket}' and uploading object...")
        if client.bucket_exists(test_bucket):
            client.remove_bucket(test_bucket)
        client.make_bucket(test_bucket)

        client.put_object(
            test_bucket,
            test_object,
            BytesIO(test_content),
            len(test_content)
        )
        print(f"✅ Object uploaded to bucket")

        # Stop MinIO container
        print("\n🛑 Stopping MinIO container...")
        success, _ = run_command("docker-compose stop minio", "Stopping minio")
        if not success:
            return False
        time.sleep(3)

        # Remove MinIO container (but keep volume)
        print("\n🗑️  Removing MinIO container (volume preserved)...")
        success, _ = run_command("docker-compose rm -f minio", "Removing minio container")
        if not success:
            return False
        time.sleep(2)

        # Start new MinIO container with same volume
        print("\n🚀 Starting new MinIO container with same volume...")
        success, _ = run_command("docker-compose up -d minio", "Starting minio")
        if not success:
            return False

        # Wait for MinIO to be healthy
        if not wait_for_service("minio"):
            return False

        time.sleep(5)

        # Connect and verify data still exists
        print("\n🔍 Connecting to new container and verifying data...")
        client = Minio(
            "localhost:9000",
            access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
            secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
            secure=False
        )

        # Check bucket exists
        if not client.bucket_exists(test_bucket):
            print(f"❌ Bucket '{test_bucket}' not found")
            return False

        # Get object and verify content
        response = client.get_object(test_bucket, test_object)
        content = response.read()
        response.close()
        response.release_conn()

        if content == test_content:
            print(f"✅ Data persisted correctly: {len(content)} bytes")
            print("✅ MinIO volume persistence: PASSED")

            # Cleanup
            client.remove_object(test_bucket, test_object)
            client.remove_bucket(test_bucket)
            return True
        else:
            print(f"❌ Data not found or incorrect")
            return False

    except Exception as e:
        print(f"❌ MinIO test failed: {e}")
        return False

def main():
    """Run all volume persistence tests"""
    print("\n" + "="*80)
    print("FEATURE 31: Docker Volumes Persist Data Across Container Restarts")
    print("="*80)

    # Run all tests
    results = {
        "PostgreSQL": test_postgres_persistence(),
        "Redis": test_redis_persistence(),
        "MinIO": test_minio_persistence()
    }

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    all_passed = True
    for service, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{service} volume persistence: {status}")
        if not passed:
            all_passed = False

    print("\n" + "="*80)
    if all_passed:
        print("✅ FEATURE 31: PASSED - All volume persistence tests successful")
        print("="*80)
        return 0
    else:
        print("❌ FEATURE 31: FAILED - Some tests failed")
        print("="*80)
        return 1

if __name__ == "__main__":
    sys.exit(main())
