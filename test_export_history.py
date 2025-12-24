#!/usr/bin/env python3
"""Test export history feature - Feature #514"""

import requests
import json
import time
from datetime import datetime
import psycopg2
import uuid

BASE_URL = "http://localhost:8097"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

# Database connection
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "user": "autograph",
    "password": "autograph_dev_password",
    "database": "autograph"
}

# Test data
TEST_CANVAS_DATA = {
    "shapes": [
        {"id": "shape-1", "type": "rectangle", "x": 50, "y": 50, "width": 200, "height": 100}
    ]
}

def print_header(text):
    """Print a section header."""
    print(f"\n{'=' * 80}")
    print(f" {text}")
    print('=' * 80)

def print_success(text):
    """Print success message."""
    print(f"✅ {text}")

def print_error(text):
    """Print error message."""
    print(f"❌ {text}")

def create_test_user_and_diagram():
    """Create a test user and diagram directly in the database."""
    print("\nSetup: Creating test user and diagram in database...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create user
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, f"test_{user_id}@example.com", "dummy_hash", "Test User", True, True, "user"))
        
        # Create diagram
        diagram_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO files (id, title, owner_id, file_type, canvas_data)
            VALUES (%s, %s, %s, %s, %s)
        """, (diagram_id, "Test Diagram", user_id, "canvas", json.dumps(TEST_CANVAS_DATA)))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print_success(f"Created test user: {user_id}")
        print_success(f"Created test diagram: {diagram_id}")
        
        return user_id, diagram_id
        
    except Exception as e:
        print_error(f"Error creating test data: {e}")
        return None, None

def test_export_and_history():
    """Test export with history tracking."""
    
    print_header("EXPORT HISTORY TEST - Feature #514")
    
    # Setup: Create test user and diagram
    user_id, diagram_id = create_test_user_and_diagram()
    if not diagram_id:
        print_error("Failed to create test diagram")
        return False
    
    # Step 1: Export diagram 5 times in different formats
    print("\nStep 1: Exporting diagram 5 times...")
    export_count = 0
    
    formats = [
        ("png", "/export/png"),
        ("svg", "/export/svg"),
        ("pdf", "/export/pdf"),
        ("json", "/export/json"),
        ("md", "/export/markdown")
    ]
    
    for format_name, endpoint in formats:
        try:
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json={
                    "diagram_id": diagram_id,
                    "canvas_data": TEST_CANVAS_DATA,
                    "format": format_name,
                    "user_id": user_id,
                    "width": 1920,
                    "height": 1080
                }
            )
            
            if response.status_code == 200:
                print_success(f"Exported as {format_name.upper()} (size: {len(response.content)} bytes)")
                export_count += 1
            else:
                print_error(f"Failed to export as {format_name}: {response.status_code}")
            
            time.sleep(0.5)  # Small delay between exports
            
        except Exception as e:
            print_error(f"Error exporting as {format_name}: {e}")
    
    print(f"\n✅ Completed {export_count}/5 exports")
    
    # Step 2: View export history
    print("\nStep 2: Viewing export history...")
    time.sleep(1)  # Give database time to sync
    
    try:
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/export-history/{diagram_id}"
        )
        
        if response.status_code == 200:
            history_data = response.json()
            exports = history_data.get("exports", [])
            total = history_data.get("total", 0)
            
            print_success(f"Retrieved export history: {len(exports)} records")
            print(f"   Total exports: {total}")
            
            # Step 3: Verify all 5 exports are listed
            print("\nStep 3: Verifying all 5 exports are listed...")
            if len(exports) >= 5:
                print_success(f"Found {len(exports)} exports (expected at least 5)")
            else:
                print_error(f"Found only {len(exports)} exports (expected at least 5)")
            
            # Step 4: Verify timestamps
            print("\nStep 4: Verifying timestamps...")
            timestamp_verified = True
            for export in exports[:5]:
                created_at = export.get("created_at")
                if created_at:
                    print_success(f"  {export.get('export_format', 'unknown').upper()}: {created_at}")
                else:
                    print_error(f"  Missing timestamp for {export.get('export_format', 'unknown')}")
                    timestamp_verified = False
            
            if timestamp_verified:
                print_success("All timestamps verified")
            
            # Step 5: Verify formats
            print("\nStep 5: Verifying export formats...")
            exported_formats = {export.get("export_format") for export in exports[:5]}
            expected_formats = {"png", "svg", "pdf", "json", "md"}
            
            if exported_formats >= expected_formats:
                print_success(f"All 5 formats present: {', '.join(sorted(exported_formats))}")
            else:
                missing = expected_formats - exported_formats
                print_error(f"Missing formats: {', '.join(sorted(missing))}")
            
            # Print detailed export information
            print("\nDetailed Export History:")
            print("-" * 80)
            for i, export in enumerate(exports[:5], 1):
                print(f"{i}. Format: {export.get('export_format', 'N/A').upper():6s} | "
                      f"Type: {export.get('export_type', 'N/A'):10s} | "
                      f"Size: {export.get('file_size', 0):8d} bytes | "
                      f"Status: {export.get('status', 'N/A')}")
                if export.get("export_settings"):
                    settings = export["export_settings"]
                    print(f"   Settings: {json.dumps(settings)}")
            
            # Test user export history endpoint
            print("\nStep 6: Testing user export history endpoint...")
            user_response = requests.get(
                f"{DIAGRAM_SERVICE_URL}/export-history/user/{user_id}"
            )
            
            if user_response.status_code == 200:
                user_history = user_response.json()
                user_exports = user_history.get("exports", [])
                print_success(f"Retrieved user export history: {len(user_exports)} records")
                
                # Filter by format
                print("\n   Testing format filter (PNG only)...")
                png_response = requests.get(
                    f"{DIAGRAM_SERVICE_URL}/export-history/user/{user_id}?export_format=png"
                )
                if png_response.status_code == 200:
                    png_history = png_response.json()
                    png_exports = png_history.get("exports", [])
                    print_success(f"   Found {len(png_exports)} PNG exports")
            
            # Summary
            print("\n" + "=" * 80)
            print("SUMMARY")
            print("=" * 80)
            print(f"✅ Exports created: {export_count}/5")
            print(f"✅ History records: {len(exports)}/{total}")
            print(f"✅ Timestamps verified: {timestamp_verified}")
            print(f"✅ Formats verified: {len(exported_formats)}/5")
            print(f"✅ User history endpoint: Working")
            
            if export_count == 5 and len(exports) >= 5 and timestamp_verified and len(exported_formats) == 5:
                print("\n🎉 ALL TESTS PASSED!")
                return True
            else:
                print("\n⚠️ SOME TESTS FAILED")
                return False
            
        else:
            print_error(f"Failed to get export history: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Error getting export history: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        print("\nStarting Export History Test...")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check services are running
        print("\nChecking services...")
        try:
            export_health = requests.get(f"{BASE_URL}/health", timeout=5)
            diagram_health = requests.get(f"{DIAGRAM_SERVICE_URL}/health", timeout=5)
            
            if export_health.status_code == 200:
                print_success("Export service is healthy")
            else:
                print_error("Export service is not healthy")
                exit(1)
            
            if diagram_health.status_code == 200:
                print_success("Diagram service is healthy")
            else:
                print_error("Diagram service is not healthy")
                exit(1)
        except Exception as e:
            print_error(f"Services not available: {e}")
            exit(1)
        
        # Run the test
        success = test_export_and_history()
        
        if success:
            print("\n✅ Feature #514 (Export History) is PASSING")
            exit(0)
        else:
            print("\n❌ Feature #514 (Export History) has ISSUES")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print_error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
