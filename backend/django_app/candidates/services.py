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
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if it doesn't."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {str(e)}")
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
    
    def get_file_url(self, object_path, expires=3600):
        """Get a presigned URL for file access."""
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_path,
                expires=expires
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise
    
    def delete_file(self, object_path):
        """Delete a file from MinIO."""
        try:
            self.client.remove_object(self.bucket_name, object_path)
            logger.info(f"Deleted file from MinIO: {object_path}")
        except S3Error as e:
            logger.error(f"Error deleting file from MinIO: {str(e)}")
            raise

