"""Services for candidate management including MinIO integration."""
import os
import uuid
from datetime import datetime
from minio import Minio
from minio.error import S3Error
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class MinIOService:
    """Service for MinIO object storage operations."""
    
    def __init__(self):
        try:
            # Ensure we're using the correct endpoint format
            endpoint = settings.MINIO_ENDPOINT
            if endpoint.startswith('http://'):
                endpoint = endpoint.replace('http://', '')
            elif endpoint.startswith('https://'):
                endpoint = endpoint.replace('https://', '')
            
            logger.info(f"Initializing MinIO client with endpoint: {endpoint}")
            
            self.client = Minio(
                endpoint=endpoint,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
                region='us-east-1'  # Add region to avoid issues with some MinIO versions
            )
            self.bucket_name = settings.MINIO_BUCKET_NAME
            
            # Test connection
            try:
                if not self.client.bucket_exists(self.bucket_name):
                    logger.warning(f"Bucket {self.bucket_name} does not exist, creating it...")
                    self.client.make_bucket(self.bucket_name)
                logger.info(f"Successfully connected to MinIO. Bucket '{self.bucket_name}' is ready.")
            except Exception as e:
                logger.error(f"Failed to verify MinIO bucket: {str(e)}", exc_info=True)
                raise
                
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {str(e)}", exc_info=True)
            raise
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create it if it doesn't."""
        try:
            logger.info(f"Checking if bucket exists: {self.bucket_name}")
            if not self.client.bucket_exists(self.bucket_name):
                logger.info(f"Bucket {self.bucket_name} does not exist, creating it...")
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Successfully created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket {self.bucket_name} already exists")
        except Exception as e:
            logger.error(f"Error ensuring bucket exists: {str(e)}", exc_info=True)
            raise
    
    def upload_file(self, file, user_id):
        """Upload a file to MinIO and return the object path."""
        try:
            # Generate unique file path
            file_extension = os.path.splitext(file.name)[1]
            file_name = f"{uuid.uuid4()}{file_extension}"
            object_path = f"users/{user_id}/{datetime.now().strftime('%Y/%m/%d')}/{file_name}"
            
            # Upload file
            file.seek(0)  # Reset file pointer
            self.client.put_object(
                self.bucket_name,
                object_path,
                file,
                length=file.size,
                content_type=file.content_type
            )
            
            logger.info(f"Uploaded file to MinIO: {object_path}")
            return object_path
        except S3Error as e:
            logger.error(f"Error uploading file to MinIO: {str(e)}")
            raise
    
    def get_file_url(self, object_path, expires_seconds=3600):
        """Get a presigned URL for file access."""
        try:
            logger.info(f"Starting get_file_url for object_path: {object_path}")
            
            # Ensure object_path is a string and normalize the path
            original_path = object_path
            object_path = str(object_path).replace('%2F', '/').replace('\\', '/').lstrip('/')
            
            if original_path != object_path:
                logger.info(f"Normalized object path from '{original_path}' to '{object_path}'")
            
            # Log MinIO client configuration
            logger.info(f"MinIO Configuration - Endpoint: {self.client._endpoint_url}, Bucket: {self.bucket_name}")
            logger.info(f"Generating presigned URL for object: {object_path}")
            
            # Check if object exists first
            try:
                obj_stat = self.client.stat_object(self.bucket_name, object_path)
                logger.info(f"File found in MinIO - Size: {obj_stat.size} bytes, Last Modified: {obj_stat.last_modified}")
            except Exception as e:
                logger.error(f"File not found in MinIO: {str(e)}", exc_info=True)
                return None
            
            # Generate the presigned URL
            try:
                url = self.client.presigned_get_object(
                    bucket_name=self.bucket_name,
                    object_name=object_path,
                    expires=expires_seconds
                )
                
                if not url:
                    logger.error("Failed to generate presigned URL: Empty URL returned")
                    return None
                    
                logger.info(f"Successfully generated presigned URL: {url}")
                return url
                
            except Exception as e:
                logger.error(f"Error generating presigned URL: {str(e)}", exc_info=True)
                return None
            
        except Exception as e:
            logger.error(f"Unexpected error in get_file_url: {str(e)}", exc_info=True)
            return None
        
    def get_file(self, object_path):
        """Get a file object from MinIO."""
        try:
            # Normalize the path
            object_path = str(object_path).replace('%2F', '/').replace('\\', '/').lstrip('/')
            
            # Get object from MinIO
            response = self.client.get_object(self.bucket_name, object_path)
            return response
        except S3Error as e:
            logger.error(f"Error getting file from MinIO: {str(e)}")
            raise
    
    def delete_file(self, object_path):
        """Delete a file from MinIO."""
        try:
            self.client.remove_object(self.bucket_name, object_path)
            logger.info(f"Deleted file from MinIO: {object_path}")
        except S3Error as e:
            logger.error(f"Error deleting file from MinIO: {str(e)}")
            raise

