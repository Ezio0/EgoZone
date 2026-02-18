"""
知识库 API 路由
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import aiofiles

router = APIRouter()


class AddKnowledgeRequest(BaseModel):
    """添加知识请求"""
    content: str = Field(..., description="知识内容")
    title: Optional[str] = Field(None, description="标题")
    source: str = Field(default="manual", description="来源")
    doc_type: str = Field(default="text", description="文档类型")


class SearchRequest(BaseModel):
    """检索请求"""
    query: str = Field(..., description="查询文本")
    top_k: int = Field(default=5, description="返回结果数")


class KnowledgeDocument(BaseModel):
    """知识文档"""
    id: str
    content: str
    metadata: Dict


class SearchResult(BaseModel):
    """检索结果"""
    results: List[KnowledgeDocument]
    query: str


class KnowledgeStats(BaseModel):
    """知识库统计"""
    count: int
    name: str


def get_knowledge_base():
    """获取知识库实例"""
    from main import get_knowledge_base
    kb = get_knowledge_base()
    if not kb:
        raise HTTPException(status_code=503, detail="知识库尚未初始化")
    return kb


@router.post("/add")
async def add_knowledge(request: AddKnowledgeRequest, http_request: Request):
    """
    添加知识到知识库

    - **content**: 知识内容
    - **title**: 标题（可选）
    - **source**: 来源
    - **doc_type**: 文档类型
    """
    # 验证管理员令牌
    from config import get_settings
    settings = get_settings()

    # 获取管理员令牌
    admin_token = http_request.headers.get("x-admin-token")
    if not admin_token:
        # 尝试从Authorization头获取
        auth_header = http_request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            admin_token = auth_header[len("Bearer "):]

    # 验证管理员令牌
    from api.auth import is_admin_token_valid

    if not is_admin_token_valid(admin_token):
        raise HTTPException(status_code=401, detail="需要有效的管理员令牌")

    kb = get_knowledge_base()

    doc_ids = await kb.add_document(
        content=request.content,
        source=request.source,
        doc_type=request.doc_type,
        metadata={"title": request.title} if request.title else None
    )

    return {
        "status": "success",
        "message": f"添加了 {len(doc_ids)} 个文档块",
        "doc_ids": doc_ids
    }


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    doc_type: str = Form("text"),
    http_request: Request = None
):
    """
    上传文档文件

    支持 .txt, .md 文件
    """
    # 验证管理员令牌
    from config import get_settings
    settings = get_settings()

    # 获取管理员令牌
    admin_token = http_request.headers.get("x-admin-token")
    if not admin_token:
        # 尝试从Authorization头获取
        auth_header = http_request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            admin_token = auth_header[len("Bearer "):]

    # 验证管理员令牌
    from api.auth import is_admin_token_valid

    if not is_admin_token_valid(admin_token):
        raise HTTPException(status_code=401, detail="需要有效的管理员令牌")

    kb = get_knowledge_base()

    # 检查文件类型
    allowed_extensions = {'.txt', '.md', '.markdown'}
    file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}，支持: {', '.join(allowed_extensions)}"
        )

    # 读取文件内容
    content = await file.read()
    text_content = content.decode('utf-8')

    # 添加到知识库
    doc_ids = await kb.add_document(
        content=text_content,
        source="document_import",
        doc_type=doc_type,
        metadata={
            "title": title or file.filename,
            "filename": file.filename
        }
    )

    return {
        "status": "success",
        "message": f"上传成功，添加了 {len(doc_ids)} 个文档块",
        "filename": file.filename,
        "doc_ids": doc_ids
    }


@router.post("/search", response_model=SearchResult)
async def search_knowledge(request: SearchRequest):
    """
    语义检索知识库
    
    - **query**: 查询文本
    - **top_k**: 返回结果数
    """
    kb = get_knowledge_base()
    
    results = await kb.search(
        query=request.query,
        top_k=request.top_k
    )
    
    documents = [
        KnowledgeDocument(
            id=r.get("id", ""),
            content=r.get("content", ""),
            metadata=r.get("metadata", {})
        )
        for r in results
    ]
    
    return SearchResult(
        results=documents,
        query=request.query
    )


@router.get("/list")
async def list_knowledge(limit: int = 50, offset: int = 0):
    """
    列出知识库中的文档
    
    - **limit**: 每页数量
    - **offset**: 偏移量
    """
    kb = get_knowledge_base()
    
    documents = await kb.get_all_documents(limit=limit, offset=offset)
    
    return {
        "documents": documents,
        "count": len(documents),
        "limit": limit,
        "offset": offset
    }


@router.delete("/{doc_id}")
async def delete_knowledge(doc_id: str, request: Request):
    """
    删除知识文档

    - **doc_id**: 文档 ID
    """
    # 验证管理员令牌
    from config import get_settings
    settings = get_settings()

    # 获取管理员令牌
    admin_token = request.headers.get("x-admin-token")
    if not admin_token:
        # 尝试从Authorization头获取
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            admin_token = auth_header[len("Bearer "):]

    # 验证管理员令牌
    from api.auth import is_admin_token_valid

    if not is_admin_token_valid(admin_token):
        raise HTTPException(status_code=401, detail="需要有效的管理员令牌")

    kb = get_knowledge_base()

    await kb.delete_document(doc_id)

    return {
        "status": "success",
        "message": f"已删除文档 {doc_id}"
    }


@router.get("/stats", response_model=KnowledgeStats)
async def get_stats():
    """
    获取知识库统计信息
    """
    kb = get_knowledge_base()
    stats = kb.get_stats()
    
    return KnowledgeStats(**stats)
