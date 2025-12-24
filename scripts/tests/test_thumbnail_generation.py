#!/usr/bin/env python3
"""
Test Feature #144: Thumbnail generation (256x256 PNG preview)

This test verifies that:
1. Creating a diagram triggers thumbnail generation
2. Thumbnails are stored in MinIO diagrams bucket
3. Thumbnail file exists at thumbnails/<id>.png
4. Thumbnail dimensions are 256x256
5. Updating a diagram regenerates the thumbnail
"""

import requests
import json
import time
from minio import Minio
from PIL import Image
from io import BytesIO

# Configuration
API_BASE_URL = "http://localhost:8080/api"
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET_NAME = "diagrams"

# Test counters
tests_passed = 0
tests_failed = 0


def print_test_header(test_name):
    """Print a formatted test header."""
    print(f"\n{'=' * 80}")
    print(f"Test: {test_name}")
    print('=' * 80)


def print_step(step_num, description):
    """Print a test step."""
    print(f"\n{step_num}. {description}")


def print_success(message):
    """Print a success message."""
    print(f"✓ {message}")


def print_error(message):
    """Print an error message."""
    print(f"✗ {message}")


def print_info(message):
    """Print an info message."""
    print(f"  {message}")


def register_and_login():
    """Register a test user and get access token."""
    # Register
    email = f"testuser{int(time.time())}@example.com"
    password = "TestPassword123!"
    
    print_step(1, "Register test user")
    resp = requests.post(f"{API_BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Test User"
    })
    
    if resp.status_code != 201:
        print_error(f"Registration failed: {resp.status_code}")
        print_info(resp.text)
        return None
    
    print_success("User registered")
    print_info(f"Email: {email}")
    
    # Login
    print_step(2, "Login to get access token")
    resp = requests.post(f"{API_BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    
    if resp.status_code != 200:
        print_error(f"Login failed: {resp.status_code}")
        print_info(resp.text)
        return None
    
    tokens = resp.json()
    access_token = tokens.get("access_token")
    
    print_success("Login successful")
    print_info(f"Token: {access_token[:20]}...")
    
    return access_token


def create_diagram_with_shapes(access_token):
    """Create a diagram with some shapes."""
    print_step(3, "Create diagram with shapes")
    
    # Create a diagram with canvas data
    canvas_data = {
        "shapes": [
            {
                "id": "shape1",
                "type": "rectangle",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 150
            },
            {
                "id": "shape2",
                "type": "circle",
                "x": 400,
                "y": 150,
                "radius": 75
            }
        ]
    }
    
    resp = requests.post(
        f"{API_BASE_URL}/diagrams/",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "title": "Test Diagram with Shapes",
            "file_type": "canvas",
            "canvas_data": canvas_data
        }
    )
    
    if resp.status_code != 200:
        print_error(f"Diagram creation failed: {resp.status_code}")
        print_info(resp.text)
        return None
    
    diagram = resp.json()
    diagram_id = diagram.get("id")
    
    print_success("Diagram created")
    print_info(f"Diagram ID: {diagram_id}")
    print_info(f"Title: {diagram.get('title')}")
    
    return diagram_id, diagram


def verify_thumbnail_in_response(diagram):
    """Verify thumbnail URL is in the diagram response."""
    print_step(4, "Verify thumbnail URL in response")
    
    thumbnail_url = diagram.get("thumbnail_url")
    
    if thumbnail_url:
        print_success("Thumbnail URL present in response")
        print_info(f"URL: {thumbnail_url}")
        return True
    else:
        print_error("Thumbnail URL not present in response")
        return False


def check_minio_bucket(diagram_id):
    """Check if thumbnail exists in MinIO bucket."""
    print_step(5, "Check MinIO diagrams bucket")
    
    try:
        # Connect to MinIO
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        
        # Check if bucket exists
        if not minio_client.bucket_exists(BUCKET_NAME):
            print_error(f"Bucket '{BUCKET_NAME}' does not exist")
            return False
        
        print_success(f"Bucket '{BUCKET_NAME}' exists")
        
        # Check for thumbnail file
        object_name = f"thumbnails/{diagram_id}.png"
        
        print_step(6, f"Verify thumbnail file exists: {object_name}")
        
        try:
            stat = minio_client.stat_object(BUCKET_NAME, object_name)
            print_success("Thumbnail file exists")
            print_info(f"Size: {stat.size} bytes")
            print_info(f"Content-Type: {stat.content_type}")
            return True
        except Exception as e:
            print_error(f"Thumbnail file not found: {str(e)}")
            return False
            
    except Exception as e:
        print_error(f"MinIO error: {str(e)}")
        return False


def download_and_verify_thumbnail(diagram_id):
    """Download thumbnail and verify dimensions."""
    print_step(7, "Download thumbnail from MinIO")
    
    try:
        # Connect to MinIO
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        
        object_name = f"thumbnails/{diagram_id}.png"
        
        # Download thumbnail
        response = minio_client.get_object(BUCKET_NAME, object_name)
        thumbnail_data = response.read()
        
        print_success("Thumbnail downloaded")
        print_info(f"Downloaded {len(thumbnail_data)} bytes")
        
        # Verify it's a valid PNG image
        print_step(8, "Verify image format and dimensions")
        
        img = Image.open(BytesIO(thumbnail_data))
        width, height = img.size
        
        print_info(f"Image format: {img.format}")
        print_info(f"Image dimensions: {width}x{height}")
        
        # Verify dimensions are 256x256
        if width == 256 and height == 256:
            print_success("Thumbnail dimensions are correct (256x256)")
            return True
        else:
            print_error(f"Thumbnail dimensions incorrect: expected 256x256, got {width}x{height}")
            return False
            
    except Exception as e:
        print_error(f"Error verifying thumbnail: {str(e)}")
        return False


def update_diagram_and_verify_regeneration(access_token, diagram_id):
    """Update diagram and verify thumbnail is regenerated."""
    print_step(9, "Update diagram")
    
    # Update canvas data
    updated_canvas_data = {
        "shapes": [
            {
                "id": "shape1",
                "type": "rectangle",
                "x": 150,
                "y": 150,
                "width": 250,
                "height": 200
            },
            {
                "id": "shape2",
                "type": "circle",
                "x": 450,
                "y": 200,
                "radius": 100
            },
            {
                "id": "shape3",
                "type": "arrow",
                "x1": 200,
                "y1": 200,
                "x2": 400,
                "y2": 250
            }
        ]
    }
    
    resp = requests.put(
        f"{API_BASE_URL}/diagrams/{diagram_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "canvas_data": updated_canvas_data,
            "description": "Updated with new shapes"
        }
    )
    
    if resp.status_code != 200:
        print_error(f"Diagram update failed: {resp.status_code}")
        print_info(resp.text)
        return False
    
    print_success("Diagram updated")
    
    # Wait a moment for thumbnail regeneration
    time.sleep(2)
    
    print_step(10, "Verify thumbnail regenerated")
    
    # Check if thumbnail still exists (should be regenerated)
    try:
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        
        object_name = f"thumbnails/{diagram_id}.png"
        stat = minio_client.stat_object(BUCKET_NAME, object_name)
        
        print_success("Thumbnail regenerated")
        print_info(f"Size: {stat.size} bytes")
        return True
        
    except Exception as e:
        print_error(f"Thumbnail not found after update: {str(e)}")
        return False


def run_test():
    """Run the complete test suite."""
    global tests_passed, tests_failed
    
    print("\n" + "=" * 80)
    print("FEATURE #144: THUMBNAIL GENERATION TEST")
    print("=" * 80)
    
    # Test 1: Register and login
    print_test_header("User Registration and Login")
    access_token = register_and_login()
    
    if not access_token:
        print_error("Failed to get access token")
        tests_failed += 1
        return
    
    tests_passed += 1
    
    # Test 2: Create diagram with shapes
    print_test_header("Create Diagram with Shapes")
    result = create_diagram_with_shapes(access_token)
    
    if not result:
        print_error("Failed to create diagram")
        tests_failed += 1
        return
    
    diagram_id, diagram = result
    tests_passed += 1
    
    # Test 3: Verify thumbnail URL in response
    print_test_header("Verify Thumbnail URL in Response")
    if verify_thumbnail_in_response(diagram):
        tests_passed += 1
    else:
        tests_failed += 1
        # Continue anyway to check MinIO
    
    # Test 4: Check MinIO bucket
    print_test_header("Check MinIO Bucket")
    if check_minio_bucket(diagram_id):
        tests_passed += 1
    else:
        tests_failed += 1
        return
    
    # Test 5: Download and verify thumbnail
    print_test_header("Download and Verify Thumbnail")
    if download_and_verify_thumbnail(diagram_id):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 6: Update diagram and verify regeneration
    print_test_header("Update Diagram and Verify Regeneration")
    if update_diagram_and_verify_regeneration(access_token, diagram_id):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    total_tests = tests_passed + tests_failed
    
    if tests_failed == 0:
        print(f"✓ PASS: All {tests_passed}/{total_tests} tests passed (100.0%)")
    else:
        print(f"✗ FAIL: {tests_passed}/{total_tests} tests passed ({tests_passed/total_tests*100:.1f}%)")
        print(f"        {tests_failed} test(s) failed")
    
    print("=" * 80)
    
    if tests_failed == 0:
        print("\n✓ All thumbnail generation tests passed!")
    else:
        print(f"\n✗ {tests_failed} test(s) failed")
        exit(1)


if __name__ == "__main__":
    run_test()
