"""
用户画像管理
存储和管理用户的个性特征、知识背景、说话风格等信息
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import json
import os
from pathlib import Path


class UserProfile(BaseModel):
    """用户画像数据模型"""
    
    # 基本信息
    name: str = "我"
    avatar: Optional[str] = None
    
    # 教育与职业背景
    education: str = ""  # 教育背景
    profession: str = ""  # 职业
    company: Optional[str] = None  # 公司（可选）
    work_experience_years: Optional[int] = None  # 工作年限
    
    # 专业领域
    expertise_areas: List[str] = Field(default_factory=list)  # 专长领域
    technical_skills: List[str] = Field(default_factory=list)  # 技术技能
    industry_knowledge: List[str] = Field(default_factory=list)  # 行业知识
    
    # 性格特征
    personality_traits: List[str] = Field(default_factory=list)  # 性格特点
    values: List[str] = Field(default_factory=list)  # 价值观
    interests: List[str] = Field(default_factory=list)  # 兴趣爱好
    
    # 沟通风格
    communication_style: str = "友好、专业"  # 沟通风格描述
    tone_of_voice: str = "温和"  # 语气风格
    formality_level: str = "semi-formal"  # 正式程度: formal, semi-formal, casual
    
    # 语言习惯
    common_expressions: List[str] = Field(default_factory=list)  # 常用表达/口头禅
    emoji_usage: str = "moderate"  # emoji 使用习惯: none, light, moderate, heavy
    preferred_language: str = "zh-CN"  # 首选语言
    
    # 观点和经验（通过问答采集）
    collected_insights: List[Dict] = Field(default_factory=list)  # 采集的观点
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_insight(self, question: str, answer: str, category: str = "general"):
        """添加采集的观点"""
        self.collected_insights.append({
            "question": question,
            "answer": answer,
            "category": category,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def get_summary(self) -> str:
        """生成用户画像摘要"""
        summary_parts = []
        
        if self.name:
            summary_parts.append(f"我是{self.name}")
        if self.education:
            summary_parts.append(f"教育背景是{self.education}")
        if self.profession:
            summary_parts.append(f"职业是{self.profession}")
        if self.expertise_areas:
            summary_parts.append(f"专长于{', '.join(self.expertise_areas)}")
        if self.personality_traits:
            summary_parts.append(f"性格特点包括{', '.join(self.personality_traits)}")
        if self.communication_style:
            summary_parts.append(f"沟通风格是{self.communication_style}")
            
        return "。".join(summary_parts) + "。" if summary_parts else ""


class UserProfileManager:
    """用户画像管理器"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.profile_path = self.data_dir / "user_profile.json"
        self.gcs_path = "data/user_profile.json"  # GCS 中的路径
        self.profile: Optional[UserProfile] = None
        self._gcs_storage = None
    
    @property
    def gcs_storage(self):
        """延迟导入 GCS 存储"""
        if self._gcs_storage is None:
            from core.storage import get_gcs_storage
            self._gcs_storage = get_gcs_storage()
        return self._gcs_storage
        
    async def initialize(self):
        """初始化，加载或创建用户画像"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 优先从 GCS 加载
        await self.load()
        
        if self.profile is None:
            # 创建默认画像（包含用户提供的背景信息）
            self.profile = UserProfile(
                education="计算机专业本科",
                profession="互联网产品经理",
                expertise_areas=["产品设计", "用户体验", "需求分析", "项目管理"],
                technical_skills=["产品规划", "原型设计", "数据分析", "敏捷开发"],
                industry_knowledge=["互联网行业", "软件开发流程", "用户增长"],
                communication_style="专业且友好，善于倾听和表达",
                personality_traits=["逻辑清晰", "注重细节", "善于沟通"]
            )
            await self.save()
    
    async def load(self):
        """加载用户画像（优先 GCS，其次本地）"""
        try:
            # 首先尝试从 GCS 加载
            if self.gcs_storage.use_gcs:
                data = self.gcs_storage.download_json(self.gcs_path)
                if data:
                    self.profile = UserProfile(**data)
                    # 同步到本地
                    with open(self.profile_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                    return
            
            # 从本地加载
            if self.profile_path.exists():
                with open(self.profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.profile = UserProfile(**data)
        except Exception as e:
            print(f"加载用户画像失败: {e}")
            self.profile = None
    
    async def save(self):
        """保存用户画像（同时保存到本地和 GCS）"""
        if not self.profile:
            return
            
        try:
            data = self.profile.model_dump()
            
            # 保存到本地
            with open(self.profile_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            # 同步到 GCS
            if self.gcs_storage.use_gcs:
                self.gcs_storage.upload_json(data, self.gcs_path)
                
        except Exception as e:
            print(f"保存用户画像失败: {e}")
    
    async def update(self, **kwargs):
        """更新用户画像"""
        if self.profile:
            for key, value in kwargs.items():
                if hasattr(self.profile, key):
                    setattr(self.profile, key, value)
            self.profile.updated_at = datetime.now()
            await self.save()
    
    async def add_insight(self, question: str, answer: str, category: str = "general"):
        """添加采集的观点"""
        if self.profile:
            self.profile.add_insight(question, answer, category)
            await self.save()
    
    def get_profile(self) -> Optional[UserProfile]:
        """获取当前用户画像"""
        return self.profile
    
    def build_personality_prompt(self) -> str:
        """构建个性化 System Prompt"""
        if not self.profile:
            return ""
        
        prompt_parts = [
            "你是一个 AI 数字分身，你正在模拟以下这个人的说话方式和思维方式进行对话：",
            "",
            f"## 基本背景",
            self.profile.get_summary(),
            "",
            f"## 沟通风格",
            f"- 语气风格：{self.profile.tone_of_voice}",
            f"- 沟通特点：{self.profile.communication_style}",
            f"- 正式程度：{'正式' if self.profile.formality_level == 'formal' else '半正式' if self.profile.formality_level == 'semi-formal' else '随意'}",
        ]
        
        if self.profile.common_expressions:
            prompt_parts.append(f"- 常用表达：{', '.join(self.profile.common_expressions)}")
        
        emoji_desc = {
            "none": "不使用",
            "light": "偶尔使用",
            "moderate": "适度使用",
            "heavy": "经常使用"
        }
        prompt_parts.append(f"- Emoji 使用：{emoji_desc.get(self.profile.emoji_usage, '适度使用')}")
        
        if self.profile.personality_traits:
            prompt_parts.extend([
                "",
                "## 性格特点",
                "、".join(self.profile.personality_traits)
            ])
        
        if self.profile.values:
            prompt_parts.extend([
                "",
                "## 价值观",
                "、".join(self.profile.values)
            ])
        
        # 添加采集的观点（最近10条）
        if self.profile.collected_insights:
            recent_insights = self.profile.collected_insights[-10:]
            prompt_parts.extend([
                "",
                "## 我的一些观点和经验"
            ])
            for insight in recent_insights:
                prompt_parts.append(f"- 问：{insight['question']}")
                prompt_parts.append(f"  答：{insight['answer']}")
        
        prompt_parts.extend([
            "",
            "## 重要提示",
            "- 请用第一人称回答问题，就像这个人在亲自回答一样",
            "- 保持这个人的说话风格和思维方式",
            "- 如果遇到不确定的问题，可以诚实地说不太确定",
            "- 回答要自然、真实，像和朋友聊天一样"
        ])
        
        return "\n".join(prompt_parts)
