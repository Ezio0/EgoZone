"""
Gemini API 客户端封装
"""

import google.generativeai as genai
from typing import List, Dict, Optional, AsyncIterator
import asyncio


class GeminiClient:
    """Gemini 3.0 Pro API 客户端"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        """
        初始化 Gemini 客户端
        
        Args:
            api_key: Gemini API Key
            model_name: 模型名称
        """
        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        
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
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        # 如果有系统指令，创建新的模型实例
        if system_instruction:
            model = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_instruction,
                generation_config=generation_config
            )
        else:
            model = genai.GenerativeModel(
                self.model_name,
                generation_config=generation_config
            )
        
        # 构建对话历史
        chat_history = []
        if history:
            for msg in history:
                chat_history.append({
                    "role": msg["role"],
                    "parts": [msg["content"]]
                })
        
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
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        if system_instruction:
            model = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_instruction,
                generation_config=generation_config
            )
        else:
            model = genai.GenerativeModel(
                self.model_name,
                generation_config=generation_config
            )
        
        chat_history = []
        if history:
            for msg in history:
                chat_history.append({
                    "role": msg["role"],
                    "parts": [msg["content"]]
                })
        
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
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
        )
        return result['embedding']
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文本嵌入向量
        
        Args:
            texts: 输入文本列表
            
        Returns:
            嵌入向量列表
        """
        embeddings = []
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        return embeddings
