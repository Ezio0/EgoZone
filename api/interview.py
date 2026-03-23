"""
Q&A Collection API Routes
Used to collect user perspectives and experiences through Q&A format
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import random

router = APIRouter()

# Question bank
INTERVIEW_QUESTIONS = {
    "personal_background": {
        "name": "Personal Background",
        "questions": [
            "Can you briefly introduce yourself?",
            "What is your educational background?",
            "What made you choose your current career?",
            "What is the most fulfilling thing you've accomplished in your work?",
        ],
    },
    "professional_insights": {
        "name": "Professional Insights",
        "questions": [
            "As a product manager, how do you define a good product?",
            "What do you think is the most important skill for a product manager?",
            "When facing conflicting requirements, how do you usually handle them?",
            "How do you view user feedback?",
            "What is your product methodology?",
            "How do you balance user needs and business goals?",
        ],
    },
    "thinking_patterns": {
        "name": "Thinking Patterns",
        "questions": [
            "When encountering complex problems, how do you usually analyze them?",
            "How do you make decisions? Do you have any principles?",
            "How do you keep learning and growing?",
            "How do you view failure and setbacks?",
            "What is your time management approach?",
        ],
    },
    "communication_style": {
        "name": "Communication Style",
        "questions": [
            "What tone do you prefer to use when communicating with others?",
            "What kind of person do you think you are?",
            "Do you have any habits or techniques when communicating with colleagues?",
            "How do you give feedback to others?",
            "Do you have any catchphrases or common expressions?",
        ],
    },
    "values_and_beliefs": {
        "name": "Values",
        "questions": [
            "What is your life motto or slogan?",
            "What do you value most in your work?",
            "What is your ideal way of working?",
            "How do you view work-life balance?",
            "What kind of people do you admire most?",
        ],
    },
    "interests_and_hobbies": {
        "name": "Interests and Hobbies",
        "questions": [
            "What do you like to do outside of work?",
            "What books are you reading lately or what topics are you following?",
            "Do you have any special hobbies or skills?",
            "How do you usually spend your weekends?",
        ],
    },
}


class AnswerRequest(BaseModel):
    """Answer request"""

    question_id: str = Field(..., description="Question ID")
    question: str = Field(..., description="Question content")
    answer: str = Field(..., description="Answer content")
    category: str = Field(..., description="Question category")


class Question(BaseModel):
    """Question"""

    id: str
    question: str
    category: str
    category_name: str


class CategoryInfo(BaseModel):
    """Category information"""

    id: str
    name: str
    question_count: int
    answered_count: int


def get_profile_manager():
    """Get user profile manager"""
    from main import get_profile_manager

    pm = get_profile_manager()
    if not pm:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return pm


@router.get("/categories")
async def get_categories() -> List[CategoryInfo]:
    """
    Get all question categories
    """
    pm = get_profile_manager()
    profile = pm.get_profile()

    # Count answered questions for each category
    answered_questions = {}
    if profile and profile.collected_insights:
        for insight in profile.collected_insights:
            cat = insight.get("category", "general")
            answered_questions[cat] = answered_questions.get(cat, 0) + 1

    categories = []
    for cat_id, cat_data in INTERVIEW_QUESTIONS.items():
        categories.append(
            CategoryInfo(
                id=cat_id,
                name=cat_data["name"],
                question_count=len(cat_data["questions"]),
                answered_count=answered_questions.get(cat_id, 0),
            )
        )

    return categories


@router.get("/questions/{category}")
async def get_questions(category: str) -> List[Question]:
    """
    Get question list for specified category

    - **category**: Question category ID
    """
    if category not in INTERVIEW_QUESTIONS:
        raise HTTPException(status_code=404, detail=f"Category not found: {category}")

    cat_data = INTERVIEW_QUESTIONS[category]
    questions = []

    for i, q in enumerate(cat_data["questions"]):
        questions.append(
            Question(
                id=f"{category}_{i}",
                question=q,
                category=category,
                category_name=cat_data["name"],
            )
        )

    return questions


@router.get("/random")
async def get_random_question() -> Question:
    """
    Get a random question
    """
    category = random.choice(list(INTERVIEW_QUESTIONS.keys()))
    cat_data = INTERVIEW_QUESTIONS[category]
    question = random.choice(cat_data["questions"])
    question_index = cat_data["questions"].index(question)

    return Question(
        id=f"{category}_{question_index}",
        question=question,
        category=category,
        category_name=cat_data["name"],
    )


@router.get("/next")
async def get_next_question() -> Question:
    """
    Get the next recommended question (intelligently select unanswered questions)
    """
    pm = get_profile_manager()
    profile = pm.get_profile()

    # Collect answered questions
    answered_questions = set()
    if profile and profile.collected_insights:
        for insight in profile.collected_insights:
            answered_questions.add(insight.get("question", ""))

    # Find unanswered questions
    unanswered = []
    for cat_id, cat_data in INTERVIEW_QUESTIONS.items():
        for i, q in enumerate(cat_data["questions"]):
            if q not in answered_questions:
                unanswered.append(
                    {
                        "id": f"{cat_id}_{i}",
                        "question": q,
                        "category": cat_id,
                        "category_name": cat_data["name"],
                    }
                )

    if not unanswered:
        # All questions answered, return random question
        return await get_random_question()

    # Randomly select an unanswered question
    selected = random.choice(unanswered)
    return Question(**selected)


@router.post("/answer")
async def submit_answer(request: AnswerRequest):
    """
    Submit answer to question

    - **question_id**: Question ID
    - **question**: Question content
    - **answer**: Answer content
    - **category**: Question category
    """
    if not request.answer.strip():
        raise HTTPException(status_code=400, detail="Answer cannot be empty")

    pm = get_profile_manager()

    await pm.add_insight(
        question=request.question, answer=request.answer, category=request.category
    )

    return {
        "status": "success",
        "message": "Answer saved",
        "question_id": request.question_id,
    }


@router.get("/progress")
async def get_progress():
    """
    Get Q&A progress
    """
    pm = get_profile_manager()
    profile = pm.get_profile()

    total_questions = sum(len(cat["questions"]) for cat in INTERVIEW_QUESTIONS.values())

    answered_count = 0
    if profile and profile.collected_insights:
        answered_count = len(profile.collected_insights)

    return {
        "total_questions": total_questions,
        "answered_count": answered_count,
        "progress_percent": round(answered_count / total_questions * 100, 1)
        if total_questions > 0
        else 0,
    }


@router.get("/insights")
async def get_all_insights():
    """
    Get all collected insights
    """
    pm = get_profile_manager()
    profile = pm.get_profile()

    if not profile or not profile.collected_insights:
        return {"insights": [], "count": 0}

    return {
        "insights": profile.collected_insights,
        "count": len(profile.collected_insights),
    }
