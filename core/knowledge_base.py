"""
Knowledge Base Management
Semantic retrieval system based on vector database
"""

from typing import List, Dict, Optional, Any, Union  # Added Union import
from datetime import datetime
import chromadb
from chromadb.config import Settings
from pathlib import Path
import hashlib
import json


class KnowledgeDocument:
    """Knowledge document"""

    def __init__(
        self,
        content: str,
        source: str = "manual",
        doc_type: str = "text",
        metadata: Optional[Dict] = None,
    ):
        self.id = self._generate_id(content)
        self.content = content
        self.source = source  # manual, chat_import, document_import, interview
        self.doc_type = doc_type  # text, chat, article, note
        self.metadata = metadata or {}
        self.created_at = datetime.now()

    def _generate_id(self, content: str) -> str:
        """Generate document ID"""
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "doc_type": self.doc_type,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


class KnowledgeBase:
    """Knowledge base management"""

    def __init__(
        self,
        data_dir: str = "./data/knowledge",
        collection_name: str = "egozone_knowledge",
    ):
        """
        Initialize knowledge base

        Args:
            data_dir: Data storage directory
            collection_name: ChromaDB collection name
        """
        self.data_dir = Path(data_dir)
        self.chromadb_path = self.data_dir / "chromadb"
        self.gcs_prefix = "data/knowledge/chromadb"  # Path in GCS
        self.collection_name = collection_name
        self.client: Optional[chromadb.Client] = None
        self.collection: Optional[Any] = None
        self._gcs_storage = None

    @property
    def gcs_storage(self):
        """Lazy import GCS storage"""
        if self._gcs_storage is None:
            from core.storage import get_gcs_storage

            self._gcs_storage = get_gcs_storage()
        return self._gcs_storage

    async def initialize(self):
        """Initialize knowledge base"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Download ChromaDB data from GCS (if exists)
        if self.gcs_storage.use_gcs:
            self.gcs_storage.download_directory(
                self.gcs_prefix, str(self.chromadb_path)
            )

        # Initialize ChromaDB (using persistent storage)
        self.client = chromadb.PersistentClient(path=str(self.chromadb_path))

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "EgoZone personal knowledge base"},
        )

        print(
            f"📚 Knowledge base initialized, current document count: {self.collection.count()}"
        )

    async def sync_to_gcs(self):
        """Sync ChromaDB data to GCS"""
        if self.gcs_storage.use_gcs:
            self.gcs_storage.upload_directory(str(self.chromadb_path), self.gcs_prefix)

    async def add_document(
        self,
        content: str,
        source: str = "manual",
        doc_type: str = "text",
        metadata: Optional[Dict] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> List[str]:
        """
        Add knowledge document

        Args:
            content: Document content
            source: Source
            doc_type: Document type
            metadata: Metadata
            chunk_size: Chunk size
            chunk_overlap: Chunk overlap

        Returns:
            List of added document IDs
        """
        # Text chunking
        chunks = self._split_text(content, chunk_size, chunk_overlap)

        if not chunks:
            return []

        # Prepare data
        doc_ids = []
        documents = []
        metadatas = []

        base_metadata = {
            "source": source,
            "doc_type": doc_type,
            "created_at": datetime.now().isoformat(),
            **(metadata or {}),
        }

        for i, chunk in enumerate(chunks):
            doc_id = hashlib.md5(f"{content[:50]}_{i}".encode()).hexdigest()[:16]
            doc_ids.append(doc_id)
            documents.append(chunk)
            metadatas.append(
                {**base_metadata, "chunk_index": i, "total_chunks": len(chunks)}
            )

        # Add to vector database
        self.collection.add(ids=doc_ids, documents=documents, metadatas=metadatas)

        # Sync to GCS
        await self.sync_to_gcs()

        print(f"✅ Added {len(chunks)} document chunks")
        return doc_ids

    async def search(
        self, query: str, top_k: int = 5, filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Semantic search

        Args:
            query: Query text
            top_k: Number of results to return
            filter_metadata: Metadata filter conditions

        Returns:
            List of search results
        """
        if not self.collection:
            return []

        # Build query parameters
        query_params = {"query_texts": [query], "n_results": top_k}

        if filter_metadata:
            query_params["where"] = filter_metadata

        # Execute search
        results = self.collection.query(**query_params)

        # Format results
        formatted_results = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                result = {
                    "content": doc,
                    "id": results["ids"][0][i] if results["ids"] else None,
                    "metadata": results["metadatas"][0][i]
                    if results["metadatas"]
                    else {},
                    "distance": results["distances"][0][i]
                    if results.get("distances")
                    else None,
                }
                formatted_results.append(result)

        return formatted_results

    async def delete_document(self, doc_id: str):
        """Delete document"""
        if self.collection:
            self.collection.delete(ids=[doc_id])

    async def get_all_documents(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all documents"""
        if not self.collection:
            return []

        results = self.collection.get(
            limit=limit, offset=offset, include=["documents", "metadatas"]
        )

        documents = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"]):
                documents.append(
                    {
                        "id": results["ids"][i],
                        "content": doc,
                        "metadata": results["metadatas"][i]
                        if results["metadatas"]
                        else {},
                    }
                )

        return documents

    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        if not self.collection:
            return {"count": 0}

        return {"count": self.collection.count(), "name": self.collection_name}

    def _split_text(
        self, text: str, chunk_size: int = 500, chunk_overlap: int = 50
    ) -> List[str]:
        """
        Text chunking

        Uses simple sliding window approach, prioritizing sentence boundary splits
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

            # Try to split at sentence boundary
            split_chars = [".", "!", "?", "\n"]
            best_split = end

            for char in split_chars:
                pos = text.rfind(char, start, end)
                if pos > start + chunk_size // 2:  # Ensure at least half length
                    best_split = pos + 1
                    break

            chunks.append(text[start:best_split])
            start = best_split - chunk_overlap

        return chunks


class KnowledgeImporter:
    """Knowledge importer"""

    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base

    async def import_text(self, text: str, title: Optional[str] = None) -> List[str]:
        """Import plain text"""
        return await self.kb.add_document(
            content=text,
            source="manual",
            doc_type="text",
            metadata={"title": title} if title else None,
        )

    async def import_markdown(
        self, content: str, title: Optional[str] = None
    ) -> List[str]:
        """Import Markdown document"""
        # Simple Markdown processing (remove some formatting symbols)
        import re

        # Keep content, remove complex formatting
        clean_content = re.sub(r"```[\s\S]*?```", "", content)  # Remove code blocks
        clean_content = re.sub(r"!\[.*?\]\(.*?\)", "", clean_content)  # Remove images
        clean_content = re.sub(
            r"\[([^\]]+)\]\([^\)]+\)", r"\1", clean_content
        )  # Links keep text only

        return await self.kb.add_document(
            content=clean_content,
            source="document_import",
            doc_type="article",
            metadata={"title": title, "format": "markdown"},
        )

    async def import_chat_history(
        self, messages: List[Dict], platform: str = "unknown"
    ) -> List[str]:
        """
        Import chat history

        Args:
            messages: Message list [{"role": "user/other", "content": "...", "timestamp": "..."}]
            platform: Platform source
        """
        # Only keep user's own messages
        user_messages = [m for m in messages if m.get("role") == "user"]

        if not user_messages:
            return []

        # Combine user messages
        combined_content = "\n".join([f"- {m['content']}" for m in user_messages])

        return await self.kb.add_document(
            content=combined_content,
            source="chat_import",
            doc_type="chat",
            metadata={"platform": platform, "message_count": len(user_messages)},
        )

    async def import_pdf(
        self, file_path: str, title: Optional[str] = None
    ) -> List[str]:
        """
        Import PDF file

        Args:
            file_path: PDF file path
            title: Document title

        Returns:
            List of added document IDs
        """
        try:
            import PyPDF2
            import re

            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""

                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"

                # Clean extra whitespace in text
                text_content = re.sub(r"\s+", " ", text_content)

            return await self.kb.add_document(
                content=text_content,
                source="pdf_import",
                doc_type="pdf",
                metadata={
                    "title": title or file_path,
                    "format": "pdf",
                    "page_count": len(pdf_reader.pages),
                    "file_path": file_path,
                },
            )
        except ImportError:
            raise ImportError("Need to install PyPDF2: pip install PyPDF2")
        except Exception as e:
            print(f"Failed to import PDF: {e}")
            return []

    async def import_docx(
        self, file_path: str, title: Optional[str] = None
    ) -> List[str]:
        """
        Import Word document (DOCX)

        Args:
            file_path: DOCX file path
            title: Document title

        Returns:
            List of added document IDs
        """
        try:
            from docx import Document
            import re

            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text_content = "\n".join(paragraphs)

            # Clean extra whitespace in text
            text_content = re.sub(r"\s+", " ", text_content)

            return await self.kb.add_document(
                content=text_content,
                source="docx_import",
                doc_type="word",
                metadata={
                    "title": title or file_path,
                    "format": "docx",
                    "paragraph_count": len(paragraphs),
                    "file_path": file_path,
                },
            )
        except ImportError:
            raise ImportError("Need to install python-docx: pip install python-docx")
        except Exception as e:
            print(f"Failed to import Word document: {e}")
            return []

    async def import_web_page(self, url: str, title: Optional[str] = None) -> List[str]:
        """
        Import web page content

        Args:
            url: Web page URL
            title: Document title

        Returns:
            List of added document IDs
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            import re

            response = requests.get(
                url, headers={"User-Agent": "Mozilla/5.0 (compatible; EgoZone Bot)"}
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract main content
            content_selectors = [
                "main",
                ".content",
                "#content",
                "article",
                ".post",
                ".entry-content",
            ]
            content = None

            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    break

            if not content:
                content = soup.find("body")

            text_content = (
                content.get_text(strip=True, separator="\n")
                if content
                else soup.get_text(strip=True, separator="\n")
            )

            # Clean extra whitespace
            text_content = re.sub(r"\n\s*\n", "\n\n", text_content)
            text_content = re.sub(r"[ \t]+", " ", text_content)

            return await self.kb.add_document(
                content=text_content,
                source="web_import",
                doc_type="webpage",
                metadata={"title": title or url, "url": url, "format": "webpage"},
            )
        except ImportError:
            raise ImportError(
                "Need to install requests and beautifulsoup4: pip install requests beautifulsoup4"
            )
        except Exception as e:
            print(f"Failed to import web page: {e}")
            return []

    async def import_json_data(
        self, data: Union[str, Dict, List], title: Optional[str] = None
    ) -> List[str]:
        """
        Import JSON data

        Args:
            data: JSON string or object
            title: Document title

        Returns:
            List of added document IDs
        """
        import json
        from typing import Union

        try:
            if isinstance(data, str):
                parsed_data = json.loads(data)
            else:
                parsed_data = data

            # Convert JSON data to readable text
            def json_to_text(obj, indent=0):
                text = ""
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        text += "  " * indent + f"{key}: "
                        if isinstance(value, (dict, list)):
                            text += "\n" + json_to_text(value, indent + 1)
                        else:
                            text += f"{value}\n"
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        text += "  " * indent + f"[{i}]: "
                        if isinstance(item, (dict, list)):
                            text += "\n" + json_to_text(item, indent + 1)
                        else:
                            text += f"{item}\n"
                else:
                    text += f"{obj}\n"
                return text

            text_content = json_to_text(parsed_data)

            return await self.kb.add_document(
                content=text_content,
                source="json_import",
                doc_type="structured_data",
                metadata={
                    "title": title or "JSON Data",
                    "format": "json",
                    "data_type": type(parsed_data).__name__,
                },
            )
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            return []
        except Exception as e:
            print(f"Failed to import JSON data: {e}")
            return []

    async def import_csv(
        self, file_path: str, title: Optional[str] = None
    ) -> List[str]:
        """
        Import CSV file

        Args:
            file_path: CSV file path
            title: Document title

        Returns:
            List of added document IDs
        """
        import csv
        import io

        try:
            rows = []
            with open(file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    rows.append(
                        ", ".join(row)
                    )  # Convert each row to comma-separated string

            content = "\n".join(rows)

            return await self.kb.add_document(
                content=content,
                source="csv_import",
                doc_type="tabular_data",
                metadata={
                    "title": title or file_path,
                    "format": "csv",
                    "row_count": len(rows),
                    "file_path": file_path,
                },
            )
        except Exception as e:
            print(f"Failed to import CSV file: {e}")
            return []
