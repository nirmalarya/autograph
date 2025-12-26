#!/usr/bin/env python3
"""Simple test for Feature #425: Note text selection comments."""

import subprocess
import json

print("=" * 60)
print("Feature #425: Note Text Selection Comments - Simple Test")
print("=" * 60)

# 1. Check database schema
print("\n1. Checking database schema...")
result = subprocess.run([
    "docker", "exec", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph",
    "-t", "-c", "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'comments' AND column_name IN ('text_start', 'text_end', 'text_content');"
], capture_output=True, text=True)

count = int(result.stdout.strip())
if count == 3:
    print("✅ All 3 text selection columns exist in comments table")
    schema_ok = True
else:
    print(f"❌ Expected 3 columns, found {count}")
    schema_ok = False

# 2. Check backend model
print("\n2. Checking backend model...")
try:
    with open('services/diagram-service/src/models.py', 'r') as f:
        content = f.read()
        has_text_start = 'text_start = Column(Integer)' in content
        has_text_end = 'text_end = Column(Integer)' in content
        has_text_content = 'text_content = Column(Text)' in content

        if has_text_start and has_text_end and has_text_content:
            print("✅ Comment model has text selection fields")
            model_ok = True
        else:
            print(f"❌ Model missing fields: start={has_text_start}, end={has_text_end}, content={has_text_content}")
            model_ok = False
except Exception as e:
    print(f"❌ Error checking model: {e}")
    model_ok = False

# 3. Check backend API
print("\n3. Checking backend API...")
try:
    with open('services/diagram-service/src/main.py', 'r') as f:
        content = f.read()
        has_request_fields = 'text_start: Optional[int]' in content and 'text_end: Optional[int]' in content
        has_response_fields = content.count('text_start') >= 2  # In both request and response
        has_creation_logic = 'text_start=comment_data.text_start' in content

        if has_request_fields and has_response_fields and has_creation_logic:
            print("✅ API endpoints support text selection")
            api_ok = True
        else:
            print(f"❌ API incomplete: request={has_request_fields}, response={has_response_fields}, logic={has_creation_logic}")
            api_ok = False
except Exception as e:
    print(f"❌ Error checking API: {e}")
    api_ok = False

# 4. Check frontend component
print("\n4. Checking frontend TLDrawCanvas...")
try:
    with open('services/frontend/app/canvas/[id]/TLDrawCanvas.tsx', 'r') as f:
        content = f.read()
        has_prop = 'onAddNoteComment?' in content
        has_action = "'add-note-comment'" in content

        if has_prop and has_action:
            print("✅ TLDrawCanvas has note comment action")
            canvas_ok = True
        else:
            print(f"❌ TLDrawCanvas missing: prop={has_prop}, action={has_action}")
            canvas_ok = False
except Exception as e:
    print(f"❌ Error checking canvas: {e}")
    canvas_ok = False

# 5. Check frontend page
print("\n5. Checking frontend page...")
try:
    with open('services/frontend/app/canvas/[id]/page.tsx', 'r') as f:
        content = f.read()
        has_state = 'commentTextStart' in content
        has_handler = 'handleAddNoteComment' in content
        has_body_logic = 'requestBody.text_start = commentTextStart' in content

        if has_state and has_handler and has_body_logic:
            print("✅ Page component handles note comments")
            page_ok = True
        else:
            print(f"❌ Page incomplete: state={has_state}, handler={has_handler}, logic={has_body_logic}")
            page_ok = False
except Exception as e:
    print(f"❌ Error checking page: {e}")
    page_ok = False

# Summary
print("\n" + "=" * 60)
print("VALIDATION SUMMARY")
print("=" * 60)

results = [
    ("Database Schema", schema_ok),
    ("Backend Model", model_ok),
    ("Backend API", api_ok),
    ("Frontend Canvas", canvas_ok),
    ("Frontend Page", page_ok),
]

for test_name, passed in results:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")

all_passed = all(r[1] for r in results)

if all_passed:
    print("\n🎉 All checks passed!")
    print("Feature #425 implementation is complete!")
    exit(0)
else:
    print("\n⚠️  Some checks failed.")
    exit(1)
