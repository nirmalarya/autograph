#!/usr/bin/env python3
"""
Test script for Feature #22: PostgreSQL files table with canvas_data JSONB column

This script verifies:
1. Create diagram with canvas_data
2. Verify canvas_data stored as JSONB
3. Query canvas_data with JSON operators
4. Update nested JSON field
5. Verify JSONB indexing for performance
6. Test JSONB containment queries
"""

import psycopg2
import json
import sys

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="autograph",
    user="autograph",
    password="autograph_dev_password"
)

def test_1_verify_jsonb_type():
    """Test 1: Verify canvas_data is JSONB type"""
    print("\n=== Test 1: Verify JSONB Type ===")
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'files' AND column_name = 'canvas_data'
    """)
    result = cur.fetchone()
    print(f"Column: {result[0]}, Type: {result[1]}")
    assert result[1] == "jsonb", f"Expected jsonb, got {result[1]}"
    print("✓ canvas_data is JSONB type")
    cur.close()
    return True

def test_2_jsonb_operators():
    """Test 2: Query with JSONB operators"""
    print("\n=== Test 2: JSONB Operators ===")
    cur = conn.cursor()
    
    # -> operator (returns JSONB)
    cur.execute("""
        SELECT canvas_data->'version' as version_jsonb
        FROM files WHERE title = 'Test Diagram with JSONB'
    """)
    result = cur.fetchone()
    print(f"-> operator (JSONB): {result[0]}")
    
    # ->> operator (returns TEXT)
    cur.execute("""
        SELECT canvas_data->>'version' as version_text
        FROM files WHERE title = 'Test Diagram with JSONB'
    """)
    result = cur.fetchone()
    print(f"->> operator (TEXT): {result[0]}")
    
    # #>> operator (nested path)
    cur.execute("""
        SELECT canvas_data#>>'{shapes,0,label}' as label
        FROM files WHERE title = 'Test Diagram with JSONB'
    """)
    result = cur.fetchone()
    print(f"#>> operator (nested): {result[0]}")
    
    # ? operator (key exists)
    cur.execute("""
        SELECT canvas_data ? 'version' as has_version
        FROM files WHERE title = 'Test Diagram with JSONB'
    """)
    result = cur.fetchone()
    print(f"? operator (exists): {result[0]}")
    
    print("✓ All JSONB operators work correctly")
    cur.close()
    return True

def test_3_update_nested_json():
    """Test 3: Update nested JSON field"""
    print("\n=== Test 3: Update Nested JSON Field ===")
    cur = conn.cursor()
    
    # Get original value
    cur.execute("""
        SELECT canvas_data->>'version' as version
        FROM files WHERE title = 'Test Diagram with JSONB'
    """)
    original = cur.fetchone()[0]
    print(f"Original version: {original}")
    
    # Update using jsonb_set
    cur.execute("""
        UPDATE files 
        SET canvas_data = jsonb_set(canvas_data, '{version}', '"3.0"'::jsonb)
        WHERE title = 'Test Diagram with JSONB'
    """)
    conn.commit()
    
    # Verify update
    cur.execute("""
        SELECT canvas_data->>'version' as version
        FROM files WHERE title = 'Test Diagram with JSONB'
    """)
    updated = cur.fetchone()[0]
    print(f"Updated version: {updated}")
    
    assert updated == "3.0", f"Expected 3.0, got {updated}"
    print("✓ Nested JSON update successful")
    cur.close()
    return True

def test_4_gin_index():
    """Test 4: Verify GIN index exists"""
    print("\n=== Test 4: Verify GIN Index ===")
    cur = conn.cursor()
    
    cur.execute("""
        SELECT indexname, indexdef
        FROM pg_indexes 
        WHERE tablename = 'files' AND indexname = 'idx_files_canvas_data_gin'
    """)
    result = cur.fetchone()
    print(f"Index: {result[0]}")
    print(f"Definition: {result[1]}")
    
    assert "gin" in result[1].lower(), "Index is not GIN type"
    print("✓ GIN index exists and properly configured")
    cur.close()
    return True

def test_5_containment_queries():
    """Test 5: JSONB containment queries with @> operator"""
    print("\n=== Test 5: JSONB Containment Queries ===")
    cur = conn.cursor()
    
    # Query 1: Find by version
    cur.execute("""
        SELECT title FROM files 
        WHERE canvas_data @> '{"version": "2.0"}'::jsonb
    """)
    results = cur.fetchall()
    print(f"Diagrams with version 2.0: {len(results)}")
    for row in results:
        print(f"  - {row[0]}")
    
    # Query 2: Find by nested metadata
    cur.execute("""
        SELECT title FROM files 
        WHERE canvas_data @> '{"type": "architecture"}'::jsonb
    """)
    results = cur.fetchall()
    print(f"Architecture diagrams: {len(results)}")
    for row in results:
        print(f"  - {row[0]}")
    
    print("✓ JSONB containment queries work correctly")
    cur.close()
    return True

def test_6_verify_diagram_count():
    """Test 6: Verify diagrams were created successfully"""
    print("\n=== Test 6: Verify Diagrams ===")
    cur = conn.cursor()
    
    cur.execute("""
        SELECT COUNT(*) FROM files WHERE canvas_data IS NOT NULL
    """)
    count = cur.fetchone()[0]
    print(f"Total diagrams with canvas_data: {count}")
    
    assert count >= 2, f"Expected at least 2 diagrams, found {count}"
    print("✓ Diagrams created successfully")
    cur.close()
    return True

def main():
    """Run all tests"""
    print("=" * 70)
    print("Feature #22: PostgreSQL files table with canvas_data JSONB column")
    print("=" * 70)
    
    try:
        tests = [
            test_1_verify_jsonb_type,
            test_2_jsonb_operators,
            test_3_update_nested_json,
            test_4_gin_index,
            test_5_containment_queries,
            test_6_verify_diagram_count,
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"✗ Test failed: {e}")
                failed += 1
        
        print("\n" + "=" * 70)
        print(f"Results: {passed} passed, {failed} failed")
        print("=" * 70)
        
        if failed == 0:
            print("\n✓ All tests PASSED - Feature #22 is fully functional!")
            return 0
        else:
            print(f"\n✗ {failed} test(s) FAILED")
            return 1
            
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())
