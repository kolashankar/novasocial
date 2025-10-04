import boto3
import base64
import os
import uuid
from typing import Optional
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class CloudStorage:
    def __init__(self):
        """Initialize cloud storage with AWS S3 configuration"""
        self.s3_client = None
        self.bucket_name = os.getenv('AWS_S3_BUCKET', 'novasocial-media')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Try to initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=self.region
            )
        except Exception as e:
            logger.warning(f"Could not initialize S3 client: {e}")
            logger.info("Will use base64 storage as fallback")

    def upload_media(self, base64_data: str, media_type: str = 'image', file_extension: str = 'jpg') -> str:
        """
        Upload media to cloud storage or keep as base64 if cloud is unavailable
        
        Args:
            base64_data: Base64 encoded media data
            media_type: Type of media (image, video)
            file_extension: File extension (jpg, png, mp4, etc.)
            
        Returns:
            URL of uploaded file or original base64 if cloud upload fails
        """
        try:
            if not self.s3_client or not base64_data:
                return base64_data
            
            # Remove data URL prefix if present
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]
            
            # Decode base64 data
            try:
                file_data = base64.b64decode(base64_data)
            except Exception as e:
                logger.error(f"Failed to decode base64 data: {e}")
                return base64_data
            
            # Generate unique filename
            filename = f"{media_type}s/{uuid.uuid4()}.{file_extension}"
            
            # Set content type
            content_type_map = {
                'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                'png': 'image/png', 'gif': 'image/gif',
                'mp4': 'video/mp4', 'mov': 'video/quicktime',
                'webm': 'video/webm'
            }
            content_type = content_type_map.get(file_extension.lower(), 'application/octet-stream')
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=file_data,
                ContentType=content_type,
                ACL='public-read'
            )
            
            # Return public URL
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{filename}"
            logger.info(f"Successfully uploaded {filename} to S3")
            return url
            
        except ClientError as e:
            logger.error(f"AWS S3 upload failed: {e}")
            return base64_data
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return base64_data

    def delete_media(self, url: str) -> bool:
        """
        Delete media from cloud storage
        
        Args:
            url: URL of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.s3_client or not url:
                return False
            
            # Check if it's a cloud URL
            if not url.startswith('https://'):
                return False
            
            # Extract filename from URL
            if self.bucket_name in url:
                filename = url.split(f"{self.bucket_name}.s3.{self.region}.amazonaws.com/")[1]
                
                # Delete from S3
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=filename
                )
                
                logger.info(f"Successfully deleted {filename} from S3")
                return True
            
        except Exception as e:
            logger.error(f"Failed to delete media: {e}")
            return False

    def create_bucket_if_not_exists(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            if not self.s3_client:
                return False
            
            # Check if bucket exists
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"Bucket {self.bucket_name} already exists")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    # Bucket doesn't exist, create it
                    try:
                        if self.region == 'us-east-1':
                            self.s3_client.create_bucket(Bucket=self.bucket_name)
                        else:
                            self.s3_client.create_bucket(
                                Bucket=self.bucket_name,
                                CreateBucketConfiguration={'LocationConstraint': self.region}
                            )
                        
                        # Set bucket policy for public read
                        bucket_policy = {
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Sid": "PublicRead",
                                    "Effect": "Allow",
                                    "Principal": "*",
                                    "Action": "s3:GetObject",
                                    "Resource": f"arn:aws:s3:::{self.bucket_name}/*"
                                }
                            ]
                        }
                        
                        import json
                        self.s3_client.put_bucket_policy(
                            Bucket=self.bucket_name,
                            Policy=json.dumps(bucket_policy)
                        )
                        
                        logger.info(f"Created bucket {self.bucket_name} successfully")
                        return True
                    except Exception as create_error:
                        logger.error(f"Failed to create bucket: {create_error}")
                        return False
                else:
                    logger.error(f"Error checking bucket: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"Unexpected error in bucket creation: {e}")
            return False

    def get_storage_type(self) -> str:
        """Get current storage type being used"""
        return "cloud" if self.s3_client else "base64"


# Global instance
cloud_storage = CloudStorage()


# Helper functions for easy import
def upload_to_cloud(base64_data: str, media_type: str = 'image', file_extension: str = 'jpg') -> str:
    """Helper function to upload media to cloud storage"""
    return cloud_storage.upload_media(base64_data, media_type, file_extension)


def delete_from_cloud(url: str) -> bool:
    """Helper function to delete media from cloud storage"""
    return cloud_storage.delete_media(url)


def init_cloud_storage():
    """Initialize cloud storage (create bucket if needed)"""
    return cloud_storage.create_bucket_if_not_exists()