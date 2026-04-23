"""
"今日爸妈"子女安心日报服务
核心卖点实现 — 让子女一目了然"爸妈今天过得怎么样"

每日生成一份简报推送给子女，包含：
- 今日情绪状态（开心/平静/低落/焦虑）
- 关键对话摘要（今天聊了什么）
- 健康数据（血压/心率/血糖/用药情况）
- 活动记录（运动/社交/外出）
- 安心指数（综合评分1-10）
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

@dataclass
class EmotionSummary:
    """情绪摘要"""
    dominant_emotion: str = "平静"  # 开心/平静/低落/焦虑/孤独
    emotion_score: int = 7  # 1-10, 10最积极
    emotion_changes: List[str] = field(default_factory=list)  # 情绪变化轨迹
    highlights: List[str] = field(default_factory=list)  # 情绪亮点

    def to_dict(self) -> Dict:
        return {
            "dominant_emotion": self.dominant_emotion,
            "emotion_score": self.emotion_score,
            "emotion_changes": self.emotion_changes,
            "highlights": self.highlights,
        }


@dataclass
class ConversationSummary:
    """对话摘要"""
    total_conversations: int = 0  # 今日对话次数
    total_messages: int = 0  # 今日消息条数
    topics: List[str] = field(default_factory=list)  # 聊天话题
    key_quotes: List[str] = field(default_factory=list)  # 关键引用（脱敏）
    first_chat_time: Optional[str] = None  # 首次对话时间
    last_chat_time: Optional[str] = None  # 最后对话时间

    def to_dict(self) -> Dict:
        return {
            "total_conversations": self.total_conversations,
            "total_messages": self.total_messages,
            "topics": self.topics,
            "key_quotes": self.key_quotes,
            "first_chat_time": self.first_chat_time,
            "last_chat_time": self.last_chat_time,
        }


@dataclass
class HealthSummary:
    """健康摘要"""
    blood_pressure: Optional[str] = None  # "135/85 正常"
    heart_rate: Optional[str] = None  # "72 正常"
    blood_glucose: Optional[str] = None
    blood_oxygen: Optional[str] = None
    medication_taken: bool = True  # 是否按时服药
    medication_details: List[str] = field(default_factory=list)  # 用药详情
    health_alerts: List[str] = field(default_factory=list)  # 健康告警
    overall_status: str = "正常"  # 正常/注意/告警

    def to_dict(self) -> Dict:
        return {
            "blood_pressure": self.blood_pressure,
            "heart_rate": self.heart_rate,
            "blood_glucose": self.blood_glucose,
            "blood_oxygen": self.blood_oxygen,
            "medication_taken": self.medication_taken,
            "medication_details": self.medication_details,
            "health_alerts": self.health_alerts,
            "overall_status": self.overall_status,
        }


@dataclass
class ActivitySummary:
    """活动摘要"""
    steps: Optional[int] = None  # 步数
    exercise_minutes: int = 0  # 运动时长
    social_interactions: List[str] = field(default_factory=list)  # 社交活动
    outdoor_time: int = 0  # 外出时长（分钟）
    sleep_time: Optional[str] = None  # 入睡时间
    wake_time: Optional[str] = None  # 起床时间

    def to_dict(self) -> Dict:
        return {
            "steps": self.steps,
            "exercise_minutes": self.exercise_minutes,
            "social_interactions": self.social_interactions,
            "outdoor_time": self.outdoor_time,
            "sleep_time": self.sleep_time,
            "wake_time": self.wake_time,
        }


@dataclass
class DailyReport:
    """每日安心日报"""
    user_id: int
    user_name: str
    report_date: str  # YYYY-MM-DD
    anxin_score: int  # 安心指数 1-10
    anxin_level: str  # 很安心/比较安心/需关注/需立即关注
    one_line_summary: str  # 一句话总结
    emotion: EmotionSummary = field(default_factory=EmotionSummary)
    conversation: ConversationSummary = field(default_factory=ConversationSummary)
    health: HealthSummary = field(default_factory=HealthSummary)
    activity: ActivitySummary = field(default_factory=ActivitySummary)
    tips_for_children: List[str] = field(default_factory=list)  # 给子女的建议

    def to_dict(self) -> Dict:
        share_tags = [
            f"安心指数{self.anxin_score}",
            self.anxin_level,
            self.emotion.dominant_emotion,
            self.health.overall_status,
        ]
        topic_tags = self.conversation.topics[:2]
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "report_date": self.report_date,
            "anxin_score": self.anxin_score,
            "anxin_level": self.anxin_level,
            "one_line_summary": self.one_line_summary,
            "emotion": self.emotion.to_dict(),
            "conversation": self.conversation.to_dict(),
            "health": self.health.to_dict(),
            "activity": self.activity.to_dict(),
            "tips_for_children": self.tips_for_children,
            "share_card": {
                "title": f"{self.user_name}今日安心日报",
                "subtitle": self.one_line_summary,
                "score_text": f"安心指数 {self.anxin_score}/10 · {self.anxin_level}",
                "share_text": f"{self.user_name}今日安心指数 {self.anxin_score}/10，{self.anxin_level}。{self.one_line_summary}",
                "highlights": self.tips_for_children[:3],
                "tags": share_tags + topic_tags,
            },
            "generated_at": datetime.now().isoformat(),
        }


# ==================== 日报生成服务 ====================

class DailyReportService:
    """
    今日爸妈 — 日报生成服务

    从多个数据源聚合信息，生成结构化日报：
    1. 对话记录 → 情绪分析 + 话题提取
    2. 健康数据 → 健康摘要
    3. 用药记录 → 服药情况
    4. 活动数据 → 活动摘要
    5. 综合评估 → 安心指数
    """

    def generate_report(
        self,
        db: Session,
        user_id: int,
        report_date: Optional[date] = None
    ) -> DailyReport:
        """生成指定日期的安心日报"""
        if report_date is None:
            report_date = date.today()

        date_str = report_date.isoformat()

        # 获取用户信息
        user_name = self._get_user_name(db, user_id)

        # 聚合各维度数据
        emotion = self._analyze_emotions(db, user_id, report_date)
        conversation = self._summarize_conversations(db, user_id, report_date)
        health = self._summarize_health(db, user_id, report_date)
        activity = self._summarize_activity(db, user_id, report_date)

        # 计算安心指数
        anxin_score = self._calculate_anxin_score(emotion, health, activity, conversation)
        anxin_level = self._get_anxin_level(anxin_score)

        # 生成一句话总结
        one_line = self._generate_one_line_summary(
            user_name, emotion, conversation, health
        )

        # 生成给子女的建议
        tips = self._generate_tips(emotion, health, conversation, activity)

        return DailyReport(
            user_id=user_id,
            user_name=user_name,
            report_date=date_str,
            anxin_score=anxin_score,
            anxin_level=anxin_level,
            one_line_summary=one_line,
            emotion=emotion,
            conversation=conversation,
            health=health,
            activity=activity,
            tips_for_children=tips,
        )

    def _get_user_name(self, db: Session, user_id: int) -> str:
        """获取用户姓名"""
        try:
            from app.models.database import User
            user = db.query(User).filter(User.id == user_id).first()
            return user.name if user and user.name else "爸妈"
        except Exception:
            return "爸妈"

    def _analyze_emotions(
        self, db: Session, user_id: int, report_date: date
    ) -> EmotionSummary:
        """分析今日情绪（优先使用AI存储结果，次选关键词匹配）"""
        summary = EmotionSummary()

        try:
            from app.models.database import Conversation
            import json as _json
            start = datetime.combine(report_date, datetime.min.time())
            end = start + timedelta(days=1)

            # 获取AI回复记录（含风险评分和分类）
            ai_messages = db.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.created_at >= start,
                Conversation.created_at < end,
                Conversation.role == "assistant"
            ).all()

            # 获取用户消息
            user_messages = db.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.created_at >= start,
                Conversation.created_at < end,
                Conversation.role == "user"
            ).order_by(Conversation.created_at).all()

            if not user_messages:
                summary.dominant_emotion = "无数据"
                summary.emotion_score = 5
                return summary

            # 从AI消息中提取情绪信号
            risk_scores = []
            emotion_categories = []
            lonely_signals = 0

            for msg in ai_messages:
                if msg.risk_score and msg.risk_score > 0:
                    risk_scores.append(msg.risk_score)
                if msg.category:
                    emotion_categories.append(msg.category)
                # 从 metadata JSON 中提取 emotion 字段
                if hasattr(msg, 'metadata') and msg.metadata:
                    try:
                        meta = _json.loads(msg.metadata) if isinstance(msg.metadata, str) else msg.metadata
                        emotion = meta.get("emotion", "")
                        if emotion in ("孤独", "寂寞", "想念"):
                            lonely_signals += 1
                        if emotion:
                            emotion_categories.append(emotion)
                    except Exception:
                        pass

            if risk_scores:
                # 有AI数据：用 risk_score 映射情绪
                avg_risk = sum(risk_scores) / len(risk_scores)
                max_risk = max(risk_scores)

                if lonely_signals >= 2:
                    summary.dominant_emotion = "想念家人"
                    summary.emotion_score = 4
                    summary.highlights.append("今天提到了想念家人")
                elif max_risk >= 7:
                    summary.dominant_emotion = "有些低落"
                    summary.emotion_score = max(2, 10 - int(avg_risk))
                    summary.highlights.append("今天情绪有波动")
                elif avg_risk >= 5:
                    summary.dominant_emotion = "平静"
                    summary.emotion_score = 6
                elif avg_risk <= 2:
                    summary.dominant_emotion = "开心"
                    summary.emotion_score = 8
                    summary.highlights.append("今天心情很好")
                else:
                    summary.dominant_emotion = "比较开心"
                    summary.emotion_score = 7

                return summary

            # 兜底：关键词匹配
            positive_words = ["开心", "高兴", "好", "不错", "快乐", "舒服", "棒", "喜欢"]
            negative_words = ["难过", "不好", "痛", "累", "烦", "闷", "想", "孤独", "无聊"]
            lonely_words = ["一个人", "想你", "想孩子", "想家", "没人", "孤独", "寂寞"]

            pos_count = neg_count = lonely_count = 0
            for conv in user_messages:
                content = conv.content or ""
                pos_count += sum(1 for w in positive_words if w in content)
                neg_count += sum(1 for w in negative_words if w in content)
                lonely_count += sum(1 for w in lonely_words if w in content)

            if lonely_count >= 2:
                summary.dominant_emotion = "想念家人"
                summary.emotion_score = 4
                summary.highlights.append("今天提到了想念家人")
            elif neg_count > pos_count * 2:
                summary.dominant_emotion = "有些低落"
                summary.emotion_score = 4
            elif pos_count > neg_count * 2:
                summary.dominant_emotion = "开心"
                summary.emotion_score = 8
                summary.highlights.append("今天心情很好")
            elif pos_count > neg_count:
                summary.dominant_emotion = "比较开心"
                summary.emotion_score = 7
            else:
                summary.dominant_emotion = "平静"
                summary.emotion_score = 6

        except Exception as e:
            logger.error(f"情绪分析失败: {e}")

        return summary

    def _summarize_conversations(
        self, db: Session, user_id: int, report_date: date
    ) -> ConversationSummary:
        """汇总今日对话"""
        summary = ConversationSummary()

        try:
            from app.models.database import Conversation
            start = datetime.combine(report_date, datetime.min.time())
            end = start + timedelta(days=1)

            conversations = db.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.created_at >= start,
                Conversation.created_at < end,
            ).order_by(Conversation.created_at).all()

            if not conversations:
                return summary

            summary.total_messages = len(conversations)

            # 统计会话数
            sessions = set()
            for c in conversations:
                if c.session_id:
                    sessions.add(c.session_id)
            summary.total_conversations = max(len(sessions), 1)

            # 提取时间范围
            user_msgs = [c for c in conversations if c.role == "user"]
            if user_msgs:
                summary.first_chat_time = user_msgs[0].created_at.strftime("%H:%M")
                summary.last_chat_time = user_msgs[-1].created_at.strftime("%H:%M")

            # 提取话题关键词
            topic_keywords = {
                "天气": ["天气", "下雨", "晴", "冷", "热", "风"],
                "饮食": ["吃", "饭", "菜", "汤", "做饭", "恰"],
                "健康": ["头晕", "血压", "不舒服", "痛", "药", "医院"],
                "家人": ["儿子", "女儿", "孩子", "孙子", "老伴"],
                "运动": ["散步", "走路", "锻炼", "广场舞", "太极"],
                "社交": ["邻居", "朋友", "打牌", "聊天", "串门"],
                "兴趣": ["电视", "戏", "歌", "花", "鸟", "新闻"],
            }

            all_user_text = " ".join(c.content or "" for c in user_msgs)
            for topic, keywords in topic_keywords.items():
                if any(kw in all_user_text for kw in keywords):
                    summary.topics.append(topic)

            # 关键引用脱敏：不直接把老人原话转给家属
            # 老人对 AI 倾诉常涉及对儿媳/老伴/邻里的抱怨、健康隐私、情绪低谷，
            # 原话直出会破坏老人对产品的信任，是产品级的伦理风险。
            # 这里改为基于已抽取的 topics 输出脱敏短语，保持 List[str] 契约不变。
            _SENSITIVE_KEYWORDS = (
                "儿媳", "媳妇", "女婿", "老伴", "对象",
                "吵架", "讨厌", "烦", "骂", "气",
                "痛", "病", "血压", "头晕", "不舒服",
                "钱", "存款", "遗嘱",
            )

            def _is_safe_for_family(text: str) -> bool:
                return not any(kw in text for kw in _SENSITIVE_KEYWORDS)

            # 优先：基于已抽取的 topics 输出脱敏短语
            safe_topic_phrases = [
                f"和安心宝聊到了「{t}」"
                for t in summary.topics
                if t != "健康"  # 健康类话题统一走 health_alerts，不在此暴露细节
            ]
            for phrase in safe_topic_phrases[:2]:
                summary.key_quotes.append(phrase)

            # 回退：没有 topic 时，挑选 1 条通过敏感词检查的最长原话（截断 + 加引号）
            if not summary.key_quotes:
                for content in sorted(
                    [(c.content or "") for c in user_msgs if c.content],
                    key=len,
                    reverse=True,
                ):
                    if _is_safe_for_family(content):
                        quote = content[:30] + ("…" if len(content) > 30 else "")
                        summary.key_quotes.append(f"今天提到：「{quote}」")
                        break

        except Exception as e:
            logger.error(f"对话汇总失败: {e}")

        return summary

    def _summarize_health(
        self, db: Session, user_id: int, report_date: date
    ) -> HealthSummary:
        """汇总今日健康数据"""
        summary = HealthSummary()

        try:
            from app.models.database import HealthRecord, Medication, MedicationRecord
            start = datetime.combine(report_date, datetime.min.time())
            end = start + timedelta(days=1)

            # 获取最新血压
            bp_record = db.query(HealthRecord).filter(
                HealthRecord.user_id == user_id,
                HealthRecord.record_type == "blood_pressure",
                HealthRecord.measured_at >= start,
                HealthRecord.measured_at < end,
            ).order_by(HealthRecord.measured_at.desc()).first()

            if bp_record:
                systolic = bp_record.value_primary
                diastolic = bp_record.value_secondary
                if systolic and diastolic:
                    status = "正常"
                    if systolic >= 140 or diastolic >= 90:
                        status = "偏高"
                        summary.health_alerts.append(
                            f"血压偏高: {int(systolic)}/{int(diastolic)}"
                        )
                    elif systolic < 90 or diastolic < 60:
                        status = "偏低"
                        summary.health_alerts.append(
                            f"血压偏低: {int(systolic)}/{int(diastolic)}"
                        )
                    summary.blood_pressure = f"{int(systolic)}/{int(diastolic)} {status}"

            # 获取最新心率
            hr_record = db.query(HealthRecord).filter(
                HealthRecord.user_id == user_id,
                HealthRecord.record_type == "heart_rate",
                HealthRecord.measured_at >= start,
                HealthRecord.measured_at < end,
            ).order_by(HealthRecord.measured_at.desc()).first()

            if hr_record and hr_record.value_primary:
                rate = int(hr_record.value_primary)
                hr_status = "正常"
                if rate > 100:
                    hr_status = "偏快"
                elif rate < 60:
                    hr_status = "偏慢"
                summary.heart_rate = f"{rate} {hr_status}"

            # 今日用药计划 + 实际服药情况
            today_records = db.query(MedicationRecord).filter(
                MedicationRecord.user_id == user_id,
                MedicationRecord.scheduled_time >= start,
                MedicationRecord.scheduled_time < end,
            ).all()

            if today_records:
                # 有计划服药才判断是否漏服
                missed = [r for r in today_records if r.status == "missed"]
                taken = [r for r in today_records if r.status == "taken"]
                summary.medication_taken = len(missed) == 0 and len(taken) > 0
                summary.medication_details = list({
                    r.medication.name for r in today_records
                    if r.medication and r.medication.name
                })[:5]
            else:
                # 无记录时查活跃药物作为基础展示
                active_meds = db.query(Medication).filter(
                    Medication.user_id == user_id,
                    Medication.is_active == True,
                ).limit(5).all()
                summary.medication_details = [m.name for m in active_meds]
                # 无记录时保持默认 True，不给出漏服告警

            # 判定总体健康状态
            if summary.health_alerts:
                summary.overall_status = "注意"
            else:
                summary.overall_status = "正常"

        except Exception as e:
            logger.error(f"健康汇总失败: {e}")

        return summary

    def _summarize_activity(
        self, db: Session, user_id: int, report_date: date
    ) -> ActivitySummary:
        """汇总今日活动"""
        summary = ActivitySummary()

        try:
            from app.models.database import SocialInteraction
            start = datetime.combine(report_date, datetime.min.time())
            end = start + timedelta(days=1)

            interactions = db.query(SocialInteraction).filter(
                SocialInteraction.user_id == user_id,
                SocialInteraction.interaction_at >= start,
                SocialInteraction.interaction_at < end,
            ).all()

            for interaction in interactions:
                if interaction.interaction_type:
                    summary.social_interactions.append(interaction.interaction_type)

        except Exception as e:
            logger.error(f"活动汇总失败: {e}")

        return summary

    def _calculate_anxin_score(
        self,
        emotion: EmotionSummary,
        health: HealthSummary,
        activity: ActivitySummary,
        conversation: ConversationSummary,
    ) -> int:
        """
        计算安心指数（1-10）

        权重分配：
        - 情绪状态：30%
        - 健康状况：30%
        - 社交活跃度：20%
        - 对话频率：20%
        """
        # 情绪分（直接使用emotion_score）
        emotion_score = emotion.emotion_score

        # 健康分
        health_score = 8
        if health.overall_status == "注意":
            health_score = 5
        elif health.overall_status == "告警":
            health_score = 2
        if not health.medication_taken:
            health_score -= 2

        # 社交分
        social_score = 5  # 基础分
        social_count = len(activity.social_interactions)
        if social_count >= 3:
            social_score = 9
        elif social_count >= 1:
            social_score = 7

        # 对话分
        chat_score = 5  # 基础分
        if conversation.total_messages >= 20:
            chat_score = 9
        elif conversation.total_messages >= 10:
            chat_score = 8
        elif conversation.total_messages >= 5:
            chat_score = 7
        elif conversation.total_messages == 0:
            chat_score = 3

        # 加权计算
        total = (
            emotion_score * 0.3
            + health_score * 0.3
            + social_score * 0.2
            + chat_score * 0.2
        )

        return max(1, min(10, round(total)))

    def _get_anxin_level(self, score: int) -> str:
        """安心指数转文字"""
        if score >= 8:
            return "很安心"
        elif score >= 6:
            return "比较安心"
        elif score >= 4:
            return "需关注"
        else:
            return "需立即关注"

    def _generate_one_line_summary(
        self,
        name: str,
        emotion: EmotionSummary,
        conversation: ConversationSummary,
        health: HealthSummary,
    ) -> str:
        """生成一句话总结"""
        parts = []

        # 情绪
        if emotion.dominant_emotion == "开心":
            parts.append(f"{name}今天心情很好")
        elif emotion.dominant_emotion == "想念家人":
            parts.append(f"{name}今天有点想家人")
        elif emotion.dominant_emotion == "有些低落":
            parts.append(f"{name}今天情绪有些低落")
        else:
            parts.append(f"{name}今天状态平稳")

        # 对话
        if conversation.topics:
            parts.append(f"聊了{'/'.join(conversation.topics[:3])}")

        # 健康
        if health.health_alerts:
            parts.append("健康方面需要注意")
        elif health.medication_taken:
            parts.append("按时服药")

        return "，".join(parts) + "。"

    def _generate_tips(
        self,
        emotion: EmotionSummary,
        health: HealthSummary,
        conversation: ConversationSummary,
        activity: ActivitySummary,
    ) -> List[str]:
        """生成给子女的建议"""
        tips = []

        # 情绪相关建议
        if emotion.dominant_emotion == "想念家人":
            tips.append("爸妈今天提到了想念您，有空给他们打个电话吧")
        if emotion.dominant_emotion == "有些低落":
            tips.append("爸妈今天情绪偏低，建议近期多关心，聊聊开心的事")
        if emotion.emotion_score <= 4:
            tips.append("情绪持续偏低，建议本周安排视频通话")

        # 健康相关建议
        for alert in health.health_alerts:
            tips.append(f"健康提醒：{alert}，建议关注")
        if not health.medication_taken:
            tips.append("今天有漏服药物，建议提醒")

        # 社交相关建议
        if len(activity.social_interactions) == 0 and conversation.total_messages < 5:
            tips.append("今天社交活动较少，建议鼓励爸妈多出门走走")

        # 默认建议
        if not tips:
            tips.append("今天一切正常，爸妈过得不错")

        return tips


# 全局服务实例
daily_report_service = DailyReportService()
