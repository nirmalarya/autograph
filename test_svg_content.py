import requests

# Login
response = requests.post(
    "http://localhost:8080/api/auth/login",
    json={"email": "svgopt517@test.com", "password": "TestPass123!"}
)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Create diagram
diagram_response = requests.post(
    "http://localhost:8080/api/diagrams",
    headers=headers,
    json={
        "title": "SVG Test",
        "diagram_type": "canvas",
        "canvas_data": {"shapes": []}
    }
)
diagram_id = diagram_response.json()["id"]

# Export SVG
export_response = requests.post(
    f"http://localhost:8080/api/diagrams/{diagram_id}/export/svg",
    headers=headers,
    json={"width": 800, "height": 600}
)

print(f"Status: {export_response.status_code}")
print(f"Content: {export_response.content[:500]}")
print(f"\nFull SVG:")
print(export_response.content.decode('utf-8'))
