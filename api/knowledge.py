"""
Knowledge Base API Routes
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import aiofiles

router = APIRouter()


class AddKnowledgeRequest(BaseModel):
    """Add knowledge request"""

    content: str = Field(..., description="Knowledge content")
    title: Optional[str] = Field(None, description="Title")
    source: str = Field(default="manual", description="Source")
    doc_type: str = Field(default="text", description="Document type")


class SearchRequest(BaseModel):
    """Search request"""

    query: str = Field(..., description="Query text")
    top_k: int = Field(default=5, description="Number of results to return")


class KnowledgeDocument(BaseModel):
    """Knowledge document"""

    id: str
    content: str
    metadata: Dict


class SearchResult(BaseModel):
    """Search result"""

    results: List[KnowledgeDocument]
    query: str


class KnowledgeStats(BaseModel):
    """Knowledge base statistics"""

    count: int
    name: str


def get_knowledge_base():
    """Get knowledge base instance"""
    from main import get_knowledge_base

    kb = get_knowledge_base()
    if not kb:
        raise HTTPException(
            status_code=503, detail="Knowledge base not initialized yet"
        )
    return kb


@router.post("/add")
async def add_knowledge(request: AddKnowledgeRequest, http_request: Request):
    """
    Add knowledge to knowledge base

    - **content**: Knowledge content
    - **title**: Title (optional)
    - **source**: Source
    - **doc_type**: Document type
    """
    # Verify admin token
    from config import get_settings

    settings = get_settings()

    # Get admin token
    admin_token = http_request.headers.get("x-admin-token")
    if not admin_token:
        # Try to get from Authorization header
        auth_header = http_request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            admin_token = auth_header[len("Bearer ") :]

    # Verify admin token
    from api.auth import is_admin_token_valid

    if not is_admin_token_valid(admin_token):
        raise HTTPException(status_code=401, detail="Valid admin token required")

    kb = get_knowledge_base()

    doc_ids = await kb.add_document(
        content=request.content,
        source=request.source,
        doc_type=request.doc_type,
        metadata={"title": request.title} if request.title else None,
    )

    return {
        "status": "success",
        "message": f"Added {len(doc_ids)} document chunks",
        "doc_ids": doc_ids,
    }


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    doc_type: str = Form("text"),
    http_request: Request = None,
):
    """
    Upload document file

    Supports .txt, .md files
    """
    # Verify admin token
    from config import get_settings

    settings = get_settings()

    # Get admin token
    admin_token = http_request.headers.get("x-admin-token")
    if not admin_token:
        # Try to get from Authorization header
        auth_header = http_request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            admin_token = auth_header[len("Bearer ") :]

    # Verify admin token
    from api.auth import is_admin_token_valid

    if not is_admin_token_valid(admin_token):
        raise HTTPException(status_code=401, detail="Valid admin token required")

    kb = get_knowledge_base()

    # Check file type
    allowed_extensions = {".txt", ".md", ".markdown"}
    file_ext = (
        "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    )

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}, supported: {', '.join(allowed_extensions)}",
        )

    # Read file content
    content = await file.read()
    text_content = content.decode("utf-8")

    # Add to knowledge base
    doc_ids = await kb.add_document(
        content=text_content,
        source="document_import",
        doc_type=doc_type,
        metadata={"title": title or file.filename, "filename": file.filename},
    )

    return {
        "status": "success",
        "message": f"Upload successful, added {len(doc_ids)} document chunks",
        "filename": file.filename,
        "doc_ids": doc_ids,
    }


@router.post("/search", response_model=SearchResult)
async def search_knowledge(request: SearchRequest):
    """
    Semantic search in knowledge base

    - **query**: Query text
    - **top_k**: Number of results to return
    """
    kb = get_knowledge_base()

    results = await kb.search(query=request.query, top_k=request.top_k)

    documents = [
        KnowledgeDocument(
            id=r.get("id", ""),
            content=r.get("content", ""),
            metadata=r.get("metadata", {}),
        )
        for r in results
    ]

    return SearchResult(results=documents, query=request.query)


@router.get("/list")
async def list_knowledge(limit: int = 50, offset: int = 0):
    """
    List documents in knowledge base

    - **limit**: Items per page
    - **offset**: Offset
    """
    kb = get_knowledge_base()

    documents = await kb.get_all_documents(limit=limit, offset=offset)

    return {
        "documents": documents,
        "count": len(documents),
        "limit": limit,
        "offset": offset,
    }


@router.delete("/{doc_id}")
async def delete_knowledge(doc_id: str, request: Request):
    """
    Delete knowledge document

    - **doc_id**: Document ID
    """
    # Verify admin token
    from config import get_settings

    settings = get_settings()

    # Get admin token
    admin_token = request.headers.get("x-admin-token")
    if not admin_token:
        # Try to get from Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            admin_token = auth_header[len("Bearer ") :]

    # Verify admin token
    from api.auth import is_admin_token_valid

    if not is_admin_token_valid(admin_token):
        raise HTTPException(status_code=401, detail="Valid admin token required")

    kb = get_knowledge_base()

    await kb.delete_document(doc_id)

    return {"status": "success", "message": f"Deleted document {doc_id}"}


@router.get("/stats", response_model=KnowledgeStats)
async def get_stats():
    """
    Get knowledge base statistics
    """
    kb = get_knowledge_base()
    stats = kb.get_stats()

    return KnowledgeStats(**stats)
