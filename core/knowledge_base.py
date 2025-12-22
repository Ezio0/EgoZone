"""
知识库管理
基于向量数据库的语义检索系统
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import chromadb
from chromadb.config import Settings
from pathlib import Path
import hashlib
import json


class KnowledgeDocument:
    """知识文档"""
    
    def __init__(
        self,
        content: str,
        source: str = "manual",
        doc_type: str = "text",
        metadata: Optional[Dict] = None
    ):
        self.id = self._generate_id(content)
        self.content = content
        self.source = source  # manual, chat_import, document_import, interview
        self.doc_type = doc_type  # text, chat, article, note
        self.metadata = metadata or {}
        self.created_at = datetime.now()
    
    def _generate_id(self, content: str) -> str:
        """生成文档 ID"""
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "doc_type": self.doc_type,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class KnowledgeBase:
    """知识库管理"""
    
    def __init__(
        self,
        data_dir: str = "./data/knowledge",
        collection_name: str = "egozone_knowledge"
    ):
        """
        初始化知识库
        
        Args:
            data_dir: 数据存储目录
            collection_name: ChromaDB 集合名称
        """
        self.data_dir = Path(data_dir)
        self.chromadb_path = self.data_dir / "chromadb"
        self.gcs_prefix = "data/knowledge/chromadb"  # GCS 中的路径
        self.collection_name = collection_name
        self.client: Optional[chromadb.Client] = None
        self.collection: Optional[Any] = None
        self._gcs_storage = None
    
    @property
    def gcs_storage(self):
        """延迟导入 GCS 存储"""
        if self._gcs_storage is None:
            from core.storage import get_gcs_storage
            self._gcs_storage = get_gcs_storage()
        return self._gcs_storage
    
    async def initialize(self):
        """初始化知识库"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 从 GCS 下载 ChromaDB 数据（如果存在）
        if self.gcs_storage.use_gcs:
            self.gcs_storage.download_directory(self.gcs_prefix, str(self.chromadb_path))
        
        # 初始化 ChromaDB（使用持久化存储）
        self.client = chromadb.PersistentClient(
            path=str(self.chromadb_path)
        )
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "EgoZone 个人知识库"}
        )
        
        print(f"📚 知识库初始化完成，当前文档数: {self.collection.count()}")
    
    async def sync_to_gcs(self):
        """同步 ChromaDB 数据到 GCS"""
        if self.gcs_storage.use_gcs:
            self.gcs_storage.upload_directory(str(self.chromadb_path), self.gcs_prefix)
    
    async def add_document(
        self,
        content: str,
        source: str = "manual",
        doc_type: str = "text",
        metadata: Optional[Dict] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> List[str]:
        """
        添加知识文档
        
        Args:
            content: 文档内容
            source: 来源
            doc_type: 文档类型
            metadata: 元数据
            chunk_size: 分块大小
            chunk_overlap: 分块重叠
            
        Returns:
            添加的文档 ID 列表
        """
        # 文本分块
        chunks = self._split_text(content, chunk_size, chunk_overlap)
        
        if not chunks:
            return []
        
        # 准备数据
        doc_ids = []
        documents = []
        metadatas = []
        
        base_metadata = {
            "source": source,
            "doc_type": doc_type,
            "created_at": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        for i, chunk in enumerate(chunks):
            doc_id = hashlib.md5(f"{content[:50]}_{i}".encode()).hexdigest()[:16]
            doc_ids.append(doc_id)
            documents.append(chunk)
            metadatas.append({
                **base_metadata,
                "chunk_index": i,
                "total_chunks": len(chunks)
            })
        
        # 添加到向量数据库
        self.collection.add(
            ids=doc_ids,
            documents=documents,
            metadatas=metadatas
        )
        
        # 同步到 GCS
        await self.sync_to_gcs()
        
        print(f"✅ 添加了 {len(chunks)} 个文档块")
        return doc_ids
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        语义检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数
            filter_metadata: 元数据过滤条件
            
        Returns:
            检索结果列表
        """
        if not self.collection:
            return []
        
        # 构建查询参数
        query_params = {
            "query_texts": [query],
            "n_results": top_k
        }
        
        if filter_metadata:
            query_params["where"] = filter_metadata
        
        # 执行检索
        results = self.collection.query(**query_params)
        
        # 格式化结果
        formatted_results = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                result = {
                    "content": doc,
                    "id": results['ids'][0][i] if results['ids'] else None,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results.get('distances') else None
                }
                formatted_results.append(result)
        
        return formatted_results
    
    async def delete_document(self, doc_id: str):
        """删除文档"""
        if self.collection:
            self.collection.delete(ids=[doc_id])
    
    async def get_all_documents(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """获取所有文档"""
        if not self.collection:
            return []
        
        results = self.collection.get(
            limit=limit,
            offset=offset,
            include=["documents", "metadatas"]
        )
        
        documents = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents']):
                documents.append({
                    "id": results['ids'][i],
                    "content": doc,
                    "metadata": results['metadatas'][i] if results['metadatas'] else {}
                })
        
        return documents
    
    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        if not self.collection:
            return {"count": 0}
        
        return {
            "count": self.collection.count(),
            "name": self.collection_name
        }
    
    def _split_text(
        self,
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> List[str]:
        """
        文本分块
        
        使用简单的滑动窗口方式分块，优先在句子边界分割
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # 尝试在句子边界分割
            split_chars = ['。', '！', '？', '\n', '.', '!', '?']
            best_split = end
            
            for char in split_chars:
                pos = text.rfind(char, start, end)
                if pos > start + chunk_size // 2:  # 确保至少有一半长度
                    best_split = pos + 1
                    break
            
            chunks.append(text[start:best_split])
            start = best_split - chunk_overlap
        
        return chunks


class KnowledgeImporter:
    """知识导入器"""
    
    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
    
    async def import_text(self, text: str, title: Optional[str] = None) -> List[str]:
        """导入纯文本"""
        return await self.kb.add_document(
            content=text,
            source="manual",
            doc_type="text",
            metadata={"title": title} if title else None
        )
    
    async def import_markdown(self, content: str, title: Optional[str] = None) -> List[str]:
        """导入 Markdown 文档"""
        # 简单处理 Markdown（去除一些格式符号）
        import re
        # 保留内容，去除复杂格式
        clean_content = re.sub(r'```[\s\S]*?```', '', content)  # 移除代码块
        clean_content = re.sub(r'!\[.*?\]\(.*?\)', '', clean_content)  # 移除图片
        clean_content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_content)  # 链接保留文字
        
        return await self.kb.add_document(
            content=clean_content,
            source="document_import",
            doc_type="article",
            metadata={"title": title, "format": "markdown"}
        )
    
    async def import_chat_history(
        self,
        messages: List[Dict],
        platform: str = "unknown"
    ) -> List[str]:
        """
        导入聊天记录
        
        Args:
            messages: 消息列表 [{"role": "user/other", "content": "...", "timestamp": "..."}]
            platform: 平台来源
        """
        # 只保留用户自己说的话
        user_messages = [m for m in messages if m.get("role") == "user"]
        
        if not user_messages:
            return []
        
        # 合并用户消息
        combined_content = "\n".join([
            f"- {m['content']}" for m in user_messages
        ])
        
        return await self.kb.add_document(
            content=combined_content,
            source="chat_import",
            doc_type="chat",
            metadata={"platform": platform, "message_count": len(user_messages)}
        )
