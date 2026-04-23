"""
认知训练模块API测试
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import json


class TestCognitiveGames:
    """认知游戏测试"""

    def test_create_cognitive_game(self, client: TestClient, admin_auth_headers, db_session):
        """测试创建认知游戏"""
        game_data = {
            "name": "数字记忆挑战",
            "game_type": "memory",
            "difficulty_levels": 5,
            "description": "测试您的数字记忆能力",
            "instructions": "记住屏幕上显示的数字序列",
            "benefits": "提升短期记忆力"
        }

        response = client.post(
            "/cognitive/games",
            json=game_data,
            headers=admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "数字记忆挑战"
        assert data["game_type"] == "memory"
        assert data["difficulty_levels"] == 5
        assert data["is_active"] is True

    def test_get_cognitive_games(self, client: TestClient, db_session):
        """测试获取游戏列表"""
        # 先创建一些游戏
        from app.models.database import CognitiveGame

        games = [
            CognitiveGame(
                name="记忆游戏",
                game_type="memory",
                difficulty_levels=3,
                is_active=True
            ),
            CognitiveGame(
                name="注意力游戏",
                game_type="attention",
                difficulty_levels=3,
                is_active=True
            ),
        ]
        for game in games:
            db_session.add(game)
        db_session.commit()

        response = client.get("/cognitive/games")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_get_games_by_type(self, client: TestClient, db_session):
        """测试按类型筛选游戏"""
        from app.models.database import CognitiveGame

        db_session.add(CognitiveGame(
            name="计算游戏",
            game_type="calculation",
            difficulty_levels=3,
            is_active=True
        ))
        db_session.commit()

        response = client.get("/cognitive/games?game_type=calculation")

        assert response.status_code == 200
        data = response.json()
        for game in data:
            assert game["game_type"] == "calculation"


class TestGameSessions:
    """游戏会话测试"""

    @pytest.fixture
    def sample_game(self, db_session):
        """创建测试游戏"""
        from app.models.database import CognitiveGame

        game = CognitiveGame(
            name="测试记忆游戏",
            game_type="memory",
            difficulty_levels=5,
            is_active=True
        )
        db_session.add(game)
        db_session.commit()
        db_session.refresh(game)
        return game

    def test_start_game_session(self, client: TestClient, auth_headers, sample_user, sample_game, db_session):
        """测试开始游戏会话"""
        request_data = {
            "user_id": sample_user.id,
            "game_id": sample_game.id,
            "difficulty": 2
        }

        response = client.post(
            "/cognitive/sessions/start",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "game_data" in data
        assert data["difficulty"] == 2
        assert "questions" in data["game_data"]

    def test_start_session_invalid_difficulty(self, client: TestClient, auth_headers, sample_user, sample_game):
        """测试使用无效难度开始会话"""
        request_data = {
            "user_id": sample_user.id,
            "game_id": sample_game.id,
            "difficulty": 10  # 超过最大难度
        }

        response = client.post(
            "/cognitive/sessions/start",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 400

    def test_submit_game_answer(self, client: TestClient, auth_headers, sample_user, sample_game, db_session):
        """测试提交游戏答案"""
        # 先开始一个游戏会话
        from app.models.database import CognitiveGameSession
        import json

        session = CognitiveGameSession(
            user_id=sample_user.id,
            game_id=sample_game.id,
            difficulty=1,
            score=0,
            max_score=100,
            status="in_progress",
            game_data=json.dumps({
                "questions": [
                    {"id": 1, "question": "1+1=?", "answer": 2, "points": 10},
                    {"id": 2, "question": "2+2=?", "answer": 4, "points": 10}
                ],
                "current_question_index": 0
            }),
            started_at=datetime.utcnow()
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        # 提交答案
        answer_data = {
            "session_id": session.id,
            "answer": 2,
            "time_taken_seconds": 5
        }

        response = client.post(
            "/cognitive/sessions/answer",
            json=answer_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True
        assert data["current_score"] == 10

    def test_end_game_session(self, client: TestClient, auth_headers, sample_user, sample_game, db_session):
        """测试结束游戏会话"""
        from app.models.database import CognitiveGameSession
        import json

        session = CognitiveGameSession(
            user_id=sample_user.id,
            game_id=sample_game.id,
            difficulty=1,
            score=50,
            max_score=100,
            status="in_progress",
            game_data=json.dumps({"questions": [], "current_question_index": 5}),
            started_at=datetime.utcnow()
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        # 结束会话
        end_data = {
            "session_id": session.id,
            "abandon": False
        }

        response = client.post(
            "/cognitive/sessions/end",
            json=end_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_get_user_game_history(self, client: TestClient, auth_headers, sample_user, sample_game, db_session):
        """测试获取用户游戏记录"""
        from app.models.database import CognitiveGameSession

        # 创建几条历史记录
        for i in range(3):
            session = CognitiveGameSession(
                user_id=sample_user.id,
                game_id=sample_game.id,
                difficulty=1,
                score=50 + i * 10,
                max_score=100,
                status="completed",
                started_at=datetime.utcnow() - timedelta(days=i)
            )
            db_session.add(session)
        db_session.commit()

        response = client.get(
            f"/cognitive/sessions/user/{sample_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3


class TestCognitiveAssessments:
    """认知评估测试"""

    def test_start_assessment(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试开始认知评估"""
        request_data = {
            "user_id": sample_user.id,
            "assessment_type": "daily"
        }

        response = client.post(
            "/cognitive/assessments/start",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "assessment_id" in data
        assert "questions" in data
        assert data["assessment_type"] == "daily"

    def test_submit_assessment(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试提交评估答案"""
        from app.models.database import CognitiveAssessment
        import json

        # 创建评估记录
        assessment = CognitiveAssessment(
            user_id=sample_user.id,
            assessment_type="daily",
            assessment_date=datetime.utcnow(),
            total_score=0,
            max_score=15,
            dimension_scores=json.dumps({
                "questions": [
                    {"id": 1, "dimension": "memory", "max_points": 5, "correct_answer": "test"},
                    {"id": 2, "dimension": "calculation", "max_points": 5, "correct_answer": 42},
                    {"id": 3, "dimension": "attention", "max_points": 5, "correct_answer": "A"}
                ],
                "answers": []
            })
        )
        db_session.add(assessment)
        db_session.commit()
        db_session.refresh(assessment)

        # 提交答案
        submit_data = {
            "assessment_id": assessment.id,
            "answers": [
                {"question_id": 1, "answer": "test"},
                {"question_id": 2, "answer": 42},
                {"question_id": 3, "answer": "A"}
            ]
        }

        response = client.post(
            "/cognitive/assessments/submit",
            json=submit_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "assessment" in data
        assert "personalized_recommendations" in data
        assert data["assessment"]["total_score"] > 0

    def test_get_assessment_history(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取评估历史"""
        from app.models.database import CognitiveAssessment

        # 创建历史记录
        for i in range(3):
            assessment = CognitiveAssessment(
                user_id=sample_user.id,
                assessment_type="daily",
                assessment_date=datetime.utcnow() - timedelta(days=i * 7),
                total_score=70 + i * 5,
                max_score=100,
                cognitive_level="normal"
            )
            db_session.add(assessment)
        db_session.commit()

        response = client.get(
            f"/cognitive/assessments/user/{sample_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3


class TestTrainingPlans:
    """训练计划测试"""

    def test_create_training_plan(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试创建训练计划"""
        plan_data = {
            "user_id": sample_user.id,
            "name": "每日认知训练",
            "description": "针对记忆力的日常训练",
            "target_dimensions": ["memory", "attention"],
            "weekly_sessions": 5,
            "session_duration_minutes": 15,
            "schedule_days": [0, 1, 2, 3, 4],
            "schedule_time": "09:00",
            "start_date": datetime.utcnow().isoformat(),
            "reminder_enabled": True
        }

        response = client.post(
            "/cognitive/training-plans",
            json=plan_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "每日认知训练"
        assert data["weekly_sessions"] == 5
        assert data["is_active"] is True

    def test_update_training_plan(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试更新训练计划"""
        from app.models.database import CognitiveTrainingPlan

        plan = CognitiveTrainingPlan(
            user_id=sample_user.id,
            name="测试计划",
            weekly_sessions=3,
            session_duration_minutes=10,
            start_date=datetime.utcnow(),
            is_active=True
        )
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)

        update_data = {
            "weekly_sessions": 5,
            "session_duration_minutes": 20
        }

        response = client.put(
            f"/cognitive/training-plans/{plan.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["weekly_sessions"] == 5
        assert data["session_duration_minutes"] == 20

    def test_get_user_training_plans(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取用户训练计划"""
        from app.models.database import CognitiveTrainingPlan

        for i in range(2):
            plan = CognitiveTrainingPlan(
                user_id=sample_user.id,
                name=f"计划{i+1}",
                weekly_sessions=3,
                session_duration_minutes=15,
                start_date=datetime.utcnow(),
                is_active=True
            )
            db_session.add(plan)
        db_session.commit()

        response = client.get(
            f"/cognitive/training-plans/user/{sample_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestCognitiveStats:
    """认知统计测试"""

    def test_get_cognitive_stats(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取认知统计"""
        request_data = {
            "user_id": sample_user.id,
            "days": 30
        }

        response = client.post(
            "/cognitive/stats",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_sessions" in data
        assert "dimension_stats" in data
        assert "streak_days" in data

    def test_generate_training_report(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试生成训练报告"""
        request_data = {
            "user_id": sample_user.id,
            "period_days": 30
        }

        response = client.post(
            "/cognitive/reports/generate",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "recommendations" in data
        assert "generated_at" in data


class TestGameRecommendations:
    """游戏推荐测试"""

    def test_get_recommended_games(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取推荐游戏"""
        from app.models.database import CognitiveGame

        # 创建一些游戏
        for game_type in ["memory", "attention", "calculation"]:
            game = CognitiveGame(
                name=f"{game_type}游戏",
                game_type=game_type,
                difficulty_levels=3,
                is_active=True
            )
            db_session.add(game)
        db_session.commit()

        request_data = {
            "user_id": sample_user.id,
            "limit": 3
        }

        response = client.post(
            "/cognitive/recommendations/games",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "recommended_games" in data
        assert "daily_goal_completed" in data
        assert len(data["recommended_games"]) <= 3
