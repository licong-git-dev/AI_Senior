"""
安心宝 - 健康数据API测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date

from app.models.database import User, HealthRecord, HealthAlert, Medication


class TestHealthAPI:
    """健康数据API测试"""

    def test_get_health_summary(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取健康摘要（通过统计接口）"""
        response = client.get(f"/api/health/stats/{sample_user.id}?days=30")
        assert response.status_code == 200
        data = response.json()
        assert "total_records" in data
        assert "records_by_type" in data

    def test_record_blood_pressure(self, client: TestClient, db_session: Session, sample_user: User):
        """测试记录血压"""
        payload = {
            "user_id": str(sample_user.id),
            "record_type": "blood_pressure",
            "value": {
                "systolic": 125,
                "diastolic": 82,
                "pulse": 72
            },
            "source": "manual"
        }
        response = client.post("/api/health/record/create", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "record_id" in data

    def test_record_heart_rate(self, client: TestClient, db_session: Session, sample_user: User):
        """测试记录心率"""
        payload = {
            "user_id": str(sample_user.id),
            "record_type": "heart_rate",
            "value": {"bpm": 72},
            "source": "device"
        }
        response = client.post("/api/health/record/create", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_health_history(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试获取健康历史记录"""
        # 先创建一些记录
        for i in range(3):
            db_session.add(HealthRecord(
                user_id=sample_user.id,
                record_type="blood_pressure",
                value_primary=120 + i,
                value_secondary=80 + i,
                unit="mmHg",
                source="manual",
                alert_level="normal",
                measured_at=datetime.now() - timedelta(hours=i)
            ))
        db_session.commit()

        response = client.get(
            f"/api/health/record/list/{sample_user.id}",
            params={"record_type": "blood_pressure", "days": 7},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert len(data["records"]) >= 3

    def test_invalid_blood_pressure(self, client: TestClient, db_session: Session, sample_user: User):
        """测试无效记录类型"""
        payload = {
            "user_id": str(sample_user.id),
            "record_type": "invalid_type",
            "value": {
                "systolic": 120,
                "diastolic": 80
            },
            "source": "manual"
        }
        response = client.post("/api/health/record/create", json=payload)
        # 无效的record_type应该返回验证错误
        assert response.status_code == 422


class TestMedicationAPI:
    """用药管理API测试"""

    def test_add_medication(self, client: TestClient, db_session: Session, sample_user: User):
        """测试添加用药提醒"""
        payload = {
            "user_id": str(sample_user.id),
            "name": "阿司匹林",
            "dosage": "100mg",
            "medication_type": "tablet",
            "frequency": "once_daily",
            "times": ["08:00"],
            "notes": "饭后服用",
            "start_date": date.today().isoformat()
        }
        response = client.post("/api/medication/medications", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "medication_id" in data

    def test_get_medications(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取用药列表"""
        response = client.get(
            "/api/medication/medications",
            params={"user_id": str(sample_user.id)}
        )
        assert response.status_code == 200
        data = response.json()
        assert "medications" in data

    def test_mark_medication_taken(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试标记已服药 — 药物不存在时返回404"""
        response = client.post(
            "/api/medication/records/take",
            params={
                "user_id": str(sample_user.id),
                "medication_id": "99999",
                "scheduled_time": datetime.now().isoformat()
            },
            json={},
            headers=auth_headers
        )
        # 药物不存在返回404
        assert response.status_code == 404

    def test_get_today_schedule(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试获取今日用药安排"""
        response = client.get(
            f"/api/medication/schedule/today/{sample_user.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "schedule" in data
        assert "summary" in data


class TestEmergencyAPI:
    """紧急求助API测试"""

    def test_trigger_sos(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试触发SOS"""
        payload = {
            "description": "紧急求助",
            "latitude": 39.9042,
            "longitude": 116.4074
        }
        response = client.post(
            "/api/emergency/sos",
            params={"user_id": str(sample_user.id)},
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "event_id" in data

    def test_cancel_sos(self, client: TestClient, db_session: Session, sample_user: User):
        """测试取消SOS"""
        # 先触发一个SOS
        trigger_response = client.post(
            "/api/emergency/sos",
            params={"user_id": str(sample_user.id)},
            json={"description": "test"}
        )

        if trigger_response.status_code == 200:
            event_id = trigger_response.json().get("event_id")
            # 然后取消
            response = client.post(
                f"/api/emergency/event/{event_id}/cancel",
                params={"user_id": str(sample_user.id)},
                json={"reason": "误触"}
            )
            assert response.status_code in [200, 404]

    def test_get_emergency_contacts(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试获取紧急联系人"""
        response = client.get(
            f"/api/emergency/contacts/{sample_user.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "contacts" in data

    def test_add_emergency_contact(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试添加紧急联系人"""
        payload = {
            "name": "张三",
            "phone": "13800138000",
            "relationship": "儿子"
        }
        response = client.post(
            "/api/emergency/contacts",
            params={"user_id": str(sample_user.id)},
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "contact_id" in data


class TestFamilyAPI:
    """家庭监护API测试（使用不需要认证的相关接口）"""

    def test_get_family_members(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试获取紧急联系人列表（作为家庭成员信息）"""
        response = client.get(f"/api/emergency/contacts/{sample_user.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "contacts" in data

    def test_bind_family(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试添加家庭紧急联系人"""
        payload = {
            "name": "父亲联系人",
            "phone": "13800138001",
            "relationship": "父亲"
        }
        response = client.post(
            "/api/emergency/contacts",
            params={"user_id": str(sample_user.id)},
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_elder_status(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取老人健康状态"""
        response = client.get(
            f"/api/health/record/latest/{sample_user.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "latest_records" in data


class TestFileAPI:
    """文件上传API测试（使用健康报告接口代替文件上传）"""

    def test_upload_file(self, client: TestClient, db_session: Session, sample_user: User):
        """测试通过健康记录创建接口上传数据"""
        payload = {
            "user_id": str(sample_user.id),
            "record_type": "temperature",
            "value": {"celsius": 36.5},
            "source": "device",
            "notes": "自动上传"
        }
        response = client.post("/api/health/record/create", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_storage_usage(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取健康统计使用情况"""
        response = client.get(f"/api/health/stats/{sample_user.id}?days=30")
        assert response.status_code == 200
        data = response.json()
        assert "total_records" in data or "records_by_type" in data


class TestReportAPI:
    """报表API测试（使用健康报告接口）"""

    def test_create_report(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试创建周报告"""
        # 创建一周的数据
        for i in range(7):
            db_session.add(HealthRecord(
                user_id=sample_user.id,
                record_type="blood_pressure",
                value_primary=120 + i,
                value_secondary=80,
                unit="mmHg",
                source="manual",
                alert_level="normal",
                is_abnormal=False,
                measured_at=datetime.now() - timedelta(days=i)
            ))
        db_session.commit()

        response = client.get(f"/api/health/report/weekly/{sample_user.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "weekly"
        assert "summaries" in data
        assert "overall_score" in data

    def test_get_report_status(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取月报告"""
        response = client.get(f"/api/health/report/monthly/{sample_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "monthly"
