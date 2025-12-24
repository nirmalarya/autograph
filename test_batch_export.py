#!/usr/bin/env python3
"""
Test script for Batch Export to ZIP feature.

Tests:
1. Create multiple test diagrams in database
2. Call batch export endpoint with 10 diagrams
3. Verify ZIP file is created
4. Extract ZIP and verify 10 files present
5. Verify each file has correct format and content
"""

import requests
import json
import psycopg2
import uuid
from datetime import datetime
import zipfile
import io
import os
import tempfile

# Configuration
EXPORT_SERVICE_URL = "http://localhost:8097"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}

# Test canvas data
TEST_CANVAS_DATA = {
    "shapes": [
        {"id": "shape1", "type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 150},
        {"id": "shape2", "type": "circle", "x": 400, "y": 200, "radius": 75},
        {"id": "shape3", "type": "text", "x": 250, "y": 350, "text": "Test Diagram"}
    ],
    "version": "1.0"
}


def create_test_user_and_diagrams(num_diagrams=10):
    """Create test user and multiple diagrams in database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Create test user if not exists
    user_id = str(uuid.uuid4())
    email = f"batch_test_{user_id[:8]}@test.com"
    
    try:
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            email,
            "$2b$12$dummy_hash_for_testing",
            "Batch Test User",
            True,
            True,
            "user"
        ))
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        # User already exists, that's fine
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user_id = cursor.fetchone()[0]
    else:
        conn.commit()
    
    # Create multiple test diagrams
    diagram_ids = []
    for i in range(num_diagrams):
        diagram_id = str(uuid.uuid4())
        title = f"Test Diagram {i+1}"
        
        try:
            cursor.execute("""
                INSERT INTO files (id, title, owner_id, file_type, canvas_data, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                diagram_id,
                title,
                user_id,
                "canvas",
                json.dumps(TEST_CANVAS_DATA),
                datetime.utcnow(),
                datetime.utcnow()
            ))
            conn.commit()
            diagram_ids.append((diagram_id, title))
            print(f"✓ Created diagram: {title} ({diagram_id})")
        except Exception as e:
            print(f"✗ Failed to create diagram {title}: {e}")
            conn.rollback()
    
    cursor.close()
    conn.close()
    
    return user_id, diagram_ids


def test_batch_export_png(diagrams, user_id):
    """Test batch export to ZIP with PNG format."""
    print("\n" + "="*80)
    print("TEST 1: Batch Export - PNG Format")
    print("="*80)
    
    # Prepare batch export request
    batch_request = {
        "diagrams": [
            {
                "diagram_id": diagram_id,
                "title": title,
                "canvas_data": TEST_CANVAS_DATA
            }
            for diagram_id, title in diagrams
        ],
        "format": "png",
        "user_id": user_id,
        "width": 1920,
        "height": 1080,
        "scale": 2,
        "quality": "high",
        "background": "white"
    }
    
    print(f"\nExporting {len(diagrams)} diagrams as PNG to ZIP...")
    response = requests.post(
        f"{EXPORT_SERVICE_URL}/export/batch",
        json=batch_request,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"✗ Batch export failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return False
    
    print(f"✓ Batch export succeeded (Status: {response.status_code})")
    
    # Verify it's a ZIP file
    if response.headers.get('content-type') != 'application/zip':
        print(f"✗ Response is not a ZIP file: {response.headers.get('content-type')}")
        return False
    
    print(f"✓ Response is a ZIP file")
    
    # Save ZIP to temporary file and extract
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
        temp_file.write(response.content)
        zip_path = temp_file.name
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            # List files in ZIP
            file_list = zipf.namelist()
            print(f"\n✓ ZIP contains {len(file_list)} files:")
            for filename in file_list:
                file_info = zipf.getinfo(filename)
                print(f"  - {filename} ({file_info.file_size} bytes)")
            
            # Verify we have the expected number of files
            if len(file_list) != len(diagrams):
                print(f"✗ Expected {len(diagrams)} files, found {len(file_list)}")
                return False
            
            print(f"\n✓ All {len(diagrams)} diagrams present in ZIP")
            
            # Verify all files are PNG
            png_files = [f for f in file_list if f.endswith('.png')]
            if len(png_files) != len(diagrams):
                print(f"✗ Not all files are PNG: {len(png_files)}/{len(diagrams)}")
                return False
            
            print(f"✓ All files have .png extension")
            
            # Verify each file is valid PNG
            for filename in png_files:
                file_data = zipf.read(filename)
                # Check PNG magic number
                if not file_data.startswith(b'\x89PNG\r\n\x1a\n'):
                    print(f"✗ {filename} is not a valid PNG file")
                    return False
            
            print(f"✓ All PNG files are valid")
            
            # Extract to temporary directory for verification
            extract_dir = tempfile.mkdtemp()
            zipf.extractall(extract_dir)
            print(f"\n✓ Extracted ZIP to: {extract_dir}")
            
            return True
            
    finally:
        # Clean up
        os.unlink(zip_path)


def test_batch_export_svg(diagrams, user_id):
    """Test batch export to ZIP with SVG format."""
    print("\n" + "="*80)
    print("TEST 2: Batch Export - SVG Format")
    print("="*80)
    
    # Use only first 5 diagrams for SVG test
    test_diagrams = diagrams[:5]
    
    batch_request = {
        "diagrams": [
            {
                "diagram_id": diagram_id,
                "title": title,
                "canvas_data": TEST_CANVAS_DATA
            }
            for diagram_id, title in test_diagrams
        ],
        "format": "svg",
        "user_id": user_id,
        "width": 1920,
        "height": 1080
    }
    
    print(f"\nExporting {len(test_diagrams)} diagrams as SVG to ZIP...")
    response = requests.post(
        f"{EXPORT_SERVICE_URL}/export/batch",
        json=batch_request,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"✗ Batch export failed: {response.status_code}")
        return False
    
    print(f"✓ Batch export succeeded")
    
    # Extract and verify SVG files
    zip_data = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_data, 'r') as zipf:
        file_list = zipf.namelist()
        print(f"✓ ZIP contains {len(file_list)} SVG files")
        
        # Verify all are SVG
        svg_files = [f for f in file_list if f.endswith('.svg')]
        if len(svg_files) != len(test_diagrams):
            print(f"✗ Expected {len(test_diagrams)} SVG files, found {len(svg_files)}")
            return False
        
        print(f"✓ All files have .svg extension")
        
        # Verify SVG content
        for filename in svg_files:
            svg_content = zipf.read(filename).decode('utf-8')
            if not svg_content.startswith('<?xml') and '<svg' not in svg_content:
                print(f"✗ {filename} is not valid SVG")
                return False
        
        print(f"✓ All SVG files are valid")
        return True


def test_batch_export_json(diagrams, user_id):
    """Test batch export to ZIP with JSON format."""
    print("\n" + "="*80)
    print("TEST 3: Batch Export - JSON Format")
    print("="*80)
    
    # Use only first 3 diagrams for JSON test
    test_diagrams = diagrams[:3]
    
    batch_request = {
        "diagrams": [
            {
                "diagram_id": diagram_id,
                "title": title,
                "canvas_data": TEST_CANVAS_DATA
            }
            for diagram_id, title in test_diagrams
        ],
        "format": "json",
        "user_id": user_id
    }
    
    print(f"\nExporting {len(test_diagrams)} diagrams as JSON to ZIP...")
    response = requests.post(
        f"{EXPORT_SERVICE_URL}/export/batch",
        json=batch_request,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"✗ Batch export failed: {response.status_code}")
        return False
    
    print(f"✓ Batch export succeeded")
    
    # Extract and verify JSON files
    zip_data = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_data, 'r') as zipf:
        file_list = zipf.namelist()
        print(f"✓ ZIP contains {len(file_list)} JSON files")
        
        # Verify all are JSON
        json_files = [f for f in file_list if f.endswith('.json')]
        if len(json_files) != len(test_diagrams):
            print(f"✗ Expected {len(test_diagrams)} JSON files, found {len(json_files)}")
            return False
        
        print(f"✓ All files have .json extension")
        
        # Verify JSON content
        for filename in json_files:
            try:
                json_content = json.loads(zipf.read(filename).decode('utf-8'))
                if 'shapes' not in json_content:
                    print(f"✗ {filename} missing 'shapes' key")
                    return False
            except json.JSONDecodeError:
                print(f"✗ {filename} is not valid JSON")
                return False
        
        print(f"✓ All JSON files are valid")
        return True


def test_export_history(diagrams, user_id):
    """Verify exports are logged to export_history table."""
    print("\n" + "="*80)
    print("TEST 4: Verify Export History")
    print("="*80)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Check export history for batch exports
    cursor.execute("""
        SELECT COUNT(*) FROM export_history
        WHERE user_id = %s AND export_type = 'batch'
    """, (user_id,))
    
    count = cursor.fetchone()[0]
    print(f"\n✓ Found {count} batch export history entries")
    
    # Get details of recent batch exports
    cursor.execute("""
        SELECT export_format, COUNT(*) as count
        FROM export_history
        WHERE user_id = %s AND export_type = 'batch'
        GROUP BY export_format
        ORDER BY export_format
    """, (user_id,))
    
    results = cursor.fetchall()
    print("\nBatch exports by format:")
    for format_name, count in results:
        print(f"  - {format_name}: {count} exports")
    
    cursor.close()
    conn.close()
    
    return True


def main():
    """Run all batch export tests."""
    print("="*80)
    print("BATCH EXPORT TO ZIP - TEST SUITE")
    print("="*80)
    
    # Check services are healthy
    print("\nChecking services...")
    try:
        response = requests.get(f"{EXPORT_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Export service is healthy")
        else:
            print(f"✗ Export service not healthy: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ Export service not accessible: {e}")
        return
    
    # Create test data
    print("\nSetting up test data...")
    user_id, diagrams = create_test_user_and_diagrams(num_diagrams=10)
    print(f"\n✓ Created {len(diagrams)} test diagrams")
    
    # Run tests
    results = []
    
    # Test 1: PNG batch export
    results.append(("PNG Batch Export", test_batch_export_png(diagrams, user_id)))
    
    # Test 2: SVG batch export
    results.append(("SVG Batch Export", test_batch_export_svg(diagrams, user_id)))
    
    # Test 3: JSON batch export
    results.append(("JSON Batch Export", test_batch_export_json(diagrams, user_id)))
    
    # Test 4: Export history
    results.append(("Export History", test_export_history(diagrams, user_id)))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
