"""
对话 API 路由
使用新的认证中间件系统
"""

from fastapi import APIRouter, HTTPException, Depends, Request
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


def verify_access_token_from_request(request: Request) -> bool:
    """从请求中验证访问令牌 - 使用新的中间件"""
    from api.middleware import validate_request_token
    return validate_request_token(request, require_admin=False)


def get_engine():
    """获取个性化引擎实例"""
    from main import get_personality_engine
    engine = get_personality_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="服务尚未初始化")
    return engine


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest, http_request: Request):
    """
    发送消息并获取回复

    - **message**: 用户消息内容
    - **chat_id**: 会话 ID，用于区分不同对话
    - **stream**: 是否使用流式输出
    """
    # 验证访问令牌
    from config import get_settings
    settings = get_settings()

    # 如果设置了访问密码，则需要验证访问令牌
    if settings.access_password:
        if not verify_access_token_from_request(http_request):
            raise HTTPException(status_code=401, detail="需要有效的访问令牌")

    engine = get_engine()

    if request.stream:
        # 流式输出
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
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # 普通输出
        try:
            response = await engine.chat(request.chat_id, request.message)
            return ChatResponse(message=response, chat_id=request.chat_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@router.get("/history/{chat_id}", response_model=ConversationHistory)
async def get_history(chat_id: str, request: Request):
    """获取对话历史"""
    # 验证访问权限
    from config import get_settings
    settings = get_settings()
    
    if settings.access_password:
        if not verify_access_token_from_request(request):
            raise HTTPException(status_code=401, detail="需要有效的访问令牌")
    
    engine = get_engine()
    
    try:
        history = engine.get_conversation_history(chat_id)
        return ConversationHistory(chat_id=chat_id, messages=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")


@router.delete("/history/{chat_id}")
async def clear_history(chat_id: str, request: Request):
    """清除对话历史"""
    # 验证访问权限
    from config import get_settings
    settings = get_settings()
    
    if settings.access_password:
        if not verify_access_token_from_request(request):
            raise HTTPException(status_code=401, detail="需要有效的访问令牌")
    
    engine = get_engine()
    
    try:
        engine.clear_conversation(chat_id)
        return {"message": "对话历史已清除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除历史失败: {str(e)}")


@router.post("/stream")
async def stream_message(request: ChatRequest):
    """流式对话接口（独立端点）"""
    # 注意：此端点需要单独验证令牌
    # 实际实现中应该复用验证逻辑
    
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
            "X-Accel-Buffering": "no"
        }
    )
