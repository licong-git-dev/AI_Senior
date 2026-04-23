"""
主动交互系统API测试
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import json


class TestProactiveGreetings:
    """主动问候测试"""

    def test_create_greeting_config(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试创建问候配置"""
        greeting_data = {
            "user_id": sample_user.id,
            "greeting_type": "morning",
            "schedule_time": "08:00",
            "include_weather": True,
            "include_health_tip": True,
            "include_medication_reminder": True
        }

        response = client.post(
            "/api/proactive/greetings",
            json=greeting_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "greeting_id" in data

    def test_get_user_greetings(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取用户问候配置列表"""
        from app.models.database import ProactiveGreeting

        # 创建测试数据
        for greeting_type in ["morning", "evening"]:
            greeting = ProactiveGreeting(
                user_id=sample_user.id,
                greeting_type=greeting_type,
                schedule_time="08:00" if greeting_type == "morning" else "20:00",
                is_enabled=True
            )
            db_session.add(greeting)
        db_session.commit()

        response = client.get(
            f"/api/proactive/greetings/{sample_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["greetings"]) == 2

    def test_update_greeting_config(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试更新问候配置"""
        from app.models.database import ProactiveGreeting

        greeting = ProactiveGreeting(
            user_id=sample_user.id,
            greeting_type="morning",
            schedule_time="08:00",
            include_weather=True,
            is_enabled=True
        )
        db_session.add(greeting)
        db_session.commit()
        db_session.refresh(greeting)

        update_data = {
            "schedule_time": "07:30",
            "include_weather": False
        }

        response = client.put(
            f"/api/proactive/greetings/{greeting.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_trigger_greeting(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试触发问候"""
        from app.models.database import ProactiveGreeting

        greeting = ProactiveGreeting(
            user_id=sample_user.id,
            greeting_type="morning",
            schedule_time="08:00",
            include_weather=True,
            include_health_tip=True,
            is_enabled=True
        )
        db_session.add(greeting)
        db_session.commit()
        db_session.refresh(greeting)

        trigger_data = {
            "user_id": sample_user.id,
            "greeting_type": "morning"
        }

        response = client.post(
            "/api/proactive/trigger/greeting",
            json=trigger_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "greeting_content" in data
        assert "includes" in data


class TestProactiveReminders:
    """主动提醒测试"""

    def test_create_reminder(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试创建提醒"""
        reminder_data = {
            "user_id": sample_user.id,
            "reminder_type": "water",
            "title": "喝水提醒",
            "trigger_type": "interval",
            "interval_minutes": 60,
            "content": "记得喝水保持水分"
        }

        response = client.post(
            "/api/proactive/reminders",
            json=reminder_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reminder_id" in data

    def test_get_user_reminders(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取用户提醒列表"""
        from app.models.database import ProactiveReminder

        for reminder_type in ["water", "stand_up", "medication"]:
            reminder = ProactiveReminder(
                user_id=sample_user.id,
                reminder_type=reminder_type,
                title=f"{reminder_type}提醒",
                trigger_type="interval",
                is_enabled=True
            )
            db_session.add(reminder)
        db_session.commit()

        response = client.get(
            f"/api/proactive/reminders/{sample_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["reminders"]) == 3

    def test_trigger_reminder(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试触发提醒"""
        from app.models.database import ProactiveReminder

        reminder = ProactiveReminder(
            user_id=sample_user.id,
            reminder_type="water",
            title="喝水提醒",
            trigger_type="interval",
            content="喝水提醒",
            is_enabled=True
        )
        db_session.add(reminder)
        db_session.commit()
        db_session.refresh(reminder)

        trigger_data = {
            "user_id": sample_user.id,
            "reminder_id": reminder.id
        }

        response = client.post(
            "/api/proactive/trigger/reminder",
            json=trigger_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "reminder_content" in data


class TestBehaviorPatterns:
    """行为模式测试"""

    def test_get_user_behavior_patterns(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取用户行为模式"""
        from app.models.database import UserBehaviorPattern
        import json

        # 创建行为模式数据
        pattern = UserBehaviorPattern(
            user_id=sample_user.id,
            pattern_type="activity_peak",
            pattern_value=json.dumps({"peak_hour": 9, "distribution": {"9": 10, "10": 8}}),
            confidence=0.8,
            sample_count=100
        )
        db_session.add(pattern)
        db_session.commit()

        response = client.get(
            f"/api/proactive/behavior-patterns/{sample_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["patterns"]) >= 1

    def test_learn_behavior_patterns(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试学习行为模式"""
        request_data = {
            "user_id": sample_user.id,
            "pattern_type": "activity_peak",
            "pattern_value": "09:00-11:00",
            "confidence": 0.75
        }

        response = client.post(
            "/api/proactive/behavior-patterns/learn",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "pattern_id" in data


class TestPendingInteractions:
    """待处理交互测试"""

    def test_get_pending_interactions(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取待处理交互"""
        from app.models.database import ProactiveInteractionLog
        import json

        # 创建未响应的交互日志
        for i in range(3):
            log = ProactiveInteractionLog(
                user_id=sample_user.id,
                interaction_type="greeting" if i % 2 == 0 else "reminder",
                trigger_source="scheduled",
                content=f"测试消息 {i}",
                triggered_at=datetime.utcnow() - timedelta(hours=i)
            )
            db_session.add(log)
        db_session.commit()

        response = client.get(
            f"/api/proactive/pending/{sample_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "pending_greetings" in data
        assert "pending_reminders" in data

    def test_mark_interaction_responded(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试标记交互已响应"""
        from app.models.database import ProactiveInteractionLog
        import json

        log = ProactiveInteractionLog(
            user_id=sample_user.id,
            interaction_type="greeting",
            trigger_source="scheduled",
            content="早安",
            triggered_at=datetime.utcnow()
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        response = client.put(
            f"/api/proactive/interactions/{log.id}/response",
            json={"user_response": "早上好", "response_type": "positive"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestSmartGreetingGeneration:
    """智能问候生成测试"""

    def test_generate_smart_greeting(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试生成智能问候"""
        request_data = {
            "user_id": sample_user.id,
            "context": {
                "time_of_day": "morning",
                "weather": "晴朗",
                "last_interaction_hours_ago": 12
            }
        }

        response = client.post(
            "/api/proactive/generate-greeting",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "greeting" in data


class TestInteractionLogs:
    """交互日志测试"""

    def test_get_interaction_logs(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取交互日志"""
        from app.models.database import ProactiveInteractionLog

        for i in range(5):
            log = ProactiveInteractionLog(
                user_id=sample_user.id,
                interaction_type="greeting",
                trigger_source="scheduled",
                content=f"问候 {i}",
                triggered_at=datetime.utcnow() - timedelta(days=i)
            )
            db_session.add(log)
        db_session.commit()

        response = client.get(
            f"/api/proactive/interactions/{sample_user.id}?limit=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5

    def test_get_interaction_stats(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取交互统计"""
        from app.models.database import ProactiveInteractionLog

        for i in range(10):
            log = ProactiveInteractionLog(
                user_id=sample_user.id,
                interaction_type="greeting" if i < 5 else "reminder",
                trigger_source="scheduled",
                content=f"消息 {i}",
                triggered_at=datetime.utcnow() - timedelta(days=i % 7)
            )
            db_session.add(log)
        db_session.commit()

        response = client.get(
            f"/api/proactive/stats/{sample_user.id}?days=30",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_interactions" in data
        assert "response_rate" in data
