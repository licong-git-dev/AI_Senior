"""
API路由 - 健康数据管理
实现健康记录的CRUD操作，支持血压、心率、血糖、血氧、体温等生命体征的记录和分析
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json

from app.core.deps import get_db, get_current_user
from app.core.security import UserInfo
from app.models.database import (
    HealthRecord as HealthRecordModel,
    HealthAlert as HealthAlertModel,
    HealthReport as HealthReportModel,
    User
)
from app.schemas.health import (
    HealthRecordType,
    HealthDataSource,
    HealthAlertLevel,
    HealthRecordCreate,
    HealthRecordUpdate,
    HealthRecordResponse,
    HealthTrendResponse,
    HealthTrendPoint,
    HealthAlertCreate,
    HealthAlertResponse,
    HealthReportResponse,
    HealthReportSummary,
    HandleAlertRequest,
    BloodPressureValue,
    HeartRateValue,
    BloodSugarValue,
    BloodOxygenValue,
    TemperatureValue
)

router = APIRouter(prefix="/api/health", tags=["健康管理"])


# ========== 工具函数 ==========

def get_unit_for_type(record_type: str) -> str:
    """根据记录类型获取单位"""
    units = {
        'blood_pressure': 'mmHg',
        'heart_rate': 'bpm',
        'blood_sugar': 'mmol/L',
        'blood_oxygen': '%',
        'temperature': '°C',
        'weight': 'kg',
        'steps': '步',
        'sleep': "分钟"
    }
    return units.get(record_type, "")


def evaluate_alert_level(record_type: str, value: Dict[str, Any]) -> tuple[str, bool]:
    """评估健康数据的告警级别"""
    level = HealthAlertLevel.NORMAL.value
    is_abnormal = False

    try:
        if record_type == "blood_pressure":
            bp = BloodPressureValue(**value)
            level = bp.level.value
        elif record_type == 'heart_rate':
            hr = HeartRateValue(**value)
            level = hr.level.value
        elif record_type == "blood_sugar":
            bs = BloodSugarValue(**value)
            level = bs.level.value
        elif record_type == "blood_oxygen":
            bo = BloodOxygenValue(**value)
            level = bo.level.value
        elif record_type == "temperature":
            temp = TemperatureValue(**value)
            level = temp.level.value
    except Exception:
        pass

    is_abnormal = level in [HealthAlertLevel.HIGH.value, HealthAlertLevel.CRITICAL.value]
    return level, is_abnormal


def extract_values_from_dict(record_type: str, value: Dict[str, Any]) -> tuple[float, float, float]:
    """从值字典中提取数值"""
    primary = None
    secondary = None
    tertiary = None

    if record_type == "blood_pressure":
        primary = value.get("systolic")
        secondary = value.get('diastolic')
        tertiary = value.get('pulse')
    elif record_type == 'heart_rate':
        primary = value.get('bpm')
    elif record_type == "blood_sugar":
        primary = value.get("value")
    elif record_type == "blood_oxygen":
        primary = value.get("spo2")
    elif record_type == "temperature":
        primary = value.get("celsius")
    elif record_type == 'weight':
        primary = value.get('kg') or value.get('weight')
    elif record_type == 'steps':
        primary = value.get('count')
        secondary = value.get("distance_meters")
        tertiary = value.get('calories')
    elif record_type == 'sleep':
        primary = value.get("total_minutes")
        secondary = value.get("deep_sleep_minutes")
        tertiary = value.get("awake_times")

    return primary, secondary, tertiary


def build_value_dict(record: HealthRecordModel) -> Dict[str, Any]:
    """从数据库记录构建值字典"""
    record_type = record.record_type
    value = {}

    if record_type == "blood_pressure":
        value = {
            'systolic': int(record.value_primary) if record.value_primary else None,
            'diastolic': int(record.value_secondary) if record.value_secondary else None,
            'pulse': int(record.value_tertiary) if record.value_tertiary else None
        }
    elif record_type == 'heart_rate':
        value = {'bpm': int(record.value_primary) if record.value_primary else None}
    elif record_type == "blood_sugar":
        value = {'value': record.value_primary}
    elif record_type == "blood_oxygen":
        value = {'spo2': int(record.value_primary) if record.value_primary else None}
    elif record_type == "temperature":
        value = {'celsius': record.value_primary}
    elif record_type == 'weight':
        value = {'kg': record.value_primary}
    elif record_type == 'steps':
        value = {
            'count': int(record.value_primary) if record.value_primary else None,
            "distance_meters": int(record.value_secondary) if record.value_secondary else None,
            'calories': int(record.value_tertiary) if record.value_tertiary else None
        }
    elif record_type == 'sleep':
        value = {
            "total_minutes": int(record.value_primary) if record.value_primary else None,
            "deep_sleep_minutes": int(record.value_secondary) if record.value_secondary else None,
            "awake_times": int(record.value_tertiary) if record.value_tertiary else None
        }

    # 移除None值
    value = {k: v for k, v in value.items() if v is not None}
    return value


# ========== 健康数据记录 ==========

@router.post("/record/create", response_model=dict)
async def create_health_record(
    request: HealthRecordCreate,
    db: Session = Depends(get_db)
):
    """
    记录健康数据

    支持的记录类型:
    - blood_pressure: 血压 (systolic, diastolic, pulse)
    - heart_rate: 心率 (bpm)
    - blood_sugar: 血糖 (value, is_fasting)
    - blood_oxygen: 血氧 (spo2)
    - temperature: 体温 (celsius)
    - weight: 体重 (kg)
    - steps: 步数 (count, distance_meters, calories)
    - sleep: 睡眠 (total_minutes, deep_sleep_minutes, awake_times)
    """
    # 提取数值（use_enum_values=True使枚举已转为字符串）
    record_type_str = request.record_type if isinstance(request.record_type, str) else request.record_type.value
    source_str = request.source if isinstance(request.source, str) else request.source.value

    primary, secondary, tertiary = extract_values_from_dict(
        record_type_str,
        request.value
    )

    # 评估告警级别
    alert_level, is_abnormal = evaluate_alert_level(
        record_type_str,
        request.value
    )

    # 创建记录
    db_record = HealthRecordModel(
        user_id=int(request.user_id),
        record_type=record_type_str,
        value_primary=primary,
        value_secondary=secondary,
        value_tertiary=tertiary,
        unit=get_unit_for_type(record_type_str),
        source=source_str,
        device_id=request.device_id,
        notes=request.notes,
        alert_level=alert_level,
        is_abnormal=is_abnormal,
        measured_at=request.measured_at or datetime.now()
    )

    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    # 如果异常，创建告警
    if is_abnormal:
        await _create_health_alert(
            db=db,
            user_id=int(request.user_id),
            record=db_record,
            level=alert_level,
            value=request.value
        )

    return {
        'success': True,
        "record_id": str(db_record.id),
        "alert_level": alert_level,
        "is_abnormal": is_abnormal,
        'message': "健康数据记录成功"
    }


@router.get("/record/list/{user_id}", response_model=dict)
async def get_health_records(
    user_id: str,
    record_type: Optional[str] = None,
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """获取健康数据记录列表"""
    cutoff = datetime.now() - timedelta(days=days)

    query = db.query(HealthRecordModel).filter(
        HealthRecordModel.user_id == int(user_id),
        HealthRecordModel.measured_at > cutoff
    )

    if record_type:
        query = query.filter(HealthRecordModel.record_type == record_type)

    total = query.count()
    records = query.order_by(
        HealthRecordModel.measured_at.desc()
    ).offset(offset).limit(limit).all()

    return {
        'user_id': user_id,
        'days': days,
        'total': total,
        'records': [
            {
                'id': str(r.id),
                'user_id': str(r.user_id),
                "record_type": r.record_type,
                'value': build_value_dict(r),
                'unit': r.unit,
                'source': r.source,
                'device_id': r.device_id,
                'notes': r.notes,
                "alert_level": r.alert_level,
                "is_abnormal": r.is_abnormal,
                "measured_at": r.measured_at.isoformat(),
                'created_at': r.created_at.isoformat()
            }
            for r in records
        ]
    }


@router.get("/record/latest/{user_id}", response_model=dict)
async def get_latest_health_data(
    user_id: str,
    db: Session = Depends(get_db)
):
    """获取最新的各项健康数据"""
    from sqlalchemy.orm import aliased
    from sqlalchemy import distinct

    # 获取所有记录类型
    record_types = db.query(
        distinct(HealthRecordModel.record_type)
    ).filter(
        HealthRecordModel.user_id == int(user_id)
    ).all()

    latest = {}
    for (rt,) in record_types:
        record = db.query(HealthRecordModel).filter(
            HealthRecordModel.user_id == int(user_id),
            HealthRecordModel.record_type == rt
        ).order_by(
            HealthRecordModel.measured_at.desc()
        ).first()

        if record:
            latest[rt] = {
                'id': str(record.id),
                'value': build_value_dict(record),
                "unit": record.unit,
                "alert_level": record.alert_level,
                "measured_at": record.measured_at.isoformat()
            }

    return {
        'user_id': user_id,
        "latest_records": latest
    }


@router.get("/record/{record_id}", response_model=dict)
async def get_health_record(
    record_id: str,
    db: Session = Depends(get_db)
):
    """获取单条健康记录详情"""
    record = db.query(HealthRecordModel).filter(
        HealthRecordModel.id == int(record_id)
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail='记录不存在')

    return {
        'id': str(record.id),
        "user_id": str(record.user_id),
        "record_type": record.record_type,
        'value': build_value_dict(record),
        'unit': record.unit,
        'source': record.source,
        'device_id': record.device_id,
        'notes': record.notes,
        "alert_level": record.alert_level,
        "is_abnormal": record.is_abnormal,
        "measured_at": record.measured_at.isoformat(),
        'created_at': record.created_at.isoformat()
    }


@router.put("/record/{record_id}", response_model=dict)
async def update_health_record(
    record_id: str,
    request: HealthRecordUpdate,
    db: Session = Depends(get_db)
):
    """更新健康记录"""
    record = db.query(HealthRecordModel).filter(
        HealthRecordModel.id == int(record_id)
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail='记录不存在')

    if request.value is not None:
        primary, secondary, tertiary = extract_values_from_dict(
            record.record_type,
            request.value
        )
        alert_level, is_abnormal = evaluate_alert_level(
            record.record_type,
            request.value
        )

        record.value_primary = primary
        record.value_secondary = secondary
        record.value_tertiary = tertiary
        record.alert_level = alert_level
        record.is_abnormal = is_abnormal

    if request.notes is not None:
        record.notes = request.notes

    db.commit()

    return {
        'success': True,
        'message': "记录更新成功"
    }


@router.delete("/record/{record_id}", response_model=dict)
async def delete_health_record(
    record_id: str,
    db: Session = Depends(get_db)
):
    """删除健康记录"""
    record = db.query(HealthRecordModel).filter(
        HealthRecordModel.id == int(record_id)
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail='记录不存在')

    db.delete(record)
    db.commit()

    return {
        'success': True,
        'message': "记录已删除"
    }


# ========== 健康趋势分析 ==========

@router.get("/trend/{user_id}/{record_type}", response_model=dict)
async def get_health_trend(
    user_id: str,
    record_type: str,
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """获取健康数据趋势"""
    cutoff = datetime.now() - timedelta(days=days)

    records = db.query(HealthRecordModel).filter(
        HealthRecordModel.user_id == int(user_id),
        HealthRecordModel.record_type == record_type,
        HealthRecordModel.measured_at > cutoff
    ).order_by(
        HealthRecordModel.measured_at.asc()
    ).all()

    # 按日期分组
    daily_data: Dict[str, List[Dict]] = {}
    for record in records:
        date_str = record.measured_at.date().isoformat()
        if date_str not in daily_data:
            daily_data[date_str] = []
        daily_data[date_str].append(build_value_dict(record))

    # 计算趋势
    trend_data = []
    values_for_trend = []

    for date_str in sorted(daily_data.keys()):
        values = daily_data[date_str]

        # 计算主数值的平均值
        primary_values = []
        for v in values:
            if record_type == "blood_pressure":
                primary_values.append(v.get('systolic', 0))
            elif record_type in ['heart_rate', 'blood_sugar', 'blood_oxygen', 'temperature', 'weight']:
                primary_values.append(list(v.values())[0] if v else 0)
            elif record_type == 'steps':
                primary_values.append(v.get('count', 0))
            elif record_type == 'sleep':
                primary_values.append(v.get("total_minutes", 0))

        avg_value = sum(primary_values) / len(primary_values) if primary_values else None
        values_for_trend.append(avg_value)

        trend_data.append({
            'date': date_str,
            'values': values,
            'average': round(avg_value, 2) if avg_value else None,
            'min_value': min(primary_values) if primary_values else None,
            'max_value': max(primary_values) if primary_values else None
        })

    # 判断整体趋势
    overall_trend = 'stable'
    if len(values_for_trend) >= 7:
        recent = [v for v in values_for_trend[-7:] if v is not None]
        earlier = [v for v in values_for_trend[:7] if v is not None]
        if recent and earlier:
            recent_avg = sum(recent) / len(recent)
            earlier_avg = sum(earlier) / len(earlier)
            diff_pct = (recent_avg - earlier_avg) / earlier_avg * 100 if earlier_avg else 0

            if diff_pct > 5:
                overall_trend = 'increasing'
            elif diff_pct < -5:
                overall_trend = 'decreasing'

    return {
        "user_id": user_id,
        "record_type": record_type,
        "period_days": days,
        'trend': trend_data,
        "overall_trend": overall_trend,
        "record_count": len(records)
    }


# ========== 健康告警 ==========

async def _create_health_alert(
    db: Session,
    user_id: int,
    record: HealthRecordModel,
    level: str,
    value: Dict[str, Any]
):
    """内部方法：创建健康告警"""
    alert_titles = {
        'blood_pressure': '血压异常告警',
        'heart_rate': '心率异常告警',
        'blood_sugar': '血糖异常告警',
        'blood_oxygen': '血氧异常告警',
        'temperature': '体温异常告警'
    }

    title = alert_titles.get(record.record_type, '健康指标异常')
    content = f"检测到{record.record_type}指标异常，数值: {json.dumps(value, ensure_ascii=False)}"

    alert = HealthAlertModel(
        user_id=user_id,
        record_id=record.id,
        alert_type=f"{record.record_type}_abnormal",
        level=level,
        title=title,
        content=content,
        record_type=record.record_type,
        record_value=json.dumps(value, ensure_ascii=False)
    )

    db.add(alert)
    db.commit()


@router.get("/alert/list/{user_id}", response_model=dict)
async def get_health_alerts(
    user_id: str,
    is_handled: Optional[bool] = None,
    level: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """获取健康告警列表"""
    cutoff = datetime.now() - timedelta(days=days)

    query = db.query(HealthAlertModel).filter(
        HealthAlertModel.user_id == int(user_id),
        HealthAlertModel.created_at > cutoff
    )

    if is_handled is not None:
        query = query.filter(HealthAlertModel.is_handled == is_handled)

    if level:
        query = query.filter(HealthAlertModel.level == level)

    total = query.count()
    alerts = query.order_by(
        HealthAlertModel.created_at.desc()
    ).offset(offset).limit(limit).all()

    return {
        'user_id': user_id,
        'total': total,
        'alerts': [
            {
                'id': str(a.id),
                'user_id': str(a.user_id),
                'alert_type': a.alert_type,
                'level': a.level,
                'title': a.title,
                'content': a.content,
                "record_type": a.record_type,
                "record_value": json.loads(a.record_value) if a.record_value else None,
                'is_read': a.is_read,
                'is_handled': a.is_handled,
                'handled_at': a.handled_at.isoformat() if a.handled_at else None,
                'handled_by': a.handled_by,
                "handle_notes": a.handle_notes,
                'created_at': a.created_at.isoformat()
            }
            for a in alerts
        ]
    }


@router.put("/alert/{alert_id}/read", response_model=dict)
async def mark_alert_read(
    alert_id: str,
    db: Session = Depends(get_db)
):
    """标记告警为已读"""
    alert = db.query(HealthAlertModel).filter(
        HealthAlertModel.id == int(alert_id)
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail='告警不存在')

    alert.is_read = True
    db.commit()

    return {'success': True, 'message': "已标记为已读"}


@router.put("/alert/{alert_id}/handle", response_model=dict)
async def handle_alert(
    alert_id: str,
    request: HandleAlertRequest,
    db: Session = Depends(get_db)
):
    """处理健康告警"""
    alert = db.query(HealthAlertModel).filter(
        HealthAlertModel.id == int(alert_id)
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail='告警不存在')

    alert.is_handled = True
    alert.handled_at = datetime.now()
    alert.handled_by = request.handled_by
    alert.handle_notes = request.handle_notes
    alert.is_read = True

    db.commit()

    return {
        'success': True,
        'message': "告警已处理"
    }


# ========== 健康报告 ==========

@router.get("/report/weekly/{user_id}", response_model=dict)
async def get_weekly_health_report(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """获取周健康报告"""
    week_ago = datetime.now() - timedelta(days=7)

    # 获取本周健康数据
    records = db.query(HealthRecordModel).filter(
        HealthRecordModel.user_id == int(user_id),
        HealthRecordModel.measured_at > week_ago
    ).all()

    # 按类型统计
    type_stats: Dict[str, List] = {}
    for r in records:
        if r.record_type not in type_stats:
            type_stats[r.record_type] = []
        type_stats[r.record_type].append(r)

    # 生成报告摘要
    summaries = []
    total_score = 100
    recommendations = []

    for record_type, type_records in type_stats.items():
        abnormal_count = sum(1 for r in type_records if r.is_abnormal)

        # 最新值
        latest = max(type_records, key=lambda r: r.measured_at)
        latest_value = build_value_dict(latest)

        # 平均值（只取主数值）
        primary_values = [r.value_primary for r in type_records if r.value_primary]
        avg_value = sum(primary_values) / len(primary_values) if primary_values else None

        # 趋势判断
        trend = "stable"
        if len(type_records) >= 3:
            sorted_records = sorted(type_records, key=lambda r: r.measured_at)
            first_half = [r.value_primary for r in sorted_records[:len(sorted_records)//2] if r.value_primary]
            second_half = [r.value_primary for r in sorted_records[len(sorted_records)//2:] if r.value_primary]
            if first_half and second_half:
                first_avg = sum(first_half) / len(first_half)
                second_avg = sum(second_half) / len(second_half)
                if second_avg > first_avg * 1.05:
                    trend = 'increasing'
                elif second_avg < first_avg * 0.95:
                    trend = 'decreasing'

        summaries.append({
            "record_type": record_type,
            "record_count": len(type_records),
            "latest_value": latest_value,
            "average_value": round(avg_value, 2) if avg_value else None,
            "alert_count": abnormal_count,
            'trend': trend
        })

        # 根据异常情况扣分
        if abnormal_count > 0:
            total_score -= abnormal_count * 5
            recommendations.append(f"本周{record_type}指标出现{abnormal_count}次异常，请注意监测")

    # 健康建议
    if not type_stats:
        recommendations.append("本周暂无健康数据记录，建议定期测量血压、心率等指标")
        total_score = 0
    else:
        if "blood_pressure" not in type_stats:
            recommendations.append("建议每日测量血压，及时掌握心血管健康状况")
        if "heart_rate" not in type_stats:
            recommendations.append("建议定期检测心率，了解心脏功能状态")

    total_score = max(0, min(100, total_score))

    return {
        'user_id': user_id,
        'report_type': 'weekly',
        'start_date': week_ago.date().isoformat(),
        'end_date': datetime.now().date().isoformat(),
        "summaries": summaries,
        "overall_score": total_score,
        "recommendations": recommendations,
        "generated_at": datetime.now().isoformat()
    }


@router.get("/report/monthly/{user_id}", response_model=dict)
async def get_monthly_health_report(
    user_id: str,
    db: Session = Depends(get_db)
):
    """获取月健康报告"""
    month_ago = datetime.now() - timedelta(days=30)

    records = db.query(HealthRecordModel).filter(
        HealthRecordModel.user_id == int(user_id),
        HealthRecordModel.measured_at > month_ago
    ).all()

    # 告警统计
    alerts = db.query(HealthAlertModel).filter(
        HealthAlertModel.user_id == int(user_id),
        HealthAlertModel.created_at > month_ago
    ).all()

    type_stats: Dict[str, List] = {}
    for r in records:
        if r.record_type not in type_stats:
            type_stats[r.record_type] = []
        type_stats[r.record_type].append(r)

    summaries = []
    for record_type, type_records in type_stats.items():
        abnormal_count = sum(1 for r in type_records if r.is_abnormal)
        latest = max(type_records, key=lambda r: r.measured_at)
        latest_value = build_value_dict(latest)

        primary_values = [r.value_primary for r in type_records if r.value_primary]
        avg_value = sum(primary_values) / len(primary_values) if primary_values else None

        summaries.append({
            "record_type": record_type,
            "record_count": len(type_records),
            "latest_value": latest_value,
            "average_value": round(avg_value, 2) if avg_value else None,
            "alert_count": abnormal_count,
            'trend': 'stable'
        })

    # 计算评分
    total_alerts = len(alerts)
    critical_alerts = sum(1 for a in alerts if a.level == 'critical')
    high_alerts = sum(1 for a in alerts if a.level == 'high')

    score = 100 - (critical_alerts * 15) - (high_alerts * 8) - (total_alerts * 2)
    score = max(0, min(100, score))

    recommendations = []
    if critical_alerts > 0:
        recommendations.append(f"本月有{critical_alerts}次严重告警，建议尽快就医检查")
    if high_alerts > 0:
        recommendations.append(f"本月有{high_alerts}次高级别告警，请密切关注相关指标")
    if score >= 80:
        recommendations.append("整体健康状况良好，请继续保持")

    return {
        'user_id': user_id,
        'report_type': 'monthly',
        'start_date': month_ago.date().isoformat(),
        'end_date': datetime.now().date().isoformat(),
        "summaries": summaries,
        "overall_score": score,
        "total_records": len(records),
        "total_alerts": total_alerts,
        "critical_alerts": critical_alerts,
        "high_alerts": high_alerts,
        "recommendations": recommendations,
        "generated_at": datetime.now().isoformat()
    }


# ========== 健康统计 ==========

@router.get("/stats/{user_id}", response_model=dict)
async def get_health_statistics(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """获取健康数据统计"""
    cutoff = datetime.now() - timedelta(days=days)

    # 记录统计
    records = db.query(HealthRecordModel).filter(
        HealthRecordModel.user_id == int(user_id),
        HealthRecordModel.measured_at > cutoff
    ).all()

    # 告警统计
    alerts = db.query(HealthAlertModel).filter(
        HealthAlertModel.user_id == int(user_id),
        HealthAlertModel.created_at > cutoff
    ).all()

    # 按类型统计
    type_counts = {}
    abnormal_counts = {}
    for r in records:
        type_counts[r.record_type] = type_counts.get(r.record_type, 0) + 1
        if r.is_abnormal:
            abnormal_counts[r.record_type] = abnormal_counts.get(r.record_type, 0) + 1

    # 告警级别统计
    alert_levels = {}
    for a in alerts:
        alert_levels[a.level] = alert_levels.get(a.level, 0) + 1

    return {
        "user_id": user_id,
        "period_days": days,
        "total_records": len(records),
        "total_alerts": len(alerts),
        "records_by_type": type_counts,
        "abnormal_by_type": abnormal_counts,
        "alerts_by_level": alert_levels,
        "unhandled_alerts": sum(1 for a in alerts if not a.is_handled)
    }
