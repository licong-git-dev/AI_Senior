"""
API路由 - 用药管理
实现用药计划CRUD、服药记录、提醒、依从性统计等功能
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
import json

from app.core.deps import get_db, get_current_user
from app.core.security import UserInfo
from app.models.database import (
    Medication as MedicationModel,
    MedicationRecord as MedicationRecordModel,
    User
)
from app.schemas.medication import (
    MedicationFrequency,
    MedicationStatus,
    MedicationType,
    MedicationCreate,
    MedicationUpdate,
    MedicationResponse,
    MedicationRecordCreate,
    MedicationRecordUpdate,
    TakeMedicationRequest,
    SkipMedicationRequest,
    MedicationReminderSettings,
    UpdateReminderSettingsRequest
)

router = APIRouter(prefix="/api/medication", tags=["用药管理"])


# ========== 工具函数 ==========

def parse_times(times_str: Optional[str]) -> List[str]:
    """解析时间JSON字符串"""
    if not times_str:
        return []
    try:
        return json.loads(times_str)
    except (json.JSONDecodeError, TypeError):
        return []


def serialize_times(times: List[str]) -> str:
    """序列化时间列表为JSON"""
    return json.dumps(times)


def generate_today_schedule(db: Session, user_id: int) -> List[Dict]:
    """生成今日服药计划"""
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    # 获取所有活跃的用药计划
    medications = db.query(MedicationModel).filter(
        MedicationModel.user_id == user_id,
        MedicationModel.is_active == True,
        or_(
            MedicationModel.end_date.is_(None),
            MedicationModel.end_date >= today_start
        ),
        MedicationModel.start_date <= today_end
    ).all()

    schedule = []
    for med in medications:
        times = parse_times(med.times)
        for time_str in times:
            # 检查是否已有记录
            scheduled_dt = datetime.strptime(f"{today.isoformat()} {time_str}", '%Y-%m-%d %H:%M')

            record = db.query(MedicationRecordModel).filter(
                MedicationRecordModel.medication_id == med.id,
                MedicationRecordModel.scheduled_time == scheduled_dt
            ).first()

            status = record.status if record else 'pending'
            record_id = str(record.id) if record else None

            schedule.append({
                "medication_id": str(med.id),
                "medication_name": med.name,
                'dosage': med.dosage,
                "medication_type": med.medication_type,
                "scheduled_time": time_str,
                "scheduled_datetime": scheduled_dt.isoformat(),
                'status': status,
                'record_id': record_id,
                "instructions": med.instructions,
                'notes': med.notes
            })

    # 按时间排序
    schedule.sort(key=lambda x: x["scheduled_time"])
    return schedule


# ========== 用药计划管理 ==========

@router.post("/medications", response_model=dict)
async def create_medication(
    request: MedicationCreate,
    db: Session = Depends(get_db)
):
    """
    创建用药计划

    设置定时服药提醒，支持多种服药频率
    """
    # 创建药物记录（use_enum_values=True使枚举已转为字符串）
    med_type = request.medication_type if isinstance(request.medication_type, str) else request.medication_type.value
    freq = request.frequency if isinstance(request.frequency, str) else request.frequency.value

    medication = MedicationModel(
        user_id=int(request.user_id),
        name=request.name,
        dosage=request.dosage,
        medication_type=med_type,
        frequency=freq,
        times=serialize_times(request.times),
        instructions=request.instructions,
        side_effects=request.side_effects,
        notes=request.notes,
        prescriber=request.prescriber,
        pharmacy=request.pharmacy,
        quantity=request.quantity or 0,
        start_date=datetime.combine(request.start_date, datetime.min.time()),
        end_date=datetime.combine(request.end_date, datetime.min.time()) if request.end_date else None,
        is_active=True
    )

    db.add(medication)
    db.commit()
    db.refresh(medication)

    return {
        "success": True,
        "medication_id": str(medication.id),
        'message': f"用药计划 {request.name} 已创建"
    }


@router.get("/medications", response_model=dict)
async def get_medications(
    user_id: str,
    active_only: bool = Query(True, description="仅显示启用的计划"),
    db: Session = Depends(get_db)
):
    """获取用药计划列表"""
    query = db.query(MedicationModel).filter(
        MedicationModel.user_id == int(user_id)
    )

    if active_only:
        query = query.filter(MedicationModel.is_active == True)

    medications = query.order_by(MedicationModel.created_at.desc()).all()

    return {
        'user_id': user_id,
        "medications": [
            {
                'id': str(m.id),
                'name': m.name,
                'dosage': m.dosage,
                "medication_type": m.medication_type,
                'frequency': m.frequency,
                'times': parse_times(m.times),
                "instructions": m.instructions,
                "side_effects": m.side_effects,
                'notes': m.notes,
                'prescriber': m.prescriber,
                'pharmacy': m.pharmacy,
                'quantity': m.quantity,
                "low_stock_threshold": m.low_stock_threshold,
                "is_low_stock": m.quantity <= m.low_stock_threshold if m.quantity else False,
                'start_date': m.start_date.date().isoformat() if m.start_date else None,
                'end_date': m.end_date.date().isoformat() if m.end_date else None,
                'is_active': m.is_active,
                'created_at': m.created_at.isoformat()
            }
            for m in medications
        ],
        'count': len(medications)
    }


@router.get("/medications/{medication_id}", response_model=dict)
async def get_medication(
    medication_id: str,
    db: Session = Depends(get_db)
):
    """获取单个用药计划详情"""
    medication = db.query(MedicationModel).filter(
        MedicationModel.id == int(medication_id)
    ).first()

    if not medication:
        raise HTTPException(status_code=404, detail='用药计划不存在')

    # 获取最近服药记录
    recent_records = db.query(MedicationRecordModel).filter(
        MedicationRecordModel.medication_id == medication.id
    ).order_by(
        MedicationRecordModel.scheduled_time.desc()
    ).limit(10).all()

    return {
        'id': str(medication.id),
        'user_id': str(medication.user_id),
        'name': medication.name,
        "dosage": medication.dosage,
        "medication_type": medication.medication_type,
        'frequency': medication.frequency,
        'times': parse_times(medication.times),
        "instructions": medication.instructions,
        "side_effects": medication.side_effects,
        'notes': medication.notes,
        'prescriber': medication.prescriber,
        'pharmacy': medication.pharmacy,
        'quantity': medication.quantity,
        "low_stock_threshold": medication.low_stock_threshold,
        'start_date': medication.start_date.date().isoformat() if medication.start_date else None,
        'end_date': medication.end_date.date().isoformat() if medication.end_date else None,
        'is_active': medication.is_active,
        'created_at': medication.created_at.isoformat(),
        'updated_at': medication.updated_at.isoformat() if medication.updated_at else None,
        "recent_records": [
            {
                'id': str(r.id),
                "scheduled_time": r.scheduled_time.isoformat(),
                'taken_time': r.taken_time.isoformat() if r.taken_time else None,
                'status': r.status,
                'notes': r.notes
            }
            for r in recent_records
        ]
    }


@router.put("/medications/{medication_id}", response_model=dict)
async def update_medication(
    medication_id: str,
    request: MedicationUpdate,
    db: Session = Depends(get_db)
):
    """更新用药计划"""
    medication = db.query(MedicationModel).filter(
        MedicationModel.id == int(medication_id)
    ).first()

    if not medication:
        raise HTTPException(status_code=404, detail='用药计划不存在')

    if request.dosage is not None:
        medication.dosage = request.dosage
    if request.frequency is not None:
        medication.frequency = request.frequency.value
    if request.times is not None:
        medication.times = serialize_times(request.times)
    if request.notes is not None:
        medication.notes = request.notes
    if request.instructions is not None:
        medication.instructions = request.instructions
    if request.end_date is not None:
        medication.end_date = datetime.combine(request.end_date, datetime.min.time())
    if request.quantity is not None:
        medication.quantity = request.quantity
    if request.is_active is not None:
        medication.is_active = request.is_active

    db.commit()

    return {
        'success': True,
        'message': "用药计划已更新"
    }


@router.delete("/medications/{medication_id}", response_model=dict)
async def disable_medication(
    medication_id: str,
    db: Session = Depends(get_db)
):
    """停用用药计划"""
    medication = db.query(MedicationModel).filter(
        MedicationModel.id == int(medication_id)
    ).first()

    if not medication:
        raise HTTPException(status_code=404, detail='用药计划不存在')

    medication.is_active = False
    db.commit()

    return {
        'success': True,
        "message": f"用药计划 {medication.name} 已停用"
    }


# ========== 今日服药计划 ==========

@router.get("/schedule/today/{user_id}", response_model=dict)
async def get_today_schedule(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """获取今日服药计划"""
    schedule = generate_today_schedule(db, int(user_id))

    # 统计
    total = len(schedule)
    taken = sum(1 for s in schedule if s['status'] == "taken")
    missed = sum(1 for s in schedule if s['status'] == 'missed')
    skipped = sum(1 for s in schedule if s['status'] == 'skipped')
    pending = sum(1 for s in schedule if s['status'] == 'pending')

    return {
        'user_id': user_id,
        'date': date.today().isoformat(),
        'schedule': schedule,
        # 顶层字段供前端直接访问
        'total_count': total,
        'taken_count': taken,
        'pending_count': pending,
        'summary': {
            'total': total,
            'taken': taken,
            'missed': missed,
            'skipped': skipped,
            'pending': pending,
            "completion_rate": round(taken / total * 100, 1) if total > 0 else 0
        }
    }


@router.get("/schedule/pending/{user_id}", response_model=dict)
async def get_pending_reminders(
    user_id: str,
    db: Session = Depends(get_db)
):
    """获取待处理的服药提醒"""
    schedule = generate_today_schedule(db, int(user_id))
    now = datetime.now()

    pending = []
    for item in schedule:
        if item['status'] == 'pending':
            scheduled_dt = datetime.fromisoformat(item["scheduled_datetime"])
            # 包括已过时但未处理的
            if scheduled_dt <= now + timedelta(hours=1):
                item["is_overdue"] = scheduled_dt < now
                pending.append(item)

    # 按时间排序
    pending.sort(key=lambda x: x["scheduled_datetime"])

    return {
        'user_id': user_id,
        "pending_reminders": pending,
        'count': len(pending)
    }


# ========== 服药记录 ==========

@router.post("/records/take", response_model=dict)
async def record_medication_taken(
    user_id: str,
    medication_id: str,
    scheduled_time: str,
    request: TakeMedicationRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """记录已服药"""
    # 验证药物存在
    medication = db.query(MedicationModel).filter(
        MedicationModel.id == int(medication_id),
        MedicationModel.user_id == int(user_id)
    ).first()

    if not medication:
        raise HTTPException(status_code=404, detail='用药计划不存在')

    scheduled_dt = datetime.fromisoformat(scheduled_time)
    taken_time = request.taken_time or datetime.now()

    # 查找或创建记录
    record = db.query(MedicationRecordModel).filter(
        MedicationRecordModel.medication_id == int(medication_id),
        MedicationRecordModel.scheduled_time == scheduled_dt
    ).first()

    if record:
        record.status = 'taken'
        record.taken_time = taken_time
        record.notes = request.notes
    else:
        record = MedicationRecordModel(
            user_id=int(user_id),
            medication_id=int(medication_id),
            scheduled_time=scheduled_dt,
            taken_time=taken_time,
            status='taken',
            notes=request.notes
        )
        db.add(record)

    # 减少库存
    if medication.quantity and medication.quantity > 0:
        medication.quantity -= 1

    db.commit()
    db.refresh(record)

    return {
        'success': True,
        "record_id": str(record.id),
        "medication_name": medication.name,
        'taken_time': taken_time.isoformat(),
        "remaining_quantity": medication.quantity,
        'message': f"已记录服用 {medication.name}"
    }


@router.post("/records/skip", response_model=dict)
async def skip_medication(
    user_id: str,
    medication_id: str,
    scheduled_time: str,
    request: SkipMedicationRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """跳过服药"""
    medication = db.query(MedicationModel).filter(
        MedicationModel.id == int(medication_id),
        MedicationModel.user_id == int(user_id)
    ).first()

    if not medication:
        raise HTTPException(status_code=404, detail='用药计划不存在')

    scheduled_dt = datetime.fromisoformat(scheduled_time)

    record = db.query(MedicationRecordModel).filter(
        MedicationRecordModel.medication_id == int(medication_id),
        MedicationRecordModel.scheduled_time == scheduled_dt
    ).first()

    if record:
        record.status = 'skipped'
        record.skip_reason = request.reason
    else:
        record = MedicationRecordModel(
            user_id=int(user_id),
            medication_id=int(medication_id),
            scheduled_time=scheduled_dt,
            status='skipped',
            skip_reason=request.reason
        )
        db.add(record)

    db.commit()

    return {
        'success': True,
        'message': "已跳过服药"
    }


@router.get("/records/{user_id}", response_model=dict)
async def get_medication_records(
    user_id: str,
    medication_id: Optional[str] = None,
    status: Optional[str] = None,
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """获取服药记录"""
    cutoff = datetime.now() - timedelta(days=days)

    query = db.query(MedicationRecordModel).filter(
        MedicationRecordModel.user_id == int(user_id),
        MedicationRecordModel.scheduled_time > cutoff
    )

    if medication_id:
        query = query.filter(MedicationRecordModel.medication_id == int(medication_id))
    if status:
        query = query.filter(MedicationRecordModel.status == status)

    total = query.count()
    records = query.order_by(
        MedicationRecordModel.scheduled_time.desc()
    ).offset(offset).limit(limit).all()

    # 获取药物名称映射
    medication_ids = list(set(r.medication_id for r in records))
    medications = db.query(MedicationModel).filter(
        MedicationModel.id.in_(medication_ids)
    ).all()
    med_names = {m.id: m.name for m in medications}

    return {
        'user_id': user_id,
        'days': days,
        'total': total,
        'records': [
            {
                "id": str(r.id),
                "medication_id": str(r.medication_id),
                "medication_name": med_names.get(r.medication_id, "未知"),
                "scheduled_time": r.scheduled_time.isoformat(),
                'taken_time': r.taken_time.isoformat() if r.taken_time else None,
                'status': r.status,
                "skip_reason": r.skip_reason,
                'notes': r.notes,
                'created_at': r.created_at.isoformat()
            }
            for r in records
        ]
    }


# ========== 依从性统计 ==========

@router.get("/adherence/{user_id}", response_model=dict)
async def get_adherence_stats(
    user_id: str,
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db)
):
    """获取服药依从性统计"""
    cutoff = datetime.now() - timedelta(days=days)

    records = db.query(MedicationRecordModel).filter(
        MedicationRecordModel.user_id == int(user_id),
        MedicationRecordModel.scheduled_time > cutoff
    ).all()

    total = len(records)
    taken = sum(1 for r in records if r.status == "taken")
    missed = sum(1 for r in records if r.status == 'missed')
    skipped = sum(1 for r in records if r.status == 'skipped')

    # 计算准时率（在计划时间前后30分钟内服药）
    on_time = 0
    for r in records:
        if r.status == 'taken' and r.taken_time:
            diff = abs((r.taken_time - r.scheduled_time).total_seconds())
            if diff <= 1800:  # 30分钟内
                on_time += 1

    adherence_rate = round(taken / total * 100, 1) if total > 0 else 0
    on_time_rate = round(on_time / taken * 100, 1) if taken > 0 else 0

    # 按药物统计
    med_stats = {}
    for r in records:
        if r.medication_id not in med_stats:
            med_stats[r.medication_id] = {'taken': 0, 'total': 0}
        med_stats[r.medication_id]['total'] += 1
        if r.status == 'taken':
            med_stats[r.medication_id]["taken"] += 1

    # 获取药物名称
    medication_ids = list(med_stats.keys())
    medications = db.query(MedicationModel).filter(
        MedicationModel.id.in_(medication_ids)
    ).all()
    med_names = {m.id: m.name for m in medications}

    by_medication = [
        {
            "medication_id": str(med_id),
            "medication_name": med_names.get(med_id, "未知"),
            "adherence_rate": round(stats['taken'] / stats['total'] * 100, 1) if stats['total'] > 0 else 0,
            'taken_count': stats['taken'],
            'total_count': stats['total']
        }
        for med_id, stats in med_stats.items()
    ]

    return {
        'user_id': user_id,
        "period_days": days,
        'overall': {
            "adherence_rate": adherence_rate,
            "on_time_rate": on_time_rate,
            "total_scheduled": total,
            "taken_count": taken,
            "missed_count": missed,
            "skipped_count": skipped
        },
        "by_medication": by_medication,
        "recommendation": _get_adherence_recommendation(adherence_rate)
    }


def _get_adherence_recommendation(rate: float) -> str:
    """根据依从率生成建议"""
    if rate >= 90:
        return "您的服药依从性非常好，请继续保持！"
    elif rate >= 80:
        return "服药依从性良好，建议设置更多提醒以进一步提高。"
    elif rate >= 60:
        return "服药依从性一般，建议调整服药时间或使用语音提醒。"
    else:
        return "服药依从性较低，建议与家人或医生沟通，寻找更好的解决方案。"


# ========== 库存管理 ==========

@router.put("/medications/{medication_id}/stock", response_model=dict)
async def update_medication_stock(
    medication_id: str,
    quantity: int,
    low_stock_threshold: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """更新药品库存"""
    medication = db.query(MedicationModel).filter(
        MedicationModel.id == int(medication_id)
    ).first()

    if not medication:
        raise HTTPException(status_code=404, detail='用药计划不存在')

    medication.quantity = quantity
    if low_stock_threshold is not None:
        medication.low_stock_threshold = low_stock_threshold

    db.commit()

    return {
        "success": True,
        "medication_name": medication.name,
        'quantity': medication.quantity,
        "low_stock_threshold": medication.low_stock_threshold,
        "is_low_stock": medication.quantity <= medication.low_stock_threshold
    }


@router.get("/stock/alerts/{user_id}", response_model=dict)
async def get_stock_alerts(
    user_id: str,
    db: Session = Depends(get_db)
):
    """获取库存告警"""
    medications = db.query(MedicationModel).filter(
        MedicationModel.user_id == int(user_id),
        MedicationModel.is_active == True
    ).all()

    low_stock = []
    for med in medications:
        if med.quantity is not None and med.quantity <= med.low_stock_threshold:
            low_stock.append({
                "medication_id": str(med.id),
                "medication_name": med.name,
                "current_quantity": med.quantity,
                "low_stock_threshold": med.low_stock_threshold,
                'pharmacy': med.pharmacy
            })

    return {
        'user_id': user_id,
        "low_stock_medications": low_stock,
        'count': len(low_stock)
    }


# ========== 仪表板 ==========

@router.get("/dashboard/{user_id}", response_model=dict)
async def get_medication_dashboard(
    user_id: str,
    db: Session = Depends(get_db)
):
    """获取用药管理仪表板"""
    # 今日计划
    schedule = generate_today_schedule(db, int(user_id))
    total_today = len(schedule)
    taken_today = sum(1 for s in schedule if s['status'] == "taken")
    pending_today = sum(1 for s in schedule if s['status'] == 'pending')

    # 下一个待服药
    now = datetime.now()
    next_pending = None
    for item in sorted(schedule, key=lambda x: x["scheduled_time"]):
        if item['status'] == 'pending':
            scheduled_dt = datetime.fromisoformat(item["scheduled_datetime"])
            if scheduled_dt >= now - timedelta(hours=1):
                next_pending = item
                break

    # 近7天依从性
    week_ago = datetime.now() - timedelta(days=7)
    week_records = db.query(MedicationRecordModel).filter(
        MedicationRecordModel.user_id == int(user_id),
        MedicationRecordModel.scheduled_time > week_ago
    ).all()
    week_taken = sum(1 for r in week_records if r.status == "taken")
    week_total = len(week_records)
    week_rate = round(week_taken / week_total * 100, 1) if week_total > 0 else 0

    # 库存警告
    low_stock_meds = db.query(MedicationModel).filter(
        MedicationModel.user_id == int(user_id),
        MedicationModel.is_active == True,
        MedicationModel.quantity <= MedicationModel.low_stock_threshold
    ).all()

    # 活跃药物数量
    active_count = db.query(MedicationModel).filter(
        MedicationModel.user_id == int(user_id),
        MedicationModel.is_active == True
    ).count()

    return {
        'user_id': user_id,
        'today': {
            'date': date.today().isoformat(),
            'total': total_today,
            'taken': taken_today,
            "pending": pending_today,
            "completion_rate": round(taken_today / total_today * 100, 1) if total_today > 0 else 0,
            "next_reminder": next_pending
        },
        'adherence': {
            'period': '最近7天',
            "rate": week_rate,
            "taken_count": week_taken,
            "total_count": week_total
        },
        'alerts': {
            "low_stock_count": len(low_stock_meds),
            "low_stock_items": [m.name for m in low_stock_meds[:3]]
        },
        "medications": {
            "active_count": active_count
        }
    }
