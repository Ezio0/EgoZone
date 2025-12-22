"""
GCS 存储工具
用于将数据持久化到 Google Cloud Storage
"""

from google.cloud import storage
from pathlib import Path
import json
import os
from typing import Optional, Any
from config import get_settings


class GCSStorage:
    """Google Cloud Storage 存储工具"""
    
    def __init__(self, bucket_name: Optional[str] = None):
        settings = get_settings()
        self.bucket_name = bucket_name or settings.gcs_bucket
        self.use_gcs = settings.use_gcs and self.bucket_name
        self._client = None
        self._bucket = None
    
    @property
    def client(self):
        """延迟初始化 GCS 客户端"""
        if self._client is None and self.use_gcs:
            self._client = storage.Client()
        return self._client
    
    @property
    def bucket(self):
        """获取 bucket"""
        if self._bucket is None and self.client:
            self._bucket = self.client.bucket(self.bucket_name)
        return self._bucket
    
    def upload_json(self, data: Any, gcs_path: str) -> bool:
        """
        上传 JSON 数据到 GCS
        
        Args:
            data: 要上传的数据（可 JSON 序列化）
            gcs_path: GCS 中的路径，如 'data/user_profile.json'
        
        Returns:
            是否成功
        """
        if not self.use_gcs:
            return False
        
        try:
            blob = self.bucket.blob(gcs_path)
            json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            blob.upload_from_string(json_str, content_type='application/json')
            print(f"✅ 已上传到 GCS: gs://{self.bucket_name}/{gcs_path}")
            return True
        except Exception as e:
            print(f"❌ 上传到 GCS 失败: {e}")
            return False
    
    def download_json(self, gcs_path: str) -> Optional[Any]:
        """
        从 GCS 下载 JSON 数据
        
        Args:
            gcs_path: GCS 中的路径
        
        Returns:
            解析后的 JSON 数据，如果失败返回 None
        """
        if not self.use_gcs:
            return None
        
        try:
            blob = self.bucket.blob(gcs_path)
            if not blob.exists():
                print(f"📂 GCS 文件不存在: gs://{self.bucket_name}/{gcs_path}")
                return None
            
            json_str = blob.download_as_text()
            data = json.loads(json_str)
            print(f"✅ 已从 GCS 下载: gs://{self.bucket_name}/{gcs_path}")
            return data
        except Exception as e:
            print(f"❌ 从 GCS 下载失败: {e}")
            return None
    
    def upload_file(self, local_path: str, gcs_path: str) -> bool:
        """上传本地文件到 GCS"""
        if not self.use_gcs:
            return False
        
        try:
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_filename(local_path)
            print(f"✅ 已上传文件到 GCS: {local_path} -> gs://{self.bucket_name}/{gcs_path}")
            return True
        except Exception as e:
            print(f"❌ 上传文件到 GCS 失败: {e}")
            return False
    
    def download_file(self, gcs_path: str, local_path: str) -> bool:
        """从 GCS 下载文件到本地"""
        if not self.use_gcs:
            return False
        
        try:
            blob = self.bucket.blob(gcs_path)
            if not blob.exists():
                return False
            
            # 确保目录存在
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(local_path)
            print(f"✅ 已从 GCS 下载文件: gs://{self.bucket_name}/{gcs_path} -> {local_path}")
            return True
        except Exception as e:
            print(f"❌ 从 GCS 下载文件失败: {e}")
            return False
    
    def upload_directory(self, local_dir: str, gcs_prefix: str) -> bool:
        """递归上传目录到 GCS"""
        if not self.use_gcs:
            return False
        
        try:
            local_path = Path(local_dir)
            if not local_path.exists():
                return False
            
            for file_path in local_path.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(local_path)
                    gcs_path = f"{gcs_prefix}/{relative_path}"
                    self.upload_file(str(file_path), gcs_path)
            
            print(f"✅ 已上传目录到 GCS: {local_dir} -> gs://{self.bucket_name}/{gcs_prefix}")
            return True
        except Exception as e:
            print(f"❌ 上传目录到 GCS 失败: {e}")
            return False
    
    def download_directory(self, gcs_prefix: str, local_dir: str) -> bool:
        """从 GCS 下载目录"""
        if not self.use_gcs:
            return False
        
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=gcs_prefix)
            downloaded = False
            
            for blob in blobs:
                if blob.name.endswith('/'):  # 跳过目录标记
                    continue
                
                relative_path = blob.name[len(gcs_prefix):].lstrip('/')
                local_path = Path(local_dir) / relative_path
                local_path.parent.mkdir(parents=True, exist_ok=True)
                blob.download_to_filename(str(local_path))
                downloaded = True
            
            if downloaded:
                print(f"✅ 已从 GCS 下载目录: gs://{self.bucket_name}/{gcs_prefix} -> {local_dir}")
            return downloaded
        except Exception as e:
            print(f"❌ 从 GCS 下载目录失败: {e}")
            return False


# 全局存储实例
_gcs_storage: Optional[GCSStorage] = None


def get_gcs_storage() -> GCSStorage:
    """获取 GCS 存储实例（单例）"""
    global _gcs_storage
    if _gcs_storage is None:
        _gcs_storage = GCSStorage()
    return _gcs_storage
