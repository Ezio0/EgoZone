"""
个性化对话引擎
核心对话处理模块，整合用户画像、知识库和对话记忆
"""

from typing import List, Dict, Optional, AsyncIterator, Union
from .gemini_client import GeminiClient
from .knowledge_base import KnowledgeBase
from .user_profile import UserProfileManager
from .memory import ConversationMemory, ConversationManager


class PersonalityEngine:
    """个性化对话引擎"""
    
    def __init__(
        self,
        gemini_client: GeminiClient,
        knowledge_base: KnowledgeBase,
        profile_manager: UserProfileManager
    ):
        """
        初始化个性化引擎
        
        Args:
            gemini_client: Gemini API 客户端
            knowledge_base: 知识库实例
            profile_manager: 用户画像管理器
        """
        self.gemini = gemini_client
        self.knowledge_base = knowledge_base
        self.profile_manager = profile_manager
        self.conversation_manager = ConversationManager()
    
    async def generate_response(
        self,
        user_input: str,
        chat_id: str = "default",
        use_knowledge: bool = True,
        stream: bool = False
    ) -> Union[str, AsyncIterator[str]]:
        """
        生成个性化回复
        
        Args:
            user_input: 用户输入
            chat_id: 聊天会话 ID
            use_knowledge: 是否使用知识库检索
            stream: 是否使用流式输出
            
        Returns:
            生成的回复（字符串或异步迭代器）
        """
        # 1. 获取对话记忆
        memory = self.conversation_manager.get_memory(chat_id)
        
        # 2. 检索相关知识
        relevant_knowledge = ""
        if use_knowledge:
            docs = await self.knowledge_base.search(user_input, top_k=3)
            if docs:
                knowledge_parts = ["## 相关背景知识"]
                for doc in docs:
                    content = doc["content"][:300]  # 限制长度
                    knowledge_parts.append(f"- {content}")
                relevant_knowledge = "\n".join(knowledge_parts)
        
        # 3. 构建系统 Prompt
        system_prompt = self._build_system_prompt(relevant_knowledge)
        
        # 4. 获取对话历史
        history = memory.get_recent_context(n=10)
        
        # 5. 生成回复
        if stream:
            return self._generate_stream(
                user_input, system_prompt, history, memory
            )
        else:
            response = await self.gemini.generate(
                prompt=user_input,
                system_instruction=system_prompt,
                history=history
            )
            
            # 6. 保存对话记录
            memory.add_user_message(user_input)
            memory.add_assistant_message(response)
            
            return response
    
    async def _generate_stream(
        self,
        user_input: str,
        system_prompt: str,
        history: List[Dict],
        memory: ConversationMemory
    ) -> AsyncIterator[str]:
        """流式生成回复"""
        full_response = ""
        
        async for chunk in self.gemini.generate_stream(
            prompt=user_input,
            system_instruction=system_prompt,
            history=history
        ):
            full_response += chunk
            yield chunk
        
        # 保存完整对话记录
        memory.add_user_message(user_input)
        memory.add_assistant_message(full_response)
    
    def _build_system_prompt(self, relevant_knowledge: str = "") -> str:
        """构建系统 Prompt"""
        # 基础个性化 Prompt
        personality_prompt = self.profile_manager.build_personality_prompt()
        
        # 组合完整 Prompt
        parts = [personality_prompt]
        
        if relevant_knowledge:
            parts.append("")
            parts.append(relevant_knowledge)
        
        return "\n".join(parts)
    
    async def chat(
        self,
        message: str,
        chat_id: str = "default"
    ) -> str:
        """
        简单对话接口
        
        Args:
            message: 用户消息
            chat_id: 聊天 ID
            
        Returns:
            AI 回复
        """
        return await self.generate_response(
            user_input=message,
            chat_id=chat_id,
            use_knowledge=True,
            stream=False
        )
    
    async def chat_stream(
        self,
        message: str,
        chat_id: str = "default"
    ) -> AsyncIterator[str]:
        """
        流式对话接口
        
        Args:
            message: 用户消息
            chat_id: 聊天 ID
            
        Yields:
            AI 回复片段
        """
        async for chunk in await self.generate_response(
            user_input=message,
            chat_id=chat_id,
            use_knowledge=True,
            stream=True
        ):
            yield chunk
    
    def get_conversation_history(self, chat_id: str = "default") -> List[Dict]:
        """获取对话历史"""
        memory = self.conversation_manager.get_memory(chat_id)
        return memory.get_context()
    
    def clear_conversation(self, chat_id: str = "default"):
        """清空对话历史"""
        memory = self.conversation_manager.get_memory(chat_id)
        memory.clear()
        memory.start_session()
    
    async def save_all_conversations(self):
        """保存所有对话"""
        await self.conversation_manager.save_all()
