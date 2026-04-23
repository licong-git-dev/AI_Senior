"""
今日爸妈-安心日报服务单元测试
"""
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.daily_report import (
    daily_report_service,
    DailyReportService,
    DailyReport,
    EmotionSummary,
    ConversationSummary,
    HealthSummary,
    ActivitySummary,
)


class TestEmotionSummary:
    """情绪摘要数据模型测试"""

    @pytest.mark.unit
    def test_default_values(self):
        """测试默认值"""
        summary = EmotionSummary()
        assert summary.dominant_emotion == "平静"
        assert summary.emotion_score == 7
        assert summary.emotion_changes == []
        assert summary.highlights == []

    @pytest.mark.unit
    def test_to_dict(self):
        """测试转字典"""
        summary = EmotionSummary(
            dominant_emotion="开心", emotion_score=9, highlights=["很开心"]
        )
        d = summary.to_dict()
        assert d["dominant_emotion"] == "开心"
        assert d["emotion_score"] == 9
        assert "很开心" in d["highlights"]


class TestConversationSummary:
    """对话摘要数据模型测试"""

    @pytest.mark.unit
    def test_default_values(self):
        """测试默认值"""
        summary = ConversationSummary()
        assert summary.total_conversations == 0
        assert summary.total_messages == 0
        assert summary.topics == []

    @pytest.mark.unit
    def test_to_dict(self):
        """测试转字典"""
        summary = ConversationSummary(
            total_conversations=3,
            total_messages=15,
            topics=["天气", "饮食"],
            first_chat_time="08:30",
            last_chat_time="20:15",
        )
        d = summary.to_dict()
        assert d["total_conversations"] == 3
        assert d["total_messages"] == 15
        assert "天气" in d["topics"]


class TestHealthSummary:
    """健康摘要数据模型测试"""

    @pytest.mark.unit
    def test_default_values(self):
        """测试默认值"""
        summary = HealthSummary()
        assert summary.overall_status == "正常"
        assert summary.medication_taken is True

    @pytest.mark.unit
    def test_to_dict(self):
        """测试转字典"""
        summary = HealthSummary(
            blood_pressure="135/85 正常",
            heart_rate="72 正常",
            overall_status="正常",
        )
        d = summary.to_dict()
        assert d["blood_pressure"] == "135/85 正常"
        assert d["overall_status"] == "正常"


class TestDailyReport:
    """日报数据模型测试"""

    @pytest.mark.unit
    def test_to_dict(self):
        """测试日报转字典"""
        report = DailyReport(
            user_id=1,
            user_name="张妈妈",
            report_date="2026-03-03",
            anxin_score=8,
            anxin_level="很安心",
            one_line_summary="张妈妈今天心情很好，聊了天气/饮食，按时服药。",
        )
        d = report.to_dict()
        assert d["user_id"] == 1
        assert d["user_name"] == "张妈妈"
        assert d["anxin_score"] == 8
        assert d["anxin_level"] == "很安心"
        assert "generated_at" in d
        assert "emotion" in d
        assert "conversation" in d
        assert "health" in d
        assert "activity" in d


class TestAnxinScoreCalculation:
    """安心指数计算测试"""

    @pytest.mark.unit
    def test_high_score(self):
        """测试高安心指数"""
        service = DailyReportService()
        score = service._calculate_anxin_score(
            emotion=EmotionSummary(emotion_score=9),
            health=HealthSummary(overall_status="正常", medication_taken=True),
            activity=ActivitySummary(social_interactions=["散步", "聊天", "打牌"]),
            conversation=ConversationSummary(total_messages=25),
        )
        assert score >= 8

    @pytest.mark.unit
    def test_low_score_health_alert(self):
        """测试健康告警导致低安心指数"""
        service = DailyReportService()
        score = service._calculate_anxin_score(
            emotion=EmotionSummary(emotion_score=4),
            health=HealthSummary(
                overall_status="告警",
                medication_taken=False,
                health_alerts=["血压偏高"],
            ),
            activity=ActivitySummary(social_interactions=[]),
            conversation=ConversationSummary(total_messages=0),
        )
        assert score <= 4

    @pytest.mark.unit
    def test_medium_score(self):
        """测试中等安心指数"""
        service = DailyReportService()
        score = service._calculate_anxin_score(
            emotion=EmotionSummary(emotion_score=6),
            health=HealthSummary(overall_status="正常"),
            activity=ActivitySummary(social_interactions=["散步"]),
            conversation=ConversationSummary(total_messages=8),
        )
        assert 5 <= score <= 8

    @pytest.mark.unit
    def test_score_clamped_to_range(self):
        """测试安心指数限制在1-10"""
        service = DailyReportService()
        # 极端低分
        score_low = service._calculate_anxin_score(
            emotion=EmotionSummary(emotion_score=1),
            health=HealthSummary(overall_status="告警", medication_taken=False),
            activity=ActivitySummary(),
            conversation=ConversationSummary(),
        )
        assert 1 <= score_low <= 10

        # 极端高分
        score_high = service._calculate_anxin_score(
            emotion=EmotionSummary(emotion_score=10),
            health=HealthSummary(overall_status="正常"),
            activity=ActivitySummary(social_interactions=["a", "b", "c", "d"]),
            conversation=ConversationSummary(total_messages=30),
        )
        assert 1 <= score_high <= 10


class TestAnxinLevel:
    """安心等级映射测试"""

    @pytest.mark.unit
    def test_anxin_levels(self):
        """测试安心等级文字"""
        service = DailyReportService()
        assert service._get_anxin_level(10) == "很安心"
        assert service._get_anxin_level(8) == "很安心"
        assert service._get_anxin_level(7) == "比较安心"
        assert service._get_anxin_level(6) == "比较安心"
        assert service._get_anxin_level(5) == "需关注"
        assert service._get_anxin_level(4) == "需关注"
        assert service._get_anxin_level(3) == "需立即关注"
        assert service._get_anxin_level(1) == "需立即关注"


class TestOneLineSummary:
    """一句话总结生成测试"""

    @pytest.mark.unit
    def test_happy_summary(self):
        """测试开心情绪摘要"""
        service = DailyReportService()
        summary = service._generate_one_line_summary(
            name="张妈妈",
            emotion=EmotionSummary(dominant_emotion="开心"),
            conversation=ConversationSummary(topics=["天气", "饮食"]),
            health=HealthSummary(medication_taken=True),
        )
        assert "张妈妈" in summary
        assert "心情很好" in summary
        assert "天气" in summary

    @pytest.mark.unit
    def test_lonely_summary(self):
        """测试想家情绪摘要"""
        service = DailyReportService()
        summary = service._generate_one_line_summary(
            name="李阿姨",
            emotion=EmotionSummary(dominant_emotion="想念家人"),
            conversation=ConversationSummary(topics=[]),
            health=HealthSummary(),
        )
        assert "李阿姨" in summary
        assert "想家人" in summary

    @pytest.mark.unit
    def test_health_alert_summary(self):
        """测试健康告警摘要"""
        service = DailyReportService()
        summary = service._generate_one_line_summary(
            name="王叔叔",
            emotion=EmotionSummary(dominant_emotion="平静"),
            conversation=ConversationSummary(topics=["健康"]),
            health=HealthSummary(health_alerts=["血压偏高"]),
        )
        assert "王叔叔" in summary
        assert "注意" in summary


class TestTipsGeneration:
    """子女建议生成测试"""

    @pytest.mark.unit
    def test_tips_for_lonely_parent(self):
        """测试想念家人的建议"""
        service = DailyReportService()
        tips = service._generate_tips(
            emotion=EmotionSummary(dominant_emotion="想念家人", emotion_score=4),
            health=HealthSummary(),
            conversation=ConversationSummary(total_messages=5),
            activity=ActivitySummary(),
        )
        assert any("打个电话" in t for t in tips)

    @pytest.mark.unit
    def test_tips_for_health_alert(self):
        """测试健康告警建议"""
        service = DailyReportService()
        tips = service._generate_tips(
            emotion=EmotionSummary(),
            health=HealthSummary(health_alerts=["血压偏高: 152/95"]),
            conversation=ConversationSummary(total_messages=10),
            activity=ActivitySummary(social_interactions=["散步"]),
        )
        assert any("血压" in t for t in tips)

    @pytest.mark.unit
    def test_tips_low_social(self):
        """测试社交活动少的建议"""
        service = DailyReportService()
        tips = service._generate_tips(
            emotion=EmotionSummary(),
            health=HealthSummary(),
            conversation=ConversationSummary(total_messages=2),
            activity=ActivitySummary(social_interactions=[]),
        )
        assert any("社交" in t or "出门" in t for t in tips)

    @pytest.mark.unit
    def test_tips_all_good(self):
        """测试一切正常的建议"""
        service = DailyReportService()
        tips = service._generate_tips(
            emotion=EmotionSummary(emotion_score=8),
            health=HealthSummary(),
            conversation=ConversationSummary(total_messages=15),
            activity=ActivitySummary(social_interactions=["聊天"]),
        )
        assert any("正常" in t or "不错" in t for t in tips)

    @pytest.mark.unit
    def test_missed_medication_tip(self):
        """测试漏服药物建议"""
        service = DailyReportService()
        tips = service._generate_tips(
            emotion=EmotionSummary(),
            health=HealthSummary(medication_taken=False),
            conversation=ConversationSummary(total_messages=10),
            activity=ActivitySummary(social_interactions=["散步"]),
        )
        assert any("漏服" in t or "药" in t for t in tips)
