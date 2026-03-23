"""
Personalized Conversation Engine
Core conversation processing module, integrating user profile, knowledge base, and conversation memory
"""

from typing import List, Dict, Optional, AsyncIterator, Union
from .gemini_client import GeminiClient
from .knowledge_base import KnowledgeBase
from .user_profile import UserProfileManager
from .memory import ConversationMemory, ConversationManager


class PersonalityEngine:
    """Personalized conversation engine"""

    def __init__(
        self,
        gemini_client: GeminiClient,
        knowledge_base: KnowledgeBase,
        profile_manager: UserProfileManager,
    ):
        """
        Initialize personalized engine

        Args:
            gemini_client: Gemini API client
            knowledge_base: Knowledge base instance
            profile_manager: User profile manager
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
        stream: bool = False,
        max_context_messages: Optional[int] = 15,  # Increased context message count
    ) -> Union[str, AsyncIterator[str]]:
        """
        Generate personalized response

        Args:
            user_input: User input
            chat_id: Chat session ID
            use_knowledge: Whether to use knowledge base retrieval
            stream: Whether to use streaming output
            max_context_messages: Maximum context message count

        Returns:
            Generated response (string or async iterator)
        """
        # 1. Get conversation memory
        memory = self.conversation_manager.get_memory(chat_id)

        # 2. Retrieve relevant knowledge
        relevant_knowledge = ""
        if use_knowledge:
            docs = await self.knowledge_base.search(user_input, top_k=3)
            if docs:
                knowledge_parts = ["## Relevant Background Knowledge"]
                for doc in docs:
                    content = doc["content"][:500]  # Increased knowledge snippet length
                    knowledge_parts.append(f"- {content}")
                relevant_knowledge = "\n".join(knowledge_parts)

        # 3. Build system prompt
        system_prompt = self._build_system_prompt(relevant_knowledge)

        # 4. Get conversation history (using optimized memory mechanism)
        history = memory.get_context(max_messages=max_context_messages)

        # 5. Generate response
        if stream:
            return self._generate_stream(user_input, system_prompt, history, memory)
        else:
            response = await self.gemini.generate(
                prompt=user_input, system_instruction=system_prompt, history=history
            )

            # 6. Save conversation record
            memory.add_user_message(user_input)
            memory.add_assistant_message(response)

            return response

    async def _generate_stream(
        self,
        user_input: str,
        system_prompt: str,
        history: List[Dict],
        memory: ConversationMemory,
    ) -> AsyncIterator[str]:
        """Stream generate response"""
        full_response = ""

        async for chunk in self.gemini.generate_stream(
            prompt=user_input, system_instruction=system_prompt, history=history
        ):
            full_response += chunk
            yield chunk

        # Save complete conversation record
        memory.add_user_message(user_input)
        memory.add_assistant_message(full_response)

    def _build_system_prompt(self, relevant_knowledge: str = "") -> str:
        """Build system prompt"""
        # Base personality prompt
        personality_prompt = self.profile_manager.build_personality_prompt()

        # Combine complete prompt
        parts = [personality_prompt]

        if relevant_knowledge:
            parts.append("")
            parts.append(relevant_knowledge)

        return "\n".join(parts)

    async def chat(self, message: str, chat_id: str = "default") -> str:
        """
        Simple chat interface

        Args:
            message: User message
            chat_id: Chat ID

        Returns:
            AI response
        """
        return await self.generate_response(
            user_input=message, chat_id=chat_id, use_knowledge=True, stream=False
        )

    async def chat_stream(
        self, message: str, chat_id: str = "default"
    ) -> AsyncIterator[str]:
        """
        Streaming chat interface

        Args:
            message: User message
            chat_id: Chat ID

        Yields:
            AI response chunks
        """
        async for chunk in await self.generate_response(
            user_input=message, chat_id=chat_id, use_knowledge=True, stream=True
        ):
            yield chunk

    def get_conversation_history(self, chat_id: str = "default") -> List[Dict]:
        """Get conversation history"""
        memory = self.conversation_manager.get_memory(chat_id)
        return memory.get_context()

    def get_conversation_summary(self, chat_id: str = "default") -> str:
        """Get conversation summary"""
        memory = self.conversation_manager.get_memory(chat_id)
        return memory.get_session_summary()

    def get_memory_state(self, chat_id: str = "default") -> Dict:
        """Get memory state"""
        memory = self.conversation_manager.get_memory(chat_id)
        return memory.get_memory_state()

    def clear_conversation(self, chat_id: str = "default"):
        """Clear conversation history"""
        memory = self.conversation_manager.get_memory(chat_id)
        memory.clear()
        memory.start_session()

    async def save_all_conversations(self):
        """Save all conversations"""
        await self.conversation_manager.save_all()
