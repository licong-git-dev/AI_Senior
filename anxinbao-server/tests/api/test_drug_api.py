"""
药品识别模块API测试
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import json
import base64


class TestDrugInfo:
    """药品信息测试"""

    def test_create_drug_info(self, client: TestClient, admin_auth_headers, db_session):
        """测试创建药品信息"""
        drug_data = {
            "name": "阿司匹林",
            "generic_name": "乙酰水杨酸",
            "brand_names": ["拜阿司匹灵", "阿司匹林肠溶片"],
            "barcode": "6901234567890",
            "specification": "100mg*30片",
            "dosage_form": "tablet",
            "manufacturer": "拜耳医药",
            "drug_category": "otc",
            "indications": "用于普通感冒或流行性感冒引起的发热，也用于缓解轻至中度疼痛",
            "dosage_instructions": "口服，成人一次1片，一日1-3次",
            "contraindications": "对本品过敏者禁用",
            "side_effects": "可能引起胃肠道反应",
            "elderly_precautions": "老年人应在医生指导下使用，注意胃肠道反应"
        }

        response = client.post(
            "/api/drug/drugs",
            json=drug_data,
            headers=admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "drug_id" in data

    def test_get_drug_info(self, client: TestClient, auth_headers, db_session):
        """测试获取药品信息"""
        from app.models.database import DrugInfo

        drug = DrugInfo(
            name="降压药",
            generic_name="氨氯地平",
            dosage_form="tablet",
            drug_category="prescription",
            is_active=True
        )
        db_session.add(drug)
        db_session.commit()
        db_session.refresh(drug)

        response = client.get(
            f"/api/drug/drugs/{drug.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["drug"]["name"] == "降压药"

    def test_search_drugs(self, client: TestClient, auth_headers, db_session):
        """测试搜索药品"""
        from app.models.database import DrugInfo

        drugs = [
            DrugInfo(name="阿莫西林胶囊", generic_name="阿莫西林", dosage_form="capsule", is_active=True),
            DrugInfo(name="阿奇霉素片", generic_name="阿奇霉素", dosage_form="tablet", is_active=True),
            DrugInfo(name="布洛芬缓释胶囊", generic_name="布洛芬", dosage_form="capsule", is_active=True)
        ]
        for drug in drugs:
            db_session.add(drug)
        db_session.commit()

        response = client.get(
            "/api/drug/drugs/search?keyword=阿",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2  # 阿莫西林和阿奇霉素


class TestDrugRecognition:
    """药品识别测试"""

    def test_recognize_drug_by_barcode(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试通过条形码识别药品"""
        from app.models.database import DrugInfo

        drug = DrugInfo(
            name="测试药品",
            barcode="6901234567890",
            is_active=True
        )
        db_session.add(drug)
        db_session.commit()

        request_data = {
            "user_id": sample_user.id,
            "barcode": "6901234567890"
        }

        response = client.post(
            "/api/drug/recognize",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["matched_drug"]["name"] == "测试药品"

    def test_recognize_drug_by_image(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试通过图片识别药品（模拟）"""
        # 创建一个小的测试图片base64
        fake_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        request_data = {
            "user_id": sample_user.id,
            "image_base64": fake_image
        }

        response = client.post(
            "/api/drug/recognize",
            json=request_data,
            headers=auth_headers
        )

        # OCR识别可能失败（因为是假图片），但API应该正常响应
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_correct_recognition(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试更正识别结果"""
        from app.models.database import DrugRecognitionLog, DrugInfo

        drug = DrugInfo(name="正确的药品", is_active=True)
        db_session.add(drug)
        db_session.commit()
        db_session.refresh(drug)

        log = DrugRecognitionLog(
            user_id=sample_user.id,
            recognized_text="错误识别",
            status="partial",
            recognized_at=datetime.utcnow()
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        correction_data = {
            "recognition_id": log.id,
            "correct_drug_name": "正确的药品",
            "correct_drug_id": drug.id
        }

        response = client.post(
            f"/api/drug/recognition/{log.id}/correct",
            json=correction_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_recognition_history(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取识别历史"""
        from app.models.database import DrugRecognitionLog

        for i in range(3):
            log = DrugRecognitionLog(
                user_id=sample_user.id,
                recognized_text=f"药品{i}",
                status="success",
                recognized_at=datetime.utcnow() - timedelta(days=i)
            )
            db_session.add(log)
        db_session.commit()

        response = client.get(
            f"/api/drug/recognition-logs/{sample_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) == 3


class TestDrugInteractions:
    """药物相互作用测试"""

    @pytest.fixture
    def sample_drugs(self, db_session):
        """创建测试药品"""
        from app.models.database import DrugInfo

        drugs = [
            DrugInfo(name="华法林", generic_name="华法林钠", is_active=True),
            DrugInfo(name="阿司匹林", generic_name="乙酰水杨酸", is_active=True),
            DrugInfo(name="布洛芬", generic_name="布洛芬", is_active=True)
        ]
        for drug in drugs:
            db_session.add(drug)
        db_session.commit()

        for drug in drugs:
            db_session.refresh(drug)
        return drugs

    def test_create_drug_interaction(self, client: TestClient, admin_auth_headers, sample_drugs, db_session):
        """测试创建药物相互作用记录"""
        interaction_data = {
            "drug_a_id": sample_drugs[0].id,  # 华法林
            "drug_b_id": sample_drugs[1].id,  # 阿司匹林
            "interaction_type": "major",
            "severity": "high",
            "description": "同时使用可能增加出血风险",
            "recommendation": "避免同时使用，如必须使用需密切监测"
        }

        response = client.post(
            "/api/drug/interactions",
            json=interaction_data,
            headers=admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "interaction_id" in data

    def test_check_drug_interactions(self, client: TestClient, auth_headers, sample_user, sample_drugs, db_session):
        """测试检查药物相互作用"""
        from app.models.database import DrugInteraction

        # 创建相互作用记录
        interaction = DrugInteraction(
            drug_a_id=sample_drugs[0].id,
            drug_b_id=sample_drugs[1].id,
            interaction_type="major",
            severity="high",
            description="有相互作用"
        )
        db_session.add(interaction)
        db_session.commit()

        request_data = {
            "user_id": sample_user.id,
            "drug_ids": [sample_drugs[0].id, sample_drugs[1].id]
        }

        response = client.post(
            "/api/drug/check-interactions",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_interactions"] is True
        assert data["total_interactions"] >= 1

    def test_check_all_medications_interactions(self, client: TestClient, auth_headers, sample_user, sample_drugs, db_session):
        """测试检查用户所有用药的相互作用"""
        from app.models.database import Medication, DrugInteraction

        # 为用户添加用药记录
        for drug in sample_drugs[:2]:
            med = Medication(
                user_id=sample_user.id,
                name=drug.name,
                dosage="1片",
                frequency="once_daily",
                start_date=datetime.utcnow(),
                is_active=True
            )
            db_session.add(med)

        # 添加相互作用
        interaction = DrugInteraction(
            drug_a_id=sample_drugs[0].id,
            drug_b_id=sample_drugs[1].id,
            interaction_type="moderate",
            severity="medium"
        )
        db_session.add(interaction)
        db_session.commit()

        request_data = {
            "user_id": sample_user.id,
            "check_all_medications": True
        }

        response = client.post(
            "/api/drug/check-interactions",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "has_interactions" in data


class TestElderlyDrugTips:
    """老年人用药提示测试"""

    def test_get_elderly_drug_tips(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取老年人用药提示"""
        from app.models.database import DrugInfo

        drug = DrugInfo(
            name="测试药品",
            elderly_precautions="老年人应减量使用，注意监测肾功能",
            contraindications="肾功能不全者慎用",
            side_effects="可能引起头晕",
            is_active=True
        )
        db_session.add(drug)
        db_session.commit()
        db_session.refresh(drug)

        response = client.get(
            f"/api/drug/elderly-tips/{drug.id}?user_id={sample_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "general_tips" in data
        assert len(data["general_tips"]) > 0

    def test_get_personalized_elderly_tips(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试获取个性化的老年人用药提示"""
        from app.models.database import DrugInfo, UserProfile
        import json

        # 创建用户画像
        user_profile = UserProfile(
            user_id=sample_user.id,
            chronic_conditions=json.dumps(["高血压", "糖尿病"], ensure_ascii=False),
            allergies=json.dumps(["青霉素"], ensure_ascii=False)
        )
        db_session.add(user_profile)

        drug = DrugInfo(
            name="某降压药",
            elderly_precautions="老年高血压患者使用需监测血压",
            contraindications="糖尿病患者慎用",
            is_active=True
        )
        db_session.add(drug)
        db_session.commit()
        db_session.refresh(drug)

        response = client.get(
            f"/api/drug/elderly-tips/{drug.id}?user_id={sample_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "personalized_tips" in data


class TestAddToMedication:
    """添加到用药计划测试"""

    def test_add_recognition_to_medication(self, client: TestClient, auth_headers, sample_user, db_session):
        """测试将识别结果添加到用药计划"""
        from app.models.database import DrugRecognitionLog, DrugInfo

        drug = DrugInfo(name="测试药品", is_active=True)
        db_session.add(drug)
        db_session.commit()
        db_session.refresh(drug)

        log = DrugRecognitionLog(
            user_id=sample_user.id,
            drug_info_id=drug.id,
            matched_name=drug.name,
            status="success",
            recognized_at=datetime.utcnow()
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        request_data = {
            "recognition_id": log.id,
            "dosage": "1片",
            "frequency": "twice_daily",
            "times": ["08:00", "20:00"],
            "instructions": "饭后服用"
        }

        response = client.post(
            f"/api/drug/recognition/{log.id}/add-to-medication",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "medication_id" in data


class TestDrugCategories:
    """药品分类测试"""

    def test_get_drugs_by_category(self, client: TestClient, auth_headers, db_session):
        """测试按分类获取药品"""
        from app.models.database import DrugInfo

        drugs = [
            DrugInfo(name="感冒药", drug_category="otc", is_active=True),
            DrugInfo(name="抗生素", drug_category="prescription", is_active=True),
            DrugInfo(name="中成药", drug_category="chinese_medicine", is_active=True)
        ]
        for drug in drugs:
            db_session.add(drug)
        db_session.commit()

        response = client.get(
            "/api/drug/drugs/search?keyword=感冒药&category=otc",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(d["name"] == "感冒药" for d in data["drugs"])
