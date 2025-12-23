"""
AutoGraph v3 - Database and MinIO Backup and Restore Utilities

Provides utilities for backing up and restoring PostgreSQL database and MinIO buckets.
Supports pg_dump, pg_restore, and MinIO bucket mirroring.
"""

import os
import subprocess
import datetime
import logging
import shutil
import tempfile
from typing import Optional, Dict, Any, List
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


class MinIOBucketBackupManager:
    """Manages MinIO bucket backups and restores"""
    
    def __init__(
        self,
        minio_endpoint: str,
        minio_access_key: str,
        minio_secret_key: str,
        backup_dir: str = "/tmp/minio_backups",
        backup_bucket: str = "minio-backups"
    ):
        """
        Initialize MinIO Bucket Backup Manager
        
        Args:
            minio_endpoint: MinIO endpoint URL (e.g., http://minio:9000)
            minio_access_key: MinIO access key
            minio_secret_key: MinIO secret key
            backup_dir: Local directory for temporary backup files
            backup_bucket: Bucket to store backup archives
        """
        self.minio_endpoint = minio_endpoint
        self.backup_dir = backup_dir
        self.backup_bucket_name = backup_bucket  # Renamed to avoid shadowing method
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialize boto3 S3 client for MinIO
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=minio_endpoint,
                aws_access_key_id=minio_access_key,
                aws_secret_access_key=minio_secret_key,
                region_name='us-east-1'
            )
            
            # Ensure backup bucket exists
            try:
                self.s3_client.head_bucket(Bucket=self.backup_bucket_name)
            except ClientError:
                self.s3_client.create_bucket(Bucket=self.backup_bucket_name)
                logger.info(f"Created MinIO backup bucket: {self.backup_bucket_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            raise
    
    def list_buckets(self) -> List[str]:
        """List all MinIO buckets"""
        try:
            response = self.s3_client.list_buckets()
            buckets = [bucket['Name'] for bucket in response.get('Buckets', [])]
            logger.info(f"Found {len(buckets)} MinIO buckets")
            return buckets
        except Exception as e:
            logger.error(f"Failed to list buckets: {e}")
            raise
    
    def backup_bucket(
        self,
        bucket_name: str,
        backup_name: Optional[str] = None,
        include_versions: bool = False
    ) -> Dict[str, Any]:
        """
        Backup a MinIO bucket by downloading all objects and creating an archive
        
        Args:
            bucket_name: Name of the bucket to backup
            backup_name: Name for the backup (auto-generated if not provided)
            include_versions: Include object versions in backup
        
        Returns:
            Dict with backup metadata
        """
        # Generate backup name if not provided
        if not backup_name:
            timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"bucket_{bucket_name}_{timestamp}"
        
        # Create temporary directory for bucket contents
        temp_bucket_dir = os.path.join(self.backup_dir, f"temp_{backup_name}")
        os.makedirs(temp_bucket_dir, exist_ok=True)
        
        try:
            # List all objects in the bucket
            logger.info(f"Starting backup of bucket: {bucket_name}")
            objects = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=bucket_name):
                objects.extend(page.get('Contents', []))
            
            logger.info(f"Found {len(objects)} objects in bucket {bucket_name}")
            
            # Download all objects
            total_size = 0
            for obj in objects:
                object_key = obj['Key']
                object_path = os.path.join(temp_bucket_dir, object_key)
                
                # Create subdirectories if needed
                os.makedirs(os.path.dirname(object_path), exist_ok=True)
                
                try:
                    self.s3_client.download_file(bucket_name, object_key, object_path)
                    total_size += obj['Size']
                    logger.debug(f"Downloaded: {object_key}")
                except Exception as e:
                    logger.warning(f"Failed to download {object_key}: {e}")
            
            # Create backup metadata file
            metadata_file = os.path.join(temp_bucket_dir, '.backup_metadata.json')
            metadata = {
                "bucket_name": bucket_name,
                "backup_name": backup_name,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "object_count": len(objects),
                "total_size_bytes": total_size,
                "include_versions": include_versions
            }
            
            import json
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Create tar.gz archive
            archive_name = f"{backup_name}.tar.gz"
            archive_path = os.path.join(self.backup_dir, archive_name)
            
            logger.info(f"Creating archive: {archive_name}")
            shutil.make_archive(
                archive_path.replace('.tar.gz', ''),
                'gztar',
                temp_bucket_dir
            )
            
            archive_size = os.path.getsize(archive_path)
            
            # Upload archive to backup bucket
            backup_key = f"buckets/{archive_name}"
            logger.info(f"Uploading archive to MinIO: {backup_key}")
            self.s3_client.upload_file(archive_path, self.backup_bucket_name, backup_key)
            
            # Clean up temporary directory
            shutil.rmtree(temp_bucket_dir, ignore_errors=True)
            
            backup_metadata = {
                "backup_name": backup_name,
                "bucket_name": bucket_name,
                "archive_path": archive_path,
                "archive_size_bytes": archive_size,
                "archive_size_mb": round(archive_size / (1024 * 1024), 2),
                "object_count": len(objects),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "backup_key": backup_key,
                "success": True
            }
            
            logger.info(
                f"Backup completed: {backup_name} "
                f"({len(objects)} objects, {backup_metadata['archive_size_mb']} MB)"
            )
            
            return backup_metadata
            
        except Exception as e:
            logger.error(f"Bucket backup failed: {str(e)}")
            # Clean up on error
            if os.path.exists(temp_bucket_dir):
                shutil.rmtree(temp_bucket_dir, ignore_errors=True)
            raise
    
    def restore_bucket(
        self,
        backup_name: str,
        target_bucket: Optional[str] = None,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Restore a MinIO bucket from backup
        
        Args:
            backup_name: Name of the backup to restore (without .tar.gz extension)
            target_bucket: Target bucket name (uses original if not provided)
            overwrite: Whether to overwrite existing objects
        
        Returns:
            Dict with restore metadata
        """
        archive_name = f"{backup_name}.tar.gz"
        archive_path = os.path.join(self.backup_dir, archive_name)
        
        # Download archive from backup bucket if not present locally
        if not os.path.exists(archive_path):
            backup_key = f"buckets/{archive_name}"
            logger.info(f"Downloading backup archive from MinIO: {backup_key}")
            try:
                self.s3_client.download_file(self.backup_bucket_name, backup_key, archive_path)
            except Exception as e:
                logger.error(f"Failed to download backup archive: {e}")
                raise Exception(f"Backup archive not found: {backup_name}")
        
        # Create temporary directory for extraction
        temp_restore_dir = os.path.join(self.backup_dir, f"restore_{backup_name}")
        os.makedirs(temp_restore_dir, exist_ok=True)
        
        try:
            # Extract archive
            logger.info(f"Extracting archive: {archive_name}")
            shutil.unpack_archive(archive_path, temp_restore_dir)
            
            # Read backup metadata
            metadata_file = os.path.join(temp_restore_dir, '.backup_metadata.json')
            if os.path.exists(metadata_file):
                import json
                with open(metadata_file, 'r') as f:
                    backup_metadata = json.load(f)
                original_bucket = backup_metadata.get('bucket_name')
            else:
                logger.warning("Backup metadata not found, proceeding without it")
                original_bucket = None
            
            # Determine target bucket
            if not target_bucket:
                if original_bucket:
                    target_bucket = original_bucket
                else:
                    raise Exception("Target bucket must be specified (metadata not found)")
            
            # Ensure target bucket exists
            try:
                self.s3_client.head_bucket(Bucket=target_bucket)
            except ClientError:
                logger.info(f"Creating target bucket: {target_bucket}")
                self.s3_client.create_bucket(Bucket=target_bucket)
            
            # Upload all files from backup to target bucket
            uploaded_count = 0
            total_size = 0
            
            for root, dirs, files in os.walk(temp_restore_dir):
                for file in files:
                    if file == '.backup_metadata.json':
                        continue
                    
                    file_path = os.path.join(root, file)
                    # Get relative path from temp_restore_dir
                    relative_path = os.path.relpath(file_path, temp_restore_dir)
                    object_key = relative_path.replace(os.sep, '/')
                    
                    # Check if object already exists
                    if not overwrite:
                        try:
                            self.s3_client.head_object(Bucket=target_bucket, Key=object_key)
                            logger.debug(f"Skipping existing object: {object_key}")
                            continue
                        except ClientError:
                            pass  # Object doesn't exist, proceed with upload
                    
                    try:
                        self.s3_client.upload_file(file_path, target_bucket, object_key)
                        uploaded_count += 1
                        total_size += os.path.getsize(file_path)
                        logger.debug(f"Uploaded: {object_key}")
                    except Exception as e:
                        logger.warning(f"Failed to upload {object_key}: {e}")
            
            # Clean up temporary directory
            shutil.rmtree(temp_restore_dir, ignore_errors=True)
            
            restore_metadata = {
                "backup_name": backup_name,
                "target_bucket": target_bucket,
                "uploaded_count": uploaded_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "success": True
            }
            
            logger.info(
                f"Restore completed: {backup_name} to {target_bucket} "
                f"({uploaded_count} objects, {restore_metadata['total_size_mb']} MB)"
            )
            
            return restore_metadata
            
        except Exception as e:
            logger.error(f"Bucket restore failed: {str(e)}")
            # Clean up on error
            if os.path.exists(temp_restore_dir):
                shutil.rmtree(temp_restore_dir, ignore_errors=True)
            raise
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available bucket backups
        
        Returns:
            List of backup metadata dicts
        """
        backups = []
        
        try:
            # List backups in MinIO backup bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.backup_bucket_name, Prefix='buckets/'):
                for obj in page.get('Contents', []):
                    if obj['Key'].endswith('.tar.gz'):
                        backup_name = obj['Key'].replace('buckets/', '').replace('.tar.gz', '')
                        backups.append({
                            "backup_name": backup_name,
                            "key": obj['Key'],
                            "size_bytes": obj['Size'],
                            "size_mb": round(obj['Size'] / (1024 * 1024), 2),
                            "modified": obj['LastModified'].isoformat()
                        })
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                logger.warning(f"Backup bucket does not exist: {self.backup_bucket_name}")
            else:
                logger.error(f"Failed to list backups: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            raise
        
        # Also check local backup directory
        if os.path.exists(self.backup_dir):
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.tar.gz'):
                    file_path = os.path.join(self.backup_dir, filename)
                    stat = os.stat(file_path)
                    backup_name = filename.replace('.tar.gz', '')
                    
                    # Check if already in list from MinIO
                    if not any(b['backup_name'] == backup_name for b in backups):
                        backups.append({
                            "backup_name": backup_name,
                            "path": file_path,
                            "size_bytes": stat.st_size,
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "local_only": True
                        })
        
        return backups
    
    def delete_backup(self, backup_name: str, delete_local: bool = True) -> Dict[str, Any]:
        """
        Delete a bucket backup
        
        Args:
            backup_name: Name of the backup to delete
            delete_local: Also delete local copy if present
        
        Returns:
            Dict with deletion results
        """
        results = {
            "minio_deleted": False,
            "local_deleted": False
        }
        
        # Delete from MinIO backup bucket
        backup_key = f"buckets/{backup_name}.tar.gz"
        try:
            self.s3_client.delete_object(Bucket=self.backup_bucket_name, Key=backup_key)
            results["minio_deleted"] = True
            logger.info(f"Deleted backup from MinIO: {backup_key}")
        except Exception as e:
            logger.warning(f"Failed to delete from MinIO: {e}")
        
        # Delete local copy
        if delete_local:
            local_file = os.path.join(self.backup_dir, f"{backup_name}.tar.gz")
            if os.path.exists(local_file):
                try:
                    os.remove(local_file)
                    results["local_deleted"] = True
                    logger.info(f"Deleted local backup: {local_file}")
                except Exception as e:
                    logger.warning(f"Failed to delete local backup: {e}")
        
        return results
