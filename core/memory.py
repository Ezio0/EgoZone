"""
对话记忆管理
管理对话上下文和历史记录
"""

from typing import List, Dict, Optional
from datetime import datetime
from collections import deque
import json
from pathlib import Path


class Message:
    """消息对象"""
    
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        self.role = role  # "user" 或 "model"
        self.content = content
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None
        )


class ConversationMemory:
    """对话记忆管理"""
    
    def __init__(
        self, 
        max_context_messages: int = 20,
        data_dir: str = "./data/conversations"
    ):
        """
        初始化对话记忆
        
        Args:
            max_context_messages: 上下文最大消息数
            data_dir: 对话历史存储目录
        """
        self.max_context_messages = max_context_messages
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前会话消息（使用 deque 自动限制长度）
        self.current_session: deque = deque(maxlen=max_context_messages)
        
        # 会话 ID
        self.session_id: Optional[str] = None
    
    def start_session(self, session_id: Optional[str] = None):
        """开始新会话"""
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session.clear()
        return self.session_id
    
    def add_message(self, role: str, content: str):
        """添加消息到当前会话"""
        message = Message(role=role, content=content)
        self.current_session.append(message)
    
    def add_user_message(self, content: str):
        """添加用户消息"""
        self.add_message("user", content)
    
    def add_assistant_message(self, content: str):
        """添加助手消息"""
        self.add_message("model", content)
    
    def get_context(self, max_messages: Optional[int] = None) -> List[Dict]:
        """
        获取对话上下文
        
        Args:
            max_messages: 最大消息数，None 表示全部
            
        Returns:
            消息列表，格式: [{"role": "user/model", "content": "..."}]
        """
        messages = list(self.current_session)
        if max_messages:
            messages = messages[-max_messages:]
        
        return [{"role": m.role, "content": m.content} for m in messages]
    
    def get_recent_context(self, n: int = 10) -> List[Dict]:
        """获取最近 n 条消息"""
        return self.get_context(max_messages=n)
    
    async def save_session(self):
        """保存当前会话到文件"""
        if not self.session_id or not self.current_session:
            return
        
        session_file = self.data_dir / f"{self.session_id}.json"
        data = {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.current_session],
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
            
            return True
        except Exception as e:
            print(f"加载会话失败: {e}")
            return False
    
    def clear(self):
        """清空当前会话"""
        self.current_session.clear()
    
    def get_session_summary(self) -> str:
        """获取会话摘要（用于长期记忆）"""
        if not self.current_session:
            return ""
        
        messages = list(self.current_session)
        summary_parts = []
        
        for msg in messages[-5:]:  # 最近5条消息
            role_name = "用户" if msg.role == "user" else "AI"
            content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            summary_parts.append(f"{role_name}: {content_preview}")
        
        return "\n".join(summary_parts)


class ConversationManager:
    """多会话管理器"""
    
    def __init__(self, data_dir: str = "./data/conversations"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memories: Dict[str, ConversationMemory] = {}
    
    def get_memory(self, chat_id: str) -> ConversationMemory:
        """获取或创建指定聊天的记忆"""
        if chat_id not in self.memories:
            memory = ConversationMemory(data_dir=str(self.data_dir / chat_id))
            memory.start_session()
            self.memories[chat_id] = memory
        return self.memories[chat_id]
    
    async def save_all(self):
        """保存所有会话"""
        for memory in self.memories.values():
            await memory.save_session()
