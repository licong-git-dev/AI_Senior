"""
情感记忆系统API测试
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import json


class TestUserProfile:
    """用户画像测试"""

    def test_create_user_profile(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试创建用户画像"""
        profile_data = {
            "user_id": sample_user.id,
            "nickname": "张爷爷",
            "hometown": "北京",
            "current_city": "上海"
        }

        response = client.post(
            "/api/memory/profile",
            json=profile_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "profile_id" in data

    def test_get_user_profile(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取用户画像"""
        from app.models.database import UserProfile
        import json

        profile = UserProfile(
            user_id=sample_user.id,
            hobbies=json.dumps(["读书", "散步"]),
            hometown="上海",
            ai_persona="wise_mentor"
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get(
            f"/api/memory/profile/{sample_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert data["profile"]["hometown"] == "上海"

    def test_update_user_profile(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试更新用户画像"""
        from app.models.database import UserProfile
        import json

        profile = UserProfile(
            user_id=sample_user.id,
            hobbies=json.dumps(["读书"]),
            hometown="广州"
        )
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)

        update_data = {
            "hobbies": ["读书", "养花", "书法"],
            "chronic_conditions": ["高血压", "糖尿病"]
        }

        response = client.put(
            f"/api/memory/profile/{sample_user.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestUserMemories:
    """用户记忆测试"""

    def test_create_memory(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试创建记忆"""
        memory_data = {
            "user_id": sample_user.id,
            "memory_type": "family",
            "key": "grandson_name",
            "value": "小明",
            "importance": 8
        }

        response = client.post(
            "/api/memory/memories",
            json=memory_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "memory_id" in data

    def test_get_user_memories(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取用户记忆列表"""
        from app.models.database import UserMemory

        memories = [
            UserMemory(
                user_id=sample_user.id,
                memory_type="family",
                key="spouse_name",
                value="王阿姨",
                importance=10,
                extracted_at=datetime.now()
            ),
            UserMemory(
                user_id=sample_user.id,
                memory_type="preference",
                key="favorite_food",
                value="红烧肉",
                importance=5,
                extracted_at=datetime.now()
            )
        ]
        for m in memories:
            db_session.add(m)
        db_session.commit()

        response = client.get(
            f"/api/memory/memories/{sample_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["memories"]) == 2

    def test_get_memories_by_type(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试按类型获取记忆"""
        from app.models.database import UserMemory

        db_session.add(UserMemory(
            user_id=sample_user.id,
            memory_type="health",
            key="allergy",
            value="花生过敏",
            importance=10,
            extracted_at=datetime.now()
        ))
        db_session.commit()

        response = client.get(
            f"/api/memory/memories/{sample_user.id}?memory_type=health",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        for memory in data["memories"]:
            assert memory["memory_type"] == "health"

    def test_extract_memories_from_conversation(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试从对话中提取记忆"""
        request_data = {
            "user_id": sample_user.id,
            "conversation_id": 1,
            "conversation_content": "我孙子小明今年6岁了，他特别喜欢画画。明天是我老伴王阿姨的生日。"
        }

        response = client.post(
            "/api/memory/memories/extract",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "extracted_memories" in data or "extracted_count" in data

    def test_retrieve_relevant_memories(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试检索相关记忆"""
        from app.models.database import UserMemory

        memories = [
            UserMemory(
                user_id=sample_user.id,
                memory_type="family",
                key="grandson_name",
                value="小明",
                importance=8,
                extracted_at=datetime.now()
            ),
            UserMemory(
                user_id=sample_user.id,
                memory_type="family",
                key="grandson_hobby",
                value="画画",
                importance=5,
                extracted_at=datetime.now()
            )
        ]
        for m in memories:
            db_session.add(m)
        db_session.commit()

        request_data = {
            "user_id": sample_user.id,
            "keywords": ["孙子"],
            "limit": 5
        }

        response = client.post(
            "/api/memory/memories/retrieve",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "memories" in data


class TestImportantDates:
    """重要日期测试"""

    def test_create_important_date(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试创建重要日期"""
        date_data = {
            "user_id": sample_user.id,
            "date_type": "birthday",
            "title": "老伴生日",
            "month": 6,
            "day": 15,
            "year": 1950,
            "related_person": "王阿姨",
            "reminder_enabled": True,
            "reminder_days_before": 3
        }

        response = client.post(
            "/api/memory/important-dates",
            json=date_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "date_id" in data

    def test_get_upcoming_dates(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取即将到来的重要日期"""
        from app.models.database import ImportantDate
        from datetime import date

        # 创建一些测试日期
        today = date.today()
        next_month = (today.month % 12) + 1
        next_next_month = ((today.month + 1) % 12) + 1
        dates = [
            ImportantDate(
                user_id=sample_user.id,
                date_type="birthday",
                title="孙子生日",
                month=next_month,
                day=15,
                reminder_enabled=True
            ),
            ImportantDate(
                user_id=sample_user.id,
                date_type="anniversary",
                title="结婚纪念日",
                month=next_next_month,
                day=20,
                reminder_enabled=True
            )
        ]
        for d in dates:
            db_session.add(d)
        db_session.commit()

        response = client.get(
            f"/api/memory/important-dates/{sample_user.id}/upcoming?days=90",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "upcoming_dates" in data or "today_dates" in data

    def test_update_important_date(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试更新重要日期"""
        from app.models.database import ImportantDate

        imp_date = ImportantDate(
            user_id=sample_user.id,
            date_type="birthday",
            title="测试生日",
            month=5,
            day=10,
            reminder_enabled=False
        )
        db_session.add(imp_date)
        db_session.commit()
        db_session.refresh(imp_date)

        update_data = {
            "reminder_enabled": True,
            "reminder_days_before": 7
        }

        response = client.put(
            f"/api/memory/important-dates/{imp_date.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestLifeStories:
    """人生故事测试"""

    def test_create_life_story(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试创建人生故事"""
        story_data = {
            "user_id": sample_user.id,
            "category": "childhood",
            "title": "小时候的故事",
            "content": "我小时候在农村长大，每天放学后帮家里放牛...",
            "era": "1960年代",
            "location": "河北农村",
            "emotion_tags": ["温馨"]
        }

        response = client.post(
            "/api/memory/life-stories",
            json=story_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "story_id" in data

    def test_get_user_life_stories(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取用户人生故事"""
        from app.models.database import LifeStory

        stories = [
            LifeStory(
                user_id=sample_user.id,
                category="career",
                title="工作经历",
                content="我在工厂工作了30年...",
                era="1980-2010",
                recorded_at=datetime.now()
            ),
            LifeStory(
                user_id=sample_user.id,
                category="family",
                title="结婚的故事",
                content="我们是经人介绍认识的...",
                era="1975年",
                recorded_at=datetime.now()
            )
        ]
        for s in stories:
            db_session.add(s)
        db_session.commit()

        response = client.get(
            f"/api/memory/life-stories/{sample_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["stories"]) == 2


class TestPersonalizationContext:
    """个性化上下文测试"""

    def test_get_personalization_context(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取个性化上下文"""
        from app.models.database import UserProfile, UserMemory, ImportantDate
        import json

        # 创建用户画像
        profile = UserProfile(
            user_id=sample_user.id,
            hobbies=json.dumps(["下棋", "养花"]),
            hometown="北京",
            ai_persona="caring_companion"
        )
        db_session.add(profile)

        # 创建一些记忆
        memory = UserMemory(
            user_id=sample_user.id,
            memory_type="family",
            key="spouse_name",
            value="王阿姨",
            importance=10,
            extracted_at=datetime.now()
        )
        db_session.add(memory)

        # 创建重要日期
        from datetime import date
        next_month = (date.today().month % 12) + 1
        imp_date = ImportantDate(
            user_id=sample_user.id,
            date_type="birthday",
            title="老伴生日",
            month=next_month,
            day=15,
            reminder_enabled=True
        )
        db_session.add(imp_date)
        db_session.commit()

        response = client.get(
            f"/api/memory/personalization-context/{sample_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "profile" in data
        assert "relevant_memories" in data
        assert "upcoming_dates" in data
