#!/usr/bin/env python3
"""Debug version search by checking actual database content."""

import psycopg2
import json

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="autograph",
    user="autograph",
    password="autograph_pass"
)

cur = conn.cursor()

# Find recent Debug Search diagrams
cur.execute("""
    SELECT id, title FROM files
    WHERE title LIKE 'Debug Search%%'
    ORDER BY created_at DESC
    LIMIT 1
""")

diagram = cur.fetchone()
if diagram:
    diagram_id, title = diagram
    print(f"Checking diagram: {title} ({diagram_id})")

    # Get versions
    cur.execute("""
        SELECT version_number, description, canvas_data, note_content
        FROM versions
        WHERE file_id = %s
        ORDER BY version_number
    """, (diagram_id,))

    versions = cur.fetchall()
    print(f"\nFound {len(versions)} versions:")

    for v_num, desc, canvas, notes in versions:
        print(f"\n--- Version {v_num} ({desc}) ---")

        # Check canvas_data
        if canvas:
            canvas_str = json.dumps(canvas)
            has_database = 'database' in canvas_str.lower()
            has_react = 'react' in canvas_str.lower()
            print(f"Canvas: {canvas_str[:100]}...")
            print(f"  Contains 'database': {has_database}")
            print(f"  Contains 'react': {has_react}")

        # Check note_content
        if notes:
            has_database_note = 'database' in notes.lower()
            has_react_note = 'react' in notes.lower()
            print(f"Notes: {notes[:100]}")
            print(f"  Contains 'database': {has_database_note}")
            print(f"  Contains 'react': {has_react_note}")
else:
    print("No Debug Search diagram found")

cur.close()
conn.close()
