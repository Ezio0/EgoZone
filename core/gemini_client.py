"""
Gemini API Client Wrapper
Supports both Vertex AI and Google AI Studio API modes
"""

import os
from typing import List, Dict, Optional, AsyncIterator
import asyncio


class GeminiClient:
    """Gemini API client, supports both Vertex AI and Google AI Studio API modes"""

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        model_name: str = "gemini-1.5-pro",
        api_key: Optional[str] = None,
    ):
        """
        Initialize Gemini client

        Args:
            project_id: GCP project ID (for Vertex AI)
            location: GCP region (for Vertex AI)
            model_name: Model name
            api_key: Google AI Studio API key (for Google AI Studio API mode)
        """
        self.project_id = project_id or os.environ.get(
            "GOOGLE_CLOUD_PROJECT", "egozone"
        )
        self.location = location
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

        # Determine mode based on whether API key is available
        if self.api_key:
            # Use Google AI Studio API mode
            self.use_vertex_ai = False
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                },
            )
        else:
            # Use Vertex AI mode
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
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate response

        Args:
            prompt: User input
            system_instruction: System instruction
            history: Conversation history
            temperature: Temperature parameter
            max_tokens: Maximum generation length

        Returns:
            Generated response text
        """
        if self.use_vertex_ai:
            # Vertex AI mode
            from vertexai.generative_models import GenerationConfig, Content, Part

            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            # If system instruction exists, create new model instance
            if system_instruction:
                model = self.model
                # Setting system instruction in Vertex AI requires special handling
                # Add system instruction to the prompt
                prompt = f"{system_instruction}\n\n{prompt}"
            else:
                model = self.model

            # Build conversation history
            chat_history = []
            if history:
                for msg in history:
                    role = "user" if msg["role"] == "user" else "model"
                    chat_history.append(
                        Content(role=role, parts=[Part.from_text(msg["content"])])
                    )

            # Create chat session
            chat = model.start_chat(history=chat_history)

            # Generate response (execute sync call in thread pool)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: chat.send_message(prompt)
            )

            return response.text
        else:
            # Google AI Studio API mode
            import google.generativeai as genai

            # Prepare conversation history
            chat_history = []
            if history:
                for msg in history:
                    role = "user" if msg["role"] == "user" else "model"
                    chat_history.append({"role": role, "parts": [msg["content"]]})

            # Create chat session
            chat = self.model.start_chat(history=chat_history)

            # Prepare generation config
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            # Handle system instruction
            if system_instruction:
                # For Google AI Studio, we pass system instruction as first conversation turn
                prompt = f"{system_instruction}\n\n{prompt}"

            # Generate response
            response = await chat.send_message_async(
                prompt, generation_config=generation_config
            )

            return response.text

    async def generate_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """
        Stream generate response

        Args:
            prompt: User input
            system_instruction: System instruction
            history: Conversation history
            temperature: Temperature parameter
            max_tokens: Maximum generation length

        Yields:
            Generated text chunks
        """
        if self.use_vertex_ai:
            # Vertex AI mode
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

            # Stream generation
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: chat.send_message(prompt, stream=True)
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text
        else:
            # Google AI Studio API mode
            import google.generativeai as genai

            chat_history = []
            if history:
                for msg in history:
                    role = "user" if msg["role"] == "user" else "model"
                    chat_history.append({"role": role, "parts": [msg["content"]]})

            chat = self.model.start_chat(history=chat_history)

            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            if system_instruction:
                prompt = f"{system_instruction}\n\n{prompt}"

            response = await chat.send_message_async(
                prompt, generation_config=generation_config, stream=True
            )

            async for chunk in response:
                if chunk.text:
                    yield chunk.text

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate text embedding vector

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        if self.use_vertex_ai:
            # Vertex AI mode
            from vertexai.language_models import TextEmbeddingModel

            loop = asyncio.get_event_loop()
            model = TextEmbeddingModel.from_pretrained("text-embedding-004")

            result = await loop.run_in_executor(
                None, lambda: model.get_embeddings([text])
            )

            return result[0].values
        else:
            # Google AI Studio API mode
            import google.generativeai as genai

            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document",
            )

            return result["embedding"]

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Batch generate text embedding vectors

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        if self.use_vertex_ai:
            # Vertex AI mode
            from vertexai.language_models import TextEmbeddingModel

            loop = asyncio.get_event_loop()
            model = TextEmbeddingModel.from_pretrained("text-embedding-004")

            result = await loop.run_in_executor(
                None, lambda: model.get_embeddings(texts)
            )

            return [embedding.values for embedding in result]
        else:
            # Google AI Studio API mode
            import google.generativeai as genai

            result = genai.embed_content(
                model="models/text-embedding-004",
                content=texts,
                task_type="retrieval_document",
            )

            return result["embedding"]
