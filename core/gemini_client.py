"""
Gemini API 客户端封装
支持 Vertex AI 和 Google AI Studio API 两种模式
"""

import os
from typing import List, Dict, Optional, AsyncIterator
import asyncio

class GeminiClient:
    """Gemini API 客户端，支持 Vertex AI 和 Google AI Studio API 两种模式"""

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        model_name: str = "gemini-1.5-pro",
        api_key: Optional[str] = None
    ):
        """
        初始化 Gemini 客户端

        Args:
            project_id: GCP 项目 ID（用于 Vertex AI）
            location: GCP 区域（用于 Vertex AI）
            model_name: 模型名称
            api_key: Google AI Studio API 密钥（用于 Google AI Studio API 模式）
        """
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT", "egozone")
        self.location = location
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

        # 根据是否有API密钥决定使用哪种模式
        if self.api_key:
            # 使用 Google AI Studio API 模式
            self.use_vertex_ai = False
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                }
            )
        else:
            # 使用 Vertex AI 模式
            self.use_vertex_ai = True
            import vertexai
            from vertexai.generative_models import GenerativeModel
            vertexai.init(project=self.project_id, location=self.location)
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
        if self.use_vertex_ai:
            # Vertex AI 模式
            from vertexai.generative_models import GenerationConfig, Content, Part

            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            # 如果有系统指令，创建新的模型实例
            if system_instruction:
                model = self.model
                # 在Vertex AI中设置系统指令需要特殊处理
                # 将系统指令添加到提示中
                prompt = f"{system_instruction}\n\n{prompt}"
            else:
                model = self.model

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
        else:
            # Google AI Studio API 模式
            import google.generativeai as genai

            # 准备对话历史
            chat_history = []
            if history:
                for msg in history:
                    role = "user" if msg["role"] == "user" else "model"
                    chat_history.append({
                        "role": role,
                        "parts": [msg["content"]]
                    })

            # 创建聊天会话
            chat = self.model.start_chat(history=chat_history)

            # 准备生成配置
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            # 处理系统指令
            if system_instruction:
                # 对于Google AI Studio，我们将系统指令作为第一轮对话
                prompt = f"{system_instruction}\n\n{prompt}"

            # 生成回复
            response = await chat.send_message_async(
                prompt,
                generation_config=generation_config
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
        if self.use_vertex_ai:
            # Vertex AI 模式
            from vertexai.generative_models import GenerationConfig, Content, Part

            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            if system_instruction:
                model = self.model
                prompt = f"{system_instruction}\n\n{prompt}"
            else:
                model = self.model

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
        else:
            # Google AI Studio API 模式
            import google.generativeai as genai

            chat_history = []
            if history:
                for msg in history:
                    role = "user" if msg["role"] == "user" else "model"
                    chat_history.append({
                        "role": role,
                        "parts": [msg["content"]]
                    })

            chat = self.model.start_chat(history=chat_history)

            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            if system_instruction:
                prompt = f"{system_instruction}\n\n{prompt}"

            response = await chat.send_message_async(
                prompt,
                generation_config=generation_config,
                stream=True
            )

            async for chunk in response:
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
        if self.use_vertex_ai:
            # Vertex AI 模式
            from vertexai.language_models import TextEmbeddingModel

            loop = asyncio.get_event_loop()
            model = TextEmbeddingModel.from_pretrained("text-embedding-004")

            result = await loop.run_in_executor(
                None,
                lambda: model.get_embeddings([text])
            )

            return result[0].values
        else:
            # Google AI Studio API 模式
            import google.generativeai as genai

            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
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
        if self.use_vertex_ai:
            # Vertex AI 模式
            from vertexai.language_models import TextEmbeddingModel

            loop = asyncio.get_event_loop()
            model = TextEmbeddingModel.from_pretrained("text-embedding-004")

            result = await loop.run_in_executor(
                None,
                lambda: model.get_embeddings(texts)
            )

            return [embedding.values for embedding in result]
        else:
            # Google AI Studio API 模式
            import google.generativeai as genai

            result = genai.embed_content(
                model="models/text-embedding-004",
                content=texts,
                task_type="retrieval_document"
            )

            return result['embedding']
