from app_config.logger import get_logger
from minio import Minio, S3Error


logger = get_logger("minio")

BUCKET = "reports"


def get_minio(minio_endpoint, minio_access_key, minio_secret_key):
    """
    Returns a Minio client instance.

    Args:
        minio_endpoint (str): Minio endpoint.
        minio_access_key (str): Minio access key.
        minio_secret_key (str): Minio secret key.

    Returns:
        Minio: Minio client instance.
    """
    return Minio(
        endpoint=minio_endpoint,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
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
