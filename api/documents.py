"""
Document Import API Router
Supports importing documents in multiple formats
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
    """Import result"""

    success: bool
    message: str
    document_ids: list = []
    details: Optional[Dict[str, Any]] = None


def get_importer():
    """Get knowledge importer instance"""
    from main import get_knowledge_base

    kb = get_knowledge_base()
    if not kb:
        raise HTTPException(
            status_code=503, detail="Knowledge base service not initialized"
        )

    from core.knowledge_base import KnowledgeImporter

    return KnowledgeImporter(kb)


@router.post("/upload/pdf", response_model=ImportResult)
async def upload_pdf(
    file: UploadFile = File(...),
    title: str = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Upload and import PDF file

    - **file**: PDF file
    - **title**: Document title (optional)
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    importer = get_importer()

    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        # Save uploaded file to temporary location
        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        # Import PDF
        document_ids = await importer.import_pdf(
            temp_file.name, title=title or file.filename
        )

        result = ImportResult(
            success=True,
            message=f"Successfully imported PDF file, added {len(document_ids)} document chunks",
            document_ids=document_ids,
            details={"file_name": file.filename, "chunks_added": len(document_ids)},
        )

        # Delete temporary file
        os.unlink(temp_file.name)

        return result

    except Exception as e:
        # Ensure temp file is cleaned up
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

        raise HTTPException(status_code=500, detail=f"Failed to import PDF: {str(e)}")


@router.post("/upload/docx", response_model=ImportResult)
async def upload_docx(file: UploadFile = File(...), title: str = Form(None)):
    """
    Upload and import DOCX file

    - **file**: DOCX file
    - **title**: Document title (optional)
    """
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only DOCX files are supported")

    importer = get_importer()

    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    try:
        # Save uploaded file to temporary location
        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        # Import DOCX
        document_ids = await importer.import_docx(
            temp_file.name, title=title or file.filename
        )

        result = ImportResult(
            success=True,
            message=f"Successfully imported Word document, added {len(document_ids)} document chunks",
            document_ids=document_ids,
            details={"file_name": file.filename, "chunks_added": len(document_ids)},
        )

        # Delete temporary file
        os.unlink(temp_file.name)

        return result

    except Exception as e:
        # Ensure temp file is cleaned up
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

        raise HTTPException(
            status_code=500, detail=f"Failed to import Word document: {str(e)}"
        )


@router.post("/import/webpage", response_model=ImportResult)
async def import_webpage(url: str = Form(...), title: str = Form(None)):
    """
    Import webpage content

    - **url**: Webpage URL
    - **title**: Document title (optional)
    """
    importer = get_importer()

    try:
        document_ids = await importer.import_web_page(url, title=title)

        result = ImportResult(
            success=True,
            message=f"Successfully imported webpage content, added {len(document_ids)} document chunks",
            document_ids=document_ids,
            details={"url": url, "chunks_added": len(document_ids)},
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to import webpage: {str(e)}"
        )


@router.post("/import/text", response_model=ImportResult)
async def import_text(content: str = Form(...), title: str = Form(None)):
    """
    Import plain text

    - **content**: Text content
    - **title**: Document title (optional)
    """
    importer = get_importer()

    try:
        document_ids = await importer.import_text(content, title=title)

        result = ImportResult(
            success=True,
            message=f"Successfully imported text, added {len(document_ids)} document chunks",
            document_ids=document_ids,
            details={"chunks_added": len(document_ids)},
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import text: {str(e)}")


@router.post("/import/markdown", response_model=ImportResult)
async def import_markdown(content: str = Form(...), title: str = Form(None)):
    """
    Import Markdown text

    - **content**: Markdown content
    - **title**: Document title (optional)
    """
    importer = get_importer()

    try:
        document_ids = await importer.import_markdown(content, title=title)

        result = ImportResult(
            success=True,
            message=f"Successfully imported Markdown content, added {len(document_ids)} document chunks",
            document_ids=document_ids,
            details={"chunks_added": len(document_ids)},
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to import Markdown: {str(e)}"
        )


@router.post("/upload/csv", response_model=ImportResult)
async def upload_csv(file: UploadFile = File(...), title: str = Form(None)):
    """
    Upload and import CSV file

    - **file**: CSV file
    - **title**: Document title (optional)
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    importer = get_importer()

    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    try:
        # Save uploaded file to temporary location
        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        # Import CSV
        document_ids = await importer.import_csv(
            temp_file.name, title=title or file.filename
        )

        result = ImportResult(
            success=True,
            message=f"Successfully imported CSV file, added {len(document_ids)} document chunks",
            document_ids=document_ids,
            details={"file_name": file.filename, "chunks_added": len(document_ids)},
        )

        # Delete temporary file
        os.unlink(temp_file.name)

        return result

    except Exception as e:
        # Ensure temp file is cleaned up
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

        raise HTTPException(
            status_code=500, detail=f"Failed to import CSV file: {str(e)}"
        )
