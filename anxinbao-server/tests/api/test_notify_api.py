"""
通知中心 API 回归测试
验证家属通知列表的访问控制与已读/已处理链路。
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.notify import create_family_notification
from app.models.database import Notification as NotificationModel


class TestNotifyAuthorization:
    @pytest.mark.api
    def test_family_can_list_own_notifications(
        self,
        client: TestClient,
        db_session: Session,
        family_auth_headers,
        sample_family_auth,
        sample_user,
    ):
        create_family_notification(
            db=db_session,
            user_id=str(sample_user.id),
            family_id=str(sample_family_auth.id),
            title="紧急求助通知",
            content="测试老人：紧急求助",
            risk_score=10,
            category="emergency",
        )

        response = client.get(
            f"/api/notify/list/{sample_family_auth.id}",
            headers=family_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 1
        assert data["notifications"][0]["category"] == "emergency"

    @pytest.mark.api
    def test_family_cannot_list_other_family_notifications(self, client: TestClient, family_auth_headers):
        response = client.get("/api/notify/list/99999", headers=family_auth_headers)
        assert response.status_code == 403

    @pytest.mark.api
    def test_elder_cannot_list_family_notifications(self, client: TestClient, auth_headers, sample_family_auth):
        response = client.get(
            f"/api/notify/list/{sample_family_auth.id}",
            headers=auth_headers,
        )
        assert response.status_code == 403

    @pytest.mark.api
    def test_family_can_mark_own_notification_handled(
        self,
        client: TestClient,
        db_session: Session,
        family_auth_headers,
        sample_family_auth,
        sample_user,
    ):
        notification = create_family_notification(
            db=db_session,
            user_id=str(sample_user.id),
            family_id=str(sample_family_auth.id),
            title="健康异常通知",
            content="测试老人：血压偏高",
            risk_score=8,
            category="health",
        )

        response = client.put(
            f"/api/notify/handle/{notification.id}?family_id={sample_family_auth.id}",
            headers=family_auth_headers,
        )

        assert response.status_code == 200
        db_notification = db_session.query(NotificationModel).filter(NotificationModel.id == int(notification.id)).first()
        assert db_notification is not None
        assert db_notification.is_read is True
        assert '"is_handled": true' in (db_notification.data or '').lower()

    @pytest.mark.api
    def test_non_admin_cannot_create_notification(self, client: TestClient, family_auth_headers, sample_family_auth, sample_user):
        response = client.post(
            "/api/notify/create",
            headers=family_auth_headers,
            json={
                "user_id": str(sample_user.id),
                "family_id": str(sample_family_auth.id),
                "title": "伪造通知",
                "content": "不应被普通家属创建",
                "risk_score": 10,
                "category": "emergency",
            },
        )

        assert response.status_code == 403
