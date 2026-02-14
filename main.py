"""
EgoZone - AI 数字分身
主应用入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path

from config import get_settings
from api import chat, knowledge, interview, auth, settings
from api.documents import router as documents_router  # 新增文档导入路由
from core.gemini_client import GeminiClient
from core.personality_engine import PersonalityEngine
from core.knowledge_base import KnowledgeBase
from core.user_profile import UserProfileManager

# 全局实例
gemini_client: GeminiClient = None
personality_engine: PersonalityEngine = None
knowledge_base: KnowledgeBase = None
profile_manager: UserProfileManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global gemini_client, personality_engine, knowledge_base, profile_manager
    
    settings = get_settings()
    
    # 初始化核心组件
    print("🚀 正在初始化 EgoZone...")
    
    # Gemini 客户端 (支持 Vertex AI 和 Google AI Studio API 两种模式)
    gemini_client = GeminiClient(
        project_id=settings.gcp_project,
        location=settings.gcp_location,
        model_name=settings.gemini_model,
        api_key=settings.gemini_api_key
    )
    
    # 知识库
    knowledge_base = KnowledgeBase()
    await knowledge_base.initialize()
    
    # 用户画像管理
    profile_manager = UserProfileManager()
    await profile_manager.initialize()
    
    # 个性化引擎
    personality_engine = PersonalityEngine(
        gemini_client=gemini_client,
        knowledge_base=knowledge_base,
        profile_manager=profile_manager
    )
    
    print("✅ EgoZone 初始化完成!")
    print(f"📡 使用模型: {settings.gemini_model}")
    
    yield
    
    # 清理资源
    print("👋 EgoZone 正在关闭...")


# 创建 FastAPI 应用
app = FastAPI(
    title="EgoZone API",
    description="AI 数字分身 API 服务",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router, prefix="/api/chat", tags=["对话"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识库"])
app.include_router(interview.router, prefix="/api/interview", tags=["问答采集"])
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(settings.router, prefix="/api/settings", tags=["设置"])
app.include_router(documents_router, tags=["文档导入"])  # 新增文档导入路由

# 静态文件服务
WEB_DIR = Path(__file__).parent / "web"
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/")
async def root():
    """Web 首页"""
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "name": "EgoZone",
        "description": "AI 数字分身服务",
        "version": "0.1.0",
        "status": "running",
        "web_ui": "/static/index.html"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


def get_personality_engine() -> PersonalityEngine:
    """获取个性化引擎实例"""
    return personality_engine


def get_knowledge_base() -> KnowledgeBase:
    """获取知识库实例"""
    return knowledge_base


def get_profile_manager() -> UserProfileManager:
    """获取用户画像管理器"""
    return profile_manager
