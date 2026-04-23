"""
健康管理API单元测试
测试健康数据记录、告警、趋势、报告等功能
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.database import (
    HealthRecord, HealthAlert, HealthReport, User
)


class TestHealthRecordAPI:
    """健康数据记录API测试"""

    def test_create_blood_pressure_record(self, client: TestClient, db_session: Session, sample_user: User):
        """测试创建血压记录"""
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
        assert data["alert_level"] == "normal"
        assert data["is_abnormal"] is False

    def test_create_high_blood_pressure_record(self, client: TestClient, db_session: Session, sample_user: User):
        """测试创建高血压记录（应触发告警）"""
        payload = {
            "user_id": str(sample_user.id),
            "record_type": "blood_pressure",
            "value": {
                "systolic": 185,
                "diastolic": 125
            },
            "source": "manual"
        }
        response = client.post("/api/health/record/create", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["alert_level"] == "critical"
        assert data["is_abnormal"] is True

        # 验证告警已创建
        alerts = db_session.query(HealthAlert).filter(
            HealthAlert.user_id == sample_user.id
        ).all()
        assert len(alerts) >= 1

    def test_create_heart_rate_record(self, client: TestClient, db_session: Session, sample_user: User):
        """测试创建心率记录"""
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
        assert data["alert_level"] == "normal"

    def test_create_blood_sugar_record(self, client: TestClient, db_session: Session, sample_user: User):
        """测试创建血糖记录"""
        payload = {
            "user_id": str(sample_user.id),
            "record_type": "blood_sugar",
            "value": {"value": 5.8, "is_fasting": True},
            "source": "manual"
        }
        response = client.post("/api/health/record/create", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_create_blood_oxygen_record(self, client: TestClient, db_session: Session, sample_user: User):
        """测试创建血氧记录"""
        payload = {
            "user_id": str(sample_user.id),
            "record_type": "blood_oxygen",
            "value": {"spo2": 98},
            "source": "device"
        }
        response = client.post("/api/health/record/create", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["alert_level"] == "normal"

    def test_create_low_blood_oxygen_record(self, client: TestClient, db_session: Session, sample_user: User):
        """测试创建低血氧记录（应触发告警）"""
        payload = {
            "user_id": str(sample_user.id),
            "record_type": "blood_oxygen",
            "value": {"spo2": 88},
            "source": "device"
        }
        response = client.post("/api/health/record/create", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["alert_level"] == "critical"
        assert data["is_abnormal"] is True

    def test_get_health_records(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试获取健康记录列表"""
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

        response = client.get(f"/api/health/record/list/{sample_user.id}?days=7", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(sample_user.id)
        assert "records" in data
        assert len(data["records"]) >= 3

    def test_get_health_records_by_type(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试按类型获取健康记录"""
        # 创建不同类型的记录
        db_session.add(HealthRecord(
            user_id=sample_user.id,
            record_type="blood_pressure",
            value_primary=120,
            value_secondary=80,
            unit="mmHg",
            source="manual",
            alert_level="normal",
            measured_at=datetime.now()
        ))
        db_session.add(HealthRecord(
            user_id=sample_user.id,
            record_type="heart_rate",
            value_primary=72,
            unit="bpm",
            source="manual",
            alert_level="normal",
            measured_at=datetime.now()
        ))
        db_session.commit()

        response = client.get(f"/api/health/record/list/{sample_user.id}?record_type=blood_pressure", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        for record in data["records"]:
            assert record["record_type"] == "blood_pressure"

    def test_get_latest_health_data(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取最新健康数据"""
        # 创建记录
        db_session.add(HealthRecord(
            user_id=sample_user.id,
            record_type="blood_pressure",
            value_primary=120,
            value_secondary=80,
            unit="mmHg",
            source="manual",
            alert_level="normal",
            measured_at=datetime.now()
        ))
        db_session.commit()

        response = client.get(f"/api/health/record/latest/{sample_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert "latest_records" in data
        assert "blood_pressure" in data["latest_records"]

    def test_get_single_record(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取单条记录"""
        record = HealthRecord(
            user_id=sample_user.id,
            record_type="heart_rate",
            value_primary=75,
            unit="bpm",
            source="manual",
            alert_level="normal",
            measured_at=datetime.now()
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        response = client.get(f"/api/health/record/{record.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(record.id)
        assert data["record_type"] == "heart_rate"

    def test_update_health_record(self, client: TestClient, db_session: Session, sample_user: User):
        """测试更新健康记录"""
        record = HealthRecord(
            user_id=sample_user.id,
            record_type="blood_pressure",
            value_primary=120,
            value_secondary=80,
            unit="mmHg",
            source="manual",
            alert_level="normal",
            measured_at=datetime.now()
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        response = client.put(
            f"/api/health/record/{record.id}",
            json={"value": {"systolic": 125, "diastolic": 85}, "notes": "饭后测量"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_health_record(self, client: TestClient, db_session: Session, sample_user: User):
        """测试删除健康记录"""
        record = HealthRecord(
            user_id=sample_user.id,
            record_type="temperature",
            value_primary=36.5,
            unit="°C",
            source="manual",
            alert_level="normal",
            measured_at=datetime.now()
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        response = client.delete(f"/api/health/record/{record.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证记录已删除
        deleted = db_session.query(HealthRecord).filter(HealthRecord.id == record.id).first()
        assert deleted is None

    def test_get_nonexistent_record(self, client: TestClient):
        """测试获取不存在的记录"""
        response = client.get("/api/health/record/99999")
        assert response.status_code == 404


class TestHealthTrendAPI:
    """健康趋势API测试"""

    def test_get_health_trend(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试获取健康趋势"""
        # 创建多日数据
        for i in range(10):
            db_session.add(HealthRecord(
                user_id=sample_user.id,
                record_type="blood_pressure",
                value_primary=120 + (i % 5),
                value_secondary=80 + (i % 3),
                unit="mmHg",
                source="manual",
                alert_level="normal",
                measured_at=datetime.now() - timedelta(days=i)
            ))
        db_session.commit()

        response = client.get(f"/api/health/trend/{sample_user.id}/blood_pressure?days=30", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "trend" in data
        assert "overall_trend" in data
        assert data["record_type"] == "blood_pressure"


class TestHealthAlertAPI:
    """健康告警API测试"""

    def test_get_health_alerts(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取健康告警列表"""
        # 创建告警
        db_session.add(HealthAlert(
            user_id=sample_user.id,
            alert_type="blood_pressure_abnormal",
            level="high",
            title="血压偏高",
            content="收缩压145mmHg",
            is_read=False,
            is_handled=False
        ))
        db_session.commit()

        response = client.get(f"/api/health/alert/list/{sample_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert len(data["alerts"]) >= 1

    def test_mark_alert_read(self, client: TestClient, db_session: Session, sample_user: User):
        """测试标记告警已读"""
        alert = HealthAlert(
            user_id=sample_user.id,
            alert_type="heart_rate_abnormal",
            level="medium",
            title="心率偏快",
            content="心率105bpm",
            is_read=False,
            is_handled=False
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)

        response = client.put(f"/api/health/alert/{alert.id}/read")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证状态
        db_session.refresh(alert)
        assert alert.is_read is True

    def test_handle_alert(self, client: TestClient, db_session: Session, sample_user: User):
        """测试处理告警"""
        alert = HealthAlert(
            user_id=sample_user.id,
            alert_type="blood_sugar_high",
            level="high",
            title="血糖偏高",
            content="空腹血糖8.5mmol/L",
            is_read=False,
            is_handled=False
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)

        response = client.put(
            f"/api/health/alert/{alert.id}/handle",
            json={"handled_by": "家属张三", "handle_notes": "已联系老人，情况稳定"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证状态
        db_session.refresh(alert)
        assert alert.is_handled is True
        assert alert.handled_by == "家属张三"


class TestHealthReportAPI:
    """健康报告API测试"""

    def test_get_weekly_report(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试获取周健康报告"""
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
        assert "recommendations" in data

    def test_get_monthly_report(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取月健康报告"""
        response = client.get(f"/api/health/report/monthly/{sample_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "monthly"


class TestHealthStatsAPI:
    """健康统计API测试"""

    def test_get_health_statistics(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取健康统计"""
        # 创建一些数据
        for i in range(5):
            db_session.add(HealthRecord(
                user_id=sample_user.id,
                record_type="blood_pressure",
                value_primary=120 + i * 10,
                value_secondary=80,
                unit="mmHg",
                source="manual",
                alert_level="normal" if i < 3 else "high",
                is_abnormal=i >= 3,
                measured_at=datetime.now() - timedelta(days=i)
            ))
        db_session.commit()

        response = client.get(f"/api/health/stats/{sample_user.id}?days=30")
        assert response.status_code == 200
        data = response.json()
        assert "total_records" in data
        assert "records_by_type" in data
        assert "abnormal_by_type" in data
