"""
通义千问AI服务单元测试
测试对话、情绪识别、食疗建议等功能
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta

from app.services.qwen_service import QwenChatService, SYSTEM_PROMPT


class TestQwenChatService:
    """通义千问对话服务测试"""

    @pytest.fixture
    def chat_service(self):
        """创建对话服务实例"""
        with patch('app.services.qwen_service.dashscope') as mock_ds:
            mock_ds.api_key = "test-key"
            service = QwenChatService()
            yield service

    @pytest.fixture
    def mock_successful_response(self):
        """模拟成功的API响应"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output.choices = [Mock()]
        mock_response.output.choices[0].message.content = '''没事的，头晕很常见，可能是休息不好。您多喝点温水，坐下来休息一会儿。

```json
{"risk_score": 3, "risk_reason": "轻微头晕，建议休息", "need_notify": false, "category": "health", "emotion": {"type": "neutral", "intensity": 2, "keywords": ["头晕"]}, "topics": ["健康"]}
```'''
        return mock_response

    @pytest.mark.unit
    @pytest.mark.ai
    def test_chat_returns_reply_and_risk(self, chat_service, mock_successful_response):
        """测试对话返回回复和风险评估"""
        with patch('app.services.qwen_service.Generation.call', return_value=mock_successful_response):
            reply, risk_info = chat_service.chat("我今天有点头晕")

            assert reply is not None
            assert "头晕" in reply or "没事" in reply
            assert risk_info["risk_score"] == 3
            assert risk_info["category"] == "health"

    @pytest.mark.unit
    @pytest.mark.ai
    def test_chat_with_history(self, chat_service, mock_successful_response):
        """测试带历史记录的对话"""
        history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "您好！有什么可以帮您的？"}
        ]

        with patch('app.services.qwen_service.Generation.call', return_value=mock_successful_response):
            reply, risk_info = chat_service.chat("我头晕", conversation_history=history)

            assert reply is not None

    @pytest.mark.unit
    @pytest.mark.ai
    def test_chat_with_user_profile(self, chat_service, mock_successful_response):
        """测试带用户画像的对话"""
        profile = {
            "name": "王奶奶",
            "age": 75,
            "health_conditions": ["高血压", "糖尿病"],
            "interests": ["太极拳", "养花"],
            "family_members": ["儿子小明", "女儿小红"],
            "important_dates": {"生日": "1950-03-15"},
            "preferences": "喜欢聊家常"
        }

        with patch('app.services.qwen_service.Generation.call', return_value=mock_successful_response):
            reply, risk_info = chat_service.chat(
                "今天感觉不错",
                user_profile=profile
            )

            assert reply is not None

    @pytest.mark.unit
    @pytest.mark.ai
    def test_chat_api_failure(self, chat_service):
        """测试API调用失败"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.code = "ServerError"
        mock_response.message = "Internal Server Error"

        with patch('app.services.qwen_service.Generation.call', return_value=mock_response):
            reply, risk_info = chat_service.chat("测试消息")

            assert "没听清" in reply or "再说一遍" in reply
            assert risk_info["category"] == "error"

    @pytest.mark.unit
    @pytest.mark.ai
    def test_chat_exception_handling(self, chat_service):
        """测试异常处理"""
        with patch('app.services.qwen_service.Generation.call', side_effect=Exception("Network error")):
            reply, risk_info = chat_service.chat("测试消息")

            assert reply is not None
            assert risk_info["risk_score"] == 1


class TestResponseParsing:
    """响应解析测试"""

    @pytest.fixture
    def chat_service(self):
        with patch('app.services.qwen_service.dashscope'):
            return QwenChatService()

    @pytest.mark.unit
    def test_parse_response_with_json(self, chat_service):
        """测试解析带JSON的响应"""
        response = '''这是回复文本。

```json
{"risk_score": 5, "risk_reason": "测试", "need_notify": false, "category": "health"}
```'''

        reply, risk_info = chat_service._parse_response(response)

        assert reply == "这是回复文本。"
        assert risk_info["risk_score"] == 5

    @pytest.mark.unit
    def test_parse_response_without_json(self, chat_service):
        """测试解析无JSON的响应"""
        response = "这是一个普通的回复，没有JSON。"

        reply, risk_info = chat_service._parse_response(response)

        assert reply == response
        assert risk_info["risk_score"] == 1  # 默认值
        assert risk_info["category"] == "chat"

    @pytest.mark.unit
    def test_parse_response_with_inline_json(self, chat_service):
        """测试解析内联JSON的响应"""
        response = '''回复内容{"risk_score": 7, "risk_reason": "高风险"}'''

        reply, risk_info = chat_service._parse_response(response)

        assert risk_info["risk_score"] == 7

    @pytest.mark.unit
    def test_normalize_risk_info_complete(self, chat_service):
        """测试标准化完整的风险信息"""
        risk_info = {
            "risk_score": 5,
            "risk_reason": "测试",
            "need_notify": True,
            "category": "health",
            "emotion": {"type": "anxious", "intensity": 3, "keywords": ["担心"]},
            "topics": ["健康"]
        }

        normalized = chat_service._normalize_risk_info(risk_info)

        assert normalized["risk_score"] == 5
        assert normalized["emotion"]["type"] == "anxious"

    @pytest.mark.unit
    def test_normalize_risk_info_missing_fields(self, chat_service):
        """测试标准化缺失字段的风险信息"""
        risk_info = {"risk_score": 8}

        normalized = chat_service._normalize_risk_info(risk_info)

        assert normalized["risk_score"] == 8
        assert normalized["category"] == "chat"
        assert normalized["need_notify"] is True  # score >= 7
        assert "emotion" in normalized
        assert normalized["emotion"]["type"] == "neutral"


class TestEmotionAnalysis:
    """情绪分析测试"""

    @pytest.fixture
    def chat_service(self):
        with patch('app.services.qwen_service.dashscope'):
            return QwenChatService()

    @pytest.mark.unit
    @pytest.mark.ai
    def test_analyze_emotion_lonely(self, chat_service):
        """测试分析孤独情绪"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output.choices = [Mock()]
        mock_response.output.choices[0].message.content = '''{"type": "lonely", "intensity": 4, "keywords": ["一个人", "没人"], "suggestion": "多陪伴聊天"}'''

        with patch('app.services.qwen_service.Generation.call', return_value=mock_response):
            result = chat_service.analyze_emotion("孩子们都不在，就我一个人")

            assert result["type"] == "lonely"
            assert result["intensity"] == 4

    @pytest.mark.unit
    @pytest.mark.ai
    def test_analyze_emotion_happy(self, chat_service):
        """测试分析积极情绪"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output.choices = [Mock()]
        mock_response.output.choices[0].message.content = '''{"type": "happy", "intensity": 4, "keywords": ["开心", "来看我"], "suggestion": "一起分享喜悦"}'''

        with patch('app.services.qwen_service.Generation.call', return_value=mock_response):
            result = chat_service.analyze_emotion("今天儿子来看我了，好开心！")

            assert result["type"] == "happy"

    @pytest.mark.unit
    @pytest.mark.ai
    def test_analyze_emotion_api_failure(self, chat_service):
        """测试情绪分析API失败"""
        with patch('app.services.qwen_service.Generation.call', side_effect=Exception("Error")):
            result = chat_service.analyze_emotion("测试文本")

            assert result["type"] == "neutral"
            assert result["intensity"] == 1


class TestProactiveCare:
    """主动关怀测试"""

    @pytest.fixture
    def chat_service(self):
        with patch('app.services.qwen_service.dashscope'):
            return QwenChatService()

    @pytest.mark.unit
    @pytest.mark.ai
    def test_generate_proactive_care_birthday(self, chat_service):
        """测试生日关怀消息"""
        today = datetime.now()
        profile = {
            "name": "张奶奶",
            "important_dates": {"生日": f"1950-{today.month}-{today.day}"}
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output.choices = [Mock()]
        mock_response.output.choices[0].message.content = "张奶奶，生日快乐！祝您身体健康，笑口常开！"

        with patch('app.services.qwen_service.Generation.call', return_value=mock_response):
            message = chat_service.generate_proactive_care(profile)

            assert message is not None
            assert len(message) > 0

    @pytest.mark.unit
    @pytest.mark.ai
    def test_generate_proactive_care_long_absence(self, chat_service):
        """测试长时间未互动关怀"""
        profile = {"name": "李爷爷"}
        last_interaction = datetime.now() - timedelta(days=3)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output.choices = [Mock()]
        mock_response.output.choices[0].message.content = "李爷爷，好久没聊天了，今天怎么样？"

        with patch('app.services.qwen_service.Generation.call', return_value=mock_response):
            message = chat_service.generate_proactive_care(
                profile,
                last_interaction=last_interaction
            )

            assert message is not None


class TestFoodTherapy:
    """食疗建议测试"""

    @pytest.fixture
    def chat_service(self):
        with patch('app.services.qwen_service.dashscope'):
            return QwenChatService()

    @pytest.mark.unit
    @pytest.mark.ai
    def test_generate_food_therapy(self, chat_service):
        """测试生成食疗建议"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output.choices = [Mock()]
        mock_response.output.choices[0].message.content = '''{"name": "枸杞菊花茶", "ingredients": ["枸杞10粒", "菊花5朵"], "steps": "开水冲泡，焖5分钟", "effect": "清肝明目"}'''

        with patch('app.services.qwen_service.Generation.call', return_value=mock_response):
            result = chat_service.generate_food_therapy("头晕眼花")

            assert result["name"] == "枸杞菊花茶"
            assert "ingredients" in result
            assert "steps" in result

    @pytest.mark.unit
    @pytest.mark.ai
    def test_generate_food_therapy_default(self, chat_service):
        """测试API失败时返回默认建议"""
        with patch('app.services.qwen_service.Generation.call', side_effect=Exception("Error")):
            result = chat_service.generate_food_therapy("任意症状")

            assert result["name"] == "红枣枸杞茶"  # 默认值


class TestUserInfoExtraction:
    """用户信息提取测试"""

    @pytest.fixture
    def chat_service(self):
        with patch('app.services.qwen_service.dashscope'):
            return QwenChatService()

    @pytest.mark.unit
    @pytest.mark.ai
    def test_extract_user_info(self, chat_service):
        """测试提取用户信息"""
        history = [
            {"role": "user", "content": "我儿子小明今天来看我了"},
            {"role": "assistant", "content": "真好！"},
            {"role": "user", "content": "我喜欢在公园打太极"},
            {"role": "assistant", "content": "太极很好！"}
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output.choices = [Mock()]
        mock_response.output.choices[0].message.content = '''{"interests": ["太极拳"], "family_members": ["儿子小明"]}'''

        with patch('app.services.qwen_service.Generation.call', return_value=mock_response):
            result = chat_service.extract_user_info(history)

            assert "interests" in result or "family_members" in result

    @pytest.mark.unit
    def test_extract_user_info_short_history(self, chat_service):
        """测试历史记录太短时返回空"""
        history = [{"role": "user", "content": "你好"}]

        result = chat_service.extract_user_info(history)

        assert result == {}


class TestSystemPrompt:
    """系统提示词测试"""

    @pytest.mark.unit
    def test_system_prompt_contains_key_elements(self):
        """测试系统提示词包含关键要素"""
        assert "安心宝" in SYSTEM_PROMPT
        assert "老年人" in SYSTEM_PROMPT or "老人" in SYSTEM_PROMPT
        assert "情绪" in SYSTEM_PROMPT
        assert "风险" in SYSTEM_PROMPT or "risk" in SYSTEM_PROMPT.lower()
        assert "食疗" in SYSTEM_PROMPT

    @pytest.mark.unit
    def test_system_prompt_safety_guidelines(self):
        """测试系统提示词包含安全指南"""
        assert "不要吓唬" in SYSTEM_PROMPT or "别担心" in SYSTEM_PROMPT
        assert "不推荐" in SYSTEM_PROMPT and "药物" in SYSTEM_PROMPT
