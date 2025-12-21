"""
问答采集 API 路由
用于通过问答方式收集用户的观点和经验
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import random

router = APIRouter()

# 问题库
INTERVIEW_QUESTIONS = {
    "personal_background": {
        "name": "个人背景",
        "questions": [
            "请简单介绍一下你自己？",
            "你的教育经历是怎样的？",
            "是什么让你选择了现在的职业？",
            "你工作中最有成就感的一件事是什么？"
        ]
    },
    "professional_insights": {
        "name": "职业观点",
        "questions": [
            "作为产品经理，你如何定义一个好产品？",
            "你认为产品经理最重要的能力是什么？",
            "遇到需求冲突时，你通常如何处理？",
            "你如何看待用户反馈？",
            "你的产品方法论是什么？",
            "你如何平衡用户需求和商业目标？"
        ]
    },
    "thinking_patterns": {
        "name": "思维方式",
        "questions": [
            "遇到复杂问题时，你通常如何分析？",
            "你如何做决策？有什么原则吗？",
            "你如何保持学习和成长？",
            "你如何看待失败和挫折？",
            "你的时间管理方式是怎样的？"
        ]
    },
    "communication_style": {
        "name": "沟通风格",
        "questions": [
            "你平时喜欢用什么样的语气和别人交流？",
            "你觉得自己是什么性格的人？",
            "和同事沟通时，你有什么习惯或技巧？",
            "你如何给别人提反馈意见？",
            "有什么口头禅或常用表达吗？"
        ]
    },
    "values_and_beliefs": {
        "name": "价值观",
        "questions": [
            "你的人生信条或座右铭是什么？",
            "工作中你最看重什么？",
            "你理想的工作方式是什么样的？",
            "你如何看待工作与生活的平衡？",
            "你最欣赏什么样的人？"
        ]
    },
    "interests_and_hobbies": {
        "name": "兴趣爱好",
        "questions": [
            "工作之外你喜欢做什么？",
            "最近在读什么书或关注什么话题？",
            "有什么特别的爱好或技能吗？",
            "周末通常怎么度过？"
        ]
    }
}


class AnswerRequest(BaseModel):
    """回答请求"""
    question_id: str = Field(..., description="问题 ID")
    question: str = Field(..., description="问题内容")
    answer: str = Field(..., description="回答内容")
    category: str = Field(..., description="问题类别")


class Question(BaseModel):
    """问题"""
    id: str
    question: str
    category: str
    category_name: str


class CategoryInfo(BaseModel):
    """类别信息"""
    id: str
    name: str
    question_count: int
    answered_count: int


def get_profile_manager():
    """获取用户画像管理器"""
    from main import get_profile_manager
    pm = get_profile_manager()
    if not pm:
        raise HTTPException(status_code=503, detail="服务尚未初始化")
    return pm


@router.get("/categories")
async def get_categories() -> List[CategoryInfo]:
    """
    获取所有问题类别
    """
    pm = get_profile_manager()
    profile = pm.get_profile()
    
    # 统计每个类别已回答的问题数
    answered_questions = {}
    if profile and profile.collected_insights:
        for insight in profile.collected_insights:
            cat = insight.get("category", "general")
            answered_questions[cat] = answered_questions.get(cat, 0) + 1
    
    categories = []
    for cat_id, cat_data in INTERVIEW_QUESTIONS.items():
        categories.append(CategoryInfo(
            id=cat_id,
            name=cat_data["name"],
            question_count=len(cat_data["questions"]),
            answered_count=answered_questions.get(cat_id, 0)
        ))
    
    return categories


@router.get("/questions/{category}")
async def get_questions(category: str) -> List[Question]:
    """
    获取指定类别的问题列表
    
    - **category**: 问题类别 ID
    """
    if category not in INTERVIEW_QUESTIONS:
        raise HTTPException(status_code=404, detail=f"未找到类别: {category}")
    
    cat_data = INTERVIEW_QUESTIONS[category]
    questions = []
    
    for i, q in enumerate(cat_data["questions"]):
        questions.append(Question(
            id=f"{category}_{i}",
            question=q,
            category=category,
            category_name=cat_data["name"]
        ))
    
    return questions


@router.get("/random")
async def get_random_question() -> Question:
    """
    获取一个随机问题
    """
    category = random.choice(list(INTERVIEW_QUESTIONS.keys()))
    cat_data = INTERVIEW_QUESTIONS[category]
    question = random.choice(cat_data["questions"])
    question_index = cat_data["questions"].index(question)
    
    return Question(
        id=f"{category}_{question_index}",
        question=question,
        category=category,
        category_name=cat_data["name"]
    )


@router.get("/next")
async def get_next_question() -> Question:
    """
    获取下一个建议回答的问题（智能选择尚未回答的问题）
    """
    pm = get_profile_manager()
    profile = pm.get_profile()
    
    # 收集已回答的问题
    answered_questions = set()
    if profile and profile.collected_insights:
        for insight in profile.collected_insights:
            answered_questions.add(insight.get("question", ""))
    
    # 查找未回答的问题
    unanswered = []
    for cat_id, cat_data in INTERVIEW_QUESTIONS.items():
        for i, q in enumerate(cat_data["questions"]):
            if q not in answered_questions:
                unanswered.append({
                    "id": f"{cat_id}_{i}",
                    "question": q,
                    "category": cat_id,
                    "category_name": cat_data["name"]
                })
    
    if not unanswered:
        # 所有问题都已回答，返回随机问题
        return await get_random_question()
    
    # 随机选择一个未回答的问题
    selected = random.choice(unanswered)
    return Question(**selected)


@router.post("/answer")
async def submit_answer(request: AnswerRequest):
    """
    提交问题回答
    
    - **question_id**: 问题 ID
    - **question**: 问题内容
    - **answer**: 回答内容
    - **category**: 问题类别
    """
    if not request.answer.strip():
        raise HTTPException(status_code=400, detail="回答内容不能为空")
    
    pm = get_profile_manager()
    
    await pm.add_insight(
        question=request.question,
        answer=request.answer,
        category=request.category
    )
    
    return {
        "status": "success",
        "message": "回答已保存",
        "question_id": request.question_id
    }


@router.get("/progress")
async def get_progress():
    """
    获取问答进度
    """
    pm = get_profile_manager()
    profile = pm.get_profile()
    
    total_questions = sum(
        len(cat["questions"]) for cat in INTERVIEW_QUESTIONS.values()
    )
    
    answered_count = 0
    if profile and profile.collected_insights:
        answered_count = len(profile.collected_insights)
    
    return {
        "total_questions": total_questions,
        "answered_count": answered_count,
        "progress_percent": round(answered_count / total_questions * 100, 1) if total_questions > 0 else 0
    }


@router.get("/insights")
async def get_all_insights():
    """
    获取所有采集的观点
    """
    pm = get_profile_manager()
    profile = pm.get_profile()
    
    if not profile or not profile.collected_insights:
        return {"insights": [], "count": 0}
    
    return {
        "insights": profile.collected_insights,
        "count": len(profile.collected_insights)
    }
