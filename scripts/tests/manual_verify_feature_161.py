#!/usr/bin/env python3
"""
Manual UI verification for Feature #161: TLDraw Canvas Integration
Opens browser and guides through manual testing steps
"""

import requests
import time
import webbrowser
import sys

BASE_URL = "http://localhost:8082"
AUTH_URL = "http://localhost:8085"
FRONTEND_URL = "http://localhost:3004"

def main():
    print("\n" + "="*80)
    print("Feature #161: TLDraw Canvas Integration - Manual UI Verification")
    print("="*80 + "\n")
    
    # Create test user and diagram
    email = f"manual_test_{int(time.time())}@test.com"
    password = "TestPass123!"
    
    print("Step 1: Creating test user...")
    reg = requests.post(f"{AUTH_URL}/register", json={"email": email, "password": password})
    if reg.status_code not in [200, 201]:
        print(f"❌ Registration failed: {reg.status_code}")
        return False
    print(f"✓ User created: {email}")
    
    print("\nStep 2: Logging in...")
    login = requests.post(f"{AUTH_URL}/login", json={"email": email, "password": password})
    if login.status_code != 200:
        print(f"❌ Login failed: {login.status_code}")
        return False
    
    token = login.json()['access_token']
    import json, base64
    payload = json.loads(base64.b64decode(token.split('.')[1] + '=='))
    user_id = payload['sub']
    print(f"✓ Logged in")
    
    print("\nStep 3: Creating canvas diagram...")
    diagram = requests.post(f"{BASE_URL}/", 
        json={"title": "TLDraw Test Diagram", "file_type": "canvas", "canvas_data": {}, "note_content": ""},
        headers={"X-User-ID": user_id}
    )
    if diagram.status_code not in [200, 201]:
        print(f"❌ Diagram creation failed: {diagram.status_code}")
        return False
    
    diagram_id = diagram.json()['id']
    canvas_url = f"{FRONTEND_URL}/canvas/{diagram_id}"
    
    print(f"✓ Diagram created: {diagram_id}")
    print(f"\nCanvas URL: {canvas_url}")
    
    print("\n" + "="*80)
    print("MANUAL TESTING CHECKLIST")
    print("="*80 + "\n")
    
    print("Opening canvas in browser...")
    print(f"\nYou need to:")
    print(f"1. Login with:")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"\n2. Then navigate to: {canvas_url}")
    print(f"\n   OR go to Dashboard and open 'TLDraw Test Diagram'")
    
    print("\n" + "-"*80)
    print("Please verify the following in the browser:")
    print("-"*80)
    print("[ ] 1. TLDraw canvas loads successfully")
    print("[ ] 2. Canvas is responsive and interactive")
    print("[ ] 3. Can pan with mouse drag (or Space + drag)")
    print("[ ] 4. Can zoom with mouse wheel")
    print("[ ] 5. Canvas renders at 60 FPS (smooth animations)")
    print("[ ] 6. Drawing tools are visible in toolbar")
    print("[ ] 7. Can draw basic shapes (rectangle, circle, etc.)")
    print("-"*80)
    
    # Open login page first
    login_url = f"{FRONTEND_URL}/login"
    print(f"\nOpening login page: {login_url}")
    webbrowser.open(login_url)
    
    print("\n" + "="*80)
    print("After manual verification, clean up:")
    print(f"Delete diagram: DELETE {BASE_URL}/{diagram_id}")
    print("="*80 + "\n")
    
    input("Press Enter when you've completed manual verification...")
    
    # Cleanup
    print("\nCleaning up...")
    delete = requests.delete(f"{BASE_URL}/{diagram_id}", headers={"X-User-ID": user_id})
    if delete.status_code in [200, 204]:
        print("✓ Test diagram deleted")
    
    print("\n✅ Manual verification complete!")
    print("If all items in the checklist passed, Feature #161 is ready for production.\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Verification cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
