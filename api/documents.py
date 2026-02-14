"""
文档导入 API 路由
支持多种格式的文档导入功能
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import tempfile
import os
from pathlib import Path

router = APIRouter(prefix="/api/documents")

class ImportResult(BaseModel):
    """导入结果"""
    success: bool
    message: str
    document_ids: list = []
    details: Optional[Dict[str, Any]] = None


def get_importer():
    """获取知识导入器实例"""
    from main import get_knowledge_base
    kb = get_knowledge_base()
    if not kb:
        raise HTTPException(status_code=503, detail="知识库服务尚未初始化")

    from core.knowledge_base import KnowledgeImporter
    return KnowledgeImporter(kb)


@router.post("/upload/pdf", response_model=ImportResult)
async def upload_pdf(
    file: UploadFile = File(...),
    title: str = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    上传并导入 PDF 文件

    - **file**: PDF 文件
    - **title**: 文档标题（可选）
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

    importer = get_importer()

    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    try:
        # 保存上传的文件到临时位置
        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        # 导入 PDF
        document_ids = await importer.import_pdf(temp_file.name, title=title or file.filename)

        result = ImportResult(
            success=True,
            message=f"成功导入 PDF 文件，添加了 {len(document_ids)} 个文档块",
            document_ids=document_ids,
            details={"file_name": file.filename, "chunks_added": len(document_ids)}
        )

        # 删除临时文件
        os.unlink(temp_file.name)

        return result

    except Exception as e:
        # 确保临时文件被清理
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

        raise HTTPException(status_code=500, detail=f"导入 PDF 失败: {str(e)}")


@router.post("/upload/docx", response_model=ImportResult)
async def upload_docx(
    file: UploadFile = File(...),
    title: str = Form(None)
):
    """
    上传并导入 DOCX 文件

    - **file**: DOCX 文件
    - **title**: 文档标题（可选）
    """
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail="仅支持 DOCX 文件")

    importer = get_importer()

    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    try:
        # 保存上传的文件到临时位置
        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        # 导入 DOCX
        document_ids = await importer.import_docx(temp_file.name, title=title or file.filename)

        result = ImportResult(
            success=True,
            message=f"成功导入 Word 文档，添加了 {len(document_ids)} 个文档块",
            document_ids=document_ids,
            details={"file_name": file.filename, "chunks_added": len(document_ids)}
        )

        # 删除临时文件
        os.unlink(temp_file.name)

        return result

    except Exception as e:
        # 确保临时文件被清理
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

        raise HTTPException(status_code=500, detail=f"导入 Word 文档失败: {str(e)}")


@router.post("/import/webpage", response_model=ImportResult)
async def import_webpage(url: str = Form(...), title: str = Form(None)):
    """
    导入网页内容

    - **url**: 网页 URL
    - **title**: 文档标题（可选）
    """
    importer = get_importer()

    try:
        document_ids = await importer.import_web_page(url, title=title)

        result = ImportResult(
            success=True,
            message=f"成功导入网页内容，添加了 {len(document_ids)} 个文档块",
            document_ids=document_ids,
            details={"url": url, "chunks_added": len(document_ids)}
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入网页失败: {str(e)}")


@router.post("/import/text", response_model=ImportResult)
async def import_text(content: str = Form(...), title: str = Form(None)):
    """
    导入纯文本

    - **content**: 文本内容
    - **title**: 文档标题（可选）
    """
    importer = get_importer()

    try:
        document_ids = await importer.import_text(content, title=title)

        result = ImportResult(
            success=True,
            message=f"成功导入文本，添加了 {len(document_ids)} 个文档块",
            document_ids=document_ids,
            details={"chunks_added": len(document_ids)}
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入文本失败: {str(e)}")


@router.post("/import/markdown", response_model=ImportResult)
async def import_markdown(content: str = Form(...), title: str = Form(None)):
    """
    导入 Markdown 文本

    - **content**: Markdown 内容
    - **title**: 文档标题（可选）
    """
    importer = get_importer()

    try:
        document_ids = await importer.import_markdown(content, title=title)

        result = ImportResult(
            success=True,
            message=f"成功导入 Markdown 内容，添加了 {len(document_ids)} 个文档块",
            document_ids=document_ids,
            details={"chunks_added": len(document_ids)}
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入 Markdown 失败: {str(e)}")


@router.post("/upload/csv", response_model=ImportResult)
async def upload_csv(
    file: UploadFile = File(...),
    title: str = Form(None)
):
    """
    上传并导入 CSV 文件

    - **file**: CSV 文件
    - **title**: 文档标题（可选）
    """
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="仅支持 CSV 文件")

    importer = get_importer()

    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
    try:
        # 保存上传的文件到临时位置
        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        # 导入 CSV
        document_ids = await importer.import_csv(temp_file.name, title=title or file.filename)

        result = ImportResult(
            success=True,
            message=f"成功导入 CSV 文件，添加了 {len(document_ids)} 个文档块",
            document_ids=document_ids,
            details={"file_name": file.filename, "chunks_added": len(document_ids)}
        )

        # 删除临时文件
        os.unlink(temp_file.name)

        return result

    except Exception as e:
        # 确保临时文件被清理
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

        raise HTTPException(status_code=500, detail=f"导入 CSV 文件失败: {str(e)}")