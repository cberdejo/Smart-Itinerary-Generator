import os
from dotenv import load_dotenv
from app_config.logger import get_logger
from minio import Minio, S3Error

load_dotenv()

logger = get_logger("minio")

BUCKET = "reports"


def get_minio():
    host = os.getenv("MINIO_HOST", "localhost")
    port = os.getenv("MINIO_PORT", "9000")
    endpoint = f"{host}:{port}"
    return Minio(
        endpoint=endpoint,
        access_key=os.getenv("MINIO_ROOT_USER"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD"),
        secure=False,
    )


def setup_minio_buckets(client: Minio):
    """Create required buckets if they don't exist.
    Args:
        client (Minio): Minio client instance.
    Raises:
        S3Error: If there is an error creating or verifying the bucket.
    """
    try:
        if not client.bucket_exists(BUCKET):
            logger.info(f"Bucket '{BUCKET}' not found. Creating it...")
            client.make_bucket(BUCKET)
            logger.info(f"Bucket '{BUCKET}' created successfully.")
        else:
            logger.info(f"Bucket '{BUCKET}' already exists.")
    except S3Error as e:
        logger.error(f"Failed to create or verify bucket '{BUCKET}': {str(e)}")
        raise
