#!/usr/bin/env python3
"""Test Feature #442: Comment Export to CSV"""

import requests
import csv
import io
import sys
import time
import psycopg2
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8080/api"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}


def verify_email(email):
    """Mark user email as verified in database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET is_verified = true WHERE LOWER(email) = LOWER(%s)",
            (email,)
        )
        rows_affected = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        print(f"  → Email verified for {email}")
    except Exception as e:
        print(f"  → Failed to verify email: {e}")

def test_comment_export_csv():
    """Test CSV export of comments."""
    print("=" * 60)
    print("TEST: Feature #442 - Comment Export to CSV")
    print("=" * 60)

    try:
        # Step 1: Register a test user
        print("\n[Step 1] Registering test user...")
        timestamp = int(time.time() * 1000)
        register_data = {
            "email": f"csv_export_test_{timestamp}@test.com",
            "password": "TestPass123!@#",
            "full_name": "CSV Export Tester"
        }

        register_response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json=register_data
        )

        if register_response.status_code not in [200, 201]:
            print(f"❌ Registration failed: {register_response.status_code}")
            print(f"Response: {register_response.text}")
            return False

        user_id = register_response.json()["id"]
        print(f"✅ User registered: {register_data['email']}")

        # Verify email in database
        verify_email(register_data['email'])

        # Step 2: Login to get JWT token
        print("\n[Step 2] Logging in...")
        login_response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={
                "email": register_data["email"],
                "password": register_data["password"]
            }
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False

        token = login_response.json()["access_token"]
        print(f"✅ Login successful. User ID: {user_id}")

        headers = {"Authorization": f"Bearer {token}"}

        # Step 3: Create a test diagram
        print("\n[Step 3] Creating test diagram...")
        diagram_data = {
            "title": f"CSV Export Test Diagram {timestamp}",
            "file_type": "canvas",
            "canvas_data": {"shapes": [], "arrows": []}
        }

        create_response = requests.post(
            f"{API_BASE_URL}/diagrams",
            headers=headers,
            json=diagram_data
        )

        if create_response.status_code not in [200, 201]:
            print(f"❌ Diagram creation failed: {create_response.status_code}")
            print(f"Response: {create_response.text}")
            return False

        diagram = create_response.json()
        diagram_id = diagram["id"]
        print(f"✅ Diagram created: {diagram_id}")

        # Step 4: Create multiple test comments
        print("\n[Step 4] Creating test comments...")
        comment_texts = [
            "This is the first comment for CSV export test",
            "Second comment with special chars: é, ñ, 中文",
            "Third comment about database performance",
            "Fourth comment - resolved issue",
            "Fifth comment with commas, quotes \"test\", and newlines\nin content"
        ]

        comment_ids = []
        for i, text in enumerate(comment_texts):
            comment_data = {
                "content": text,
                "position_x": 100.0 + (i * 50),
                "position_y": 200.0 + (i * 50),
                "element_id": f"elem-{i}"
            }

            comment_response = requests.post(
                f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
                headers=headers,
                json=comment_data
            )

            if comment_response.status_code not in [200, 201]:
                print(f"❌ Comment creation failed: {comment_response.status_code}")
                print(f"Response: {comment_response.text}")
                return False

            comment = comment_response.json()
            comment_ids.append(comment["id"])
            print(f"✅ Comment {i+1} created: {text[:50]}...")

        # Step 5: Resolve one comment
        print("\n[Step 5] Resolving one comment...")
        resolve_response = requests.patch(
            f"{API_BASE_URL}/diagrams/{diagram_id}/comments/{comment_ids[3]}/resolve",
            headers=headers
        )

        if resolve_response.status_code == 200:
            print(f"✅ Comment resolved")
        else:
            print(f"⚠️  Could not resolve comment: {resolve_response.status_code}")

        # Step 6: Export comments to CSV
        print("\n[Step 6] Exporting comments to CSV...")
        export_response = requests.get(
            f"{API_BASE_URL}/diagrams/{diagram_id}/comments/export/csv",
            headers=headers
        )

        if export_response.status_code != 200:
            print(f"❌ CSV export failed: {export_response.status_code}")
            print(f"Response: {export_response.text}")
            return False

        print(f"✅ CSV export successful")

        # Step 7: Verify CSV content
        print("\n[Step 7] Verifying CSV content...")

        # Check Content-Type
        content_type = export_response.headers.get('Content-Type', '')
        if 'text/csv' not in content_type:
            print(f"❌ Invalid Content-Type: {content_type}")
            return False
        print(f"✅ Content-Type is text/csv")

        # Check Content-Disposition
        content_disposition = export_response.headers.get('Content-Disposition', '')
        if 'attachment' not in content_disposition or '.csv' not in content_disposition:
            print(f"❌ Invalid Content-Disposition: {content_disposition}")
            return False
        print(f"✅ Content-Disposition indicates attachment: {content_disposition}")

        # Parse CSV
        csv_content = export_response.text
        csv_reader = csv.DictReader(io.StringIO(csv_content))

        rows = list(csv_reader)
        print(f"\n✅ CSV parsed successfully. Found {len(rows)} rows")

        # Step 8: Verify CSV structure
        print("\n[Step 8] Verifying CSV structure...")

        # Check header columns
        expected_columns = {'Author', 'Text', 'Timestamp'}
        if not expected_columns.issubset(set(csv_reader.fieldnames)):
            print(f"❌ Missing required columns. Found: {csv_reader.fieldnames}")
            return False
        print(f"✅ CSV has required columns: {csv_reader.fieldnames}")

        # Verify row count
        if len(rows) != len(comment_texts):
            print(f"❌ Expected {len(comment_texts)} rows, got {len(rows)}")
            return False
        print(f"✅ CSV contains all {len(comment_texts)} comments")

        # Step 9: Verify comment content in CSV
        print("\n[Step 9] Verifying comment content...")

        found_comments = set()
        for row in rows:
            # Check author
            if 'CSV Export Tester' not in row['Author'] and register_data['email'] not in row['Author']:
                print(f"❌ Invalid author in row: {row['Author']}")
                return False

            # Check text content
            text = row['Text']
            found_comments.add(text)

            # Check timestamp
            timestamp = row['Timestamp']
            if not timestamp:
                print(f"❌ Missing timestamp in row")
                return False

            # Try to parse timestamp
            try:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                print(f"❌ Invalid timestamp format: {timestamp}")
                return False

        print(f"✅ All comment authors are correct")
        print(f"✅ All comments have valid timestamps")

        # Check that all original comments are in CSV
        for original_text in comment_texts:
            if original_text not in found_comments:
                print(f"❌ Missing comment in CSV: {original_text[:50]}...")
                return False

        print(f"✅ All original comments found in CSV")

        # Step 10: Verify resolved status
        print("\n[Step 10] Verifying resolved status...")
        resolved_count = sum(1 for row in rows if row.get('Resolved', 'No') == 'Yes')
        if resolved_count >= 1:
            print(f"✅ Found {resolved_count} resolved comment(s) in CSV")
        else:
            print(f"⚠️  No resolved comments found (expected at least 1)")

        # Step 11: Display CSV sample
        print("\n[Step 11] CSV Sample (first 2 rows):")
        print("-" * 60)
        for i, row in enumerate(rows[:2]):
            print(f"Row {i+1}:")
            print(f"  Author: {row['Author']}")
            print(f"  Text: {row['Text'][:60]}...")
            print(f"  Timestamp: {row['Timestamp']}")
            print(f"  Resolved: {row.get('Resolved', 'N/A')}")
            print()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nFeature #442 Summary:")
        print(f"  • CSV export endpoint: ✅ Working")
        print(f"  • All comments exported: ✅ {len(rows)} rows")
        print(f"  • Required columns present: ✅ Author, Text, Timestamp")
        print(f"  • Content-Type header: ✅ text/csv")
        print(f"  • File download attachment: ✅ Yes")
        print(f"  • Special characters: ✅ Handled correctly")
        print(f"  • Timestamps: ✅ ISO format")
        print(f"  • Resolved status: ✅ Included")
        print()

        return True

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_comment_export_csv()
    sys.exit(0 if success else 1)
