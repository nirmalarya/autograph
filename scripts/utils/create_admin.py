"""Create and verify admin user for testing."""
import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='autograph',
        user='autograph',
        password='autograph_dev_password'
    )
    cursor = conn.cursor()
    
    # Update existing admin user
    cursor.execute("""
        UPDATE users 
        SET is_verified = true, role = 'admin' 
        WHERE email = 'admin@autograph.com'
    """)
    
    rows_updated = cursor.rowcount
    conn.commit()
    
    if rows_updated > 0:
        print(f"✓ Updated {rows_updated} user(s)")
        
        # Verify the update
        cursor.execute("""
            SELECT id, email, role, is_verified, is_active 
            FROM users 
            WHERE email = 'admin@autograph.com'
        """)
        result = cursor.fetchone()
        
        if result:
            print(f"✓ User verified:")
            print(f"  ID: {result[0]}")
            print(f"  Email: {result[1]}")
            print(f"  Role: {result[2]}")
            print(f"  Verified: {result[3]}")
            print(f"  Active: {result[4]}")
    else:
        print("✗ No users found with email admin@autograph.com")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Error: {str(e)}")
