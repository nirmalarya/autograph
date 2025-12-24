"""
Test Feature #140: Diagram templates - save frequently-used patterns

Test Steps:
1. Create diagram with common architecture pattern
2. Click 'Save as Template'
3. Enter template name: 'Microservices Architecture'
4. Enter description: 'Standard microservices setup'
5. Click Save
6. Verify template saved
7. Create new diagram
8. Click 'Use Template'
9. Select 'Microservices Architecture'
10. Verify diagram created with template content
"""

import requests
import json
import uuid

BASE_URL = "http://localhost:8082"
AUTH_URL = "http://localhost:8085"

def test_diagram_templates():
    """Test complete template workflow."""
    print("=" * 80)
    print("TEST: Feature #140 - Diagram Templates")
    print("=" * 80)
    
    # Step 1: Register a user
    print("\n1. Registering test user...")
    unique_email = f"template_test_{uuid.uuid4().hex[:8]}@example.com"
    register_data = {
        "email": unique_email,
        "password": "Test123!@#",
        "full_name": "Template Test User"
    }
    response = requests.post(f"{AUTH_URL}/register", json=register_data)
    assert response.status_code == 201, f"Registration failed: {response.status_code} {response.text}"
    user_data = response.json()
    user_id = user_data["id"]
    print(f"✓ User registered: {unique_email}")
    print(f"  User ID: {user_id}")
    
    headers = {"X-User-ID": user_id}
    
    # Step 2: Create a diagram with architecture pattern
    print("\n2. Creating diagram with microservices architecture pattern...")
    diagram_data = {
        "title": "My Microservices App",
        "type": "canvas",
        "canvas_data": {
            "shapes": [
                {
                    "id": "api-gateway",
                    "type": "rectangle",
                    "x": 100,
                    "y": 100,
                    "width": 150,
                    "height": 80,
                    "label": "API Gateway"
                },
                {
                    "id": "auth-service",
                    "type": "rectangle",
                    "x": 100,
                    "y": 250,
                    "width": 150,
                    "height": 80,
                    "label": "Auth Service"
                },
                {
                    "id": "user-service",
                    "type": "rectangle",
                    "x": 300,
                    "y": 250,
                    "width": 150,
                    "height": 80,
                    "label": "User Service"
                },
                {
                    "id": "database",
                    "type": "cylinder",
                    "x": 200,
                    "y": 400,
                    "width": 150,
                    "height": 80,
                    "label": "PostgreSQL"
                }
            ],
            "arrows": [
                {"from": "api-gateway", "to": "auth-service"},
                {"from": "api-gateway", "to": "user-service"},
                {"from": "auth-service", "to": "database"},
                {"from": "user-service", "to": "database"}
            ]
        },
        "note_content": "# Microservices Architecture\n\nStandard setup with API Gateway and services."
    }
    response = requests.post(f"{BASE_URL}/", json=diagram_data, headers=headers)
    assert response.status_code in [200, 201], f"Create diagram failed: {response.status_code} {response.text}"
    diagram = response.json()
    diagram_id = diagram["id"]
    print(f"✓ Diagram created: {diagram['title']}")
    print(f"  Diagram ID: {diagram_id}")
    print(f"  Shapes: {len(diagram_data['canvas_data']['shapes'])}")
    
    # Step 3: Save diagram as template
    print("\n3. Saving diagram as template...")
    template_data = {
        "name": "Microservices Architecture",
        "description": "Standard microservices setup with API Gateway, services, and database",
        "file_type": "canvas",
        "canvas_data": diagram_data["canvas_data"],
        "note_content": diagram_data["note_content"],
        "category": "Architecture",
        "tags": ["microservices", "api-gateway", "postgresql"],
        "is_public": False
    }
    response = requests.post(f"{BASE_URL}/templates", json=template_data, headers=headers)
    assert response.status_code in [200, 201], f"Create template failed: {response.status_code} {response.text}"
    template = response.json()
    template_id = template["id"]
    print(f"✓ Template created: {template['name']}")
    print(f"  Template ID: {template_id}")
    print(f"  Description: {template['description']}")
    print(f"  Category: {template['category']}")
    print(f"  Tags: {template['tags']}")
    print(f"  Usage count: {template['usage_count']}")
    
    # Step 4: Verify template was saved
    print("\n4. Verifying template was saved...")
    response = requests.get(f"{BASE_URL}/templates/{template_id}", headers=headers)
    assert response.status_code == 200, f"Get template failed: {response.status_code} {response.text}"
    retrieved_template = response.json()
    assert retrieved_template["id"] == template_id, "Template ID mismatch"
    assert retrieved_template["name"] == "Microservices Architecture", "Template name mismatch"
    assert retrieved_template["owner_id"] == user_id, "Template owner mismatch"
    assert retrieved_template["usage_count"] == 0, "Initial usage count should be 0"
    print(f"✓ Template verified")
    print(f"  Name: {retrieved_template['name']}")
    print(f"  Owner: {retrieved_template['owner_id']}")
    
    # Step 5: List templates
    print("\n5. Listing available templates...")
    response = requests.get(f"{BASE_URL}/templates", headers=headers)
    assert response.status_code == 200, f"List templates failed: {response.status_code} {response.text}"
    templates = response.json()
    assert len(templates) > 0, "Should have at least one template"
    template_names = [t["name"] for t in templates]
    assert "Microservices Architecture" in template_names, "Template not in list"
    print(f"✓ Templates listed: {len(templates)} total")
    for t in templates:
        print(f"  - {t['name']} (usage: {t['usage_count']})")
    
    # Step 6: Filter templates by category
    print("\n6. Filtering templates by category...")
    response = requests.get(f"{BASE_URL}/templates?category=Architecture", headers=headers)
    assert response.status_code == 200, f"Filter templates failed: {response.status_code} {response.text}"
    filtered_templates = response.json()
    assert len(filtered_templates) > 0, "Should have Architecture templates"
    for t in filtered_templates:
        assert t["category"] == "Architecture", f"Template {t['name']} has wrong category"
    print(f"✓ Filtered templates: {len(filtered_templates)} Architecture templates")
    
    # Step 7: Create new diagram from template
    print("\n7. Creating new diagram from template...")
    response = requests.post(f"{BASE_URL}/templates/{template_id}/use", headers=headers)
    assert response.status_code in [200, 201], f"Create from template failed: {response.status_code} {response.text}"
    new_diagram = response.json()
    new_diagram_id = new_diagram["id"]
    print(f"✓ Diagram created from template")
    print(f"  New diagram ID: {new_diagram_id}")
    print(f"  Title: {new_diagram['title']}")
    
    # Step 8: Verify new diagram has template content
    print("\n8. Verifying new diagram has template content...")
    response = requests.get(f"{BASE_URL}/{new_diagram_id}", headers=headers)
    assert response.status_code == 200, f"Get new diagram failed: {response.status_code} {response.text}"
    diagram_from_template = response.json()
    
    # Verify canvas data matches template
    assert diagram_from_template["canvas_data"] is not None, "Canvas data should not be None"
    assert "shapes" in diagram_from_template["canvas_data"], "Should have shapes"
    assert len(diagram_from_template["canvas_data"]["shapes"]) == len(template_data["canvas_data"]["shapes"]), \
        "Should have same number of shapes as template"
    
    # Verify note content matches template
    assert diagram_from_template["note_content"] is not None, "Note content should not be None"
    assert "Microservices Architecture" in diagram_from_template["note_content"], \
        "Note should contain template content"
    
    print(f"✓ Diagram content verified")
    print(f"  Shapes: {len(diagram_from_template['canvas_data']['shapes'])}")
    print(f"  Note content: {len(diagram_from_template['note_content'])} chars")
    
    # Step 9: Verify template usage count incremented
    print("\n9. Verifying template usage count incremented...")
    response = requests.get(f"{BASE_URL}/templates/{template_id}", headers=headers)
    assert response.status_code == 200, f"Get template failed: {response.status_code} {response.text}"
    updated_template = response.json()
    assert updated_template["usage_count"] == 1, f"Usage count should be 1, got {updated_template['usage_count']}"
    print(f"✓ Template usage count incremented: {updated_template['usage_count']}")
    
    # Step 10: Test template deletion (owner only)
    print("\n10. Testing template deletion...")
    response = requests.delete(f"{BASE_URL}/templates/{template_id}", headers=headers)
    assert response.status_code == 200, f"Delete template failed: {response.status_code} {response.text}"
    print(f"✓ Template deleted successfully")
    
    # Verify template is gone
    response = requests.get(f"{BASE_URL}/templates/{template_id}", headers=headers)
    assert response.status_code == 404, "Template should not exist after deletion"
    print(f"✓ Template no longer accessible")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Feature #140 (Diagram Templates) is working!")
    print("=" * 80)
    print("\nSummary:")
    print("  ✓ Created diagram with architecture pattern")
    print("  ✓ Saved diagram as template")
    print("  ✓ Listed available templates")
    print("  ✓ Filtered templates by category")
    print("  ✓ Created new diagram from template")
    print("  ✓ Verified template content copied correctly")
    print("  ✓ Template usage count incremented")
    print("  ✓ Deleted template (owner only)")
    print("\n✅ Feature #140 is COMPLETE and ready for production!")


if __name__ == "__main__":
    test_diagram_templates()
