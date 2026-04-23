"""
今日爸妈-安心日报 API 测试
重点验证权限校验逻辑（P0修复）
"""
import pytest
from unittest.mock import patch, MagicMock


class TestDailyReportAuthorization:
    """日报接口权限测试"""

    @pytest.mark.api
    def test_unauthenticated_access_denied(self, client):
        """未登录用户无法访问日报"""
        resp = client.get("/api/daily-report/today/1")
        assert resp.status_code in (401, 403)

    @pytest.mark.api
    def test_family_can_access_own_elder(
        self, client, family_auth_headers, sample_family_member, sample_user
    ):
        """家属可以查看绑定老人的日报"""
        with patch(
            "app.services.daily_report.DailyReportService.generate_report"
        ) as mock_gen:
            mock_report = MagicMock()
            mock_report.to_dict.return_value = {
                "user_id": sample_user.id,
                "user_name": "测试老人",
                "report_date": "2026-03-03",
                "anxin_score": 8,
                "anxin_level": "很安心",
                "one_line_summary": "今天状态平稳。",
                "emotion": {"dominant_emotion": "平静", "emotion_score": 7,
                            "emotion_changes": [], "highlights": []},
                "conversation": {"total_conversations": 1, "total_messages": 5,
                                 "topics": [], "key_quotes": [],
                                 "first_chat_time": None, "last_chat_time": None},
                "health": {"blood_pressure": None, "heart_rate": None,
                           "blood_glucose": None, "blood_oxygen": None,
                           "medication_taken": True, "medication_details": [],
                           "health_alerts": [], "overall_status": "正常"},
                "activity": {"steps": None, "exercise_minutes": 0,
                             "social_interactions": [], "outdoor_time": 0,
                             "sleep_time": None, "wake_time": None},
                "tips_for_children": ["今天一切正常，爸妈过得不错"],
                "generated_at": "2026-03-03T10:00:00",
            }
            mock_gen.return_value = mock_report

            resp = client.get(
                f"/api/daily-report/today/{sample_user.id}",
                headers=family_auth_headers
            )
            assert resp.status_code == 200

    @pytest.mark.api
    def test_family_can_get_dashboard_summary_for_own_elder(
        self, client, family_auth_headers, sample_family_member, sample_user, sample_family_auth, db_session
    ):
        """家属可以获取绑定老人的安心中心聚合数据"""
        from app.models.database import Notification
        import json

        db_session.add(Notification(
            user_id=sample_family_auth.id,
            notification_type="health_alert",
            priority="high",
            title="血压偏高",
            content="晚间血压高于平时范围",
            data=json.dumps({
                "source_user_id": sample_user.id,
                "risk_score": 8,
                "category": "health",
                "is_handled": False,
            }, ensure_ascii=False),
        ))
        db_session.commit()

        resp = client.get(
            f"/api/daily-report/summary/{sample_user.id}",
            headers=family_auth_headers
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["elder"]["id"] == sample_user.id
        assert "overview" in data
        assert "alerts" in data
        assert "timeline" in data
        assert "recommended_actions" in data
        assert "empty_state" in data
        assert isinstance(data["alerts"], list)
        assert data["alerts"][0]["title"] == "血压偏高"

    @pytest.mark.api
    def test_family_can_get_share_payload_for_own_elder(
        self, client, family_auth_headers, sample_family_member, sample_user
    ):
        """家属可以获取绑定老人的日报分享卡片与邀请码"""
        with patch(
            "app.services.daily_report.DailyReportService.generate_report"
        ) as mock_gen:
            mock_report = MagicMock()
            mock_report.user_id = sample_user.id
            mock_report.user_name = "测试老人"
            mock_report.report_date = "2026-03-03"
            mock_report.anxin_score = 8
            mock_report.anxin_level = "很安心"
            mock_report.one_line_summary = "今天状态平稳。"
            mock_report.health.overall_status = "正常"
            mock_report.tips_for_children = ["今天一切正常，爸妈过得不错"]
            mock_report.conversation.key_quotes = []
            mock_gen.return_value = mock_report

            resp = client.get(
                f"/api/daily-report/share/{sample_user.id}",
                headers=family_auth_headers
            )

            assert resp.status_code == 200
            data = resp.json()
            assert "测试老人" in data["share_title"]
            assert data["invite_code"]
            assert data["invite_expires_in_days"] == 7
            assert "今天状态平稳。" in data["share_text"]
            assert data["report"]["anxin_score"] == 8

    @pytest.mark.api
    def test_share_payload_forbidden_for_unrelated_elder(
        self, client, family_auth_headers
    ):
        """家属无法获取无关老人的日报分享卡片"""
        resp = client.get(
            "/api/daily-report/share/99999",
            headers=family_auth_headers
        )
        assert resp.status_code == 403

    @pytest.mark.api
    def test_family_cannot_access_unrelated_elder(
        self, client, family_auth_headers
    ):
        """家属无法查看无关老人的日报"""
        unrelated_elder_id = 99999
        resp = client.get(
            f"/api/daily-report/today/{unrelated_elder_id}",
            headers=family_auth_headers
        )
        assert resp.status_code == 403

    @pytest.mark.api
    def test_elder_cannot_access_other_elder(
        self, client, auth_headers, sample_user
    ):
        """老人无法查看其他老人的日报"""
        other_elder_id = sample_user.id + 9999
        resp = client.get(
            f"/api/daily-report/today/{other_elder_id}",
            headers=auth_headers
        )
        assert resp.status_code == 403

    @pytest.mark.api
    def test_history_requires_auth(self, client):
        """历史日报接口需要认证"""
        resp = client.get("/api/daily-report/history/1")
        assert resp.status_code in (401, 403)

    @pytest.mark.api
    def test_history_family_forbidden_for_other_elder(
        self, client, family_auth_headers
    ):
        """家属无法查看无关老人的历史日报"""
        resp = client.get(
            "/api/daily-report/history/99999",
            headers=family_auth_headers
        )
        assert resp.status_code == 403

    @pytest.mark.api
    def test_anxin_score_requires_auth(self, client):
        """安心指数接口需要认证"""
        resp = client.get("/api/daily-report/anxin-score/1")
        assert resp.status_code in (401, 403)

    @pytest.mark.api
    def test_anxin_score_family_forbidden_for_other_elder(
        self, client, family_auth_headers
    ):
        """家属无法查看无关老人的安心指数趋势"""
        resp = client.get(
            "/api/daily-report/anxin-score/99999",
            headers=family_auth_headers
        )
        assert resp.status_code == 403

    @pytest.mark.api
    def test_admin_can_access_any_elder(
        self, client, admin_auth_headers, sample_user
    ):
        """管理员可以查看任意老人的日报"""
        with patch(
            "app.services.daily_report.DailyReportService.generate_report"
        ) as mock_gen:
            mock_report = MagicMock()
            mock_report.to_dict.return_value = {
                "user_id": sample_user.id,
                "user_name": "测试老人",
                "report_date": "2026-03-03",
                "anxin_score": 7,
                "anxin_level": "比较安心",
                "one_line_summary": "今天状态平稳。",
                "emotion": {"dominant_emotion": "平静", "emotion_score": 7,
                            "emotion_changes": [], "highlights": []},
                "conversation": {"total_conversations": 0, "total_messages": 0,
                                 "topics": [], "key_quotes": [],
                                 "first_chat_time": None, "last_chat_time": None},
                "health": {"blood_pressure": None, "heart_rate": None,
                           "blood_glucose": None, "blood_oxygen": None,
                           "medication_taken": True, "medication_details": [],
                           "health_alerts": [], "overall_status": "正常"},
                "activity": {"steps": None, "exercise_minutes": 0,
                             "social_interactions": [], "outdoor_time": 0,
                             "sleep_time": None, "wake_time": None},
                "tips_for_children": ["今天一切正常，爸妈过得不错"],
                "generated_at": "2026-03-03T10:00:00",
            }
            mock_gen.return_value = mock_report

            resp = client.get(
                f"/api/daily-report/today/{sample_user.id}",
                headers=admin_auth_headers
            )
            assert resp.status_code == 200


class TestDailyReportGreetingRateLimit:
    """对话问候接口限流测试"""

    @pytest.mark.api
    def test_greeting_requires_auth(self, client):
        """问候接口需要认证"""
        resp = client.get("/api/chat/greeting")
        assert resp.status_code in (401, 403)

    @pytest.mark.api
    def test_greeting_invalid_dialect(self, client, auth_headers):
        """无效方言被 Literal 拦截"""
        resp = client.get(
            "/api/chat/greeting?dialect=cantonese",
            headers=auth_headers
        )
        assert resp.status_code == 422

    @pytest.mark.api
    def test_greeting_valid_dialects(self, client, auth_headers):
        """有效方言返回问候语"""
        for dialect in ["mandarin", "wuhan", "ezhou"]:
            resp = client.get(
                f"/api/chat/greeting?dialect={dialect}",
                headers=auth_headers
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "greeting" in data
            assert data["dialect"] == dialect
