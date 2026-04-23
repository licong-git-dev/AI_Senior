"""
方言情感陪伴服务单元测试
"""
import pytest
from app.services.dialect_companion import (
    dialect_companion,
    DialectCompanionService,
    DIALECT_GREETINGS,
    DIALECT_EMOTION_RESPONSES,
    DIALECT_FOOD_THERAPY,
    DIALECT_CARE_REMINDERS,
)


class TestDialectGreetings:
    """方言问候语测试"""

    @pytest.mark.unit
    def test_get_greeting_mandarin_morning(self):
        """测试普通话早晨问候"""
        greeting = dialect_companion.get_greeting(
            dialect="mandarin", name="张妈妈", hour=8
        )
        assert "张妈妈" in greeting
        assert len(greeting) > 0

    @pytest.mark.unit
    def test_get_greeting_wuhan_evening(self):
        """测试武汉话晚上问候 (18-22点)"""
        greeting = dialect_companion.get_greeting(
            dialect="wuhan", name="李阿姨", hour=19
        )
        assert "李阿姨" in greeting

    @pytest.mark.unit
    def test_get_greeting_ezhou_afternoon(self):
        """测试鄂州话下午问候"""
        greeting = dialect_companion.get_greeting(
            dialect="ezhou", name="王叔叔", hour=13
        )
        assert "王叔叔" in greeting

    @pytest.mark.unit
    def test_get_greeting_night(self):
        """测试夜间问候"""
        greeting = dialect_companion.get_greeting(
            dialect="wuhan", name="张妈妈", hour=22
        )
        assert "张妈妈" in greeting

    @pytest.mark.unit
    def test_get_greeting_unknown_dialect_fallback(self):
        """测试未知方言回退到普通话"""
        greeting = dialect_companion.get_greeting(
            dialect="unknown", name="测试", hour=10
        )
        assert "测试" in greeting

    @pytest.mark.unit
    def test_get_greeting_default_hour(self):
        """测试不指定时间自动获取当前时段"""
        greeting = dialect_companion.get_greeting(dialect="mandarin", name="您")
        assert len(greeting) > 0

    @pytest.mark.unit
    def test_afternoon_period_uses_afternoon_template(self):
        """14:00-17:59 应使用下午模板（下午好），不能是晚上好 — Bug修复验证"""
        for hour in [14, 15, 16, 17]:
            greeting = dialect_companion.get_greeting(
                dialect="wuhan", name="测试", hour=hour
            )
            # 14-17点不应出现"晚上好"
            assert "晚上好" not in greeting, (
                f"hour={hour} 错误地返回了晚上好问候: {greeting}"
            )

    @pytest.mark.unit
    def test_evening_period_correct_range(self):
        """18:00-21:59 应使用晚上模板"""
        for hour in [18, 19, 20, 21]:
            greeting = dialect_companion.get_greeting(
                dialect="wuhan", name="测试", hour=hour
            )
            # 18-21点应出现"晚上好"
            assert "晚上好" in greeting or "晚" in greeting, (
                f"hour={hour} 未返回晚上问候: {greeting}"
            )


class TestDialectEmotionResponses:
    """方言情感回应测试"""

    @pytest.mark.unit
    def test_emotion_response_lonely(self):
        """测试孤独情绪回应"""
        response = dialect_companion.get_emotion_response(
            emotion="lonely", dialect="wuhan", name="张妈妈", child_name="小明"
        )
        assert "张妈妈" in response

    @pytest.mark.unit
    def test_emotion_response_happy(self):
        """测试开心情绪回应"""
        response = dialect_companion.get_emotion_response(
            emotion="happy", dialect="mandarin", name="李阿姨"
        )
        assert "李阿姨" in response

    @pytest.mark.unit
    def test_emotion_response_sad_ezhou(self):
        """测试鄂州话悲伤回应"""
        response = dialect_companion.get_emotion_response(
            emotion="sad", dialect="ezhou", name="王叔叔"
        )
        assert "王叔叔" in response

    @pytest.mark.unit
    def test_emotion_response_pain(self):
        """测试身体疼痛回应"""
        response = dialect_companion.get_emotion_response(
            emotion="pain", dialect="wuhan", name="张妈妈", child_name="张明"
        )
        assert "张妈妈" in response

    @pytest.mark.unit
    def test_emotion_response_unknown_emotion(self):
        """测试未知情绪回退"""
        response = dialect_companion.get_emotion_response(
            emotion="unknown_emotion", dialect="mandarin", name="测试"
        )
        assert "测试" in response


class TestDialectFoodTherapy:
    """方言食疗建议测试"""

    @pytest.mark.unit
    def test_food_therapy_hypertension(self):
        """测试高血压食疗"""
        tip = dialect_companion.get_food_therapy(
            condition="hypertension", dialect="wuhan", name="张妈妈"
        )
        assert "张妈妈" in tip
        assert "血压" in tip

    @pytest.mark.unit
    def test_food_therapy_insomnia(self):
        """测试失眠食疗"""
        tip = dialect_companion.get_food_therapy(
            condition="insomnia", dialect="mandarin", name="李阿姨"
        )
        assert "李阿姨" in tip

    @pytest.mark.unit
    def test_food_therapy_general(self):
        """测试一般食疗"""
        tip = dialect_companion.get_food_therapy(
            condition="general", dialect="ezhou", name="王叔叔"
        )
        assert "王叔叔" in tip

    @pytest.mark.unit
    def test_food_therapy_unknown_condition(self):
        """测试未知病症回退到general"""
        tip = dialect_companion.get_food_therapy(
            condition="unknown", dialect="wuhan", name="测试"
        )
        assert "测试" in tip


class TestDialectCareReminders:
    """方言关怀提醒测试"""

    @pytest.mark.unit
    def test_care_reminder_medication(self):
        """测试用药提醒"""
        reminder = dialect_companion.get_care_reminder(
            reminder_type="medication",
            dialect="wuhan",
            name="张妈妈",
            medicine_name="降压药"
        )
        assert "张妈妈" in reminder
        assert "降压药" in reminder

    @pytest.mark.unit
    def test_care_reminder_water(self):
        """测试喝水提醒"""
        reminder = dialect_companion.get_care_reminder(
            reminder_type="water", dialect="mandarin", name="李阿姨"
        )
        assert "李阿姨" in reminder

    @pytest.mark.unit
    def test_care_reminder_exercise(self):
        """测试运动提醒"""
        reminder = dialect_companion.get_care_reminder(
            reminder_type="exercise", dialect="ezhou", name="王叔叔"
        )
        assert "王叔叔" in reminder

    @pytest.mark.unit
    def test_care_reminder_meal(self):
        """测试吃饭提醒"""
        reminder = dialect_companion.get_care_reminder(
            reminder_type="meal", dialect="wuhan", name="张妈妈"
        )
        assert "张妈妈" in reminder

    @pytest.mark.unit
    def test_care_reminder_unknown_type(self):
        """测试未知提醒类型回退"""
        reminder = dialect_companion.get_care_reminder(
            reminder_type="unknown_type", dialect="mandarin", name="测试"
        )
        assert "测试" in reminder


class TestDialectTemplateCompleteness:
    """方言模板完整性测试"""

    @pytest.mark.unit
    def test_all_dialects_have_greetings(self):
        """所有方言都有问候语"""
        for dialect in ["wuhan", "ezhou", "mandarin"]:
            assert dialect in DIALECT_GREETINGS
            for period in ["morning", "afternoon", "evening", "night"]:
                assert period in DIALECT_GREETINGS[dialect]
                assert len(DIALECT_GREETINGS[dialect][period]) > 0

    @pytest.mark.unit
    def test_all_dialects_have_emotion_responses(self):
        """所有方言都有情感回应"""
        for dialect in ["wuhan", "ezhou", "mandarin"]:
            assert dialect in DIALECT_EMOTION_RESPONSES
            for emotion in ["lonely", "sad", "happy", "tired", "pain"]:
                assert emotion in DIALECT_EMOTION_RESPONSES[dialect]
                assert len(DIALECT_EMOTION_RESPONSES[dialect][emotion]) > 0

    @pytest.mark.unit
    def test_all_dialects_have_food_therapy(self):
        """所有方言都有食疗建议"""
        for dialect in ["wuhan", "ezhou", "mandarin"]:
            assert dialect in DIALECT_FOOD_THERAPY
            assert "general" in DIALECT_FOOD_THERAPY[dialect]

    @pytest.mark.unit
    def test_all_dialects_have_care_reminders(self):
        """所有方言都有关怀提醒"""
        for dialect in ["wuhan", "ezhou", "mandarin"]:
            assert dialect in DIALECT_CARE_REMINDERS
            for reminder_type in ["medication", "water", "exercise", "meal"]:
                assert reminder_type in DIALECT_CARE_REMINDERS[dialect]
