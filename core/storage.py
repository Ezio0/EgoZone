"""
GCS Storage Utility
Used for persisting data to Google Cloud Storage
"""

from google.cloud import storage
from pathlib import Path
import json
import os
from typing import Optional, Any
from config import get_settings


class GCSStorage:
    """Google Cloud Storage utility"""

    def __init__(self, bucket_name: Optional[str] = None):
        settings = get_settings()
        self.bucket_name = bucket_name or settings.gcs_bucket
        self.use_gcs = settings.use_gcs and self.bucket_name
        self._client = None
        self._bucket = None

    @property
    def client(self):
        """Lazy initialize GCS client"""
        if self._client is None and self.use_gcs:
            self._client = storage.Client()
        return self._client

    @property
    def bucket(self):
        """Get bucket"""
        if self._bucket is None and self.client:
            self._bucket = self.client.bucket(self.bucket_name)
        return self._bucket

    def upload_json(self, data: Any, gcs_path: str) -> bool:
        """
        Upload JSON data to GCS

        Args:
            data: Data to upload (JSON serializable)
            gcs_path: Path in GCS, e.g. 'data/user_profile.json'

        Returns:
            Whether successful
        """
        if not self.use_gcs:
            return False

        try:
            blob = self.bucket.blob(gcs_path)
            json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            blob.upload_from_string(json_str, content_type="application/json")
            print(f"✅ Uploaded to GCS: gs://{self.bucket_name}/{gcs_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to upload to GCS: {e}")
            return False

    def download_json(self, gcs_path: str) -> Optional[Any]:
        """
        Download JSON data from GCS

        Args:
            gcs_path: Path in GCS

        Returns:
            Parsed JSON data, or None if failed
        """
        if not self.use_gcs:
            return None

        try:
            blob = self.bucket.blob(gcs_path)
            if not blob.exists():
                print(f"📂 GCS file does not exist: gs://{self.bucket_name}/{gcs_path}")
                return None

            json_str = blob.download_as_text()
            data = json.loads(json_str)
            print(f"✅ Downloaded from GCS: gs://{self.bucket_name}/{gcs_path}")
            return data
        except Exception as e:
            print(f"❌ Failed to download from GCS: {e}")
            return None

    def upload_file(self, local_path: str, gcs_path: str) -> bool:
        """Upload local file to GCS"""
        if not self.use_gcs:
            return False

        try:
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_filename(local_path)
            print(
                f"✅ Uploaded file to GCS: {local_path} -> gs://{self.bucket_name}/{gcs_path}"
            )
            return True
        except Exception as e:
            print(f"❌ Failed to upload file to GCS: {e}")
            return False

    def download_file(self, gcs_path: str, local_path: str) -> bool:
        """Download file from GCS to local"""
        if not self.use_gcs:
            return False

        try:
            blob = self.bucket.blob(gcs_path)
            if not blob.exists():
                return False

            # Ensure directory exists
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(local_path)
            print(
                f"✅ Downloaded file from GCS: gs://{self.bucket_name}/{gcs_path} -> {local_path}"
            )
            return True
        except Exception as e:
            print(f"❌ Failed to download file from GCS: {e}")
            return False

    def upload_directory(self, local_dir: str, gcs_prefix: str) -> bool:
        """Recursively upload directory to GCS"""
        if not self.use_gcs:
            return False

        try:
            local_path = Path(local_dir)
            if not local_path.exists():
                return False

            for file_path in local_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(local_path)
                    gcs_path = f"{gcs_prefix}/{relative_path}"
                    self.upload_file(str(file_path), gcs_path)

            print(
                f"✅ Uploaded directory to GCS: {local_dir} -> gs://{self.bucket_name}/{gcs_prefix}"
            )
            return True
        except Exception as e:
            print(f"❌ Failed to upload directory to GCS: {e}")
            return False

    def download_directory(self, gcs_prefix: str, local_dir: str) -> bool:
        """Download directory from GCS"""
        if not self.use_gcs:
            return False

        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=gcs_prefix)
            downloaded = False

            for blob in blobs:
                if blob.name.endswith("/"):  # Skip directory markers
                    continue

                relative_path = blob.name[len(gcs_prefix) :].lstrip("/")
                local_path = Path(local_dir) / relative_path
                local_path.parent.mkdir(parents=True, exist_ok=True)
                blob.download_to_filename(str(local_path))
                downloaded = True

            if downloaded:
                print(
                    f"✅ Downloaded directory from GCS: gs://{self.bucket_name}/{gcs_prefix} -> {local_dir}"
                )
            return downloaded
        except Exception as e:
            print(f"❌ Failed to download directory from GCS: {e}")
            return False


# Global storage instance
_gcs_storage: Optional[GCSStorage] = None


def get_gcs_storage() -> GCSStorage:
    """Get GCS storage instance (singleton)"""
    global _gcs_storage
    if _gcs_storage is None:
        _gcs_storage = GCSStorage()
    return _gcs_storage
