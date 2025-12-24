#!/usr/bin/env python3
"""
Feature #24: PostgreSQL foreign key constraints enforce referential integrity

Tests that foreign key constraints work correctly:
- ON DELETE CASCADE: Child records deleted when parent deleted
- ON DELETE SET NULL: Foreign keys set to NULL when parent deleted
- ON DELETE RESTRICT: Prevents deletion of parent when children exist (if any)
"""

import psycopg2
import uuid
from datetime import datetime

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'autograph',
    'user': 'autograph',
    'password': 'autograph_dev_password'
}

def connect_db():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(**DB_CONFIG)

def cleanup_test_data(conn, user_ids=None, file_ids=None):
    """Clean up test data"""
    cursor = conn.cursor()
    try:
        if file_ids:
            for file_id in file_ids:
                cursor.execute("DELETE FROM files WHERE id = %s", (file_id,))
        if user_ids:
            for user_id in user_ids:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
    except Exception as e:
        print(f"Cleanup error (may be ok): {e}")
        conn.rollback()
    finally:
        cursor.close()

def test_cascade_delete():
    """
    Test ON DELETE CASCADE behavior
    When a user is deleted, their files should be automatically deleted
    """
    print("\n" + "="*70)
    print("Step 1: Test CASCADE delete - files deleted when user deleted")
    print("="*70)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Create test user
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, f'test-fk-{user_id}@example.com', 'hash', 'Test User', True, True, 'user'))
        conn.commit()
        print(f"✓ Created user: {user_id}")
        
        # Create test file owned by this user
        file_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO files (id, title, owner_id, file_type, is_starred, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (file_id, 'Test File', user_id, 'canvas', False, False))
        conn.commit()
        print(f"✓ Created file: {file_id} (owned by user)")
        
        # Create a version for the file
        version_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO versions (id, file_id, version_number, canvas_data, created_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (version_id, file_id, 1, '{"test": true}', user_id))
        conn.commit()
        print(f"✓ Created version: {version_id} (for file)")
        
        # Verify file exists
        cursor.execute("SELECT COUNT(*) FROM files WHERE id = %s", (file_id,))
        count = cursor.fetchone()[0]
        assert count == 1, "File should exist before user deletion"
        print(f"✓ Verified file exists in database")
        
        # Verify version exists
        cursor.execute("SELECT COUNT(*) FROM versions WHERE id = %s", (version_id,))
        count = cursor.fetchone()[0]
        assert count == 1, "Version should exist before user deletion"
        print(f"✓ Verified version exists in database")
        
        # Delete user (should CASCADE delete the file and version)
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        print(f"✓ Deleted user: {user_id}")
        
        # Verify file was automatically deleted (CASCADE)
        cursor.execute("SELECT COUNT(*) FROM files WHERE id = %s", (file_id,))
        count = cursor.fetchone()[0]
        assert count == 0, "File should be automatically deleted (CASCADE)"
        print(f"✓ PASSED: File automatically deleted due to CASCADE constraint")
        
        # Verify version was automatically deleted (CASCADE from files)
        cursor.execute("SELECT COUNT(*) FROM versions WHERE id = %s", (version_id,))
        count = cursor.fetchone()[0]
        assert count == 0, "Version should be automatically deleted (CASCADE from files)"
        print(f"✓ PASSED: Version automatically deleted due to CASCADE constraint")
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def test_set_null_delete():
    """
    Test ON DELETE SET NULL behavior
    When a user is deleted, created_by in versions should be set to NULL
    """
    print("\n" + "="*70)
    print("Step 2: Test SET NULL - created_by set to NULL when user deleted")
    print("="*70)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Create two users
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user1_id, f'test-fk-owner-{user1_id}@example.com', 'hash', 'Owner', True, True, 'user'))
        
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user2_id, f'test-fk-creator-{user2_id}@example.com', 'hash', 'Creator', True, True, 'user'))
        conn.commit()
        print(f"✓ Created user1 (owner): {user1_id}")
        print(f"✓ Created user2 (creator): {user2_id}")
        
        # Create file owned by user1
        file_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO files (id, title, owner_id, file_type, is_starred, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (file_id, 'Test File', user1_id, 'canvas', False, False))
        conn.commit()
        print(f"✓ Created file: {file_id} (owned by user1)")
        
        # Create version created by user2
        version_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO versions (id, file_id, version_number, canvas_data, created_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (version_id, file_id, 1, '{"test": true}', user2_id))
        conn.commit()
        print(f"✓ Created version: {version_id} (created_by user2)")
        
        # Verify version has created_by set
        cursor.execute("SELECT created_by FROM versions WHERE id = %s", (version_id,))
        created_by = cursor.fetchone()[0]
        assert created_by == user2_id, "created_by should be user2_id"
        print(f"✓ Verified version.created_by = {user2_id}")
        
        # Delete user2 (creator) - should SET NULL the created_by field
        cursor.execute("DELETE FROM users WHERE id = %s", (user2_id,))
        conn.commit()
        print(f"✓ Deleted user2 (creator): {user2_id}")
        
        # Verify version still exists
        cursor.execute("SELECT COUNT(*) FROM versions WHERE id = %s", (version_id,))
        count = cursor.fetchone()[0]
        assert count == 1, "Version should still exist"
        print(f"✓ Version still exists in database")
        
        # Verify created_by was set to NULL
        cursor.execute("SELECT created_by FROM versions WHERE id = %s", (version_id,))
        created_by = cursor.fetchone()[0]
        assert created_by is None, "created_by should be NULL after user deletion"
        print(f"✓ PASSED: version.created_by set to NULL due to SET NULL constraint")
        
        # Cleanup
        cleanup_test_data(conn, user_ids=[user1_id], file_ids=[file_id])
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def test_multiple_cascades():
    """
    Test multiple levels of CASCADE
    User -> File (CASCADE) -> Version (CASCADE)
    """
    print("\n" + "="*70)
    print("Step 3: Test multi-level CASCADE - user -> file -> versions")
    print("="*70)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Create user
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, f'test-cascade-{user_id}@example.com', 'hash', 'Test User', True, True, 'user'))
        conn.commit()
        print(f"✓ Created user: {user_id}")
        
        # Create file
        file_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO files (id, title, owner_id, file_type, is_starred, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (file_id, 'Test File', user_id, 'canvas', False, False))
        conn.commit()
        print(f"✓ Created file: {file_id}")
        
        # Create multiple versions
        version_ids = []
        for i in range(1, 4):
            version_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO versions (id, file_id, version_number, canvas_data, created_by)
                VALUES (%s, %s, %s, %s, %s)
            """, (version_id, file_id, i, f'{{"version": {i}}}', user_id))
            version_ids.append(version_id)
        conn.commit()
        print(f"✓ Created 3 versions: {version_ids}")
        
        # Verify all versions exist
        cursor.execute("SELECT COUNT(*) FROM versions WHERE file_id = %s", (file_id,))
        count = cursor.fetchone()[0]
        assert count == 3, "Should have 3 versions"
        print(f"✓ Verified 3 versions exist")
        
        # Delete user (should CASCADE to file, then to versions)
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        print(f"✓ Deleted user: {user_id}")
        
        # Verify file was deleted
        cursor.execute("SELECT COUNT(*) FROM files WHERE id = %s", (file_id,))
        count = cursor.fetchone()[0]
        assert count == 0, "File should be deleted"
        print(f"✓ File was CASCADE deleted")
        
        # Verify all versions were deleted
        cursor.execute("SELECT COUNT(*) FROM versions WHERE file_id = %s", (file_id,))
        count = cursor.fetchone()[0]
        assert count == 0, "All versions should be deleted"
        print(f"✓ PASSED: All 3 versions CASCADE deleted through file deletion")
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def test_folder_set_null():
    """
    Test folder_id SET NULL when folder deleted
    """
    print("\n" + "="*70)
    print("Step 4: Test folder SET NULL - folder_id nulled when folder deleted")
    print("="*70)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Create user
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, f'test-folder-{user_id}@example.com', 'hash', 'Test User', True, True, 'user'))
        conn.commit()
        print(f"✓ Created user: {user_id}")
        
        # Create folder
        folder_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO folders (id, name, owner_id, parent_id, color, icon)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (folder_id, 'Test Folder', user_id, None, 'blue', 'folder'))
        conn.commit()
        print(f"✓ Created folder: {folder_id}")
        
        # Create file in folder
        file_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO files (id, title, owner_id, folder_id, file_type, is_starred, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (file_id, 'Test File', user_id, folder_id, 'canvas', False, False))
        conn.commit()
        print(f"✓ Created file: {file_id} (in folder)")
        
        # Verify file has folder_id set
        cursor.execute("SELECT folder_id FROM files WHERE id = %s", (file_id,))
        current_folder = cursor.fetchone()[0]
        assert current_folder == folder_id, "File should be in folder"
        print(f"✓ Verified file.folder_id = {folder_id}")
        
        # Delete folder (should SET NULL the folder_id)
        cursor.execute("DELETE FROM folders WHERE id = %s", (folder_id,))
        conn.commit()
        print(f"✓ Deleted folder: {folder_id}")
        
        # Verify file still exists
        cursor.execute("SELECT COUNT(*) FROM files WHERE id = %s", (file_id,))
        count = cursor.fetchone()[0]
        assert count == 1, "File should still exist"
        print(f"✓ File still exists")
        
        # Verify folder_id was set to NULL
        cursor.execute("SELECT folder_id FROM files WHERE id = %s", (file_id,))
        current_folder = cursor.fetchone()[0]
        assert current_folder is None, "folder_id should be NULL"
        print(f"✓ PASSED: file.folder_id set to NULL due to SET NULL constraint")
        
        # Cleanup
        cleanup_test_data(conn, user_ids=[user_id], file_ids=[file_id])
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def test_team_set_null():
    """
    Test team_id SET NULL when team deleted
    """
    print("\n" + "="*70)
    print("Step 5: Test team SET NULL - team_id nulled when team deleted")
    print("="*70)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Create user
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, f'test-team-{user_id}@example.com', 'hash', 'Test User', True, True, 'user'))
        conn.commit()
        print(f"✓ Created user: {user_id}")
        
        # Create team
        team_id = str(uuid.uuid4())
        team_slug = f'test-team-{team_id[:8]}'
        cursor.execute("""
            INSERT INTO teams (id, name, slug, owner_id, plan)
            VALUES (%s, %s, %s, %s, %s)
        """, (team_id, 'Test Team', team_slug, user_id, 'free'))
        conn.commit()
        print(f"✓ Created team: {team_id}")
        
        # Create file in team
        file_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO files (id, title, owner_id, team_id, file_type, is_starred, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (file_id, 'Test File', user_id, team_id, 'canvas', False, False))
        conn.commit()
        print(f"✓ Created file: {file_id} (in team)")
        
        # Verify file has team_id set
        cursor.execute("SELECT team_id FROM files WHERE id = %s", (file_id,))
        current_team = cursor.fetchone()[0]
        assert current_team == team_id, "File should be in team"
        print(f"✓ Verified file.team_id = {team_id}")
        
        # Delete team (should SET NULL the team_id)
        cursor.execute("DELETE FROM teams WHERE id = %s", (team_id,))
        conn.commit()
        print(f"✓ Deleted team: {team_id}")
        
        # Verify file still exists
        cursor.execute("SELECT COUNT(*) FROM files WHERE id = %s", (file_id,))
        count = cursor.fetchone()[0]
        assert count == 1, "File should still exist"
        print(f"✓ File still exists")
        
        # Verify team_id was set to NULL
        cursor.execute("SELECT team_id FROM files WHERE id = %s", (file_id,))
        current_team = cursor.fetchone()[0]
        assert current_team is None, "team_id should be NULL"
        print(f"✓ PASSED: file.team_id set to NULL due to SET NULL constraint")
        
        # Cleanup
        cleanup_test_data(conn, user_ids=[user_id], file_ids=[file_id])
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def test_comments_cascade():
    """
    Test comments CASCADE when file deleted
    """
    print("\n" + "="*70)
    print("Step 6: Test comments CASCADE - deleted when file deleted")
    print("="*70)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Create user
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, f'test-comment-{user_id}@example.com', 'hash', 'Test User', True, True, 'user'))
        conn.commit()
        print(f"✓ Created user: {user_id}")
        
        # Create file
        file_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO files (id, title, owner_id, file_type, is_starred, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (file_id, 'Test File', user_id, 'canvas', False, False))
        conn.commit()
        print(f"✓ Created file: {file_id}")
        
        # Create comments
        comment_ids = []
        for i in range(1, 4):
            comment_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO comments (id, file_id, user_id, content, position_x, position_y, is_resolved)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (comment_id, file_id, user_id, f'Comment {i}', 100 * i, 100 * i, False))
            comment_ids.append(comment_id)
        conn.commit()
        print(f"✓ Created 3 comments: {comment_ids}")
        
        # Verify comments exist
        cursor.execute("SELECT COUNT(*) FROM comments WHERE file_id = %s", (file_id,))
        count = cursor.fetchone()[0]
        assert count == 3, "Should have 3 comments"
        print(f"✓ Verified 3 comments exist")
        
        # Delete file (should CASCADE delete comments)
        cursor.execute("DELETE FROM files WHERE id = %s", (file_id,))
        conn.commit()
        print(f"✓ Deleted file: {file_id}")
        
        # Verify comments were deleted
        cursor.execute("SELECT COUNT(*) FROM comments WHERE file_id = %s", (file_id,))
        count = cursor.fetchone()[0]
        assert count == 0, "Comments should be deleted"
        print(f"✓ PASSED: All 3 comments CASCADE deleted with file")
        
        # Cleanup
        cleanup_test_data(conn, user_ids=[user_id])
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def test_shares_cascade():
    """
    Test shares CASCADE when file deleted
    """
    print("\n" + "="*70)
    print("Step 7: Test shares CASCADE - deleted when file deleted")
    print("="*70)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Create user
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, f'test-share-{user_id}@example.com', 'hash', 'Test User', True, True, 'user'))
        conn.commit()
        print(f"✓ Created user: {user_id}")
        
        # Create file
        file_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO files (id, title, owner_id, file_type, is_starred, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (file_id, 'Test File', user_id, 'canvas', False, False))
        conn.commit()
        print(f"✓ Created file: {file_id}")
        
        # Create share
        share_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO shares (id, file_id, token, permission, password_hash, is_public, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (share_id, file_id, 'test-token-123', 'view', None, True, user_id))
        conn.commit()
        print(f"✓ Created share: {share_id}")
        
        # Verify share exists
        cursor.execute("SELECT COUNT(*) FROM shares WHERE file_id = %s", (file_id,))
        count = cursor.fetchone()[0]
        assert count == 1, "Share should exist"
        print(f"✓ Verified share exists")
        
        # Delete file (should CASCADE delete share)
        cursor.execute("DELETE FROM files WHERE id = %s", (file_id,))
        conn.commit()
        print(f"✓ Deleted file: {file_id}")
        
        # Verify share was deleted
        cursor.execute("SELECT COUNT(*) FROM shares WHERE id = %s", (share_id,))
        count = cursor.fetchone()[0]
        assert count == 0, "Share should be deleted"
        print(f"✓ PASSED: Share CASCADE deleted with file")
        
        # Cleanup
        cleanup_test_data(conn, user_ids=[user_id])
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def test_audit_log_set_null():
    """
    Test audit_log.user_id SET NULL when user deleted
    This preserves audit trail even when user deleted
    """
    print("\n" + "="*70)
    print("Step 8: Test audit_log SET NULL - user_id nulled, log preserved")
    print("="*70)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Create user
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, f'test-audit-{user_id}@example.com', 'hash', 'Test User', True, True, 'user'))
        conn.commit()
        print(f"✓ Created user: {user_id}")
        
        # Create audit log entry (id is auto-increment bigint)
        cursor.execute("""
            INSERT INTO audit_log (user_id, action, resource_type, resource_id, extra_data)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (user_id, 'user.login', 'user', user_id, '{"ip": "127.0.0.1"}'))
        audit_id = cursor.fetchone()[0]
        conn.commit()
        print(f"✓ Created audit log: {audit_id}")
        
        # Verify audit log has user_id
        cursor.execute("SELECT user_id FROM audit_log WHERE id = %s", (audit_id,))
        log_user = cursor.fetchone()[0]
        assert log_user == user_id, "Audit log should have user_id"
        print(f"✓ Verified audit_log.user_id = {user_id}")
        
        # Delete user (should SET NULL user_id, preserve log)
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        print(f"✓ Deleted user: {user_id}")
        
        # Verify audit log still exists
        cursor.execute("SELECT COUNT(*) FROM audit_log WHERE id = %s", (audit_id,))
        count = cursor.fetchone()[0]
        assert count == 1, "Audit log should be preserved"
        print(f"✓ Audit log preserved after user deletion")
        
        # Verify user_id set to NULL
        cursor.execute("SELECT user_id FROM audit_log WHERE id = %s", (audit_id,))
        log_user = cursor.fetchone()[0]
        assert log_user is None, "user_id should be NULL"
        print(f"✓ PASSED: audit_log.user_id set to NULL, preserving audit trail")
        
        # Cleanup
        cursor.execute("DELETE FROM audit_log WHERE id = %s", (audit_id,))
        conn.commit()
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Run all foreign key constraint tests"""
    print("="*70)
    print("Feature #24: PostgreSQL foreign key constraints enforce referential integrity")
    print("="*70)
    
    tests = [
        ("CASCADE Delete (user -> file -> versions)", test_cascade_delete),
        ("SET NULL (versions.created_by)", test_set_null_delete),
        ("Multi-level CASCADE", test_multiple_cascades),
        ("Folder SET NULL", test_folder_set_null),
        ("Team SET NULL", test_team_set_null),
        ("Comments CASCADE", test_comments_cascade),
        ("Shares CASCADE", test_shares_cascade),
        ("Audit Log SET NULL", test_audit_log_set_null),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*70)
    print("Test Results Summary")
    print("="*70)
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*70)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {len(results)}")
    
    if failed == 0:
        print("\n✓ All tests PASSED - Feature #24 is fully functional!")
        print("="*70)
        return 0
    else:
        print(f"\n✗ {failed} test(s) FAILED - Feature #24 needs fixes")
        print("="*70)
        return 1

if __name__ == "__main__":
    exit(main())
