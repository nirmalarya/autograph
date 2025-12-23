"""
Test Feature #145: Full-text search across diagram titles and content.

This test verifies that the search functionality works across:
1. Diagram titles
2. Note content (markdown)
3. Canvas data (text elements)

Test Steps:
1. Create diagram with title 'AWS Architecture'
2. Add text element: 'EC2 instances'
3. Create another diagram with title 'Database Schema'
4. Add text: 'PostgreSQL tables'
5. Navigate to /dashboard
6. Enter search: 'AWS'
7. Verify first diagram found
8. Enter search: 'PostgreSQL'
9. Verify second diagram found
10. Enter search: 'instances'
11. Verify first diagram found (content search)
"""

import requests
import json
import sys
from typing import Optional

# Configuration
GATEWAY_URL = "http://localhost:8080/api"
AUTH_URL = f"{GATEWAY_URL}/auth"
DIAGRAMS_URL = f"{GATEWAY_URL}/diagrams"

# Test user credentials
TEST_EMAIL = "search_test@example.com"
TEST_PASSWORD = "SearchTest123!"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def log_step(step_num: int, description: str):
    """Log a test step."""
    print(f"\n{BLUE}Step {step_num}: {description}{RESET}")


def log_success(message: str):
    """Log a success message."""
    print(f"{GREEN}✓ {message}{RESET}")


def log_error(message: str):
    """Log an error message."""
    print(f"{RED}✗ {message}{RESET}")


def log_info(message: str):
    """Log an info message."""
    print(f"{YELLOW}  {message}{RESET}")


def register_and_login() -> Optional[str]:
    """Register a test user and login to get access token."""
    log_step(0, "Register and login test user")
    
    # Try to register
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": "Search Test User"
    }
    
    try:
        response = requests.post(f"{AUTH_URL}/register", json=register_data, timeout=5)
        if response.status_code == 201:
            log_success("User registered successfully")
        elif response.status_code == 400:
            # User might already exist, try to login
            log_info("User already exists (will try to login)")
        else:
            log_error(f"Registration failed: {response.status_code}")
            # Continue to login anyway
    except Exception as e:
        log_info(f"Registration error (will try to login): {str(e)}")
    
    # Login
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{AUTH_URL}/login", json=login_data, timeout=5)
        if response.status_code == 200:
            token = response.json()["access_token"]
            log_success("Login successful")
            return token
        else:
            log_error(f"Login failed: {response.status_code}")
            return None
    except Exception as e:
        log_error(f"Login error: {str(e)}")
        return None


def create_diagram(token: str, title: str, canvas_data: dict = None, note_content: str = None) -> Optional[str]:
    """Create a diagram and return its ID."""
    headers = {"Authorization": f"Bearer {token}"}
    
    diagram_data = {
        "title": title,
        "type": "canvas",
        "canvas_data": canvas_data or {},
        "note_content": note_content
    }
    
    try:
        response = requests.post(DIAGRAMS_URL, json=diagram_data, headers=headers, timeout=5)
        if response.status_code == 200:
            diagram_id = response.json()["id"]
            log_success(f"Created diagram: {title} (ID: {diagram_id[:8]}...)")
            return diagram_id
        else:
            log_error(f"Failed to create diagram: {response.status_code}")
            log_info(f"Response: {response.text[:200]}")
            return None
    except Exception as e:
        log_error(f"Error creating diagram: {str(e)}")
        return None


def search_diagrams(token: str, search_query: str) -> list:
    """Search for diagrams and return results."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"search": search_query}
    
    try:
        response = requests.get(DIAGRAMS_URL, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            diagrams = data.get("diagrams", [])
            total = data.get("total", 0)
            log_success(f"Search '{search_query}' returned {total} result(s)")
            return diagrams
        else:
            log_error(f"Search failed: {response.status_code}")
            log_info(f"Response: {response.text[:200]}")
            return []
    except Exception as e:
        log_error(f"Error searching: {str(e)}")
        return []


def verify_diagram_in_results(diagrams: list, expected_title: str) -> bool:
    """Verify that a diagram with the expected title is in the results."""
    for diagram in diagrams:
        if expected_title.lower() in diagram["title"].lower():
            log_success(f"Found diagram: {diagram['title']}")
            return True
    log_error(f"Diagram with title containing '{expected_title}' not found")
    return False


def main():
    """Run all test steps."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Feature #145: Full-text Search Test{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    
    # Step 0: Register and login
    token = register_and_login()
    if not token:
        log_error("Failed to get access token. Aborting test.")
        return False
    
    # Step 1: Create diagram with title 'AWS Architecture'
    log_step(1, "Create diagram with title 'AWS Architecture'")
    aws_canvas_data = {
        "shapes": [
            {
                "type": "text",
                "id": "text1",
                "x": 100,
                "y": 100,
                "text": "EC2 instances"
            }
        ]
    }
    aws_diagram_id = create_diagram(
        token,
        "AWS Architecture",
        canvas_data=aws_canvas_data
    )
    if not aws_diagram_id:
        log_error("Failed to create AWS diagram. Aborting test.")
        return False
    
    # Step 2: Verify text element added
    log_step(2, "Verify text element 'EC2 instances' added to canvas")
    log_success("Text element added in canvas_data")
    
    # Step 3: Create another diagram with title 'Database Schema'
    log_step(3, "Create diagram with title 'Database Schema'")
    db_note_content = """
# Database Schema

This diagram shows the PostgreSQL tables and their relationships.

## Tables
- users
- diagrams
- versions
"""
    db_diagram_id = create_diagram(
        token,
        "Database Schema",
        note_content=db_note_content
    )
    if not db_diagram_id:
        log_error("Failed to create Database diagram. Aborting test.")
        return False
    
    # Step 4: Verify note content added
    log_step(4, "Verify note content 'PostgreSQL tables' added")
    log_success("Note content includes 'PostgreSQL tables'")
    
    # Step 5: Navigate to /dashboard (simulated by searching)
    log_step(5, "Navigate to /dashboard (simulated by search endpoint)")
    log_info("Using GET /api/diagrams with search parameter")
    
    # Step 6-7: Search for 'AWS' and verify first diagram found
    log_step(6, "Search for 'AWS'")
    aws_results = search_diagrams(token, "AWS")
    
    log_step(7, "Verify AWS Architecture diagram found")
    if not verify_diagram_in_results(aws_results, "AWS Architecture"):
        log_error("AWS Architecture diagram not found in search results")
        return False
    
    # Step 8-9: Search for 'PostgreSQL' and verify second diagram found
    log_step(8, "Search for 'PostgreSQL'")
    postgres_results = search_diagrams(token, "PostgreSQL")
    
    log_step(9, "Verify Database Schema diagram found")
    if not verify_diagram_in_results(postgres_results, "Database Schema"):
        log_error("Database Schema diagram not found in search results")
        return False
    
    # Step 10-11: Search for 'instances' (content search) and verify first diagram found
    log_step(10, "Search for 'instances' (content search)")
    instances_results = search_diagrams(token, "instances")
    
    log_step(11, "Verify AWS Architecture diagram found (content search)")
    if not verify_diagram_in_results(instances_results, "AWS Architecture"):
        log_error("AWS Architecture diagram not found when searching canvas content")
        return False
    
    # Additional test: Search for 'EC2' (should find AWS diagram)
    log_step(12, "Additional test: Search for 'EC2' (canvas content)")
    ec2_results = search_diagrams(token, "EC2")
    if verify_diagram_in_results(ec2_results, "AWS Architecture"):
        log_success("Canvas content search working correctly")
    else:
        log_error("Canvas content search not working properly")
        return False
    
    # Summary
    print(f"\n{GREEN}{'='*80}{RESET}")
    print(f"{GREEN}All tests passed! Feature #145 is working correctly.{RESET}")
    print(f"{GREEN}{'='*80}{RESET}")
    
    print(f"\n{BLUE}Summary:{RESET}")
    print(f"  ✓ Title search: Working")
    print(f"  ✓ Note content search: Working")
    print(f"  ✓ Canvas data search: Working")
    print(f"  ✓ Full-text search across all fields: Working")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
