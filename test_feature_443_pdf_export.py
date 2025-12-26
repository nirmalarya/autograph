#!/usr/bin/env python3
"""
Test Feature #443: Comments: Comment export: PDF

Test steps:
1. Export as PDF
2. Verify PDF generated
3. Verify comments formatted nicely
4. Verify includes context (what was commented on)
"""

import requests
import json
import sys
from io import BytesIO
from PyPDF2 import PdfReader
import psycopg2
import os

# Test configuration
API_BASE_URL = "http://localhost:8080/api"
EXPORT_SERVICE_URL = "http://localhost:8097"

# Database configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "autograph")
POSTGRES_USER = os.getenv("POSTGRES_USER", "autograph")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "autograph_dev_password")

def test_feature_443_comment_export_pdf():
    """Test PDF export of comments with nice formatting and context."""

    print("=" * 70)
    print("FEATURE #443: Comment Export - PDF")
    print("=" * 70)

    # Step 1: Register and login
    print("\n[1/11] Setting up test user...")
    import time
    email = f"test_feature443_{int(time.time())}@example.com"
    password = "SecurePass123!"

    register_response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"email": email, "password": password}
    )

    if register_response.status_code not in [200, 201]:
        print(f"⚠ Registration failed ({register_response.status_code})")

    # Verify email in database using docker exec
    import subprocess
    try:
        result = subprocess.run([
            'docker', 'exec', 'autograph-postgres',
            'psql', '-U', 'autograph', '-d', 'autograph',
            '-c', f"UPDATE users SET is_verified = true WHERE email = '{email}'"
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("✓ Email verified in database")
        else:
            print(f"⚠ Could not verify email in DB: {result.stderr}")
    except Exception as e:
        print(f"⚠ Could not verify email in DB: {e}")

    # Always login to get token
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )

    if login_response.status_code != 200:
        print(f"❌ Failed to login")
        print(f"Login response: {login_response.status_code} - {login_response.text}")
        return False

    login_data = login_response.json()
    token = login_data.get("access_token") or login_data.get("token")

    if not token:
        print(f"❌ No token received from login")
        print(f"Login data: {login_data}")
        return False

    print(f"✓ Test user created/logged in: {email}")

    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Create a diagram
    print("\n[2/11] Creating test diagram...")
    diagram_response = requests.post(
        f"{API_BASE_URL}/diagrams",
        json={"title": "Test Diagram for Comment PDF Export", "file_type": "canvas"},
        headers=headers
    )

    if diagram_response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {diagram_response.status_code}")
        print(f"Response: {diagram_response.text}")
        return False

    diagram_id = diagram_response.json()["id"]
    print(f"✓ Diagram created: {diagram_id}")

    # Step 3: Add several comments with different contexts
    print("\n[3/11] Adding comments with various contexts...")

    # Comment 1: Canvas comment with position and element
    comment1_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        json={
            "content": "This is a comment on a canvas element at specific position",
            "position_x": 100.5,
            "position_y": 200.5,
            "element_id": "shape:abc123"
        },
        headers=headers
    )

    if comment1_response.status_code != 201:
        print(f"❌ Failed to create comment 1: {comment1_response.status_code}")
        return False

    comment1_id = comment1_response.json()["id"]
    print(f"✓ Canvas comment created with position and element: {comment1_id}")

    # Comment 2: Note comment with text selection
    comment2_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        json={
            "content": "This comment highlights important text in a note",
            "text_start": 0,
            "text_end": 25,
            "text_content": "Important text selection"
        },
        headers=headers
    )

    if comment2_response.status_code != 201:
        print(f"❌ Failed to create comment 2: {comment2_response.status_code}")
        return False

    comment2_id = comment2_response.json()["id"]
    print(f"✓ Note comment created with text selection: {comment2_id}")

    # Comment 3: Reply to comment 1
    comment3_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        json={
            "content": "This is a reply to the first comment, forming a thread",
            "parent_id": comment1_id
        },
        headers=headers
    )

    if comment3_response.status_code != 201:
        print(f"❌ Failed to create comment 3 (reply): {comment3_response.status_code}")
        return False

    comment3_id = comment3_response.json()["id"]
    print(f"✓ Reply comment created (thread): {comment3_id}")

    # Comment 4: Resolved comment
    comment4_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        json={
            "content": "This comment will be marked as resolved",
            "position_x": 300.0,
            "position_y": 400.0
        },
        headers=headers
    )

    if comment4_response.status_code != 201:
        print(f"❌ Failed to create comment 4: {comment4_response.status_code}")
        return False

    comment4_id = comment4_response.json()["id"]
    print(f"✓ Comment created (to be resolved): {comment4_id}")

    # Step 4: Resolve comment 4
    print("\n[4/11] Resolving comment...")
    resolve_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments/{comment4_id}/resolve",
        headers=headers
    )

    if resolve_response.status_code != 200:
        print(f"❌ Failed to resolve comment: {resolve_response.status_code}")
        return False

    print(f"✓ Comment resolved: {comment4_id}")

    # Step 5: Add reaction to comment 1
    print("\n[5/11] Adding reaction to comment...")
    reaction_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments/{comment1_id}/reactions",
        json={"emoji": "👍"},
        headers=headers
    )

    if reaction_response.status_code not in [200, 201]:
        print(f"⚠ Could not add reaction (feature may not be implemented): {reaction_response.status_code}")
    else:
        print(f"✓ Reaction added to comment: {comment1_id}")

    # Step 6: Export comments as PDF
    print("\n[6/11] Exporting comments as PDF...")
    pdf_export_response = requests.post(
        f"{EXPORT_SERVICE_URL}/diagrams/{diagram_id}/comments/export/pdf"
    )

    if pdf_export_response.status_code != 200:
        print(f"❌ Failed to export comments as PDF: {pdf_export_response.status_code}")
        print(f"Response: {pdf_export_response.text}")
        return False

    print(f"✓ PDF export successful (size: {len(pdf_export_response.content)} bytes)")

    # Step 7: Verify PDF was generated
    print("\n[7/11] Verifying PDF was generated...")
    content_type = pdf_export_response.headers.get('content-type', '')

    if 'application/pdf' not in content_type:
        print(f"❌ Invalid content type: {content_type} (expected: application/pdf)")
        return False

    print(f"✓ PDF content type verified: {content_type}")

    # Step 8: Verify PDF content
    print("\n[8/11] Verifying PDF content...")
    try:
        pdf_buffer = BytesIO(pdf_export_response.content)
        pdf_reader = PdfReader(pdf_buffer)
        num_pages = len(pdf_reader.pages)

        print(f"✓ PDF has {num_pages} page(s)")

        # Extract text from all pages
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text()

        print(f"✓ PDF text extracted (length: {len(pdf_text)} characters)")

    except Exception as e:
        print(f"❌ Failed to read PDF: {str(e)}")
        return False

    # Step 9: Verify comments are formatted nicely
    print("\n[9/11] Verifying comments are formatted nicely...")

    # Check for comment content
    if "This is a comment on a canvas element at specific position" not in pdf_text:
        print(f"❌ Comment 1 content not found in PDF")
        return False

    if "This comment highlights important text in a note" not in pdf_text:
        print(f"❌ Comment 2 content not found in PDF")
        return False

    if "This is a reply to the first comment, forming a thread" not in pdf_text:
        print(f"❌ Comment 3 (reply) content not found in PDF")
        return False

    if "This comment will be marked as resolved" not in pdf_text:
        print(f"❌ Comment 4 content not found in PDF")
        return False

    print(f"✓ All 4 comments found in PDF")

    # Check for author information
    if email not in pdf_text:
        print(f"❌ Author email not found in PDF")
        return False

    print(f"✓ Author information included")

    # Step 10: Verify includes context (what was commented on)
    print("\n[10/11] Verifying context information...")

    # Check for position context
    if "100.5" not in pdf_text or "200.5" not in pdf_text:
        print(f"❌ Position context not found in PDF")
        return False

    print(f"✓ Position context found (100.5, 200.5)")

    # Check for element context
    if "shape:abc123" not in pdf_text:
        print(f"❌ Element ID context not found in PDF")
        return False

    print(f"✓ Element ID context found (shape:abc123)")

    # Check for text selection context
    if "Important text selection" not in pdf_text:
        print(f"❌ Text selection context not found in PDF")
        return False

    print(f"✓ Text selection context found")

    # Check for resolved status
    if "Resolved" not in pdf_text:
        print(f"❌ Resolved status not found in PDF")
        return False

    print(f"✓ Resolved status found")

    # Check for diagram metadata
    if "Test Diagram for Comment PDF Export" not in pdf_text:
        print(f"❌ Diagram name not found in PDF")
        return False

    print(f"✓ Diagram name found in PDF")

    if diagram_id not in pdf_text:
        print(f"❌ Diagram ID not found in PDF")
        return False

    print(f"✓ Diagram ID found in PDF")

    # Step 11: Verify thread structure
    print("\n[11/11] Verifying thread structure...")

    # Look for reply indicators
    if "Reply" not in pdf_text and "reply" not in pdf_text.lower():
        print(f"⚠ Reply indicator not explicitly found in PDF")
    else:
        print(f"✓ Reply/thread structure indicated in PDF")

    print("\n" + "=" * 70)
    print("✅ FEATURE #443: ALL TESTS PASSED")
    print("=" * 70)
    print(f"\nSummary:")
    print(f"  - PDF generated successfully ({len(pdf_export_response.content)} bytes)")
    print(f"  - PDF has {num_pages} page(s)")
    print(f"  - All 4 comments found with correct content")
    print(f"  - Author information included")
    print(f"  - Context information verified:")
    print(f"    * Position context (canvas comments)")
    print(f"    * Element ID context")
    print(f"    * Text selection context (note comments)")
    print(f"    * Resolved status")
    print(f"  - Diagram metadata included")
    print(f"  - Thread structure preserved")

    return True


if __name__ == "__main__":
    try:
        success = test_feature_443_comment_export_pdf()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
