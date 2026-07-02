import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class S3ClientWrapper:
    def __init__(self):
        endpoint_url = settings.S3_ENDPOINT_URL if settings.S3_ENDPOINT_URL and settings.S3_ENDPOINT_URL.strip() else None
        self.s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name=settings.S3_REGION
        )
        public_endpoint = getattr(settings, "S3_PUBLIC_ENDPOINT_URL", settings.S3_ENDPOINT_URL)
        public_endpoint_url = public_endpoint if public_endpoint and public_endpoint.strip() else None
        self.s3_public = boto3.client(
            "s3",
            endpoint_url=public_endpoint_url,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name=settings.S3_REGION
        )
        self.bucket = settings.S3_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Checks if the bucket exists; creates it if missing."""
        try:
            self.s3.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                logger.info(f"Bucket {self.bucket} not found. Creating bucket...")
                try:
                    self.s3.create_bucket(Bucket=self.bucket)
                except Exception as ex:
                    logger.error(f"Failed to create bucket: {ex}")
                    raise

    def upload_file(self, file_content: bytes, object_key: str, content_type: str = "application/octet-stream") -> str:
        """Uploads raw file content to S3 and returns the S3 URI."""
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=file_content,
                ContentType=content_type
            )
            return f"s3://{self.bucket}/{object_key}"
        except Exception as e:
            logger.error(f"Failed to upload object {object_key} to S3: {e}")
            raise

    def generate_presigned_url(self, object_key: str, expiration: int = 86400) -> str:
        """Generates a pre-signed URL to retrieve a file from S3."""
        try:
            url = self.s3_public.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": object_key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate pre-signed URL for {object_key}: {e}")
            raise

    def generate_presigned_upload_url(self, object_key: str, expiration: int = 3600) -> str:
        """Generates a PUT pre-signed URL for direct client-to-S3 upload."""
        try:
            url = self.s3_public.generate_presigned_url(
                "put_object",
                Params={"Bucket": self.bucket, "Key": object_key},
                ExpiresIn=expiration,
                HttpMethod="PUT"
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate pre-signed upload URL for {object_key}: {e}")
            raise

    def download_file(self, object_key: str) -> bytes:
        """Downloads a file from S3 and returns raw bytes."""
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=object_key)
            return response["Body"].read()
        except Exception as e:
            logger.error(f"Failed to download object {object_key} from S3: {e}")
            raise

    def file_exists(self, object_key: str) -> bool:
        """Checks if an object exists in S3 without downloading it."""
        try:
            self.s3.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                return False
            logger.error(f"Error checking if {object_key} exists: {e}")
            raise

s3_client = S3ClientWrapper()
