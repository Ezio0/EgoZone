"""
Conversation Memory Management
Manage conversation context and history
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import deque
import json
from pathlib import Path
import asyncio
import re


class Message:
    """Message object"""

    def __init__(
        self,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        importance: float = 0.5,
    ):
        self.role = role  # "user" or "model"
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.importance = importance  # Message importance score (0.0-1.0)
        self.message_id = f"{self.timestamp.timestamp()}_{hash(content) % 10000}"

    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "message_id": self.message_id,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else None,
            importance=data.get("importance", 0.5),
        )


class ConversationMemory:
    """Conversation memory management - supports intelligent context management"""

    def __init__(
        self,
        max_context_messages: int = 20,
        max_context_tokens: int = 4000,  # Maximum context token count
        importance_threshold: float = 0.3,  # Importance threshold
        data_dir: str = "./data/conversations",
    ):
        """
        Initialize conversation memory

        Args:
            max_context_messages: Maximum context message count
            max_context_tokens: Maximum context token count
            importance_threshold: Importance threshold
            data_dir: Conversation history storage directory
        """
        self.max_context_messages = max_context_messages
        self.max_context_tokens = max_context_tokens
        self.importance_threshold = importance_threshold
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Current session messages
        self.current_session: deque = deque(
            maxlen=max_context_messages * 2
        )  # Increased internal buffer
        self.session_id: Optional[str] = None

        # Statistics
        self.stats = {
            "total_messages": 0,
            "important_messages": 0,
            "summarized_sessions": 0,
        }

    def start_session(self, session_id: Optional[str] = None):
        """Start new session"""
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session.clear()
        return self.session_id

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (simplified estimation)"""
        # English by spaces, Chinese by characters
        if re.search(r"[\u4e00-\u9fff]", text):  # Contains Chinese
            # Chinese characters approximately 1 token each
            return len(re.findall(r"[\u4e00-\u9fff]|\w+", text))
        else:
            # English words approximately 1 token each
            return len(text.split())

    def calculate_importance(self, content: str, role: str) -> float:
        """Calculate message importance score (0.0-1.0)"""
        score = 0.5  # Base score

        # Question type messages have higher importance
        if role == "user":
            score += 0.1

        # Contains key question words is important
        question_keywords = [
            "?",
            "？",
            "why",
            "how",
            "what",
            "which",
            "when",
            "where",
            "whether",
        ]
        if any(keyword in content for keyword in question_keywords):
            score += 0.15

        # Contains numbers, dates, or specific information
        if re.search(r"\d{4}|\d+/\d+|\d+:\d+|\d+\.\d+|\d+%", content):
            score += 0.1

        # Contains personal pronouns (may involve context)
        personal_keywords = [
            "I",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "my",
            "your",
            "his",
            "her",
        ]
        if any(keyword in content for keyword in personal_keywords):
            score += 0.05

        # Moderately length messages may be more important
        if 20 <= len(content) <= 200:
            score += 0.05

        # Ensure score is within range
        return min(1.0, max(0.0, score))

    def add_message(self, role: str, content: str):
        """Add message to current session and calculate importance"""
        importance = self.calculate_importance(content, role)
        message = Message(role=role, content=content, importance=importance)

        self.current_session.append(message)
        self.stats["total_messages"] += 1

        if importance >= self.importance_threshold:
            self.stats["important_messages"] += 1

    def add_user_message(self, content: str):
        """Add user message"""
        self.add_message("user", content)

    def add_assistant_message(self, content: str):
        """Add assistant message"""
        self.add_message("model", content)

    def get_context_by_importance(
        self, max_messages: Optional[int] = None, min_importance: float = 0.0
    ) -> List[Dict]:
        """
        Get conversation context by importance

        Args:
            max_messages: Maximum message count, None means unlimited
            min_importance: Minimum importance threshold

        Returns:
            Message list, sorted by time in descending order
        """
        # Sort by importance and time, prioritize important messages
        messages = list(self.current_session)

        # Filter by importance
        filtered_messages = [
            msg for msg in messages if msg.importance >= min_importance
        ]

        # Sort by importance descending, time ascending
        sorted_messages = sorted(
            filtered_messages, key=lambda x: (-x.importance, x.timestamp)
        )

        if max_messages:
            # Take most important messages first, then add recent messages
            sorted_messages = sorted_messages[:max_messages]
            # Ensure correct time order (newest at end)
            sorted_messages.sort(key=lambda x: x.timestamp)

        return [{"role": m.role, "content": m.content} for m in sorted_messages]

    def get_context_by_tokens(self, max_tokens: int) -> List[Dict]:
        """
        Get conversation context by token count

        Args:
            max_tokens: Maximum token count

        Returns:
            Message list, sorted by time
        """
        messages = list(self.current_session)
        result_messages = []
        total_tokens = 0

        # Add from newest messages until reaching token limit
        for message in reversed(messages):
            message_tokens = self.estimate_tokens(message.content)
            if total_tokens + message_tokens > max_tokens:
                break

            result_messages.insert(
                0, message
            )  # Insert at beginning to maintain time order
            total_tokens += message_tokens

        return [{"role": m.role, "content": m.content} for m in result_messages]

    def get_context(self, max_messages: Optional[int] = None) -> List[Dict]:
        """
        Get conversation context - intelligently select most relevant content

        Args:
            max_messages: Maximum message count, None means all

        Returns:
            Message list, format: [{"role": "user/model", "content": "..."}]
        """
        # If no max message count set, use token limit
        if max_messages is None:
            return self.get_context_by_tokens(self.max_context_tokens)

        # Otherwise use message count limit
        messages = list(self.current_session)
        if max_messages:
            # Prioritize important messages and recent messages
            if len(messages) > max_messages:
                # Calculate how many important messages to keep
                important_msgs = [
                    m for m in messages if m.importance >= self.importance_threshold
                ]

                # Keep all important messages (not more than half of total)
                important_to_keep = min(len(important_msgs), max_messages // 2)
                recent_to_add = max_messages - important_to_keep

                # Take most important messages and recent messages
                sorted_important = sorted(
                    important_msgs, key=lambda x: x.importance, reverse=True
                )[:important_to_keep]
                recent_msgs = messages[-recent_to_add:] if recent_to_add > 0 else []

                # Merge and sort by time
                combined_messages = sorted(
                    set(sorted_important + recent_msgs), key=lambda x: x.timestamp
                )
                messages = combined_messages

        return [{"role": m.role, "content": m.content} for m in messages]

    def get_recent_context(self, n: int = 10) -> List[Dict]:
        """Get most recent n messages"""
        messages = list(self.current_session)
        recent_messages = messages[-n:] if len(messages) >= n else messages
        return [{"role": m.role, "content": m.content} for m in recent_messages]

    def get_topic_summary(self, topic_keywords: List[str] = None) -> str:
        """
        Get context summary for specific topic

        Args:
            topic_keywords: Topic keyword list

        Returns:
            Context containing topic-related information
        """
        if not topic_keywords:
            # Default to getting recent related conversations
            return self.get_session_summary()

        relevant_messages = []
        for msg in self.current_session:
            if any(keyword in msg.content for keyword in topic_keywords):
                relevant_messages.append(msg)

        if not relevant_messages:
            return ""

        summary_parts = ["Below is relevant historical conversation:"]
        for msg in relevant_messages[-5:]:  # Return at most 5 related messages
            role_name = "User said" if msg.role == "user" else "AI said"
            summary_parts.append(f"{role_name}: {msg.content}")

        return "\n".join(summary_parts)

    async def save_session(self):
        """Save current session to file"""
        if not self.session_id or not self.current_session:
            return

        session_file = self.data_dir / f"{self.session_id}.json"
        data = {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.current_session],
            "stats": self.stats,
            "saved_at": datetime.now().isoformat(),
        }

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def load_session(self, session_id: str) -> bool:
        """Load historical session"""
        session_file = self.data_dir / f"{session_id}.json"

        if not session_file.exists():
            return False

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.session_id = session_id
            self.current_session.clear()

            for msg_data in data.get("messages", []):
                message = Message.from_dict(msg_data)
                self.current_session.append(message)

            # Restore statistics
            self.stats = data.get("stats", self.stats)

            return True
        except Exception as e:
            print(f"Failed to load session: {e}")
            return False

    def clear(self):
        """Clear current session"""
        self.current_session.clear()
        # Reset statistics
        self.stats = {
            "total_messages": 0,
            "important_messages": 0,
            "summarized_sessions": 0,
        }

    def get_session_summary(self) -> str:
        """Get session summary (for long-term memory)"""
        if not self.current_session:
            return ""

        messages = list(self.current_session)
        summary_parts = ["Session summary:"]

        # Get important messages
        important_messages = [
            msg for msg in messages if msg.importance >= self.importance_threshold
        ]

        if important_messages:
            summary_parts.append("Important content:")
            for msg in important_messages[-3:]:  # Most recent 3 important messages
                role_name = "User" if msg.role == "user" else "AI"
                content_preview = (
                    msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                )
                summary_parts.append(
                    f"  [{role_name}] importance:{msg.importance:.2f} - {content_preview}"
                )

        # Add most recent messages
        recent_messages = messages[-3:] if len(messages) >= 3 else messages
        if recent_messages:
            summary_parts.append("\nRecent conversation:")
            for msg in recent_messages:
                role_name = "User" if msg.role == "user" else "AI"
                content_preview = (
                    msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
                )
                summary_parts.append(f"  {role_name}: {content_preview}")

        return "\n".join(summary_parts)

    def get_memory_state(self) -> Dict:
        """Get memory state information"""
        return {
            "session_id": self.session_id,
            "message_count": len(self.current_session),
            "important_message_count": len(
                [
                    m
                    for m in self.current_session
                    if m.importance >= self.importance_threshold
                ]
            ),
            "average_importance": sum(m.importance for m in self.current_session)
            / len(self.current_session)
            if self.current_session
            else 0,
            "estimated_tokens": sum(
                self.estimate_tokens(m.content) for m in self.current_session
            ),
            "stats": self.stats,
        }


class ConversationManager:
    """Multi-session manager - supports cross-session memory"""

    def __init__(
        self, data_dir: str = "./data/conversations", max_active_sessions: int = 10
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memories: Dict[str, ConversationMemory] = {}
        self.max_active_sessions = max_active_sessions

        # Global session statistics
        self.global_stats = {
            "total_sessions": 0,
            "total_messages": 0,
            "active_sessions": 0,
        }

    def get_memory(self, chat_id: str) -> ConversationMemory:
        """Get or create memory for specified chat"""
        if chat_id not in self.memories:
            # If max active sessions exceeded, clean up least recently used
            if len(self.memories) >= self.max_active_sessions:
                # Simply remove first session (real apps may need more complex LRU mechanism)
                oldest_key = next(iter(self.memories))
                del self.memories[oldest_key]

            memory = ConversationMemory(data_dir=str(self.data_dir / chat_id))
            memory.start_session()
            self.memories[chat_id] = memory
            self.global_stats["total_sessions"] += 1
            self.global_stats["active_sessions"] = len(self.memories)

        return self.memories[chat_id]

    def get_all_sessions_summary(self) -> Dict[str, str]:
        """Get summary of all sessions"""
        summaries = {}
        for chat_id, memory in self.memories.items():
            summaries[chat_id] = memory.get_session_summary()
        return summaries

    def get_global_stats(self) -> Dict:
        """Get global statistics"""
        self.global_stats["active_sessions"] = len(self.memories)
        self.global_stats["total_messages"] = sum(
            mem.stats["total_messages"] for mem in self.memories.values()
        )
        return self.global_stats

    async def save_all(self):
        """Save all sessions"""
        for memory in self.memories.values():
            await memory.save_session()

    async def cleanup_inactive_sessions(self, max_age_hours: int = 24):
        """Clean up sessions inactive for a long time"""
        # Session cleanup logic can be implemented here
        pass
