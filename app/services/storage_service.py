import os
import uuid
import logging
from flask import current_app

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def _get_storage_client():
    """Create a GCS client, supporting explicit credentials file or ADC."""
    from google.cloud import storage

    creds_file = current_app.config.get("GCS_CREDENTIALS_FILE") or os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )
    project_id = current_app.config.get("GCS_PROJECT_ID")

    if creds_file:
        return storage.Client.from_service_account_json(creds_file, project=project_id)
    return storage.Client(project=project_id)


def upload_avatar(file_data, filename, content_type):
    """Upload avatar image to Google Cloud Storage."""
    bucket_name = current_app.config.get("GCS_BUCKET_NAME")
    if not bucket_name:
        raise RuntimeError("GCS_BUCKET_NAME not configured")

    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(
            f"Invalid image type: {content_type}. Allowed: JPEG, PNG, GIF, WebP"
        )

    max_size = current_app.config.get("MAX_AVATAR_SIZE", 2 * 1024 * 1024)
    if len(file_data) > max_size:
        raise ValueError(
            f"Image too large. Maximum size: {max_size // (1024 * 1024)}MB"
        )

    from google.cloud import storage

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    blob_name = f"avatars/{uuid.uuid4().hex}.{ext}"

    client = _get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.upload_from_string(file_data, content_type=content_type)

    return blob_name


def get_avatar(blob_name):
    """Retrieve an avatar image from Google Cloud Storage."""
    bucket_name = current_app.config.get("GCS_BUCKET_NAME")
    if not bucket_name or not blob_name:
        return None, None

    try:
        client = _get_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        if not blob.exists():
            return None, None

        file_data = blob.download_as_bytes()
        content_type = blob.content_type or "image/jpeg"

        return file_data, content_type
    except Exception as e:
        logger.warning(f"Failed to retrieve avatar from GCS: {e}")
        return None, None


def delete_avatar(blob_name):
    """Delete an avatar image from Google Cloud Storage."""
    if not blob_name:
        return

    bucket_name = current_app.config.get("GCS_BUCKET_NAME")
    if not bucket_name:
        return

    try:
        client = _get_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()

    except Exception as e:
        logger.warning(f"Failed to delete avatar from GCS: {e}")
