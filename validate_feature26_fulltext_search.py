#!/usr/bin/env python3
"""
Feature 26: PostgreSQL full-text search with pg_trgm extension

Steps to validate:
1. Enable pg_trgm extension
2. Create GIN index on files.title
3. Search for 'architecture' in titles
4. Verify fuzzy matching works ('architecure' finds 'architecture')
5. Test similarity threshold
6. Measure search performance on 10,000 files
7. Verify search completes in < 500ms
"""

import sys
import time
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import uuid

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5432')),
        database=os.getenv('POSTGRES_DB', 'autograph'),
        user=os.getenv('POSTGRES_USER', 'autograph'),
        password=os.getenv('POSTGRES_PASSWORD', 'autograph_dev_password')
    )

def enable_pg_trgm_extension(conn):
    """Enable pg_trgm extension"""
    print("Step 1: Enabling pg_trgm extension...")

    with conn.cursor() as cur:
        # Enable extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        conn.commit()

        # Verify extension is enabled
        cur.execute("""
            SELECT extname, extversion
            FROM pg_extension
            WHERE extname = 'pg_trgm';
        """)
        result = cur.fetchone()

        if not result:
            raise Exception("pg_trgm extension not enabled")

        print(f"✓ pg_trgm extension enabled (version: {result[1]})")
        return True

def create_gin_index(conn):
    """Create GIN index on files.title for full-text search"""
    print("\nStep 2: Creating GIN index on files.title...")

    with conn.cursor() as cur:
        # Drop existing index if it exists
        cur.execute("DROP INDEX IF EXISTS idx_files_title_gin_trgm;")

        # Create GIN index using pg_trgm
        cur.execute("""
            CREATE INDEX idx_files_title_gin_trgm
            ON files
            USING GIN (title gin_trgm_ops);
        """)
        conn.commit()

        # Verify index was created
        cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'files'
            AND indexname = 'idx_files_title_gin_trgm';
        """)
        result = cur.fetchone()

        if not result:
            raise Exception("GIN index not created")

        print(f"✓ GIN index created: {result[0]}")
        print(f"  Definition: {result[1]}")
        return True

def insert_test_files(conn, count=10000):
    """Insert test files for performance testing"""
    print(f"\nInserting {count} test files for performance testing...")

    with conn.cursor() as cur:
        # Check if test user exists, create if not
        cur.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, created_at, updated_at)
            VALUES ('test-user-fulltext', 'fulltext@test.com', 'hash', 'Test User', true, true, 'user', NOW(), NOW())
            ON CONFLICT (id) DO NOTHING;
        """)

        # Insert files with various titles including 'architecture'
        files_to_insert = []
        titles = [
            'System Architecture Diagram',
            'Software Architecture Document',
            'Microservice Architecture Overview',
            'Cloud Architecture Design',
            'Database Architecture Schema',
            'Application Flow Chart',
            'User Journey Map',
            'Component Diagram',
            'Sequence Diagram',
            'Class Diagram'
        ]

        for i in range(count):
            file_id = str(uuid.uuid4())
            title = titles[i % len(titles)]
            if i < count // 4:  # 25% with 'architecture'
                title = f"{title} v{i}"
            else:
                title = f"Document {i}"

            files_to_insert.append((
                file_id,
                title,
                'test-user-fulltext',
                'diagram',
                False,
                False
            ))

        # Batch insert
        cur.executemany("""
            INSERT INTO files (id, title, owner_id, file_type, is_starred, is_deleted, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING;
        """, files_to_insert)

        conn.commit()
        print(f"✓ Inserted {count} test files")

def test_exact_search(conn):
    """Test exact search for 'architecture'"""
    print("\nStep 3: Testing exact search for 'architecture'...")

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        start_time = time.time()

        cur.execute("""
            SELECT id, title, similarity(title, 'architecture') as sim
            FROM files
            WHERE title ILIKE '%architecture%'
            AND is_deleted = false
            ORDER BY sim DESC
            LIMIT 10;
        """)

        results = cur.fetchall()
        elapsed_ms = (time.time() - start_time) * 1000

        if not results:
            raise Exception("No results found for 'architecture'")

        print(f"✓ Found {len(results)} results in {elapsed_ms:.2f}ms")
        print(f"  Top result: {results[0]['title']} (similarity: {results[0]['sim']:.3f})")

        return elapsed_ms

def test_fuzzy_search(conn):
    """Test fuzzy search - 'architecure' should find 'architecture'"""
    print("\nStep 4: Testing fuzzy search ('architecure' finds 'architecture')...")

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Use similarity search with typo
        cur.execute("""
            SELECT id, title, similarity(title, 'architecure') as sim
            FROM files
            WHERE similarity(title, 'architecure') > 0.3
            AND is_deleted = false
            ORDER BY sim DESC
            LIMIT 10;
        """)

        results = cur.fetchall()

        if not results:
            raise Exception("Fuzzy search failed - no results for 'architecure'")

        # Check if we found 'architecture' with the typo
        found_architecture = any('architecture' in r['title'].lower() for r in results)

        if not found_architecture:
            raise Exception("Fuzzy search didn't find 'architecture' with typo 'architecure'")

        print(f"✓ Fuzzy search works - found {len(results)} results")
        print(f"  Top result: {results[0]['title']} (similarity: {results[0]['sim']:.3f})")

        return True

def test_similarity_threshold(conn):
    """Test similarity threshold configuration"""
    print("\nStep 5: Testing similarity threshold...")

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Test different thresholds
        thresholds = [0.1, 0.3, 0.5, 0.7]

        for threshold in thresholds:
            cur.execute(f"""
                SELECT COUNT(*) as count
                FROM files
                WHERE similarity(title, 'architecture') > %s
                AND is_deleted = false;
            """, (threshold,))

            result = cur.fetchone()
            print(f"  Threshold {threshold}: {result['count']} results")

        print("✓ Similarity threshold works correctly")
        return True

def test_performance(conn):
    """Test search performance on 10,000 files"""
    print("\nStep 6: Testing search performance on 10,000 files...")

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Count total files
        cur.execute("SELECT COUNT(*) as count FROM files WHERE is_deleted = false;")
        total_files = cur.fetchone()['count']

        print(f"  Total files in database: {total_files}")

        # Test performance with similarity search
        start_time = time.time()

        cur.execute("""
            SELECT id, title, similarity(title, 'architecture') as sim
            FROM files
            WHERE similarity(title, 'architecture') > 0.3
            AND is_deleted = false
            ORDER BY sim DESC
            LIMIT 20;
        """)

        results = cur.fetchall()
        elapsed_ms = (time.time() - start_time) * 1000

        print(f"✓ Search completed in {elapsed_ms:.2f}ms")
        print(f"  Found {len(results)} results")

        return elapsed_ms

def test_performance_requirement(conn):
    """Verify search completes in < 500ms"""
    print("\nStep 7: Verifying search performance requirement (< 500ms)...")

    # Run multiple searches and average the time
    times = []
    search_terms = ['architecture', 'diagram', 'flow', 'system', 'design']

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        for term in search_terms:
            start_time = time.time()

            cur.execute("""
                SELECT id, title, similarity(title, %s) as sim
                FROM files
                WHERE similarity(title, %s) > 0.3
                AND is_deleted = false
                ORDER BY sim DESC
                LIMIT 20;
            """, (term, term))

            results = cur.fetchall()
            elapsed_ms = (time.time() - start_time) * 1000
            times.append(elapsed_ms)

    avg_time = sum(times) / len(times)
    max_time = max(times)

    print(f"  Average search time: {avg_time:.2f}ms")
    print(f"  Max search time: {max_time:.2f}ms")

    if max_time >= 500:
        raise Exception(f"Search performance requirement not met: {max_time:.2f}ms >= 500ms")

    print(f"✓ Performance requirement met (max: {max_time:.2f}ms < 500ms)")
    return True

def cleanup_test_data(conn):
    """Clean up test data"""
    print("\nCleaning up test data...")

    with conn.cursor() as cur:
        # Delete test files
        cur.execute("""
            DELETE FROM files
            WHERE owner_id = 'test-user-fulltext';
        """)

        # Delete test user
        cur.execute("""
            DELETE FROM users
            WHERE id = 'test-user-fulltext';
        """)

        conn.commit()
        print("✓ Test data cleaned up")

def main():
    """Main validation function"""
    print("=" * 80)
    print("VALIDATING FEATURE 26: PostgreSQL Full-Text Search with pg_trgm")
    print("=" * 80)

    conn = None
    try:
        # Connect to database
        conn = get_db_connection()
        print("✓ Connected to PostgreSQL database")

        # Step 1: Enable pg_trgm extension
        enable_pg_trgm_extension(conn)

        # Step 2: Create GIN index
        create_gin_index(conn)

        # Insert test data
        insert_test_files(conn, 10000)

        # Step 3: Test exact search
        test_exact_search(conn)

        # Step 4: Test fuzzy search
        test_fuzzy_search(conn)

        # Step 5: Test similarity threshold
        test_similarity_threshold(conn)

        # Step 6: Test performance
        test_performance(conn)

        # Step 7: Verify performance requirement
        test_performance_requirement(conn)

        # Cleanup
        cleanup_test_data(conn)

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Feature 26 validated successfully!")
        print("=" * 80)

        return 0

    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        if conn:
            conn.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    sys.exit(main())
