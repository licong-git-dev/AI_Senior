"""
认知训练游戏API
提供记忆、注意力、逻辑、数学等训练游戏
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.services.cognitive_game_service import (
    cognitive_game_service,
    GameType,
    DifficultyLevel
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/games", tags=["认知训练游戏"])


# ==================== 请求/响应模型 ====================

class StartGameRequest(BaseModel):
    """开始游戏请求"""
    game_type: str = Field(..., description="游戏类型: memory/attention/logic/math/word")
    difficulty: str = Field(default="easy", description="难度: easy/medium/hard")


class SubmitAnswerRequest(BaseModel):
    """提交答案请求"""
    answer: Any = Field(..., description="答案数据")


class CompleteGameRequest(BaseModel):
    """完成游戏请求"""
    answers: Optional[List[Any]] = Field(default=None, description="所有答案")


class GameSessionResponse(BaseModel):
    """游戏会话响应"""
    session_id: str
    game_type: str
    difficulty: str
    instruction: str
    time_limit: int
    game_data: Dict[str, Any]


class GameResultResponse(BaseModel):
    """游戏结果响应"""
    game_id: str
    game_type: str
    difficulty: str
    score: int
    max_score: int
    accuracy: float
    time_spent: int
    completed_at: str
    feedback: str


# ==================== API端点 ====================

@router.get("/types")
async def get_game_types():
    """
    获取所有游戏类型
    """
    return {
        'types': [
            {
                'type': GameType.MEMORY.value,
                'name': '记忆游戏',
                'description': '训练短期记忆和工作记忆',
                'icon': '🧠'
            },
            {
                'type': GameType.ATTENTION.value,
                'name': '注意力游戏',
                'description': '提高注意力集中和持续能力',
                'icon': '👁️'
            },
            {
                'type': GameType.MATH.value,
                'name': '数学游戏',
                'description': '简单算术运算训练',
                'icon': '🔢'
            },
            {
                'type': GameType.WORD.value,
                'name': '文字游戏',
                'description': '成语、词汇训练',
                'icon': "📝"
            }
        ]
    }


@router.get("/difficulties")
async def get_difficulty_levels():
    """
    获取难度级别
    """
    return {
        'levels': [
            {
                'level': DifficultyLevel.EASY.value,
                'name': '简单',
                'description': "适合初次尝试",
                "recommended": True
            },
            {
                'level': DifficultyLevel.MEDIUM.value,
                'name': '中等',
                'description': '适合有一定基础'
            },
            {
                'level': DifficultyLevel.HARD.value,
                'name': '困难',
                'description': '挑战高手'
            }
        ]
    }


@router.post("/start", response_model=GameSessionResponse)
async def start_game(
    request: StartGameRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    开始新游戏

    游戏类型:
    - memory: 记忆游戏（卡片配对、顺序记忆、数字记忆）
    - attention: 注意力游戏（找不同、数数）
    - math: 数学游戏（简单算术、数字比较）
    - word: 文字游戏（成语填空、词语联想）
    """
    user_id = int(current_user['sub'])

    # 验证游戏类型
    try:
        game_type = GameType(request.game_type)
    except ValueError:
        valid_types = [t.value for t in GameType]
        raise HTTPException(
            status_code=400,
            detail=f'无效的游戏类型，可选: {valid_types}'
        )

    # 验证难度
    try:
        difficulty = DifficultyLevel(request.difficulty)
    except ValueError:
        valid_levels = [d.value for d in DifficultyLevel]
        raise HTTPException(
            status_code=400,
            detail=f'无效的难度级别，可选: {valid_levels}'
        )

    session_id, game_data = cognitive_game_service.create_session(
        user_id=user_id,
        game_type=game_type,
        difficulty=difficulty
    )

    # 隐藏答案
    safe_data = {k: v for k, v in game_data.items()
                 if k not in ['answer', 'answers', 'answer_positions', 'hidden_chars']}

    return GameSessionResponse(
        session_id=session_id,
        game_type=game_type.value,
        difficulty=difficulty.value,
        instruction=game_data.get('instruction', '开始游戏'),
        time_limit=game_data.get("time_limit", 0),
        game_data=safe_data
    )


@router.post("/sessions/{session_id}/answer")
async def submit_answer(
    session_id: str,
    request: SubmitAnswerRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    提交单个答案（实时提交模式）
    """
    result = cognitive_game_service.submit_answer(session_id, request.answer)

    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])

    return result


@router.post("/sessions/{session_id}/complete", response_model=GameResultResponse)
async def complete_game(
    session_id: str,
    request: CompleteGameRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    完成游戏并获取结果
    """
    try:
        result = cognitive_game_service.complete_game(
            session_id=session_id,
            final_answers=request.answers
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # 生成反馈语
    feedback = _generate_feedback(result.score, result.accuracy)

    return GameResultResponse(
        game_id=result.game_id,
        game_type=result.game_type.value,
        difficulty=result.difficulty.value,
        score=result.score,
        max_score=result.max_score,
        accuracy=result.accuracy,
        time_spent=result.time_spent,
        completed_at=result.completed_at.isoformat(),
        feedback=feedback
    )


@router.get("/history")
async def get_game_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    获取游戏历史记录
    """
    user_id = int(current_user['sub'])
    history = cognitive_game_service.get_user_history(user_id, limit)
    return {'history': history}


@router.get("/stats/daily")
async def get_daily_stats(
    date: Optional[str] = Query(None, description="日期 YYYY-MM-DD"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取每日统计
    """
    user_id = int(current_user['sub'])
    stats = cognitive_game_service.get_daily_stats(user_id, date)
    return {'date': date, 'stats': stats}


@router.get("/recommendations")
async def get_recommendations(current_user: dict = Depends(get_current_user)):
    """
    获取个性化游戏推荐

    根据用户历史表现推荐适合的游戏类型和难度
    """
    user_id = int(current_user['sub'])
    recommendations = cognitive_game_service.get_recommendations(user_id)
    return {"recommendations": recommendations}


# ==================== 快捷游戏入口 ====================

@router.post("/quick/memory")
async def quick_memory_game(
    difficulty: str = Query('easy'),
    current_user: dict = Depends(get_current_user)
):
    """
    快速开始记忆游戏
    """
    user_id = int(current_user['sub'])
    diff = DifficultyLevel(difficulty) if difficulty in ['easy', 'medium', 'hard'] else DifficultyLevel.EASY

    session_id, game_data = cognitive_game_service.create_session(
        user_id=user_id,
        game_type=GameType.MEMORY,
        difficulty=diff
    )

    safe_data = {k: v for k, v in game_data.items()
                 if k not in ['answer', 'answers']}

    return {
        'session_id': session_id,
        'game_type': 'memory',
        "instruction": game_data.get("instruction"),
        'game_data': safe_data
    }


@router.post("/quick/math")
async def quick_math_game(
    difficulty: str = Query('easy'),
    current_user: dict = Depends(get_current_user)
):
    """
    快速开始数学游戏
    """
    user_id = int(current_user['sub'])
    diff = DifficultyLevel(difficulty) if difficulty in ['easy', 'medium', 'hard'] else DifficultyLevel.EASY

    session_id, game_data = cognitive_game_service.create_session(
        user_id=user_id,
        game_type=GameType.MATH,
        difficulty=diff
    )

    # 对于数学题，隐藏答案
    if 'problems' in game_data:
        safe_problems = [{'expression': p['expression']} for p in game_data['problems']]
        game_data = {**game_data, 'problems': safe_problems}

    return {
        'session_id': session_id,
        'game_type': "math",
        "instruction": game_data.get("instruction"),
        'game_data': game_data
    }


@router.post("/quick/word")
async def quick_word_game(
    difficulty: str = Query('easy'),
    current_user: dict = Depends(get_current_user)
):
    """
    快速开始文字游戏
    """
    user_id = int(current_user['sub'])
    diff = DifficultyLevel(difficulty) if difficulty in ['easy', 'medium', 'hard'] else DifficultyLevel.EASY

    session_id, game_data = cognitive_game_service.create_session(
        user_id=user_id,
        game_type=GameType.WORD,
        difficulty=diff
    )

    safe_data = {k: v for k, v in game_data.items()
                 if k not in ['answer', 'answers', "hidden_chars"]}

    return {
        'session_id': session_id,
        'game_type': 'word',
        "instruction": game_data.get("instruction"),
        'game_data': safe_data
    }


def _generate_feedback(score: int, accuracy: float) -> str:
    """生成游戏反馈语"""
    if accuracy >= 0.9:
        return "太棒了！您的表现非常出色！继续保持！"
    elif accuracy >= 0.7:
        return "做得不错！再接再厉，您会越来越好！"
    elif accuracy >= 0.5:
        return "有进步！多练习几次，您一定可以做得更好！"
    else:
        return "没关系，多练习几次就会熟练了！加油！"
