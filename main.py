"""
EgoZone - AI Digital Twin
Main Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path

from config import get_settings
from api import chat, knowledge, interview, auth, settings
from api.documents import router as documents_router  # Document import router
from core.gemini_client import GeminiClient
from core.personality_engine import PersonalityEngine
from core.knowledge_base import KnowledgeBase
from core.user_profile import UserProfileManager

# Global instances
gemini_client: GeminiClient = None
personality_engine: PersonalityEngine = None
knowledge_base: KnowledgeBase = None
profile_manager: UserProfileManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    global gemini_client, personality_engine, knowledge_base, profile_manager

    settings = get_settings()

    # Initialize core components
    print("🚀 Initializing EgoZone...")

    # Strict security check - block startup if issues found
    print("🔒 Running security checks...")
    from core.enhanced_security import (
        enhanced_security_validation,
        print_security_report,
    )

    is_secure, errors, warnings = enhanced_security_validation()
    print_security_report(is_secure, errors, warnings)

if not is_secure:
        print("\n❌ Critical security issues found, service startup blocked")
        print("🔧 Please fix the above issues before starting the service")
        raise RuntimeError("Security configuration check failed, service startup aborted")
    
    # Clean up expired tokens and rate limit data
    print("🧹 Cleaning up expired data...")
    from core.token_storage import get_token_storage
    from core.rate_limiter import cleanup_rate_limit_data

    token_storage = get_token_storage()
cleaned_tokens = token_storage.cleanup_expired_tokens()
    if cleaned_tokens > 0:
        print(f"✅ Cleaned up {cleaned_tokens} expired tokens")
    
    # Clean up rate limit data
    try:
        cleanup_rate_limit_data()
        print("✅ Rate limit data cleanup completed")
    except Exception as e:
        print(f"⚠️  Rate limit data cleanup failed: {e}")

    # Gemini client (supports both Vertex AI and Google AI Studio API modes)
    gemini_client = GeminiClient(
        project_id=settings.gcp_project,
        location=settings.gcp_location,
        model_name=settings.gemini_model,
        api_key=settings.gemini_api_key,
    )

# Knowledge base
    knowledge_base = KnowledgeBase()
    await knowledge_base.initialize()
    
    # User profile manager
    profile_manager = UserProfileManager()
    await profile_manager.initialize()
    
    # Personality engine
    personality_engine = PersonalityEngine(
        gemini_client=gemini_client,
        knowledge_base=knowledge_base,
        profile_manager=profile_manager,
    )

print("✅ EgoZone initialization complete!")
    print(f"📡 Using model: {settings.gemini_model}")
    
    yield
    
    # Cleanup resources
    print("👋 EgoZone is shutting down...")


# Create FastAPI application
app = FastAPI(
    title="EgoZone API",
    description="AI Digital Twin API Service",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Should be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge Base"])
app.include_router(interview.router, prefix="/api/interview", tags=["Interview"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(documents_router, tags=["Document Import"])  # Document import router

# Static file serving
WEB_DIR = Path(__file__).parent / "web"
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/")
async def root():
    """Web homepage"""
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "name": "EgoZone",
        "description": "AI Digital Twin Service",
        "version": "0.1.0",
        "status": "running",
        "web_ui": "/static/index.html"
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy"}


def get_personality_engine() -> PersonalityEngine:
    """Get personality engine instance"""
    return personality_engine


def get_knowledge_base() -> KnowledgeBase:
    """Get knowledge base instance"""
    return knowledge_base


def get_profile_manager() -> UserProfileManager:
    """Get user profile manager instance"""
    return profile_manager
