"""
紧急服务API单元测试
测试SOS触发、紧急联系人、事件处理等功能
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.database import (
    EmergencyEvent, EmergencyNotification, EmergencyContact, Notification, User, UserAuth, FamilyMember
)


class TestEmergencyContactAPI:
    """紧急联系人API测试"""

    def test_create_contact(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试创建紧急联系人"""
        payload = {
            "name": "张三",
            "phone": "13800138001",
            "relationship": "儿子",
            "is_primary": True
        }
        response = client.post(
            f"/api/emergency/contacts?user_id={sample_user.id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "contact_id" in data

        # 验证数据库
        contact = db_session.query(EmergencyContact).filter(
            EmergencyContact.user_id == sample_user.id,
            EmergencyContact.name == "张三"
        ).first()
        assert contact is not None
        assert contact.is_primary is True

    def test_create_multiple_contacts(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试创建多个紧急联系人"""
        contacts = [
            {"name": "联系人1", "phone": "13800138001", "relationship": "儿子", "is_primary": True},
            {"name": "联系人2", "phone": "13800138002", "relationship": "女儿", "is_primary": False},
            {"name": "联系人3", "phone": "13800138003", "relationship": "邻居", "is_primary": False}
        ]

        for contact in contacts:
            response = client.post(
                f"/api/emergency/contacts?user_id={sample_user.id}",
                json=contact,
                headers=auth_headers
            )
            assert response.status_code == 200

        # 验证通知顺序
        db_contacts = db_session.query(EmergencyContact).filter(
            EmergencyContact.user_id == sample_user.id
        ).order_by(EmergencyContact.notify_order).all()

        assert len(db_contacts) == 3
        # 通知顺序应递增
        for i, c in enumerate(db_contacts):
            assert c.notify_order == i + 1

    def test_get_contacts(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试获取紧急联系人列表"""
        # 创建测试数据
        db_session.add(EmergencyContact(
            user_id=sample_user.id,
            name="测试联系人",
            phone="13900139000",
            relation_type="配偶",
            is_primary=True,
            notify_order=1,
            notification_enabled=True
        ))
        db_session.commit()

        response = client.get(f"/api/emergency/contacts/{sample_user.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "contacts" in data
        assert len(data["contacts"]) >= 1

    def test_update_contact(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试更新紧急联系人"""
        contact = EmergencyContact(
            user_id=sample_user.id,
            name="原名字",
            phone="13800138000",
            relation_type="朋友",
            is_primary=False,
            notify_order=1,
            notification_enabled=True
        )
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)

        response = client.put(
            f"/api/emergency/contacts/{contact.id}",
            json={
                "name": "新名字",
                "phone": "13900139000",
                "is_primary": True
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证更新
        db_session.refresh(contact)
        assert contact.name == "新名字"
        assert contact.is_primary is True

    def test_delete_contact(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试删除紧急联系人"""
        contact = EmergencyContact(
            user_id=sample_user.id,
            name="待删除联系人",
            phone="13800138000",
            relation_type="其他",
            is_primary=False,
            notify_order=1,
            notification_enabled=True
        )
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)

        response = client.delete(f"/api/emergency/contacts/{contact.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证删除
        deleted = db_session.query(EmergencyContact).filter(
            EmergencyContact.id == contact.id
        ).first()
        assert deleted is None


class TestSOSAPI:
    """SOS触发API测试"""

    def test_trigger_sos(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试触发SOS"""
        family_member = FamilyMember(
            user_id=sample_user.id,
            name='紧急联系人',
            phone='13800138000',
            openid='notify-openid',
            is_primary=True,
        )
        db_session.add(family_member)
        db_session.commit()
        db_session.refresh(family_member)

        family_auth = UserAuth(
            username='13912345678',
            password_hash='hashed',
            role='family',
            family_id=family_member.id,
            is_active=True,
        )
        db_session.add(family_auth)
        db_session.commit()
        db_session.refresh(family_auth)

        db_session.add(EmergencyContact(
            user_id=sample_user.id,
            name='紧急联系人',
            phone='13800138000',
            relation_type='儿子',
            is_primary=True,
            notify_order=1,
            notification_enabled=True
        ))
        db_session.commit()

        payload = {
            "description": "紧急求助测试",
            "latitude": 39.9042,
            "longitude": 116.4074,
            "address": "北京市东城区"
        }
        response = client.post(
            f"/api/emergency/sos?user_id={sample_user.id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "event_id" in data
        assert data["notified_contacts"] >= 1

        # 验证事件创建
        event = db_session.query(EmergencyEvent).filter(
            EmergencyEvent.user_id == sample_user.id,
            EmergencyEvent.emergency_type == "sos"
        ).first()
        assert event is not None
        assert event.severity == "critical"

        family_notifications = db_session.query(Notification).filter(
            Notification.user_id == family_auth.id,
            Notification.is_deleted == False
        ).all()
        assert len(family_notifications) >= 1
        assert any(n.notification_type == 'emergency' for n in family_notifications)

    def test_quick_sos(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试一键SOS"""
        # 创建联系人
        db_session.add(EmergencyContact(
            user_id=sample_user.id,
            name="快速联系人",
            phone="13800138000",
            relation_type="子女",
            is_primary=True,
            notify_order=1,
            notification_enabled=True
        ))
        db_session.commit()

        response = client.post(f"/api/emergency/quick-sos/{sample_user.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "紧急求助已发送" in data["message"]


class TestDeviceEmergencyAccess:
    """设备端权限测试"""

    def test_device_can_trigger_sos_for_bound_elder(
        self,
        client: TestClient,
        db_session: Session,
        sample_user: User,
        sample_device_auth,
        device_auth_headers,
    ):
        db_session.add(EmergencyContact(
            user_id=sample_user.id,
            name='设备联系人',
            phone='13800138000',
            relation_type='子女',
            is_primary=True,
            notify_order=1,
            notification_enabled=True
        ))
        db_session.commit()

        response = client.post(
            f"/api/emergency/sos?user_id={sample_user.id}",
            json={"description": "设备触发SOS"},
            headers=device_auth_headers,
        )
        assert response.status_code == 200

    def test_device_cannot_trigger_sos_for_other_elder(
        self,
        client: TestClient,
        db_session: Session,
        sample_user: User,
        device_auth_headers,
    ):
        other_user = User(name='其他老人', device_id='other-device', dialect='mandarin')
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        response = client.post(
            f"/api/emergency/sos?user_id={other_user.id}",
            json={"description": "非法设备SOS"},
            headers=device_auth_headers,
        )
        assert response.status_code == 403

    def test_device_can_trigger_fall_alert_for_bound_elder(
        self,
        client: TestClient,
        db_session: Session,
        sample_user: User,
        device_auth_headers,
    ):
        db_session.add(EmergencyContact(
            user_id=sample_user.id,
            name='跌倒联系人',
            phone='13800138000',
            relation_type='子女',
            is_primary=True,
            notify_order=1,
            notification_enabled=True
        ))
        db_session.commit()

        response = client.post(
            f"/api/emergency/fall-alert?user_id={sample_user.id}",
            json={"confidence": 0.95, "device_id": "speaker-test-001"},
            headers=device_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["emergency_type"] == "fall"

    def test_device_cannot_manage_contacts(
        self,
        client: TestClient,
        sample_user: User,
        device_auth_headers,
    ):
        response = client.get(
            f"/api/emergency/contacts/{sample_user.id}",
            headers=device_auth_headers,
        )
        assert response.status_code == 403

    def test_device_cannot_report_safe(
        self,
        client: TestClient,
        sample_user: User,
        device_auth_headers,
    ):
        response = client.post(
            f"/api/emergency/i-am-safe/{sample_user.id}",
            headers=device_auth_headers,
        )
        assert response.status_code == 403


class TestFallAlertAPI:
    """跌倒告警API测试"""

    def test_trigger_fall_alert(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试触发跌倒告警"""
        # 创建联系人
        db_session.add(EmergencyContact(
            user_id=sample_user.id,
            name="跌倒通知联系人",
            phone="13800138000",
            relation_type="子女",
            is_primary=True,
            notify_order=1,
            notification_enabled=True
        ))
        db_session.commit()

        payload = {
            "confidence": 0.95,
            "latitude": 39.9042,
            "longitude": 116.4074,
            "device_id": "watch-001"
        }
        response = client.post(
            f"/api/emergency/fall-alert?user_id={sample_user.id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["emergency_type"] == "fall"
        assert data["severity"] == "critical"


class TestHealthAlertAPI:
    """健康异常告警API测试"""

    def test_trigger_health_alert_high_bp(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试触发高血压告警"""
        db_session.add(EmergencyContact(
            user_id=sample_user.id,
            name="健康告警联系人",
            phone="13800138000",
            relation_type="子女",
            is_primary=True,
            notify_order=1,
            notification_enabled=True
        ))
        db_session.commit()

        payload = {
            "systolic": 185,
            "diastolic": 125
        }
        response = client.post(
            f"/api/emergency/health-alert?user_id={sample_user.id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["severity"] == "critical"
        assert "血压危急" in data["description"]

    def test_trigger_health_alert_low_oxygen(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试触发低血氧告警"""
        db_session.add(EmergencyContact(
            user_id=sample_user.id,
            name="血氧联系人",
            phone="13800138000",
            relation_type="子女",
            is_primary=True,
            notify_order=1,
            notification_enabled=True
        ))
        db_session.commit()

        payload = {
            "blood_oxygen": 88
        }
        response = client.post(
            f"/api/emergency/health-alert?user_id={sample_user.id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["severity"] == "critical"
        assert "血氧危险" in data["description"]

    def test_trigger_health_alert_no_abnormal(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试无异常指标时不触发告警"""
        response = client.post(
            f"/api/emergency/health-alert?user_id={sample_user.id}",
            json={},
            headers=auth_headers
        )
        assert response.status_code == 400


class TestEventManagementAPI:
    """事件管理API测试"""

    def test_get_events(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试获取紧急事件列表"""
        # 创建测试事件
        db_session.add(EmergencyEvent(
            user_id=sample_user.id,
            emergency_type="sos",
            severity="critical",
            description="测试SOS",
            trigger_source="manual",
            status="triggered",
            triggered_at=datetime.now()
        ))
        db_session.commit()

        response = client.get(f"/api/emergency/events/{sample_user.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert len(data["events"]) >= 1

    def test_get_active_events(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试获取活跃事件"""
        # 创建活跃和已解决的事件
        db_session.add(EmergencyEvent(
            user_id=sample_user.id,
            emergency_type="sos",
            severity="critical",
            description="活跃事件",
            trigger_source="manual",
            status="triggered",
            triggered_at=datetime.now()
        ))
        db_session.add(EmergencyEvent(
            user_id=sample_user.id,
            emergency_type="fall",
            severity="critical",
            description="已解决事件",
            trigger_source="device",
            status="resolved",
            triggered_at=datetime.now() - timedelta(hours=1),
            resolved_at=datetime.now()
        ))
        db_session.commit()

        response = client.get(f"/api/emergency/events/active/{sample_user.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "active_events" in data
        for event in data["active_events"]:
            assert event["status"] in ["triggered", "notifying", "responding"]

    def test_get_event_detail(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试获取事件详情"""
        event = EmergencyEvent(
            user_id=sample_user.id,
            emergency_type="sos",
            severity="critical",
            description="详情测试事件",
            trigger_source="manual",
            status="triggered",
            latitude=39.9042,
            longitude=116.4074,
            address="测试地址",
            triggered_at=datetime.now()
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        response = client.get(f"/api/emergency/event/{event.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["emergency_type"] == "sos"
        assert data["severity"] == "critical"
        assert "notifications" in data

    def test_acknowledge_event(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试确认事件"""
        event = EmergencyEvent(
            user_id=sample_user.id,
            emergency_type="fall",
            severity="critical",
            description="确认测试事件",
            trigger_source="device",
            status="notifying",
            triggered_at=datetime.now()
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        response = client.post(
            f"/api/emergency/event/{event.id}/acknowledge",
            json={"handler": "张三", "notes": "已收到，正在赶往"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "response_time_seconds" in data

        # 验证状态
        db_session.refresh(event)
        assert event.status == "responding"
        assert event.first_response_at is not None

    def test_resolve_event(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试解决事件"""
        event = EmergencyEvent(
            user_id=sample_user.id,
            emergency_type="sos",
            severity="critical",
            description="解决测试事件",
            trigger_source="manual",
            status="responding",
            triggered_at=datetime.now() - timedelta(minutes=10)
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        response = client.post(
            f"/api/emergency/event/{event.id}/resolve",
            json={"handler": "李四", "notes": "老人安全，已确认无恙"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证状态
        db_session.refresh(event)
        assert event.status == "resolved"
        assert event.resolved_by == "李四"

    def test_cancel_event(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试取消事件"""
        event = EmergencyEvent(
            user_id=sample_user.id,
            emergency_type="sos",
            severity="critical",
            description="取消测试事件",
            trigger_source="manual",
            status="triggered",
            triggered_at=datetime.now()
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        response = client.post(
            f"/api/emergency/event/{event.id}/cancel?reason=误触发",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证状态
        db_session.refresh(event)
        assert event.status == "cancelled"

    def test_mark_false_alarm(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试标记误报"""
        event = EmergencyEvent(
            user_id=sample_user.id,
            emergency_type="fall",
            severity="critical",
            description="误报测试事件",
            trigger_source="device",
            status="responding",
            triggered_at=datetime.now()
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        response = client.post(
            f"/api/emergency/event/{event.id}/false-alarm?reason=设备误判",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证状态
        db_session.refresh(event)
        assert event.status == "false_alarm"
        assert event.is_false_alarm is True


class TestReportSafeAPI:
    """报平安API测试"""

    def test_report_safe(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试报平安"""
        # 创建活跃事件
        db_session.add(EmergencyEvent(
            user_id=sample_user.id,
            emergency_type="sos",
            severity="critical",
            description="活跃SOS",
            trigger_source="manual",
            status="triggered",
            triggered_at=datetime.now()
        ))
        db_session.add(EmergencyEvent(
            user_id=sample_user.id,
            emergency_type="fall",
            severity="critical",
            description="活跃跌倒",
            trigger_source="device",
            status="notifying",
            triggered_at=datetime.now()
        ))
        db_session.commit()

        response = client.post(f"/api/emergency/i-am-safe/{sample_user.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cancelled_events"] == 2

        # 验证所有事件已取消
        active = db_session.query(EmergencyEvent).filter(
            EmergencyEvent.user_id == sample_user.id,
            EmergencyEvent.status.in_(["triggered", "notifying", "responding"])
        ).count()
        assert active == 0


class TestEmergencyStatisticsAPI:
    """紧急事件统计API测试"""

    def test_get_statistics(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试获取统计"""
        # 创建测试数据
        for i in range(5):
            db_session.add(EmergencyEvent(
                user_id=sample_user.id,
                emergency_type="sos" if i % 2 == 0 else "fall",
                severity="critical" if i < 3 else "high",
                description=f"统计测试事件{i}",
                trigger_source="manual",
                status="resolved",
                is_false_alarm=i == 4,
                triggered_at=datetime.now() - timedelta(days=i),
                resolved_at=datetime.now() - timedelta(days=i) + timedelta(minutes=5),
                response_time_seconds=300
            ))
        db_session.commit()

        response = client.get(f"/api/emergency/statistics/{sample_user.id}?days=30", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data
        assert "by_type" in data
        assert "by_severity" in data
        assert "false_alarm_count" in data
        assert "average_response_time_seconds" in data
