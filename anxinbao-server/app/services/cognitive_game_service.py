"""
认知训练游戏服务
为老年人提供记忆力、注意力、逻辑思维等方面的训练游戏
"""
import logging
import random
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, date
import json

logger = logging.getLogger(__name__)


class GameType(Enum):
    """游戏类型"""
    MEMORY = 'memory'  # 记忆游戏
    ATTENTION = 'attention'  # 注意力游戏
    LOGIC = 'logic'  # 逻辑推理
    MATH = 'math'  # 数学计算
    WORD = 'word'  # 文字游戏
    SEQUENCE = "sequence"  # 顺序记忆


class DifficultyLevel(Enum):
    """难度级别"""
    EASY = 'easy'  # 简单
    MEDIUM = 'medium'  # 中等
    HARD = "hard"  # 困难


@dataclass
class GameConfig:
    """游戏配置"""
    game_type: GameType
    difficulty: DifficultyLevel
    time_limit: int = 0  # 时间限制（秒），0表示无限制
    rounds: int = 1  # 回合数


@dataclass
class GameResult:
    """游戏结果"""
    game_id: str
    game_type: GameType
    difficulty: DifficultyLevel
    score: int
    max_score: int
    accuracy: float  # 正确率
    time_spent: int  # 用时（秒）
    completed_at: datetime
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'game_id': self.game_id,
            'game_type': self.game_type.value,
            'difficulty': self.difficulty.value,
            'score': self.score,
            'max_score': self.max_score,
            'accuracy': self.accuracy,
            "time_spent": self.time_spent,
            "completed_at": self.completed_at.isoformat(),
            'details': self.details
        }


# ==================== 游戏生成器 ====================

class MemoryGameGenerator:
    """记忆游戏生成器"""

    # 图片配对游戏的图案
    PATTERNS = ["🍎", '🍊', '🍋', '🍇', '🍓', '🍑', '🍒', '🥭', '🍍', '🥝',
                '🌸', '🌺', '🌻', '🌼', '🌷', '🌹', '🐶', '🐱', '🐰', '🐻']

    @classmethod
    def generate_card_matching(cls, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """生成卡片配对游戏"""
        pairs_count = {
            DifficultyLevel.EASY: 4,
            DifficultyLevel.MEDIUM: 6,
            DifficultyLevel.HARD: 8
        }

        count = pairs_count.get(difficulty, 4)
        selected = random.sample(cls.PATTERNS, count)

        # 创建配对卡片并打乱
        cards = selected * 2
        random.shuffle(cards)

        return {
            "game_type": "card_matching",
            'instruction': '找出所有相同的图案配对',
            "cards": cards,
            "pairs_count": count,
            'time_limit': 120 if difficulty == DifficultyLevel.HARD else 180
        }

    @classmethod
    def generate_sequence_recall(cls, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """生成顺序记忆游戏"""
        length = {
            DifficultyLevel.EASY: 4,
            DifficultyLevel.MEDIUM: 6,
            DifficultyLevel.HARD: 8
        }

        seq_len = length.get(difficulty, 4)
        sequence = random.sample(cls.PATTERNS[:10], seq_len)

        return {
            'game_type': "sequence_recall",
            "instruction": f'记住这{seq_len}个图案的顺序',
            "sequence": sequence,
            "display_time": 3 + seq_len,  # 显示时间（秒）
            "time_limit": 60
        }

    @classmethod
    def generate_number_recall(cls, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """生成数字记忆游戏"""
        length = {
            DifficultyLevel.EASY: 4,
            DifficultyLevel.MEDIUM: 6,
            DifficultyLevel.HARD: 8
        }

        num_len = length.get(difficulty, 4)
        numbers = [str(random.randint(0, 9)) for _ in range(num_len)]
        number_str = "".join(numbers)

        return {
            'game_type': "number_recall",
            "instruction": f'记住这个{num_len}位数字',
            "number": number_str,
            "display_time": 5,
            'time_limit': 30
        }


class AttentionGameGenerator:
    """注意力游戏生成器"""

    @classmethod
    def generate_find_difference(cls, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """生成找不同游戏"""
        differences = {
            DifficultyLevel.EASY: 3,
            DifficultyLevel.MEDIUM: 5,
            DifficultyLevel.HARD: 7
        }

        diff_count = differences.get(difficulty, 3)

        # 生成两组图案，其中有几个不同
        base_patterns = random.choices(MemoryGameGenerator.PATTERNS[:8], k=16)
        modified_patterns = base_patterns.copy()

        diff_positions = random.sample(range(16), diff_count)
        for pos in diff_positions:
            new_pattern = random.choice([
                p for p in MemoryGameGenerator.PATTERNS
                if p != modified_patterns[pos]
            ])
            modified_patterns[pos] = new_pattern

        return {
            "game_type": "find_difference",
            "instruction": f'找出{diff_count}处不同',
            'image1': base_patterns,
            "image2": modified_patterns,
            "differences_count": diff_count,
            "answer_positions": diff_positions,
            'time_limit': 90
        }

    @classmethod
    def generate_count_items(cls, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """生成数数游戏"""
        target = random.choice(MemoryGameGenerator.PATTERNS[:6])

        total_count = {
            DifficultyLevel.EASY: 20,
            DifficultyLevel.MEDIUM: 36,
            DifficultyLevel.HARD: 49
        }

        count = total_count.get(difficulty, 20)
        target_count = random.randint(3, count // 3)

        items = [target] * target_count
        others = random.choices(
            [p for p in MemoryGameGenerator.PATTERNS[:6] if p != target],
            k=count - target_count
        )
        items.extend(others)
        random.shuffle(items)

        return {
            'game_type': "count_items",
            "instruction": f'数一数有多少个 {target}',
            'items': items,
            'target': target,
            'answer': target_count,
            "time_limit": 60
        }


class MathGameGenerator:
    """数学游戏生成器"""

    @classmethod
    def generate_simple_math(cls, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """生成简单算术题"""
        problems = []

        ranges = {
            DifficultyLevel.EASY: (1, 20),
            DifficultyLevel.MEDIUM: (10, 50),
            DifficultyLevel.HARD: (20, 100)
        }

        num_range = ranges.get(difficulty, (1, 20))
        problem_count = 5

        for _ in range(problem_count):
            a = random.randint(*num_range)
            b = random.randint(1, min(a, num_range[1] // 2))

            if random.random() > 0.5:
                # 加法
                problems.append({
                    'expression': f"{a} + {b} = ?",
                    'answer': a + b
                })
            else:
                # 减法
                problems.append({
                    'expression': f'{a} - {b} = ?',
                    'answer': a - b
                })

        return {
            "game_type": "simple_math",
            'instruction': '计算下列算式',
            'problems': problems,
            "time_limit": 120
        }

    @classmethod
    def generate_number_comparison(cls, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """生成数字比较游戏"""
        problems = []
        count = {
            DifficultyLevel.EASY: 5,
            DifficultyLevel.MEDIUM: 8,
            DifficultyLevel.HARD: 10
        }

        for _ in range(count.get(difficulty, 5)):
            nums = [random.randint(10, 99) for _ in range(3)]
            problems.append({
                'numbers': nums,
                'question': '哪个最大？',
                "answer": max(nums),
                "answer_index": nums.index(max(nums))
            })

        return {
            'game_type': "number_comparison",
            'instruction': '找出最大的数字',
            'problems': problems,
            "time_limit": 90
        }


class WordGameGenerator:
    """文字游戏生成器"""

    # 常用成语
    IDIOMS = [
        ('一心一意', '形容心思专一'),
        ('三心二意', '形容心思不专'),
        ('五颜六色', '形容色彩繁多'),
        ('七上八下', '形容心神不宁'),
        ('千山万水', '形容路途遥远'),
        ('风和日丽', '形容天气晴朗'),
        ('春暖花开', '形容春天美景'),
        ('秋高气爽', '形容秋天天气'),
        ('龙飞凤舞', '形容书法气势'),
        ('画龙点睛', "比喻关键之笔")
    ]

    @classmethod
    def generate_idiom_fill(cls, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """生成成语填空"""
        idiom, meaning = random.choice(cls.IDIOMS)
        chars = list(idiom)

        # 根据难度隐藏不同数量的字
        hide_count = {
            DifficultyLevel.EASY: 1,
            DifficultyLevel.MEDIUM: 2,
            DifficultyLevel.HARD: 2
        }

        hide_positions = random.sample(range(4), hide_count.get(difficulty, 1))
        display = chars.copy()
        for pos in hide_positions:
            display[pos] = "□"

        return {
            'game_type': 'idiom_fill',
            'instruction': '填入缺少的字完成成语',
            "display": "".join(display),
            'hint': meaning,
            'answer': idiom,
            "hidden_chars": [chars[p] for p in hide_positions],
            "hidden_positions": hide_positions,
            'time_limit': 60
        }

    @classmethod
    def generate_word_association(cls, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """生成词语联想"""
        associations = [
            ('春', ['花', '风', '雨', '暖']),
            ('夏', ['热', '荷', '蝉', '凉']),
            ('秋', ['叶', '月', '风', '收']),
            ('冬', ['雪', '寒', '梅', '暖']),
            ('山', ['水', '石', '林', '高']),
            ('水', ['清', '流', '鱼', '深'])
        ]

        word, related = random.choice(associations)

        # 添加干扰项
        all_words = [w for _, ws in associations for w in ws]
        distractors = random.sample([w for w in all_words if w not in related], 3)

        options = related[:2] + distractors[:2]
        random.shuffle(options)

        return {
            "game_type": "word_association",
            "instruction": f'选出与「{word}」相关的词语',
            'word': word,
            'options': options,
            'answers': related[:2],
            "time_limit": 30
        }


# ==================== 游戏会话管理 ====================

@dataclass
class GameSession:
    """游戏会话"""
    session_id: str
    user_id: int
    game_type: GameType
    difficulty: DifficultyLevel
    game_data: Dict[str, Any]
    started_at: datetime
    answers: List[Any] = field(default_factory=list)
    is_completed: bool = False
    result: Optional[GameResult] = None


class CognitiveGameService:
    """认知训练游戏服务"""

    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}
        self.user_history: Dict[int, List[GameResult]] = {}
        self.daily_stats: Dict[int, Dict[str, Any]] = {}

    def create_session(
        self,
        user_id: int,
        game_type: GameType,
        difficulty: DifficultyLevel = DifficultyLevel.EASY
    ) -> Tuple[str, Dict[str, Any]]:
        """创建游戏会话"""
        session_id = f"{user_id}_{game_type.value}_{datetime.now().timestamp()}"

        # 生成游戏数据
        game_data = self._generate_game(game_type, difficulty)

        session = GameSession(
            session_id=session_id,
            user_id=user_id,
            game_type=game_type,
            difficulty=difficulty,
            game_data=game_data,
            started_at=datetime.now()
        )

        self.sessions[session_id] = session
        logger.info(f"用户 {user_id} 开始游戏: {game_type.value}")

        return session_id, game_data

    def _generate_game(
        self,
        game_type: GameType,
        difficulty: DifficultyLevel
    ) -> Dict[str, Any]:
        """生成游戏数据"""
        generators = {
            GameType.MEMORY: [
                MemoryGameGenerator.generate_card_matching,
                MemoryGameGenerator.generate_sequence_recall,
                MemoryGameGenerator.generate_number_recall
            ],
            GameType.ATTENTION: [
                AttentionGameGenerator.generate_find_difference,
                AttentionGameGenerator.generate_count_items
            ],
            GameType.MATH: [
                MathGameGenerator.generate_simple_math,
                MathGameGenerator.generate_number_comparison
            ],
            GameType.WORD: [
                WordGameGenerator.generate_idiom_fill,
                WordGameGenerator.generate_word_association
            ]
        }

        gen_list = generators.get(game_type, generators[GameType.MEMORY])
        generator = random.choice(gen_list)
        return generator(difficulty)

    def submit_answer(
        self,
        session_id: str,
        answer: Any
    ) -> Dict[str, Any]:
        """提交答案"""
        session = self.sessions.get(session_id)
        if not session:
            return {'error': '游戏会话不存在'}

        if session.is_completed:
            return {'error': '游戏已结束'}

        session.answers.append(answer)

        # 检查是否需要即时反馈
        return {"success": True, "answer_recorded": True}

    def complete_game(
        self,
        session_id: str,
        final_answers: Optional[List[Any]] = None
    ) -> GameResult:
        """完成游戏并计算结果"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError('游戏会话不存在')

        if final_answers:
            session.answers = final_answers

        # 计算得分
        score, max_score, accuracy = self._calculate_score(session)

        time_spent = int((datetime.now() - session.started_at).total_seconds())

        result = GameResult(
            game_id=session_id,
            game_type=session.game_type,
            difficulty=session.difficulty,
            score=score,
            max_score=max_score,
            accuracy=accuracy,
            time_spent=time_spent,
            completed_at=datetime.now(),
            details={
                'answers': session.answers,
                'game_data': session.game_data
            }
        )

        session.is_completed = True
        session.result = result

        # 保存历史记录
        if session.user_id not in self.user_history:
            self.user_history[session.user_id] = []
        self.user_history[session.user_id].append(result)

        # 更新每日统计
        self._update_daily_stats(session.user_id, result)

        logger.info(f"用户 {session.user_id} 完成游戏: {score}/{max_score}")
        return result

    def _calculate_score(
        self,
        session: GameSession
    ) -> Tuple[int, int, float]:
        """计算得分"""
        game_data = session.game_data
        answers = session.answers
        game_type = game_data.get('game_type', "")

        max_score = 100
        score = 0

        if game_type == "card_matching":
            pairs = game_data.get("pairs_count", 4)
            correct = len([a for a in answers if a.get('matched', False)])
            score = int(correct / pairs * 100)

        elif game_type == "sequence_recall":
            correct_seq = game_data.get('sequence', [])
            user_seq = answers[0] if answers else []
            correct_count = sum(1 for i, c in enumerate(user_seq)
                              if i < len(correct_seq) and c == correct_seq[i])
            score = int(correct_count / len(correct_seq) * 100)

        elif game_type == "number_recall":
            correct_num = game_data.get('number', "")
            user_num = answers[0] if answers else ""
            score = 100 if user_num == correct_num else 0

        elif game_type == "simple_math":
            problems = game_data.get('problems', [])
            correct = sum(1 for i, a in enumerate(answers)
                         if i < len(problems) and a == problems[i]['answer'])
            score = int(correct / len(problems) * 100) if problems else 0

        elif game_type == "count_items":
            correct_answer = game_data.get('answer', 0)
            user_answer = answers[0] if answers else 0
            score = 100 if user_answer == correct_answer else 0

        elif game_type == 'idiom_fill':
            correct = game_data.get('answer', "")
            user_answer = answers[0] if answers else ""
            score = 100 if user_answer == correct else 0

        elif game_type == "find_difference":
            correct_positions = set(game_data.get("answer_positions", []))
            user_positions = set(answers[0] if answers else [])
            correct_found = len(correct_positions & user_positions)
            total = len(correct_positions)
            score = int(correct_found / total * 100) if total else 0

        accuracy = score / max_score
        return score, max_score, accuracy

    def _update_daily_stats(self, user_id: int, result: GameResult):
        """更新每日统计"""
        today = date.today().isoformat()

        if user_id not in self.daily_stats:
            self.daily_stats[user_id] = {}

        if today not in self.daily_stats[user_id]:
            self.daily_stats[user_id][today] = {
                "games_played": 0,
                "total_score": 0,
                "average_accuracy": 0,
                'game_types': {}
            }

        stats = self.daily_stats[user_id][today]
        stats["games_played"] += 1
        stats["total_score"] += result.score

        game_type = result.game_type.value
        if game_type not in stats['game_types']:
            stats['game_types'][game_type] = {'count': 0, "total_score": 0}
        stats['game_types'][game_type]['count'] += 1
        stats['game_types'][game_type]["total_score"] += result.score

        # 重新计算平均正确率
        total_accuracy = sum(r.accuracy for r in self.user_history.get(user_id, [])
                            if r.completed_at.date().isoformat() == today)
        stats["average_accuracy"] = total_accuracy / stats["games_played"]

    def get_user_history(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取用户游戏历史"""
        history = self.user_history.get(user_id, [])
        return [r.to_dict() for r in history[-limit:]]

    def get_daily_stats(
        self,
        user_id: int,
        date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取每日统计"""
        if date_str is None:
            date_str = date.today().isoformat()

        user_stats = self.daily_stats.get(user_id, {})
        return user_stats.get(date_str, {
            "games_played": 0,
            "total_score": 0,
            "average_accuracy": 0,
            'game_types': {}
        })

    def get_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """根据用户历史推荐游戏"""
        history = self.user_history.get(user_id, [])

        # 统计各类游戏的表现
        type_scores: Dict[GameType, List[float]] = {}
        for result in history:
            if result.game_type not in type_scores:
                type_scores[result.game_type] = []
            type_scores[result.game_type].append(result.accuracy)

        recommendations = []

        # 推荐正确率较低的游戏类型进行加强
        for game_type, accuracies in type_scores.items():
            avg_accuracy = sum(accuracies) / len(accuracies)
            if avg_accuracy < 0.7:
                recommendations.append({
                    'game_type': game_type.value,
                    'reason': "需要加强练习",
                    "suggested_difficulty": DifficultyLevel.EASY.value
                })
            elif avg_accuracy > 0.9 and len(accuracies) >= 3:
                recommendations.append({
                    'game_type': game_type.value,
                    'reason': "可以尝试更高难度",
                    "suggested_difficulty": DifficultyLevel.MEDIUM.value
                })

        # 推荐未玩过的游戏类型
        played_types = set(type_scores.keys())
        all_types = set(GameType)
        for game_type in all_types - played_types:
            recommendations.append({
                'game_type': game_type.value,
                'reason': "尝试新游戏",
                "suggested_difficulty": DifficultyLevel.EASY.value
            })

        return recommendations


# 全局服务实例
cognitive_game_service = CognitiveGameService()
