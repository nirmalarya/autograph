"""
AutoGraph v3 - Database Backup and Restore Utilities

Provides utilities for backing up and restoring PostgreSQL database.
Supports pg_dump, pg_restore, and MinIO storage integration.
"""

import os
import subprocess
import datetime
import logging
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DatabaseBackupManager:
    """Manages PostgreSQL database backups and restores"""
    
    def __init__(
        self,
        postgres_host: str,
        postgres_port: int,
        postgres_db: str,
        postgres_user: str,
        postgres_password: str,
        backup_dir: str = "/tmp/backups",
        minio_endpoint: Optional[str] = None,
        minio_access_key: Optional[str] = None,
        minio_secret_key: Optional[str] = None,
        minio_bucket: str = "backups"
    ):
        self.postgres_host = postgres_host
        self.postgres_port = postgres_port
        self.postgres_db = postgres_db
        self.postgres_user = postgres_user
        self.postgres_password = postgres_password
        self.backup_dir = backup_dir
        self.minio_bucket = minio_bucket
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialize MinIO client if credentials provided
        self.s3_client = None
        if minio_endpoint and minio_access_key and minio_secret_key:
            try:
                self.s3_client = boto3.client(
                    's3',
                    endpoint_url=minio_endpoint,
                    aws_access_key_id=minio_access_key,
                    aws_secret_access_key=minio_secret_key,
                    region_name='us-east-1'
                )
                # Ensure bucket exists
                try:
                    self.s3_client.head_bucket(Bucket=self.minio_bucket)
                except ClientError:
                    self.s3_client.create_bucket(Bucket=self.minio_bucket)
                    logger.info(f"Created MinIO bucket: {self.minio_bucket}")
            except Exception as e:
                logger.warning(f"Failed to initialize MinIO client: {e}")
    
    def create_backup(
        self,
        backup_name: Optional[str] = None,
        backup_format: str = "custom",
        upload_to_minio: bool = True
    ) -> Dict[str, Any]:
        """
        Create a PostgreSQL database backup using pg_dump
        
        Args:
            backup_name: Name for the backup file (auto-generated if not provided)
            backup_format: pg_dump format (custom, plain, directory, tar)
            upload_to_minio: Whether to upload to MinIO after backup
        
        Returns:
            Dict with backup metadata (file_path, size, timestamp, etc.)
        """
        # Generate backup filename
        if not backup_name:
            timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"autograph_backup_{timestamp}"
        
        # Determine file extension based on format
        extensions = {
            "custom": ".dump",
            "plain": ".sql",
            "directory": "",
            "tar": ".tar"
        }
        file_extension = extensions.get(backup_format, ".dump")
        backup_file = os.path.join(self.backup_dir, f"{backup_name}{file_extension}")
        
        try:
            # Set environment variable for password
            env = os.environ.copy()
            env['PGPASSWORD'] = self.postgres_password
            
            # Build pg_dump command
            cmd = [
                'pg_dump',
                '-h', self.postgres_host,
                '-p', str(self.postgres_port),
                '-U', self.postgres_user,
                '-d', self.postgres_db,
                '-F', backup_format[0],  # c for custom, p for plain, d for directory, t for tar
                '-f', backup_file,
                '--verbose'
            ]
            
            logger.info(f"Starting database backup: {backup_name}")
            logger.debug(f"Command: {' '.join(cmd)}")
            
            # Execute pg_dump
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                logger.error(f"Backup failed: {error_msg}")
                raise Exception(f"pg_dump failed: {error_msg}")
            
            # Get backup file size
            file_size = os.path.getsize(backup_file)
            
            # Upload to MinIO if requested
            minio_key = None
            if upload_to_minio and self.s3_client:
                minio_key = f"postgres/{backup_name}{file_extension}"
                try:
                    self.s3_client.upload_file(
                        backup_file,
                        self.minio_bucket,
                        minio_key
                    )
                    logger.info(f"Uploaded backup to MinIO: {minio_key}")
                except Exception as e:
                    logger.warning(f"Failed to upload to MinIO: {e}")
                    minio_key = None
            
            backup_metadata = {
                "backup_name": backup_name,
                "file_path": backup_file,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "format": backup_format,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "database": self.postgres_db,
                "uploaded_to_minio": minio_key is not None,
                "minio_key": minio_key,
                "success": True
            }
            
            logger.info(f"Backup completed successfully: {backup_name} ({backup_metadata['file_size_mb']} MB)")
            return backup_metadata
            
        except subprocess.TimeoutExpired:
            logger.error("Backup timed out after 5 minutes")
            raise Exception("Backup operation timed out")
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            raise
    
    def restore_backup(
        self,
        backup_file: Optional[str] = None,
        backup_name: Optional[str] = None,
        download_from_minio: bool = False,
        clean: bool = False
    ) -> Dict[str, Any]:
        """
        Restore a PostgreSQL database from backup using pg_restore
        
        Args:
            backup_file: Path to local backup file
            backup_name: Name of backup in MinIO (if downloading)
            download_from_minio: Whether to download from MinIO first
            clean: Whether to clean (drop) database objects before restoring
        
        Returns:
            Dict with restore metadata
        """
        # Download from MinIO if requested
        if download_from_minio and backup_name and self.s3_client:
            minio_key = f"postgres/{backup_name}"
            backup_file = os.path.join(self.backup_dir, backup_name)
            
            try:
                logger.info(f"Downloading backup from MinIO: {minio_key}")
                self.s3_client.download_file(
                    self.minio_bucket,
                    minio_key,
                    backup_file
                )
            except Exception as e:
                logger.error(f"Failed to download from MinIO: {e}")
                raise Exception(f"Failed to download backup: {str(e)}")
        
        if not backup_file or not os.path.exists(backup_file):
            raise Exception(f"Backup file not found: {backup_file}")
        
        try:
            # Set environment variable for password
            env = os.environ.copy()
            env['PGPASSWORD'] = self.postgres_password
            
            # Build pg_restore command
            cmd = [
                'pg_restore',
                '-h', self.postgres_host,
                '-p', str(self.postgres_port),
                '-U', self.postgres_user,
                '-d', self.postgres_db,
                '--verbose'
            ]
            
            if clean:
                cmd.append('--clean')
            
            cmd.append(backup_file)
            
            logger.info(f"Starting database restore from: {backup_file}")
            logger.debug(f"Command: {' '.join(cmd)}")
            
            # Execute pg_restore
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            # pg_restore may return non-zero even on success due to warnings
            # Check for critical errors
            if result.returncode != 0:
                stderr = result.stderr or ""
                # These are warnings, not errors
                if "already exists" in stderr.lower() or "no matching tables" in stderr.lower():
                    logger.warning(f"Restore completed with warnings: {stderr}")
                else:
                    logger.error(f"Restore failed: {stderr}")
                    raise Exception(f"pg_restore failed: {stderr}")
            
            restore_metadata = {
                "backup_file": backup_file,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "database": self.postgres_db,
                "success": True
            }
            
            logger.info(f"Restore completed successfully from: {backup_file}")
            return restore_metadata
            
        except subprocess.TimeoutExpired:
            logger.error("Restore timed out after 5 minutes")
            raise Exception("Restore operation timed out")
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            raise
    
    def list_backups(self, include_local: bool = True, include_minio: bool = True) -> Dict[str, Any]:
        """
        List available backups from local and/or MinIO storage
        
        Args:
            include_local: Include backups from local storage
            include_minio: Include backups from MinIO
        
        Returns:
            Dict with lists of backups
        """
        backups = {
            "local": [],
            "minio": []
        }
        
        # List local backups
        if include_local and os.path.exists(self.backup_dir):
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    backups["local"].append({
                        "name": filename,
                        "path": file_path,
                        "size_bytes": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        # List MinIO backups
        if include_minio and self.s3_client:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.minio_bucket,
                    Prefix='postgres/'
                )
                
                for obj in response.get('Contents', []):
                    backups["minio"].append({
                        "name": obj['Key'].replace('postgres/', ''),
                        "key": obj['Key'],
                        "size_bytes": obj['Size'],
                        "size_mb": round(obj['Size'] / (1024 * 1024), 2),
                        "modified": obj['LastModified'].isoformat()
                    })
            except Exception as e:
                logger.warning(f"Failed to list MinIO backups: {e}")
        
        return backups
    
    def delete_backup(self, backup_name: str, delete_local: bool = True, delete_minio: bool = True) -> Dict[str, Any]:
        """
        Delete a backup from local and/or MinIO storage
        
        Args:
            backup_name: Name of the backup to delete
            delete_local: Delete from local storage
            delete_minio: Delete from MinIO
        
        Returns:
            Dict with deletion results
        """
        results = {
            "local_deleted": False,
            "minio_deleted": False
        }
        
        # Delete local backup
        if delete_local:
            local_file = os.path.join(self.backup_dir, backup_name)
            if os.path.exists(local_file):
                try:
                    os.remove(local_file)
                    results["local_deleted"] = True
                    logger.info(f"Deleted local backup: {backup_name}")
                except Exception as e:
                    logger.warning(f"Failed to delete local backup: {e}")
        
        # Delete MinIO backup
        if delete_minio and self.s3_client:
            minio_key = f"postgres/{backup_name}"
            try:
                self.s3_client.delete_object(
                    Bucket=self.minio_bucket,
                    Key=minio_key
                )
                results["minio_deleted"] = True
                logger.info(f"Deleted MinIO backup: {minio_key}")
            except Exception as e:
                logger.warning(f"Failed to delete MinIO backup: {e}")
        
        return results
