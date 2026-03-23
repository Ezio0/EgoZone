"""
Chat API Router
Uses the new authentication middleware system
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import json

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request"""

    message: str = Field(..., description="User message")
    chat_id: str = Field(default="default", description="Session ID")
    stream: bool = Field(default=False, description="Enable streaming output")


class ChatResponse(BaseModel):
    """Chat response"""

    message: str = Field(..., description="AI response")
    chat_id: str


class ConversationHistory(BaseModel):
    """Conversation history"""

    chat_id: str
    messages: List[Dict]


def verify_access_token_from_request(request: Request) -> bool:
    """Verify access token from request - uses new middleware"""
    from api.middleware import validate_request_token

    return validate_request_token(request, require_admin=False)


def get_engine():
    """Get personality engine instance"""
    from main import get_personality_engine

    engine = get_personality_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return engine


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest, http_request: Request):
    """
    Send message and get response

    - **message**: User message content
    - **chat_id**: Session ID for distinguishing different conversations
    - **stream**: Whether to use streaming output
    """
    # Verify access token
    from config import get_settings

    settings = get_settings()

    # If access password is set, verify access token
    if settings.access_password:
        if not verify_access_token_from_request(http_request):
            raise HTTPException(status_code=401, detail="Valid access token required")

    engine = get_engine()

    if request.stream:
        # Streaming output
        async def generate():
            try:
                async for chunk in engine.chat_stream(request.chat_id, request.message):
                    yield f"data: {json.dumps({'message': chunk}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # Regular output
        try:
            response = await engine.chat(request.chat_id, request.message)
            return ChatResponse(message=response, chat_id=request.chat_id)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Chat processing failed: {str(e)}"
            )


@router.get("/history/{chat_id}", response_model=ConversationHistory)
async def get_history(chat_id: str, request: Request):
    """Get conversation history"""
    # Verify access permission
    from config import get_settings

    settings = get_settings()

    if settings.access_password:
        if not verify_access_token_from_request(request):
            raise HTTPException(status_code=401, detail="Valid access token required")

    engine = get_engine()

    try:
        history = engine.get_conversation_history(chat_id)
        return ConversationHistory(chat_id=chat_id, messages=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.delete("/history/{chat_id}")
async def clear_history(chat_id: str, request: Request):
    """Clear conversation history"""
    # Verify access permission
    from config import get_settings

    settings = get_settings()

    if settings.access_password:
        if not verify_access_token_from_request(request):
            raise HTTPException(status_code=401, detail="Valid access token required")

    engine = get_engine()

    try:
        engine.clear_conversation(chat_id)
        return {"message": "Conversation history cleared"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to clear history: {str(e)}"
        )


@router.post("/stream")
async def stream_message(request: ChatRequest):
    """Streaming chat endpoint (standalone)"""
    # Note: This endpoint requires separate token verification
    # In actual implementation, should reuse verification logic

    engine = get_engine()

    async def generate():
        try:
            async for chunk in engine.chat_stream(request.chat_id, request.message):
                yield f"data: {json.dumps({'message': chunk}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
