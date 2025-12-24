#!/usr/bin/env python3
"""
Cleanup job to permanently delete diagrams from trash after 30 days.

This script should be run periodically (e.g., daily via cron) to clean up old diagrams.
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta, timezone

# Retention period (30 days)
RETENTION_DAYS = 30

def run_sql(sql):
    """Run SQL command in PostgreSQL container."""
    result = subprocess.run(
        ["docker", "exec", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph", "-t", "-c", sql],
        capture_output=True,
        text=True
    )
    return result.stdout.strip(), result.returncode

def cleanup_old_trash():
    """Permanently delete diagrams that have been in trash for more than 30 days."""
    
    print("=" * 80)
    print("TRASH CLEANUP JOB")
    print("=" * 80)
    print(f"Retention period: {RETENTION_DAYS} days")
    print()
    
    try:
        # Calculate cutoff date (30 days ago)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
        print(f"Cutoff date: {cutoff_date.isoformat()}")
        print(f"Current time: {datetime.now(timezone.utc).isoformat()}")
        print()
        
        # Find diagrams deleted more than 30 days ago
        sql = f"""
        SELECT id, title, owner_id, deleted_at 
        FROM files 
        WHERE is_deleted = true 
        AND deleted_at < '{cutoff_date.isoformat()}'
        ORDER BY deleted_at;
        """
        
        output, code = run_sql(sql)
        
        if code != 0:
            print(f"❌ Failed to query old diagrams")
            print(output)
            return -1
        
        # Parse output
        old_diagrams = []
        if output:
            for line in output.strip().split('\n'):
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 4:
                        old_diagrams.append({
                            'id': parts[0].strip(),
                            'title': parts[1].strip(),
                            'owner_id': parts[2].strip(),
                            'deleted_at': parts[3].strip()
                        })
        
        print(f"Found {len(old_diagrams)} diagrams to permanently delete")
        
        if len(old_diagrams) == 0:
            print("No diagrams to delete. Cleanup complete.")
            return 0
        
        # Delete each diagram
        deleted_count = 0
        for diagram in old_diagrams:
            print(f"\nDeleting diagram: {diagram['id']}")
            print(f"  Title: {diagram['title']}")
            print(f"  Owner: {diagram['owner_id']}")
            print(f"  Deleted at: {diagram['deleted_at']}")
            
            # Delete all versions first
            sql = f"DELETE FROM versions WHERE file_id = '{diagram['id']}';"
            output, code = run_sql(sql)
            
            if code != 0:
                print(f"  ❌ Failed to delete versions")
                continue
            
            # Extract number of deleted rows
            if "DELETE" in output:
                versions_deleted = output.split()[-1] if output.split() else "0"
                print(f"  Versions deleted: {versions_deleted}")
            
            # Delete the diagram
            sql = f"DELETE FROM files WHERE id = '{diagram['id']}';"
            output, code = run_sql(sql)
            
            if code != 0:
                print(f"  ❌ Failed to delete diagram")
                continue
            
            deleted_count += 1
            print(f"  ✅ Diagram deleted")
        
        print()
        print("=" * 80)
        print(f"✅ Cleanup complete! Permanently deleted {deleted_count} diagrams")
        print("=" * 80)
        
        return deleted_count
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        return -1


if __name__ == "__main__":
    deleted = cleanup_old_trash()
    sys.exit(0 if deleted >= 0 else 1)
