"""
对话记忆管理
管理对话上下文和历史记录
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import deque
import json
from pathlib import Path
import asyncio
import re


class Message:
    """消息对象"""

    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None, importance: float = 0.5):
        self.role = role  # "user" 或 "model"
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.importance = importance  # 消息重要性评分 (0.0-1.0)
        self.message_id = f"{self.timestamp.timestamp()}_{hash(content) % 10000}"

    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "message_id": self.message_id
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None,
            importance=data.get("importance", 0.5)
        )


class ConversationMemory:
    """对话记忆管理 - 支持智能上下文管理"""

    def __init__(
        self,
        max_context_messages: int = 20,
        max_context_tokens: int = 4000,  # 最大上下文token数
        importance_threshold: float = 0.3,  # 重要性阈值
        data_dir: str = "./data/conversations"
    ):
        """
        初始化对话记忆

        Args:
            max_context_messages: 上下文最大消息数
            max_context_tokens: 上下文最大token数
            importance_threshold: 重要性阈值
            data_dir: 对话历史存储目录
        """
        self.max_context_messages = max_context_messages
        self.max_context_tokens = max_context_tokens
        self.importance_threshold = importance_threshold
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 当前会话消息
        self.current_session: deque = deque(maxlen=max_context_messages * 2)  # 增加内部缓冲区
        self.session_id: Optional[str] = None

        # 统计信息
        self.stats = {
            "total_messages": 0,
            "important_messages": 0,
            "summarized_sessions": 0
        }

    def start_session(self, session_id: Optional[str] = None):
        """开始新会话"""
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session.clear()
        return self.session_id

    def estimate_tokens(self, text: str) -> int:
        """估算文本的 token 数量（简化估算）"""
        # 英文按空格分割，中文按字符计数
        if re.search(r'[\u4e00-\u9fff]', text):  # 包含中文
            # 中文每个字符约1个token
            return len(re.findall(r'[\u4e00-\u9fff]|\w+', text))
        else:
            # 英文单词约1个token
            return len(text.split())

    def calculate_importance(self, content: str, role: str) -> float:
        """计算消息重要性分数 (0.0-1.0)"""
        score = 0.5  # 基础分数

        # 问题类型消息重要性更高
        if role == "user":
            score += 0.1

        # 包含关键问句的重要
        question_keywords = ['?', '？', '为什么', '怎么', '如何', '什么', '哪个', '何时', '何地', '是否']
        if any(keyword in content for keyword in question_keywords):
            score += 0.15

        # 包含数字、日期等具体信息
        if re.search(r'\d{4}年|\d+月|\d+日|\d+:\d+|\d+\.\d+|\d+%|\d+元', content):
            score += 0.1

        # 包含个人代词（可能涉及上下文）
        personal_keywords = ['我', '你', '他', '她', '它', '我们', '你们', '他们', '我的', '你的', '他的', '她的']
        if any(keyword in content for keyword in personal_keywords):
            score += 0.05

        # 长度适中的消息可能更重要
        if 20 <= len(content) <= 200:
            score += 0.05

        # 确保分数在范围内
        return min(1.0, max(0.0, score))

    def add_message(self, role: str, content: str):
        """添加消息到当前会话，并计算重要性"""
        importance = self.calculate_importance(content, role)
        message = Message(role=role, content=content, importance=importance)

        self.current_session.append(message)
        self.stats["total_messages"] += 1

        if importance >= self.importance_threshold:
            self.stats["important_messages"] += 1

    def add_user_message(self, content: str):
        """添加用户消息"""
        self.add_message("user", content)

    def add_assistant_message(self, content: str):
        """添加助手消息"""
        self.add_message("model", content)

    def get_context_by_importance(self, max_messages: Optional[int] = None, min_importance: float = 0.0) -> List[Dict]:
        """
        根据重要性获取对话上下文

        Args:
            max_messages: 最大消息数，None 表示无限制
            min_importance: 最低重要性阈值

        Returns:
            消息列表，按时间倒序排列
        """
        # 按重要性和时间排序，优先保留重要消息
        messages = list(self.current_session)

        # 过滤重要性
        filtered_messages = [msg for msg in messages if msg.importance >= min_importance]

        # 按重要性降序、时间升序排列
        sorted_messages = sorted(filtered_messages, key=lambda x: (-x.importance, x.timestamp))

        if max_messages:
            # 先取最重要的消息，然后补充较新的消息
            sorted_messages = sorted_messages[:max_messages]
            # 确保时间顺序正确（最新的在后面）
            sorted_messages.sort(key=lambda x: x.timestamp)

        return [{"role": m.role, "content": m.content} for m in sorted_messages]

    def get_context_by_tokens(self, max_tokens: int) -> List[Dict]:
        """
        根据token数量获取对话上下文

        Args:
            max_tokens: 最大token数量

        Returns:
            消息列表，按时间顺序排列
        """
        messages = list(self.current_session)
        result_messages = []
        total_tokens = 0

        # 从最新的消息开始添加，直到达到token限制
        for message in reversed(messages):
            message_tokens = self.estimate_tokens(message.content)
            if total_tokens + message_tokens > max_tokens:
                break

            result_messages.insert(0, message)  # 插入到开头以保持时间顺序
            total_tokens += message_tokens

        return [{"role": m.role, "content": m.content} for m in result_messages]

    def get_context(self, max_messages: Optional[int] = None) -> List[Dict]:
        """
        获取对话上下文 - 智能选择最相关的内容

        Args:
            max_messages: 最大消息数，None 表示全部

        Returns:
            消息列表，格式: [{"role": "user/model", "content": "..."}]
        """
        # 如果没有设置最大消息数，则使用token限制
        if max_messages is None:
            return self.get_context_by_tokens(self.max_context_tokens)

        # 否则使用消息数量限制
        messages = list(self.current_session)
        if max_messages:
            # 优先保留重要消息和最近的消息
            if len(messages) > max_messages:
                # 计算需要保留的重要消息数量
                important_msgs = [m for m in messages if m.importance >= self.importance_threshold]

                # 保留所有重要消息（不超过总数的一半）
                important_to_keep = min(len(important_msgs), max_messages // 2)
                recent_to_add = max_messages - important_to_keep

                # 取最重要的消息和最近的消息
                sorted_important = sorted(important_msgs, key=lambda x: x.importance, reverse=True)[:important_to_keep]
                recent_msgs = messages[-recent_to_add:] if recent_to_add > 0 else []

                # 合并并按时间排序
                combined_messages = sorted(set(sorted_important + recent_msgs), key=lambda x: x.timestamp)
                messages = combined_messages

        return [{"role": m.role, "content": m.content} for m in messages]

    def get_recent_context(self, n: int = 10) -> List[Dict]:
        """获取最近 n 条消息"""
        messages = list(self.current_session)
        recent_messages = messages[-n:] if len(messages) >= n else messages
        return [{"role": m.role, "content": m.content} for m in recent_messages]

    def get_topic_summary(self, topic_keywords: List[str] = None) -> str:
        """
        获取特定话题的上下文摘要

        Args:
            topic_keywords: 话题关键词列表

        Returns:
            包含话题相关信息的上下文
        """
        if not topic_keywords:
            # 默认获取最近的相关对话
            return self.get_session_summary()

        relevant_messages = []
        for msg in self.current_session:
            if any(keyword in msg.content for keyword in topic_keywords):
                relevant_messages.append(msg)

        if not relevant_messages:
            return ""

        summary_parts = ["以下是相关的历史对话信息:"]
        for msg in relevant_messages[-5:]:  # 最多返回5条相关消息
            role_name = "用户说" if msg.role == "user" else "AI说"
            summary_parts.append(f"{role_name}: {msg.content}")

        return "\n".join(summary_parts)

    async def save_session(self):
        """保存当前会话到文件"""
        if not self.session_id or not self.current_session:
            return

        session_file = self.data_dir / f"{self.session_id}.json"
        data = {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.current_session],
            "stats": self.stats,
            "saved_at": datetime.now().isoformat()
        }

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def load_session(self, session_id: str) -> bool:
        """加载历史会话"""
        session_file = self.data_dir / f"{session_id}.json"

        if not session_file.exists():
            return False

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.session_id = session_id
            self.current_session.clear()

            for msg_data in data.get("messages", []):
                message = Message.from_dict(msg_data)
                self.current_session.append(message)

            # 恢复统计信息
            self.stats = data.get("stats", self.stats)

            return True
        except Exception as e:
            print(f"加载会话失败: {e}")
            return False

    def clear(self):
        """清空当前会话"""
        self.current_session.clear()
        # 重置统计信息
        self.stats = {
            "total_messages": 0,
            "important_messages": 0,
            "summarized_sessions": 0
        }

    def get_session_summary(self) -> str:
        """获取会话摘要（用于长期记忆）"""
        if not self.current_session:
            return ""

        messages = list(self.current_session)
        summary_parts = ["会话摘要:"]

        # 获取重要的消息
        important_messages = [msg for msg in messages if msg.importance >= self.importance_threshold]

        if important_messages:
            summary_parts.append("重要内容:")
            for msg in important_messages[-3:]:  # 最近3条重要消息
                role_name = "用户" if msg.role == "user" else "AI"
                content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                summary_parts.append(f"  [{role_name}] 重要性:{msg.importance:.2f} - {content_preview}")

        # 添加最近的几条消息
        recent_messages = messages[-3:] if len(messages) >= 3 else messages
        if recent_messages:
            summary_parts.append("\n最近对话:")
            for msg in recent_messages:
                role_name = "用户" if msg.role == "user" else "AI"
                content_preview = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
                summary_parts.append(f"  {role_name}: {content_preview}")

        return "\n".join(summary_parts)

    def get_memory_state(self) -> Dict:
        """获取记忆状态信息"""
        return {
            "session_id": self.session_id,
            "message_count": len(self.current_session),
            "important_message_count": len([m for m in self.current_session if m.importance >= self.importance_threshold]),
            "average_importance": sum(m.importance for m in self.current_session) / len(self.current_session) if self.current_session else 0,
            "estimated_tokens": sum(self.estimate_tokens(m.content) for m in self.current_session),
            "stats": self.stats
        }


class ConversationManager:
    """多会话管理器 - 支持跨会话记忆"""

    def __init__(self, data_dir: str = "./data/conversations", max_active_sessions: int = 10):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memories: Dict[str, ConversationMemory] = {}
        self.max_active_sessions = max_active_sessions

        # 全局会话统计数据
        self.global_stats = {
            "total_sessions": 0,
            "total_messages": 0,
            "active_sessions": 0
        }

    def get_memory(self, chat_id: str) -> ConversationMemory:
        """获取或创建指定聊天的记忆"""
        if chat_id not in self.memories:
            # 如果超过最大活跃会话数，清理最久未使用的
            if len(self.memories) >= self.max_active_sessions:
                # 简单地移除第一个会话（实际应用中可能需要更复杂的LRU机制）
                oldest_key = next(iter(self.memories))
                del self.memories[oldest_key]

            memory = ConversationMemory(data_dir=str(self.data_dir / chat_id))
            memory.start_session()
            self.memories[chat_id] = memory
            self.global_stats["total_sessions"] += 1
            self.global_stats["active_sessions"] = len(self.memories)

        return self.memories[chat_id]

    def get_all_sessions_summary(self) -> Dict[str, str]:
        """获取所有会话的摘要"""
        summaries = {}
        for chat_id, memory in self.memories.items():
            summaries[chat_id] = memory.get_session_summary()
        return summaries

    def get_global_stats(self) -> Dict:
        """获取全局统计信息"""
        self.global_stats["active_sessions"] = len(self.memories)
        self.global_stats["total_messages"] = sum(mem.stats["total_messages"] for mem in self.memories.values())
        return self.global_stats

    async def save_all(self):
        """保存所有会话"""
        for memory in self.memories.values():
            await memory.save_session()

    async def cleanup_inactive_sessions(self, max_age_hours: int = 24):
        """清理长时间未活动的会话"""
        # 这里可以实现会话清理逻辑
        pass