"""
用药管理API单元测试
测试用药计划、服药记录、依从性统计等功能
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
import json

from app.models.database import (
    Medication, MedicationRecord, User
)


class TestMedicationPlanAPI:
    """用药计划API测试"""

    def test_create_medication(self, client: TestClient, db_session: Session, sample_user: User):
        """测试创建用药计划"""
        payload = {
            "user_id": str(sample_user.id),
            "name": "阿司匹林",
            "dosage": "100mg",
            "medication_type": "tablet",
            "frequency": "once_daily",
            "times": ["08:00"],
            "instructions": "饭后服用，多喝水",
            "start_date": date.today().isoformat()
        }
        response = client.post("/api/medication/medications", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "medication_id" in data

        # 验证数据库
        med = db_session.query(Medication).filter(
            Medication.user_id == sample_user.id,
            Medication.name == "阿司匹林"
        ).first()
        assert med is not None
        assert med.dosage == "100mg"

    def test_create_medication_multiple_times(self, client: TestClient, db_session: Session, sample_user: User):
        """测试创建多次服药的用药计划"""
        payload = {
            "user_id": str(sample_user.id),
            "name": "降压药",
            "dosage": "1片",
            "medication_type": "tablet",
            "frequency": "twice_daily",
            "times": ["08:00", "20:00"],
            "start_date": date.today().isoformat()
        }
        response = client.post("/api/medication/medications", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_medications(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取用药计划列表"""
        # 创建测试数据
        med = Medication(
            user_id=sample_user.id,
            name="测试药物",
            dosage="1片",
            medication_type="tablet",
            frequency="once_daily",
            times=json.dumps(["09:00"]),
            start_date=datetime.now(),
            is_active=True
        )
        db_session.add(med)
        db_session.commit()

        response = client.get(f"/api/medication/medications?user_id={sample_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert "medications" in data
        assert len(data["medications"]) >= 1

    def test_get_medications_active_only(self, client: TestClient, db_session: Session, sample_user: User):
        """测试只获取活跃的用药计划"""
        # 创建活跃和非活跃的药物
        db_session.add(Medication(
            user_id=sample_user.id,
            name="活跃药物",
            dosage="1片",
            medication_type="tablet",
            frequency="once_daily",
            times=json.dumps(["09:00"]),
            start_date=datetime.now(),
            is_active=True
        ))
        db_session.add(Medication(
            user_id=sample_user.id,
            name="停用药物",
            dosage="2片",
            medication_type="capsule",
            frequency="twice_daily",
            times=json.dumps(["08:00", "20:00"]),
            start_date=datetime.now(),
            is_active=False
        ))
        db_session.commit()

        response = client.get(f"/api/medication/medications?user_id={sample_user.id}&active_only=true")
        assert response.status_code == 200
        data = response.json()
        for med in data["medications"]:
            assert med["is_active"] is True

    def test_get_medication_detail(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取用药计划详情"""
        med = Medication(
            user_id=sample_user.id,
            name="详情测试药物",
            dosage="50mg",
            medication_type="capsule",
            frequency="three_times_daily",
            times=json.dumps(["08:00", "12:00", "18:00"]),
            instructions="餐前30分钟服用",
            start_date=datetime.now(),
            is_active=True
        )
        db_session.add(med)
        db_session.commit()
        db_session.refresh(med)

        response = client.get(f"/api/medication/medications/{med.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "详情测试药物"
        assert data["dosage"] == "50mg"
        assert len(data["times"]) == 3

    def test_update_medication(self, client: TestClient, db_session: Session, sample_user: User):
        """测试更新用药计划"""
        med = Medication(
            user_id=sample_user.id,
            name="更新测试药物",
            dosage="1片",
            medication_type="tablet",
            frequency="once_daily",
            times=json.dumps(["09:00"]),
            start_date=datetime.now(),
            is_active=True
        )
        db_session.add(med)
        db_session.commit()
        db_session.refresh(med)

        response = client.put(
            f"/api/medication/medications/{med.id}",
            json={
                "dosage": "2片",
                "times": ["08:00", "20:00"],
                "notes": "剂量调整"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证更新
        db_session.refresh(med)
        assert med.dosage == "2片"

    def test_disable_medication(self, client: TestClient, db_session: Session, sample_user: User):
        """测试停用用药计划"""
        med = Medication(
            user_id=sample_user.id,
            name="停用测试药物",
            dosage="1片",
            medication_type="tablet",
            frequency="once_daily",
            times=json.dumps(["09:00"]),
            start_date=datetime.now(),
            is_active=True
        )
        db_session.add(med)
        db_session.commit()
        db_session.refresh(med)

        response = client.delete(f"/api/medication/medications/{med.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证停用
        db_session.refresh(med)
        assert med.is_active is False


class TestMedicationScheduleAPI:
    """今日服药计划API测试"""

    def test_get_today_schedule(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试获取今日服药计划"""
        # 创建活跃药物
        med = Medication(
            user_id=sample_user.id,
            name="今日药物",
            dosage="1片",
            medication_type="tablet",
            frequency="twice_daily",
            times=json.dumps(["08:00", "20:00"]),
            start_date=datetime.now() - timedelta(days=7),
            is_active=True
        )
        db_session.add(med)
        db_session.commit()

        response = client.get(f"/api/medication/schedule/today/{sample_user.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "schedule" in data
        assert "summary" in data
        assert data["date"] == date.today().isoformat()

    def test_get_pending_reminders(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取待处理提醒"""
        med = Medication(
            user_id=sample_user.id,
            name="待处理药物",
            dosage="1片",
            medication_type="tablet",
            frequency="once_daily",
            times=json.dumps(["08:00"]),
            start_date=datetime.now() - timedelta(days=1),
            is_active=True
        )
        db_session.add(med)
        db_session.commit()

        response = client.get(f"/api/medication/schedule/pending/{sample_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert "pending_reminders" in data


class TestMedicationRecordAPI:
    """服药记录API测试"""

    def test_record_medication_taken(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试记录已服药"""
        med = Medication(
            user_id=sample_user.id,
            name="服药测试药物",
            dosage="1片",
            medication_type="tablet",
            frequency="once_daily",
            times=json.dumps(["08:00"]),
            start_date=datetime.now(),
            quantity=30,
            is_active=True
        )
        db_session.add(med)
        db_session.commit()
        db_session.refresh(med)

        scheduled_time = datetime.combine(date.today(), datetime.strptime("08:00", "%H:%M").time())

        response = client.post(
            "/api/medication/records/take",
            params={
                "user_id": str(sample_user.id),
                "medication_id": str(med.id),
                "scheduled_time": scheduled_time.isoformat()
            },
            json={"notes": "按时服用"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "record_id" in data
        assert data["remaining_quantity"] == 29  # 库存减1

    def test_skip_medication(self, client: TestClient, db_session: Session, sample_user: User, auth_headers):
        """测试跳过服药"""
        med = Medication(
            user_id=sample_user.id,
            name="跳过测试药物",
            dosage="1片",
            medication_type="tablet",
            frequency="once_daily",
            times=json.dumps(["08:00"]),
            start_date=datetime.now(),
            is_active=True
        )
        db_session.add(med)
        db_session.commit()
        db_session.refresh(med)

        scheduled_time = datetime.combine(date.today(), datetime.strptime("08:00", "%H:%M").time())

        response = client.post(
            "/api/medication/records/skip",
            params={
                "user_id": str(sample_user.id),
                "medication_id": str(med.id),
                "scheduled_time": scheduled_time.isoformat()
            },
            json={"reason": "外出未带药物"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_medication_records(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取服药记录"""
        med = Medication(
            user_id=sample_user.id,
            name="记录测试药物",
            dosage="1片",
            medication_type="tablet",
            frequency="once_daily",
            times=json.dumps(["08:00"]),
            start_date=datetime.now(),
            is_active=True
        )
        db_session.add(med)
        db_session.commit()
        db_session.refresh(med)

        # 创建服药记录
        for i in range(5):
            db_session.add(MedicationRecord(
                user_id=sample_user.id,
                medication_id=med.id,
                scheduled_time=datetime.now() - timedelta(days=i),
                taken_time=datetime.now() - timedelta(days=i),
                status="taken"
            ))
        db_session.commit()

        response = client.get(f"/api/medication/records/{sample_user.id}?days=7")
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert len(data["records"]) >= 5


class TestMedicationAdherenceAPI:
    """依从性统计API测试"""

    def test_get_adherence_stats(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取依从性统计"""
        med = Medication(
            user_id=sample_user.id,
            name="依从性测试药物",
            dosage="1片",
            medication_type="tablet",
            frequency="once_daily",
            times=json.dumps(["08:00"]),
            start_date=datetime.now() - timedelta(days=30),
            is_active=True
        )
        db_session.add(med)
        db_session.commit()
        db_session.refresh(med)

        # 创建服药记录（80%依从率）
        for i in range(10):
            status = "taken" if i < 8 else "missed"
            scheduled = datetime.now() - timedelta(days=i)
            db_session.add(MedicationRecord(
                user_id=sample_user.id,
                medication_id=med.id,
                scheduled_time=scheduled,
                taken_time=scheduled if status == "taken" else None,
                status=status
            ))
        db_session.commit()

        response = client.get(f"/api/medication/adherence/{sample_user.id}?days=30")
        assert response.status_code == 200
        data = response.json()
        assert "overall" in data
        assert "adherence_rate" in data["overall"]
        assert data["overall"]["adherence_rate"] == 80.0


class TestMedicationStockAPI:
    """库存管理API测试"""

    def test_update_medication_stock(self, client: TestClient, db_session: Session, sample_user: User):
        """测试更新药品库存"""
        med = Medication(
            user_id=sample_user.id,
            name="库存测试药物",
            dosage="1片",
            medication_type="tablet",
            frequency="once_daily",
            times=json.dumps(["08:00"]),
            start_date=datetime.now(),
            quantity=10,
            low_stock_threshold=7,
            is_active=True
        )
        db_session.add(med)
        db_session.commit()
        db_session.refresh(med)

        response = client.put(
            f"/api/medication/medications/{med.id}/stock",
            params={"quantity": 50, "low_stock_threshold": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["quantity"] == 50
        assert data["is_low_stock"] is False

    def test_get_stock_alerts(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取库存告警"""
        # 创建低库存药物
        db_session.add(Medication(
            user_id=sample_user.id,
            name="低库存药物",
            dosage="1片",
            medication_type="tablet",
            frequency="once_daily",
            times=json.dumps(["08:00"]),
            start_date=datetime.now(),
            quantity=5,
            low_stock_threshold=10,
            is_active=True
        ))
        db_session.commit()

        response = client.get(f"/api/medication/stock/alerts/{sample_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert "low_stock_medications" in data
        assert len(data["low_stock_medications"]) >= 1


class TestMedicationDashboardAPI:
    """用药仪表板API测试"""

    def test_get_medication_dashboard(self, client: TestClient, db_session: Session, sample_user: User):
        """测试获取用药仪表板"""
        # 创建测试数据
        med = Medication(
            user_id=sample_user.id,
            name="仪表板测试药物",
            dosage="1片",
            medication_type="tablet",
            frequency="twice_daily",
            times=json.dumps(["08:00", "20:00"]),
            start_date=datetime.now() - timedelta(days=7),
            quantity=20,
            low_stock_threshold=7,
            is_active=True
        )
        db_session.add(med)
        db_session.commit()

        response = client.get(f"/api/medication/dashboard/{sample_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert "today" in data
        assert "adherence" in data
        assert "alerts" in data
        assert "medications" in data
