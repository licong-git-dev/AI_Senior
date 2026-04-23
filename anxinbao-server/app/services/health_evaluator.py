"""
健康风险评估服务
负责判断是否需要通知子女
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from app.core.config import get_settings
from app.core.cache import cache_store

import json
import logging

logger = logging.getLogger(__name__)


class HealthRiskEvaluator:
    """健康风险评估器"""

    URGENT_KEYWORDS = [
        "胸痛", "胸口痛", "心口痛", "心脏痛",
        "胸闷", "喘不上气", "呼吸困难", "透不过气",
        "意识模糊", "说不清话", "嘴歪", "手脚麻木",
        "剧烈头痛", "头痛欲裂",
        "晕倒", "昏倒", "摔倒", "跌倒",
        "吐血", "便血", "大量出血"
    ]

    CONCERN_KEYWORDS = [
        "头晕", "头疼", "头痛",
        "恶心", "想吐", "呕吐",
        "肚子疼", "胃疼", "胃痛",
        "腰疼", "腰痛", "背痛",
        "腿疼", "腿痛", "关节痛",
        "睡不着", "失眠", "没精神",
        "没胃口", "吃不下", "便秘",
        "咳嗽", "嗓子疼", "发烧"
    ]

    def __init__(self):
        settings = get_settings()
        self.threshold = settings.health_risk_threshold
        # 内存缓存，作为Redis不可用时的回退
        self._memory_history: Dict[str, List[Dict]] = defaultdict(list)

    async def _get_symptom_history(self, user_id: str) -> List[Dict]:
        """从缓存获取症状历史"""
        cached = await cache_store.get(f"symptom_history:{user_id}")
        if cached is not None:
            return cached
        return self._memory_history.get(user_id, [])

    async def _save_symptom_history(self, user_id: str, history: List[Dict]):
        """保存症状历史到缓存"""
        self._memory_history[user_id] = history
        await cache_store.set(
            f"symptom_history:{user_id}",
            history,
            expire=86400 * 30  # 30天过期
        )

    def evaluate(self, user_id: str, message: str, ai_risk_info: Dict) -> Dict:
        """同步评估接口（保持向后兼容）"""
        base_score = ai_risk_info.get("risk_score", 1)
        category = ai_risk_info.get("category", "chat")
        keyword_score = self._check_keywords(message)
        history_score = self._analyze_history_sync(user_id, message, category)
        final_score = max(base_score, keyword_score, history_score)
        need_notify = final_score >= self.threshold

        result = {
            "risk_score": final_score,
            "base_score": base_score,
            "keyword_score": keyword_score,
            "history_score": history_score,
            "need_notify": need_notify,
            "category": category,
            "reason": self._generate_reason(final_score, keyword_score, history_score),
            "suggestion": self._generate_suggestion(final_score),
            "timestamp": datetime.now().isoformat()
        }

        if category == "health":
            self._record_symptom_sync(user_id, message, final_score)

        return result

    def _check_keywords(self, message: str) -> int:
        """关键词风险评分"""
        for keyword in self.URGENT_KEYWORDS:
            if keyword in message:
                return 8
        concern_count = sum(1 for kw in self.CONCERN_KEYWORDS if kw in message)
        if concern_count >= 3:
            return 6
        elif concern_count >= 1:
            return 4
        return 1

    def _analyze_history_sync(self, user_id: str, message: str, category: str) -> int:
        """分析历史症状（同步版本，使用内存缓存）"""
        if category != "health":
            return 1
        history = self._memory_history.get(user_id, [])
        if not history:
            return 1
        three_days_ago = datetime.now() - timedelta(days=3)
        recent = [h for h in history if datetime.fromisoformat(h["timestamp"]) > three_days_ago]
        if len(recent) >= 3:
            return 7
        elif len(recent) >= 2:
            return 5
        return 1

    def _record_symptom_sync(self, user_id: str, message: str, score: int):
        """记录症状（同步版本）"""
        self._memory_history[user_id].append({
            "message": message,
            "score": score,
            "timestamp": datetime.now().isoformat()
        })
        # 只保留30天内的记录
        thirty_days_ago = datetime.now() - timedelta(days=30)
        self._memory_history[user_id] = [
            h for h in self._memory_history[user_id]
            if datetime.fromisoformat(h["timestamp"]) > thirty_days_ago
        ]

    def _generate_reason(self, final: int, keyword: int, history: int) -> str:
        """根据评分生成风险原因描述"""
        reasons = []
        if keyword >= 8:
            reasons.append("检测到紧急症状关键词")
        elif keyword >= 4:
            reasons.append("提到身体不适症状")
        if history >= 7:
            reasons.append("连续多天反映身体问题")
        elif history >= 5:
            reasons.append("近期有类似症状记录")
        if final >= 7 and not reasons:
            reasons.append("AI评估认为需要关注")
        return "；".join(reasons) if reasons else "日常对话"

    def _generate_suggestion(self, score: int) -> str:
        """根据风险评分生成健康建议"""
        if score >= 9:
            return "建议立即联系家人，必要时拨打120"
        elif score >= 7:
            return "建议让家人带您去医院检查一下"
        elif score >= 5:
            return "注意休息，可以试试食疗调理"
        return "保持心情愉快，注意作息规律"

    def get_user_health_summary(self, user_id: str) -> Dict:
        """获取用户健康摘要（给子女看）"""
        history = self._memory_history.get(user_id, [])
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent = [h for h in history if datetime.fromisoformat(h["timestamp"]) > seven_days_ago]

        if not recent:
            return {
                "user_id": user_id,
                "recent_symptoms": [],
                "risk_level": "low",
                "last_high_risk_time": None,
                "recommendations": ["保持健康作息", "适当运动", "多喝水"]
            }

        symptoms = []
        for h in recent:
            for kw in self.CONCERN_KEYWORDS + self.URGENT_KEYWORDS:
                if kw in h["message"] and kw not in symptoms:
                    symptoms.append(kw)

        max_score = max(h["score"] for h in recent)
        avg_score = sum(h["score"] for h in recent) / len(recent)

        if max_score >= 7 or avg_score >= 6:
            risk_level = "high"
            recommendations = ["建议尽快就医检查", "保持与家人联系", "注意休息"]
        elif max_score >= 5 or avg_score >= 4:
            risk_level = "medium"
            recommendations = ["注意观察身体状况", "适当休息", "清淡饮食"]
        else:
            risk_level = "low"
            recommendations = ["保持良好心态", "规律作息", "适当运动"]

        high_risk = [h for h in recent if h["score"] >= 7]
        last_high_risk_time = max(h["timestamp"] for h in high_risk) if high_risk else None

        return {
            "user_id": user_id,
            "recent_symptoms": symptoms[:5],
            "risk_level": risk_level,
            "last_high_risk_time": last_high_risk_time,
            "recommendations": recommendations
        }


risk_evaluator = HealthRiskEvaluator()
