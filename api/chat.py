"""
对话 API 路由
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import json

router = APIRouter()


class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., description="用户消息")
    chat_id: str = Field(default="default", description="会话 ID")
    stream: bool = Field(default=False, description="是否流式输出")


class ChatResponse(BaseModel):
    """对话响应"""
    message: str = Field(..., description="AI 回复")
    chat_id: str


class ConversationHistory(BaseModel):
    """对话历史"""
    chat_id: str
    messages: List[Dict]


def get_engine():
    """获取个性化引擎实例"""
    from main import get_personality_engine
    engine = get_personality_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="服务尚未初始化")
    return engine


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    发送消息并获取回复
    
    - **message**: 用户消息内容
    - **chat_id**: 会话 ID，用于区分不同对话
    - **stream**: 是否使用流式输出
    """
    engine = get_engine()
    
    if request.stream:
        # 流式响应
        async def generate():
            async for chunk in engine.chat_stream(
                message=request.message,
                chat_id=request.chat_id
            ):
                yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
    else:
        # 普通响应
        response = await engine.chat(
            message=request.message,
            chat_id=request.chat_id
        )
        
        return ChatResponse(
            message=response,
            chat_id=request.chat_id
        )


@router.get("/history/{chat_id}", response_model=ConversationHistory)
async def get_history(chat_id: str):
    """
    获取对话历史
    
    - **chat_id**: 会话 ID
    """
    engine = get_engine()
    messages = engine.get_conversation_history(chat_id)
    
    return ConversationHistory(
        chat_id=chat_id,
        messages=messages
    )


@router.delete("/history/{chat_id}")
async def clear_history(chat_id: str):
    """
    清空对话历史
    
    - **chat_id**: 会话 ID
    """
    engine = get_engine()
    engine.clear_conversation(chat_id)
    
    return {"status": "success", "message": f"已清空会话 {chat_id} 的历史记录"}


@router.post("/stream")
async def stream_message(request: ChatRequest):
    """
    流式对话接口（SSE）
    
    返回 Server-Sent Events 格式的流式响应
    """
    engine = get_engine()
    
    async def generate():
        async for chunk in engine.chat_stream(
            message=request.message,
            chat_id=request.chat_id
        ):
            yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )
