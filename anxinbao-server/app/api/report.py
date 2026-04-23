"""
报表导出API
提供健康报告、数据导出等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta

from app.services.report_service import (
    report_service,
    ReportType,
    ExportFormat,
    ReportStatus,
    REPORT_CONFIGS
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/reports", tags=["报表导出"])


# ==================== 请求模型 ====================

class CreateReportRequest(BaseModel):
    """创建报表请求"""
    report_type: str = Field(..., description="报表类型")
    export_format: str = Field(..., description="导出格式: pdf/excel/csv/json")
    start_date: date = Field(..., description='开始日期')
    end_date: date = Field(..., description='结束日期')
    parameters: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class QuickReportRequest(BaseModel):
    """快速报表请求"""
    report_type: str = Field(..., description='报表类型')
    export_format: str = Field('pdf', description='导出格式')
    days: int = Field(7, ge=1, le=365, description='天数')


# ==================== 报表类型API ====================

@router.get("/types")
async def get_report_types(current_user: dict = Depends(get_current_user)):
    """
    获取可用的报表类型

    列出所有支持的报表类型及其配置
    """
    types = report_service.get_available_reports()

    return {
        "report_types": types,
        'count': len(types)
    }


@router.get("/types/{report_type}")
async def get_report_type_detail(
    report_type: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取报表类型详情
    """
    try:
        rtype = ReportType(report_type)
    except ValueError:
        raise HTTPException(status_code=400, detail='无效的报表类型')

    config = REPORT_CONFIGS.get(rtype)
    if not config:
        raise HTTPException(status_code=404, detail='报表类型不存在')

    return config.to_dict()


@router.get("/formats")
async def get_export_formats(current_user: dict = Depends(get_current_user)):
    """
    获取支持的导出格式
    """
    formats = [
        {'value': f.value, 'label': f.value.upper()}
        for f in ExportFormat
    ]

    return {'formats': formats}


# ==================== 报表生成API ====================

@router.post("/create")
async def create_report(
    request: CreateReportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    创建报表

    异步生成报表，返回请求ID用于查询状态
    """
    user_id = int(current_user['sub'])

    # 验证报表类型
    try:
        report_type = ReportType(request.report_type)
    except ValueError:
        valid_types = [t.value for t in ReportType]
        raise HTTPException(
            status_code=400,
            detail=f'无效的报表类型，可选: {valid_types}'
        )

    # 验证导出格式
    try:
        export_format = ExportFormat(request.export_format)
    except ValueError:
        valid_formats = [f.value for f in ExportFormat]
        raise HTTPException(
            status_code=400,
            detail=f'无效的导出格式，可选: {valid_formats}'
        )

    # 检查导出格式是否支持
    config = REPORT_CONFIGS.get(report_type)
    if config and export_format not in config.available_formats:
        available = [f.value for f in config.available_formats]
        raise HTTPException(
            status_code=400,
            detail=f'该报表类型不支持此格式，可用格式: {available}'
        )

    # 验证日期范围
    if request.end_date < request.start_date:
        raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")

    days = (request.end_date - request.start_date).days
    if config and days > config.max_days:
        raise HTTPException(
            status_code=400,
            detail=f"日期范围不能超过{config.max_days}天"
        )

    # 创建报表请求
    report_request = report_service.create_report_request(
        user_id,
        report_type,
        export_format,
        request.start_date,
        request.end_date,
        request.parameters
    )

    # 后台生成报表
    background_tasks.add_task(
        report_service.generate_report,
        report_request.request_id
    )

    return {
        'success': True,
        'request_id': report_request.request_id,
        "message": "报表正在生成中，请稍后查询状态",
        'status_url': f"/api/reports/{report_request.request_id}/status"
    }


@router.post("/quick")
async def quick_report(
    request: QuickReportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    快速生成报表

    使用默认日期范围快速生成报表
    """
    user_id = int(current_user['sub'])

    try:
        report_type = ReportType(request.report_type)
    except ValueError:
        raise HTTPException(status_code=400, detail='无效的报表类型')

    try:
        export_format = ExportFormat(request.export_format)
    except ValueError:
        raise HTTPException(status_code=400, detail='无效的导出格式')

    end_date = date.today()
    start_date = end_date - timedelta(days=request.days - 1)

    report_request = report_service.create_report_request(
        user_id,
        report_type,
        export_format,
        start_date,
        end_date
    )

    # 后台生成报表
    background_tasks.add_task(
        report_service.generate_report,
        report_request.request_id
    )

    return {
        'success': True,
        'request_id': report_request.request_id,
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
            'days': request.days
        },
        'message': "报表正在生成中"
    }


# ==================== 报表状态和下载API ====================

@router.get("/{request_id}/status")
async def get_report_status(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    查询报表状态
    """
    user_id = int(current_user['sub'])

    report_request = report_service.get_report_status(request_id)

    if not report_request:
        raise HTTPException(status_code=404, detail='报表请求不存在')

    if report_request.user_id != user_id:
        raise HTTPException(status_code=403, detail='无权访问此报表')

    return {
        "request": report_request.to_dict(),
        "can_download": report_request.status == ReportStatus.COMPLETED
    }


@router.get("/{request_id}/download")
async def download_report(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    下载报表

    下载已生成的报表文件
    """
    user_id = int(current_user['sub'])

    report_request = report_service.get_report_status(request_id)

    if not report_request:
        raise HTTPException(status_code=404, detail='报表请求不存在')

    if report_request.user_id != user_id:
        raise HTTPException(status_code=403, detail='无权访问此报表')

    if report_request.status != ReportStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f'报表尚未生成完成，当前状态: {report_request.status.value}'
        )

    if not report_request.file_path:
        raise HTTPException(status_code=500, detail='报表文件不存在')

    # 确定文件名
    config = REPORT_CONFIGS.get(report_request.report_type)
    filename = f"{config.title if config else '报表'}_{report_request.start_date}_{report_request.end_date}"

    ext_map = {
        ExportFormat.PDF: ".pdf",
        ExportFormat.EXCEL: '.xlsx',
        ExportFormat.CSV: '.csv',
        ExportFormat.JSON: '.json'
    }
    filename += ext_map.get(report_request.export_format, '.txt')

    return FileResponse(
        path=report_request.file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.delete("/{request_id}")
async def delete_report(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    删除报表
    """
    user_id = int(current_user['sub'])

    success, message = report_service.delete_report(request_id, user_id)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        'success': True,
        'message': message
    }


# ==================== 报表列表API ====================

@router.get("/list")
async def get_my_reports(
    status: Optional[str] = Query(None, description='状态筛选'),
    report_type: Optional[str] = Query(None, description='类型筛选'),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取我的报表列表
    """
    user_id = int(current_user['sub'])

    reports = report_service.get_user_reports(user_id, limit)

    # 过滤状态
    if status:
        try:
            status_filter = ReportStatus(status)
            reports = [r for r in reports if r.status == status_filter]
        except ValueError:
            pass

    # 过滤类型
    if report_type:
        try:
            type_filter = ReportType(report_type)
            reports = [r for r in reports if r.report_type == type_filter]
        except ValueError:
            pass

    return {
        'reports': [r.to_dict() for r in reports],
        "count": len(reports)
    }


# ==================== 常用报表快捷方式 ====================

@router.post("/health-summary")
async def generate_health_summary(
    days: int = Query(7, ge=1, le=90, description='天数'),
    export_format: str = Query('pdf', description="导出格式"),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    """
    生成健康摘要报告

    快速生成健康摘要
    """
    user_id = int(current_user['sub'])

    try:
        fmt = ExportFormat(export_format)
    except ValueError:
        fmt = ExportFormat.PDF

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    report_request = report_service.create_report_request(
        user_id,
        ReportType.HEALTH_SUMMARY,
        fmt,
        start_date,
        end_date
    )

    if background_tasks:
        background_tasks.add_task(
            report_service.generate_report,
            report_request.request_id
        )

    return {
        'success': True,
        'request_id': report_request.request_id,
        'message': "健康摘要报告正在生成中"
    }


@router.post("/family-report")
async def generate_family_report(
    elderly_id: int = Query(..., description='老人用户ID'),
    days: int = Query(7, ge=1, le=30, description="天数"),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    """
    生成家庭报告

    为家属生成老人健康状况报告
    """
    # 这里应该验证当前用户是否是老人的家属
    # 简化实现，直接使用elderly_id

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    report_request = report_service.create_report_request(
        elderly_id,
        ReportType.FAMILY_REPORT,
        ExportFormat.PDF,
        start_date,
        end_date,
        {"requested_by": int(current_user['sub'])}
    )

    if background_tasks:
        background_tasks.add_task(
            report_service.generate_report,
            report_request.request_id
        )

    return {
        'success': True,
        'request_id': report_request.request_id,
        'message': "家庭健康报告正在生成中"
    }


@router.post("/medication-report")
async def generate_medication_report(
    days: int = Query(30, ge=7, le=90, description='天数'),
    export_format: str = Query('pdf', description="导出格式"),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    """
    生成用药报告

    生成用药记录和依从性报告
    """
    user_id = int(current_user['sub'])

    try:
        fmt = ExportFormat(export_format)
    except ValueError:
        fmt = ExportFormat.PDF

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    report_request = report_service.create_report_request(
        user_id,
        ReportType.MEDICATION_RECORD,
        fmt,
        start_date,
        end_date
    )

    if background_tasks:
        background_tasks.add_task(
            report_service.generate_report,
            report_request.request_id
        )

    return {
        'success': True,
        'request_id': report_request.request_id,
        'message': "用药报告正在生成中"
    }
