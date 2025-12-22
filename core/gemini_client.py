"""
Gemini API 客户端封装
使用 Vertex AI SDK，支持服务账号自动认证
"""

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, Content, Part
from typing import List, Dict, Optional, AsyncIterator
import asyncio
import os


class GeminiClient:
    """Gemini API 客户端 (Vertex AI)"""
    
    def __init__(
        self, 
        project_id: Optional[str] = None, 
        location: str = "asia-east1",
        model_name: str = "gemini-2.0-flash-001"
    ):
        """
        初始化 Gemini 客户端
        
        Args:
            project_id: GCP 项目 ID（默认从环境变量获取）
            location: 区域
            model_name: 模型名称
        """
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT", "egozone")
        self.location = location
        self.model_name = model_name
        
        # 初始化 Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        
        # 创建模型实例
        self.model = GenerativeModel(model_name)
        
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        生成回复
        
        Args:
            prompt: 用户输入
            system_instruction: 系统指令
            history: 对话历史
            temperature: 温度参数
            max_tokens: 最大生成长度
            
        Returns:
            生成的回复文本
        """
        # 构建模型配置
        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        # 如果有系统指令，创建新的模型实例
        if system_instruction:
            model = GenerativeModel(
                self.model_name,
                system_instruction=system_instruction,
                generation_config=generation_config
            )
        else:
            model = GenerativeModel(
                self.model_name,
                generation_config=generation_config
            )
        
        # 构建对话历史
        chat_history = []
        if history:
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append(
                    Content(role=role, parts=[Part.from_text(msg["content"])])
                )
        
        # 创建聊天会话
        chat = model.start_chat(history=chat_history)
        
        # 生成回复（使用线程池执行同步调用）
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: chat.send_message(prompt)
        )
        
        return response.text
    
    async def generate_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> AsyncIterator[str]:
        """
        流式生成回复
        
        Args:
            prompt: 用户输入
            system_instruction: 系统指令
            history: 对话历史
            temperature: 温度参数
            max_tokens: 最大生成长度
            
        Yields:
            生成的文本片段
        """
        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        if system_instruction:
            model = GenerativeModel(
                self.model_name,
                system_instruction=system_instruction,
                generation_config=generation_config
            )
        else:
            model = GenerativeModel(
                self.model_name,
                generation_config=generation_config
            )
        
        chat_history = []
        if history:
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append(
                    Content(role=role, parts=[Part.from_text(msg["content"])])
                )
        
        chat = model.start_chat(history=chat_history)
        
        # 流式生成
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: chat.send_message(prompt, stream=True)
        )
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
    
    async def embed_text(self, text: str) -> List[float]:
        """
        生成文本嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量
        """
        from vertexai.language_models import TextEmbeddingModel
        
        loop = asyncio.get_event_loop()
        model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        
        result = await loop.run_in_executor(
            None,
            lambda: model.get_embeddings([text])
        )
        
        return result[0].values
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文本嵌入向量
        
        Args:
            texts: 输入文本列表
            
        Returns:
            嵌入向量列表
        """
        from vertexai.language_models import TextEmbeddingModel
        
        loop = asyncio.get_event_loop()
        model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        
        result = await loop.run_in_executor(
            None,
            lambda: model.get_embeddings(texts)
        )
        
        return [embedding.values for embedding in result]
