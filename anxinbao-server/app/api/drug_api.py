"""
API路由 - 药品识别模块
实现药品OCR识别、药品信息管理、药物相互作用检查等功能
"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime
import json
import base64

from app.core.deps import get_db
from app.models.database import (
    DrugInfo,
    DrugRecognitionLog,
    DrugInteraction,
    Medication,
    User
)
from app.schemas.drug import (
    RecognitionStatus,
    DrugCategory,
    InteractionSeverity,
    InteractionType,
    DrugInfoCreate,
    DrugInfoUpdate,
    DrugInfoResponse,
    DrugInfoBrief,
    RecognizeDrugRequest,
    RecognizeDrugResponse,
    CorrectRecognitionRequest,
    AddToMedicationRequest,
    DrugInteractionCreate,
    DrugInteractionResponse,
    CheckInteractionsRequest,
    CheckInteractionsResponse,
    SearchDrugsRequest,
    ElderlyDrugTipsRequest
)

router = APIRouter(prefix="/api/drug", tags=["药品识别"])


# ==================== 工具函数 ====================

def parse_json_field(value: Optional[str]) -> Optional[List]:
    """解析JSON字段"""
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def serialize_json(value) -> str:
    """序列化为JSON"""
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def drug_to_brief(drug: DrugInfo) -> dict:
    """将DrugInfo转换为简要格式"""
    return {
        'id': drug.id,
        'name': drug.name,
        "generic_name": drug.generic_name,
        "specification": drug.specification,
        "dosage_form": drug.dosage_form,
        "manufacturer": drug.manufacturer,
        'image_url': drug.image_url
    }


def drug_to_response(drug: DrugInfo) -> dict:
    """将DrugInfo转换为完整响应格式"""
    return {
        'id': drug.id,
        'name': drug.name,
        "generic_name": drug.generic_name,
        "brand_names": parse_json_field(drug.brand_names),
        'barcode': drug.barcode,
        "specification": drug.specification,
        "dosage_form": drug.dosage_form,
        "manufacturer": drug.manufacturer,
        "approval_number": drug.approval_number,
        "drug_category": drug.drug_category,
        "therapeutic_category": drug.therapeutic_category,
        "indications": drug.indications,
        "dosage_instructions": drug.dosage_instructions,
        "contraindications": drug.contraindications,
        "side_effects": drug.side_effects,
        "interactions": drug.interactions,
        "precautions": drug.precautions,
        'storage': drug.storage,
        "elderly_precautions": drug.elderly_precautions,
        'image_url': drug.image_url,
        'is_active': drug.is_active,
        'created_at': drug.created_at.isoformat(),
        'updated_at': drug.updated_at.isoformat()
    }


# ==================== 药品信息管理 ====================

@router.post("/drugs", response_model=dict)
def create_drug_info(
    request: DrugInfoCreate,
    db: Session = Depends(get_db)
):
    """创建药品信息"""
    drug = DrugInfo(
        name=request.name,
        generic_name=request.generic_name,
        brand_names=serialize_json(request.brand_names),
        barcode=request.barcode,
        specification=request.specification,
        dosage_form=request.dosage_form.value if request.dosage_form else None,
        manufacturer=request.manufacturer,
        approval_number=request.approval_number,
        drug_category=request.drug_category.value if request.drug_category else None,
        therapeutic_category=request.therapeutic_category,
        indications=request.indications,
        dosage_instructions=request.dosage_instructions,
        contraindications=request.contraindications,
        side_effects=request.side_effects,
        interactions=request.interactions,
        precautions=request.precautions,
        storage=request.storage,
        elderly_precautions=request.elderly_precautions,
        image_url=request.image_url
    )
    db.add(drug)
    db.commit()
    db.refresh(drug)

    return {
        'success': True,
        'drug_id': drug.id,
        'message': "药品信息创建成功"
    }


@router.get("/drugs/search", response_model=dict)
def search_drugs(
    keyword: str = Query(..., min_length=1),
    category: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """搜索药品"""
    query = db.query(DrugInfo).filter(
        DrugInfo.is_active == True,
        or_(
            DrugInfo.name.contains(keyword),
            DrugInfo.generic_name.contains(keyword),
            DrugInfo.brand_names.contains(keyword)
        )
    )

    if category:
        query = query.filter(DrugInfo.drug_category == category)

    drugs = query.limit(limit).all()

    return {
        'keyword': keyword,
        'drugs': [drug_to_brief(d) for d in drugs],
        'total': len(drugs)
    }


@router.get("/drugs/{drug_id}", response_model=dict)
def get_drug_info(
    drug_id: int,
    db: Session = Depends(get_db)
):
    """获取药品详情"""
    drug = db.query(DrugInfo).filter(DrugInfo.id == drug_id).first()
    if not drug:
        raise HTTPException(status_code=404, detail='药品不存在')

    return {"drug": drug_to_response(drug)}


@router.put("/drugs/{drug_id}", response_model=dict)
def update_drug_info(
    drug_id: int,
    request: DrugInfoUpdate,
    db: Session = Depends(get_db)
):
    """更新药品信息"""
    drug = db.query(DrugInfo).filter(DrugInfo.id == drug_id).first()
    if not drug:
        raise HTTPException(status_code=404, detail='药品不存在')

    update_data = request.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key == 'brand_names' and value is not None:
            setattr(drug, key, serialize_json(value))
        elif key in ['dosage_form', 'drug_category'] and value:
            setattr(drug, key, value.value if hasattr(value, 'value') else value)
        else:
            setattr(drug, key, value)

    db.commit()
    return {'success': True, 'message': "更新成功"}


@router.get("/drugs/by-barcode/{barcode}", response_model=dict)
def get_drug_by_barcode(
    barcode: str,
    db: Session = Depends(get_db)
):
    """通过条形码查询药品"""
    drug = db.query(DrugInfo).filter(
        DrugInfo.barcode == barcode,
        DrugInfo.is_active == True
    ).first()

    if not drug:
        return {'found': False, 'barcode': barcode}

    return {
        'found': True,
        'drug': drug_to_response(drug)
    }


# ==================== 药品识别 ====================

@router.post("/recognize", response_model=dict)
def recognize_drug(
    request: RecognizeDrugRequest,
    db: Session = Depends(get_db)
):
    """识别药品（模拟OCR识别）"""
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    now = datetime.now()
    recognized_text = None
    matched_drug = None
    confidence = None
    status = RecognitionStatus.FAILED
    suggestions = []

    # 如果提供了条形码，直接查询
    if request.barcode:
        drug = db.query(DrugInfo).filter(
            DrugInfo.barcode == request.barcode,
            DrugInfo.is_active == True
        ).first()
        if drug:
            matched_drug = drug
            confidence = 1.0
            status = RecognitionStatus.SUCCESS

    # 如果提供了图片，模拟OCR识别
    elif request.image_base64 or request.image_url:
        # 这里是模拟OCR识别
        # 实际应该调用OCR服务（如百度OCR、腾讯OCR等）
        recognized_text = "模拟识别文本：阿司匹林肠溶片"

        # 简单的关键词匹配
        keywords = ['阿司匹林', '布洛芬', '降压', '降糖', '感冒']
        for kw in keywords:
            if kw in recognized_text:
                drugs = db.query(DrugInfo).filter(
                    DrugInfo.is_active == True,
                    or_(
                        DrugInfo.name.contains(kw),
                        DrugInfo.generic_name.contains(kw)
                    )
                ).limit(5).all()

                if drugs:
                    matched_drug = drugs[0]
                    confidence = 0.8
                    status = RecognitionStatus.SUCCESS
                    suggestions = drugs[1:] if len(drugs) > 1 else []
                break

        if not matched_drug:
            status = RecognitionStatus.PARTIAL
            confidence = 0.3

    # 记录识别日志
    log = DrugRecognitionLog(
        user_id=request.user_id,
        image_url=request.image_url,
        recognized_text=recognized_text,
        barcode=request.barcode,
        drug_info_id=matched_drug.id if matched_drug else None,
        matched_name=matched_drug.name if matched_drug else None,
        confidence=confidence,
        status=status.value,
        recognized_at=now
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return {
        'success': status == RecognitionStatus.SUCCESS,
        "status": status.value,
        "recognition_id": log.id,
        "recognized_text": recognized_text,
        "matched_drug": drug_to_brief(matched_drug) if matched_drug else None,
        'confidence': confidence,
        "suggestions": [drug_to_brief(d) for d in suggestions] if suggestions else None,
        'message': '识别成功' if matched_drug else "未能识别，请手动输入"
    }


@router.get("/recognition-logs/{user_id}", response_model=dict)
def get_recognition_logs(
    user_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取用户的识别历史"""
    logs = db.query(DrugRecognitionLog).filter(
        DrugRecognitionLog.user_id == user_id
    ).order_by(DrugRecognitionLog.recognized_at.desc()).limit(limit).all()

    return {
        'user_id': user_id,
        'logs': [
            {
                'id': log.id,
                "matched_name": log.matched_name,
                'status': log.status,
                'confidence': log.confidence,
                "added_to_medication": log.added_to_medication,
                "recognized_at": log.recognized_at.isoformat()
            }
            for log in logs
        ],
        'total': len(logs)
    }


@router.post("/recognition/{recognition_id}/correct", response_model=dict)
def correct_recognition(
    recognition_id: int,
    request: CorrectRecognitionRequest,
    db: Session = Depends(get_db)
):
    """更正识别结果"""
    log = db.query(DrugRecognitionLog).filter(
        DrugRecognitionLog.id == recognition_id
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail='识别记录不存在')

    log.manual_correction = request.correct_drug_name
    log.status = RecognitionStatus.MANUAL.value

    if request.correct_drug_id:
        log.drug_info_id = request.correct_drug_id

    db.commit()
    return {'success': True, 'message': "更正成功"}


@router.post("/recognition/{recognition_id}/add-to-medication", response_model=dict)
def add_recognized_to_medication(
    recognition_id: int,
    request: AddToMedicationRequest,
    db: Session = Depends(get_db)
):
    """将识别的药品添加到用药计划"""
    log = db.query(DrugRecognitionLog).filter(
        DrugRecognitionLog.id == recognition_id
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="识别记录不存在")

    if log.added_to_medication:
        raise HTTPException(status_code=400, detail="该药品已添加到用药计划")

    # 获取药品信息
    drug_name = log.matched_name or log.manual_correction
    if not drug_name:
        raise HTTPException(status_code=400, detail='请先确认药品信息')

    # 创建用药计划
    medication = Medication(
        user_id=log.user_id,
        name=drug_name,
        dosage=request.dosage,
        medication_type='tablet',  # 默认值
        frequency=request.frequency,
        times=json.dumps(request.times),
        instructions=request.instructions,
        start_date=request.start_date or datetime.now(),
        quantity=request.quantity or 0,
        is_active=True
    )
    db.add(medication)

    # 更新识别日志
    log.added_to_medication = True

    db.commit()
    db.refresh(medication)

    log.medication_id = medication.id
    db.commit()

    return {
        "success": True,
        "medication_id": medication.id,
        'message': f"已将 {drug_name} 添加到用药计划"
    }


# ==================== 药物相互作用 ====================

@router.post("/interactions", response_model=dict)
def create_drug_interaction(
    request: DrugInteractionCreate,
    db: Session = Depends(get_db)
):
    """创建药物相互作用记录"""
    # 检查两种药品是否存在
    drug_a = db.query(DrugInfo).filter(DrugInfo.id == request.drug_a_id).first()
    drug_b = db.query(DrugInfo).filter(DrugInfo.id == request.drug_b_id).first()

    if not drug_a or not drug_b:
        raise HTTPException(status_code=404, detail='药品不存在')

    interaction = DrugInteraction(
        drug_a_id=request.drug_a_id,
        drug_b_id=request.drug_b_id,
        interaction_type=request.interaction_type.value,
        severity=request.severity.value,
        description=request.description,
        recommendation=request.recommendation
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    return {
        "success": True,
        "interaction_id": interaction.id,
        'message': "药物相互作用记录创建成功"
    }


@router.post("/check-interactions", response_model=dict)
def check_drug_interactions(
    request: CheckInteractionsRequest,
    db: Session = Depends(get_db)
):
    """检查药物相互作用"""
    drug_ids = []

    if request.check_all_medications:
        # 获取用户所有活跃用药的药品ID
        medications = db.query(Medication).filter(
            Medication.user_id == request.user_id,
            Medication.is_active == True
        ).all()

        # 尝试匹配药品库
        for med in medications:
            drug = db.query(DrugInfo).filter(
                or_(
                    DrugInfo.name == med.name,
                    DrugInfo.generic_name == med.name
                )
            ).first()
            if drug:
                drug_ids.append(drug.id)
    elif request.drug_ids:
        drug_ids = request.drug_ids

    if len(drug_ids) < 2:
        return {
            "has_interactions": False,
            "total_interactions": 0,
            'message': "药品数量不足，无法检查相互作用"
        }

    # 查询相互作用
    interactions = []
    for i, drug_a in enumerate(drug_ids):
        for drug_b in drug_ids[i + 1:]:
            found = db.query(DrugInteraction).filter(
                or_(
                    and_(DrugInteraction.drug_a_id == drug_a, DrugInteraction.drug_b_id == drug_b),
                    and_(DrugInteraction.drug_a_id == drug_b, DrugInteraction.drug_b_id == drug_a)
                )
            ).all()
            interactions.extend(found)

    # 按严重程度分类
    critical = []
    major = []
    moderate = []
    minor = []

    for i in interactions:
        drug_a = db.query(DrugInfo).filter(DrugInfo.id == i.drug_a_id).first()
        drug_b = db.query(DrugInfo).filter(DrugInfo.id == i.drug_b_id).first()

        interaction_data = {
            'id': i.id,
            'drug_a': drug_to_brief(drug_a) if drug_a else None,
            "drug_b": drug_to_brief(drug_b) if drug_b else None,
            "interaction_type": i.interaction_type,
            'severity': i.severity,
            "description": i.description,
            "recommendation": i.recommendation
        }

        if i.interaction_type == "contraindicated":
            critical.append(interaction_data)
        elif i.interaction_type == 'major':
            major.append(interaction_data)
        elif i.interaction_type == 'moderate':
            moderate.append(interaction_data)
        else:
            minor.append(interaction_data)

    # 生成建议
    recommendations = []
    if critical:
        recommendations.append("发现禁忌药物组合，请立即咨询医生！")
    if major:
        recommendations.append("发现严重相互作用，建议咨询医生调整用药。")
    if moderate:
        recommendations.append("存在中等程度相互作用，请注意观察用药反应。")

    return {
        "has_interactions": len(interactions) > 0,
        "total_interactions": len(interactions),
        "critical_interactions": critical,
        "major_interactions": major,
        "moderate_interactions": moderate,
        "minor_interactions": minor,
        "recommendations": recommendations
    }


# ==================== 老年人用药提示 ====================

@router.get("/elderly-tips/{drug_id}", response_model=dict)
def get_elderly_drug_tips(
    drug_id: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取老年人用药提示"""
    drug = db.query(DrugInfo).filter(DrugInfo.id == drug_id).first()
    if not drug:
        raise HTTPException(status_code=404, detail="药品不存在")

    general_tips = []
    personalized_tips = []
    warnings = []
    food_interactions = []

    # 通用老年人用药提示
    general_tips.append("请按时按量服用，不要自行调整剂量")
    general_tips.append("服药后如有不适，请及时告知家人或医生")

    if drug.elderly_precautions:
        general_tips.append(drug.elderly_precautions)

    if drug.dosage_instructions:
        general_tips.append(f'用法用量：{drug.dosage_instructions}')

    # 禁忌提示
    if drug.contraindications:
        warnings.append(f'禁忌症：{drug.contraindications}')

    # 副作用提示
    if drug.side_effects:
        warnings.append(f'可能的副作用：{drug.side_effects}')

    # 个性化提示（如提供了用户ID）
    if user_id:
        from app.models.database import UserProfile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile:
            # 检查过敏
            allergies = parse_json_field(profile.allergies)
            if allergies:
                personalized_tips.append(f'您记录的过敏信息：{', '.join(allergies)}，请确认此药不在过敏范围内')

            # 检查慢性病
            conditions = parse_json_field(profile.chronic_conditions)
            if conditions:
                personalized_tips.append(f'请注意：您有{', '.join(conditions)}，服用此药前请咨询医生')

    # 通用食物相互作用提示
    food_interactions.append("服药期间避免饮酒")
    food_interactions.append("某些药物需要空腹或餐后服用，请遵医嘱")

    return {
        "drug_name": drug.name,
        "general_tips": general_tips,
        "personalized_tips": personalized_tips if personalized_tips else None,
        'warnings': warnings if warnings else None,
        "food_interactions": food_interactions
    }


# ==================== 统计 ====================

@router.get("/stats/{user_id}", response_model=dict)
def get_drug_recognition_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取药品识别统计"""
    total_recognitions = db.query(func.count(DrugRecognitionLog.id)).filter(
        DrugRecognitionLog.user_id == user_id
    ).scalar()

    successful = db.query(func.count(DrugRecognitionLog.id)).filter(
        DrugRecognitionLog.user_id == user_id,
        DrugRecognitionLog.status == "success"
    ).scalar()

    added_to_medication = db.query(func.count(DrugRecognitionLog.id)).filter(
        DrugRecognitionLog.user_id == user_id,
        DrugRecognitionLog.added_to_medication == True
    ).scalar()

    return {
        'user_id': user_id,
        "total_recognitions": total_recognitions,
        "successful_recognitions": successful,
        "success_rate": round(successful / total_recognitions * 100, 1) if total_recognitions > 0 else 0,
        "added_to_medication": added_to_medication
    }
