#!/usr/bin/env python3
"""
Feature #158: Diagram Collaboration Count
Tests that the collaborator_count field accurately tracks the number of collaborators on a diagram.

Steps:
1. User A creates diagram
2. Verify collaborator_count=1 (owner)
3. Share with User B
4. Verify collaborator_count=2
5. Share with User C and D
6. Verify collaborator_count=4
7. Remove User B's access
8. Verify collaborator_count=3
"""

import requests
import sys
import time
import subprocess
from typing import Dict, Any

API_BASE = "http://localhost:8080/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def register_user(email: str, password: str, name: str) -> Dict[str, Any]:
    """Register a new user and auto-verify them."""
    response = requests.post(f"{API_BASE}/auth/register", json={
        "email": email,
        "password": password,
        "name": name
    })
    user_data = response.json()

    # Auto-verify the user in the database for testing
    user_id = user_data.get("id")
    if user_id:
        subprocess.run([
            "docker", "exec", "autograph-postgres",
            "psql", "-U", "autograph", "-d", "autograph",
            "-c", f"UPDATE users SET is_verified = true WHERE id = '{user_id}'"
        ], capture_output=True)

    return user_data

def login_user(email: str, password: str) -> str:
    """Login and return JWT token."""
    response = requests.post(f"{API_BASE}/auth/login", json={
        "email": email,
        "password": password
    })
    data = response.json()
    return data.get("access_token")

def get_user_id(token: str) -> str:
    """Get the user ID from /me endpoint."""
    response = requests.get(
        f"{API_BASE}/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    data = response.json()
    return data.get("id")

def create_diagram(token: str, title: str) -> Dict[str, Any]:
    """Create a new diagram."""
    response = requests.post(
        f"{API_BASE}/diagrams",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "file_type": "canvas",
            "canvas_data": {"shapes": []}
        }
    )
    return response.json()

def get_diagram(token: str, diagram_id: str) -> Dict[str, Any]:
    """Get diagram details."""
    response = requests.get(
        f"{API_BASE}/diagrams/{diagram_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

def share_diagram(token: str, diagram_id: str, user_email: str, permission: str = "view") -> Dict[str, Any]:
    """Share a diagram with a user by email."""
    response = requests.post(
        f"{API_BASE}/diagrams/{diagram_id}/share",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "shared_with_email": user_email,
            "permission": permission,
            "is_public": False  # Explicitly set to false for user-specific shares
        }
    )
    return response.json()

def revoke_share(token: str, diagram_id: str, share_id: str) -> Dict[str, Any]:
    """Revoke a share."""
    response = requests.delete(
        f"{API_BASE}/diagrams/{diagram_id}/share/{share_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code != 200:
        print_error(f"Revoke failed with status {response.status_code}: {response.text}")
    return response.json() if response.status_code == 200 else {"error": response.text}

def list_shares(token: str, diagram_id: str) -> list:
    """List all shares for a diagram."""
    response = requests.get(
        f"{API_BASE}/diagrams/{diagram_id}/shares",
        headers={"Authorization": f"Bearer {token}"}
    )
    data = response.json()
    return data.get("shares", [])

def print_step(step_num: int, description: str):
    """Print a test step header."""
    print(f"\n{Colors.BLUE}Step {step_num}: {description}{Colors.END}")

def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message: str):
    """Print an info message."""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")

def main():
    """Run the validation tests."""
    try:
        timestamp = int(time.time())

        # Create test users
        print_step(0, "Setup: Create test users")
        user_a_email = f"user_a_{timestamp}@test.com"
        user_b_email = f"user_b_{timestamp}@test.com"
        user_c_email = f"user_c_{timestamp}@test.com"
        user_d_email = f"user_d_{timestamp}@test.com"
        password = "SecurePass123!"

        register_user(user_a_email, password, "User A")
        register_user(user_b_email, password, "User B")
        register_user(user_c_email, password, "User C")
        register_user(user_d_email, password, "User D")
        print_success("All users registered")

        # Login all users
        token_a = login_user(user_a_email, password)
        token_b = login_user(user_b_email, password)
        token_c = login_user(user_c_email, password)
        token_d = login_user(user_d_email, password)
        print_success("All users logged in")

        # Step 1: User A creates diagram
        print_step(1, "User A creates diagram")
        diagram = create_diagram(token_a, f"Collaboration Test {timestamp}")
        diagram_id = diagram.get("id")
        print_success(f"Diagram created with ID: {diagram_id}")

        # Step 2: Verify collaborator_count=1 (owner)
        print_step(2, "Verify collaborator_count=1 (owner)")
        diagram = get_diagram(token_a, diagram_id)
        collab_count = diagram.get("collaborator_count")
        if collab_count == 1:
            print_success(f"Collaborator count is correct: {collab_count}")
        else:
            print_error(f"Expected collaborator_count=1, got {collab_count}")
            return False

        # Step 3: Share with User B
        print_step(3, "Share with User B")
        share_b = share_diagram(token_a, diagram_id, user_b_email, "view")
        share_b_id = share_b.get("share_id")
        print_success(f"Shared with User B (share_id: {share_b_id})")

        # Step 4: Verify collaborator_count=2
        print_step(4, "Verify collaborator_count=2")
        diagram = get_diagram(token_a, diagram_id)
        collab_count = diagram.get("collaborator_count")
        if collab_count == 2:
            print_success(f"Collaborator count is correct: {collab_count}")
        else:
            print_error(f"Expected collaborator_count=2, got {collab_count}")
            return False

        # Step 5: Share with User C and D
        print_step(5, "Share with User C and D")
        share_c = share_diagram(token_a, diagram_id, user_c_email, "view")
        share_d = share_diagram(token_a, diagram_id, user_d_email, "edit")
        print_success(f"Shared with User C and D")

        # Step 6: Verify collaborator_count=4
        print_step(6, "Verify collaborator_count=4")
        diagram = get_diagram(token_a, diagram_id)
        collab_count = diagram.get("collaborator_count")
        if collab_count == 4:
            print_success(f"Collaborator count is correct: {collab_count}")
        else:
            print_error(f"Expected collaborator_count=4, got {collab_count}")
            return False

        # Step 7: Remove User B's access
        print_step(7, "Remove User B's access")
        revoke_share(token_a, diagram_id, share_b_id)
        print_success(f"Revoked User B's access")

        # Step 8: Verify collaborator_count=3
        print_step(8, "Verify collaborator_count=3")
        diagram = get_diagram(token_a, diagram_id)
        collab_count = diagram.get("collaborator_count")
        if collab_count == 3:
            print_success(f"Collaborator count is correct: {collab_count}")
        else:
            print_error(f"Expected collaborator_count=3, got {collab_count}")
            return False

        # All steps passed
        print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}All 8 steps passed! Feature #158 is working correctly.{Colors.END}")
        print(f"{Colors.GREEN}{'='*60}{Colors.END}")
        return True

    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
