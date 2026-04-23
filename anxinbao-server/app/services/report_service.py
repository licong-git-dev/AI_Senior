"""
报表导出服务
提供PDF/Excel健康报告、数据导出等功能
"""
import logging
import io
import csv
import json
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from collections import defaultdict
import secrets

logger = logging.getLogger(__name__)


# ==================== 基础定义 ====================

class ReportType(Enum):
    """报表类型"""
    HEALTH_SUMMARY = "health_summary"  # 健康摘要
    HEALTH_DETAILED = "health_detailed"  # 健康详细报告
    MEDICATION_RECORD = "medication_record"  # 用药记录
    EXERCISE_RECORD = "exercise_record"  # 运动记录
    NUTRITION_RECORD = "nutrition_record"  # 饮食记录
    MOOD_RECORD = "mood_record"  # 情绪记录
    ACTIVITY_RECORD = "activity_record"  # 活动记录
    FAMILY_REPORT = "family_report"  # 家庭报告
    ADMIN_ANALYTICS = "admin_analytics"  # 管理员分析报表


class ExportFormat(Enum):
    """导出格式"""
    PDF = "pdf"
    EXCEL = 'excel'
    CSV = "csv"
    JSON = "json"


class ReportStatus(Enum):
    """报表状态"""
    PENDING = "pending"
    GENERATING = 'generating'
    COMPLETED = 'completed'
    FAILED = 'failed'
    EXPIRED = 'expired'


# ==================== 数据模型 ====================

@dataclass
class ReportConfig:
    """报表配置"""
    report_type: ReportType
    title: str
    description: str
    available_formats: List[ExportFormat]
    requires_date_range: bool = True
    max_days: int = 365
    default_days: int = 30

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_type": self.report_type.value,
            'title': self.title,
            "description": self.description,
            "available_formats": [f.value for f in self.available_formats],
            "requires_date_range": self.requires_date_range,
            'max_days': self.max_days,
            "default_days": self.default_days
        }


@dataclass
class ReportRequest:
    """报表请求"""
    request_id: str
    user_id: int
    report_type: ReportType
    export_format: ExportFormat
    start_date: date
    end_date: date
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: ReportStatus = ReportStatus.PENDING
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            "report_type": self.report_type.value,
            "export_format": self.export_format.value,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'status': self.status.value,
            'file_path': self.file_path,
            'file_size': self.file_size,
            "error_message": self.error_message,
            'created_at': self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class ReportTemplate:
    """报表模板"""
    template_id: str
    name: str
    report_type: ReportType
    sections: List[Dict[str, Any]]
    header_config: Dict[str, Any] = field(default_factory=dict)
    footer_config: Dict[str, Any] = field(default_factory=dict)
    style_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            'name': self.name,
            "report_type": self.report_type.value,
            'sections': self.sections
        }


# ==================== 报表配置 ====================

REPORT_CONFIGS = {
    ReportType.HEALTH_SUMMARY: ReportConfig(
        ReportType.HEALTH_SUMMARY,
        "健康摘要报告",
        "包含血压、心率、血糖等核心健康指标的周期性摘要",
        [ExportFormat.PDF, ExportFormat.EXCEL, ExportFormat.CSV],
        default_days=7
    ),
    ReportType.HEALTH_DETAILED: ReportConfig(
        ReportType.HEALTH_DETAILED,
        "健康详细报告",
        "详细的健康数据分析报告，包含趋势图表和建议",
        [ExportFormat.PDF],
        default_days=30
    ),
    ReportType.MEDICATION_RECORD: ReportConfig(
        ReportType.MEDICATION_RECORD,
        "用药记录报告",
        "用药情况记录，包含服药时间、剂量和依从性",
        [ExportFormat.PDF, ExportFormat.EXCEL, ExportFormat.CSV],
        default_days=30
    ),
    ReportType.EXERCISE_RECORD: ReportConfig(
        ReportType.EXERCISE_RECORD,
        "运动记录报告",
        "运动锻炼情况记录，包含运动类型、时长和消耗",
        [ExportFormat.PDF, ExportFormat.EXCEL],
        default_days=30
    ),
    ReportType.NUTRITION_RECORD: ReportConfig(
        ReportType.NUTRITION_RECORD,
        "饮食记录报告",
        "饮食营养记录，包含热量摄入和营养分析",
        [ExportFormat.PDF, ExportFormat.EXCEL],
        default_days=7
    ),
    ReportType.MOOD_RECORD: ReportConfig(
        ReportType.MOOD_RECORD,
        "情绪记录报告",
        "情绪变化记录和心理健康趋势",
        [ExportFormat.PDF, ExportFormat.CSV],
        default_days=30
    ),
    ReportType.ACTIVITY_RECORD: ReportConfig(
        ReportType.ACTIVITY_RECORD,
        '活动参与报告',
        '社区活动参与情况记录',
        [ExportFormat.PDF, ExportFormat.EXCEL],
        default_days=90
    ),
    ReportType.FAMILY_REPORT: ReportConfig(
        ReportType.FAMILY_REPORT,
        "家庭健康报告",
        "为家属提供的老人健康状况综合报告",
        [ExportFormat.PDF],
        default_days=7
    ),
    ReportType.ADMIN_ANALYTICS: ReportConfig(
        ReportType.ADMIN_ANALYTICS,
        "运营分析报表",
        "用户活跃度、功能使用等运营数据分析",
        [ExportFormat.PDF, ExportFormat.EXCEL],
        default_days=30,
        max_days=365
    )
}


# ==================== 数据生成器 ====================

class ReportDataGenerator:
    """报表数据生成器"""

    def generate_health_summary(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """生成健康摘要数据"""
        # 模拟数据生成
        days = (end_date - start_date).days + 1

        return {
            'user_id': user_id,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                "days": days
            },
            "vital_signs": {
                "blood_pressure": {
                    "systolic_avg": 125,
                    "systolic_max": 138,
                    "systolic_min": 118,
                    "diastolic_avg": 82,
                    "diastolic_max": 88,
                    "diastolic_min": 75,
                    "records_count": days,
                    'status': '正常'
                },
                'heart_rate': {
                    'avg': 72,
                    'max': 85,
                    "min": 62,
                    "records_count": days,
                    'status': "正常"
                },
                "blood_sugar": {
                    "fasting_avg": 5.6,
                    "postprandial_avg": 7.2,
                    "records_count": days // 2,
                    'status': '正常'
                }
            },
            "activity": {
                "total_steps": 45000,
                "avg_daily_steps": 45000 // days,
                "active_days": days - 2,
                "total_exercise_minutes": 180
            },
            'medication': {
                "compliance_rate": 92.5,
                "missed_doses": 2,
                "total_doses": 28
            },
            'sleep': {
                'avg_hours': 7.2,
                "quality_score": 75
            },
            'summary': "整体健康状况良好，建议继续保持规律作息。",
            "recommendations": [
                "血压控制良好，继续保持",
                "建议每日步数提高到6000步以上",
                "注意规律服药，提高用药依从性"
            ]
        }

    def generate_medication_record(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """生成用药记录数据"""
        return {
            'user_id': user_id,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            "medications": [
                {
                    'name': '阿司匹林肠溶片',
                    'dosage': '100mg',
                    'frequency': "每日一次",
                    "scheduled_doses": 30,
                    "taken_doses": 28,
                    "compliance_rate": 93.3
                },
                {
                    'name': '氨氯地平片',
                    'dosage': '5mg',
                    'frequency': "每日一次",
                    "scheduled_doses": 30,
                    "taken_doses": 29,
                    "compliance_rate": 96.7
                }
            ],
            "overall_compliance": 95.0,
            "missed_records": [
                {'date': "2024-01-05", 'medication': '阿司匹林肠溶片', 'reason': '外出忘记'},
                {'date': '2024-01-12', 'medication': '阿司匹林肠溶片', 'reason': "未记录"}
            ]
        }

    def generate_exercise_record(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """生成运动记录数据"""
        return {
            'user_id': user_id,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'summary': {
                "total_sessions": 15,
                "total_duration_minutes": 450,
                "total_calories": 1800,
                "active_days": 12
            },
            'by_type': [
                {'type': '散步', 'sessions': 10, 'duration': 300, 'calories': 900},
                {'type': '太极拳', 'sessions': 3, 'duration': 90, 'calories': 450},
                {'type': '健身操', 'sessions': 2, 'duration': 60, "calories": 450}
            ],
            "weekly_trend": [
                {'week': '第1周', 'sessions': 4, 'duration': 120},
                {'week': '第2周', 'sessions': 5, 'duration': 150},
                {'week': '第3周', 'sessions': 3, 'duration': 90},
                {'week': '第4周', 'sessions': 3, "duration": 90}
            ]
        }

    def generate_family_report(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """生成家庭报告数据"""
        health_data = self.generate_health_summary(user_id, start_date, end_date)

        return {
            'user_id': user_id,
            'user_name': f'老人{user_id}',
            'period': {
                'start': start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "health_overview": {
                'status': '良好',
                'score': 85,
                'trend': "稳定"
            },
            "vital_signs": health_data["vital_signs"],
            'alerts': [
                {'date': "2024-01-10", 'type': '血压偏高', 'value': '145/92', "handled": True}
            ],
            "activity_summary": {
                "social_activities": 3,
                "exercise_sessions": 15,
                "calls_with_family": 8
            },
            "care_suggestions": [
                "血压偶有波动，建议关注情绪变化",
                "近期活动量充足，状态良好",
                "建议增加视频通话频次，关心老人心理状态"
            ]
        }


# ==================== 报表生成器 ====================

class PDFGenerator:
    """PDF生成器"""

    def generate(
        self,
        data: Dict[str, Any],
        template: ReportTemplate,
        output_path: str
    ) -> Tuple[bool, str]:
        """生成PDF报告"""
        try:
            # 简化实现，实际需要使用reportlab等库
            content = self._build_pdf_content(data, template)

            # 这里应该使用PDF库生成实际文件
            # 目前创建一个模拟文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f'PDF Report: {template.name}\n')
                f.write(f'Generated: {datetime.now().isoformat()}\n')
                f.write('-' * 50 + '\n')
                f.write(json.dumps(data, ensure_ascii=False, indent=2))

            return True, 'PDF生成成功'
        except Exception as e:
            logger.error(f"PDF生成失败: {e}")
            return False, str(e)

    def _build_pdf_content(
        self,
        data: Dict[str, Any],
        template: ReportTemplate
    ) -> bytes:
        """构建PDF内容"""
        # 实际实现需要使用reportlab
        return b""


class ExcelGenerator:
    """Excel生成器"""

    def generate(
        self,
        data: Dict[str, Any],
        template: ReportTemplate,
        output_path: str
    ) -> Tuple[bool, str]:
        """生成Excel报告"""
        try:
            # 简化实现，实际需要使用openpyxl等库
            content = self._build_excel_content(data, template)

            # 创建CSV作为Excel的简化版
            with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([f'报表: {template.name}'])
                writer.writerow([f'生成时间: {datetime.now().isoformat()}'])
                writer.writerow([])

                # 写入数据
                self._write_dict_to_csv(writer, data)

            return True, 'Excel生成成功'
        except Exception as e:
            logger.error(f"Excel生成失败: {e}")
            return False, str(e)

    def _build_excel_content(
        self,
        data: Dict[str, Any],
        template: ReportTemplate
    ) -> bytes:
        """构建Excel内容"""
        return b""

    def _write_dict_to_csv(self, writer, data: Dict, prefix: str = ""):
        """将字典写入CSV"""
        for key, value in data.items():
            if isinstance(value, dict):
                writer.writerow([f'{prefix}{key}:'])
                self._write_dict_to_csv(writer, value, prefix + "  ")
            elif isinstance(value, list):
                writer.writerow([f'{prefix}{key}:'])
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        writer.writerow([f'{prefix}  [{i}]'])
                        self._write_dict_to_csv(writer, item, prefix + '    ')
                    else:
                        writer.writerow([f'{prefix}  ', item])
            else:
                writer.writerow([f'{prefix}{key}', value])


class CSVGenerator:
    """CSV生成器"""

    def generate(
        self,
        data: Dict[str, Any],
        template: ReportTemplate,
        output_path: str
    ) -> Tuple[bool, str]:
        """生成CSV报告"""
        try:
            with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                self._flatten_and_write(writer, data)

            return True, 'CSV生成成功'
        except Exception as e:
            logger.error(f"CSV生成失败: {e}")
            return False, str(e)

    def _flatten_and_write(self, writer, data: Dict):
        """展平数据并写入"""
        flat_data = self._flatten_dict(data)
        writer.writerow(['字段', '值'])
        for key, value in flat_data.items():
            writer.writerow([key, value])

    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = ".") -> Dict:
        """展平嵌套字典"""
        items = []
        for k, v in d.items():
            new_key = f'{parent_key}{sep}{k}' if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                    else:
                        items.append((f'{new_key}[{i}]', item))
            else:
                items.append((new_key, v))
        return dict(items)


class JSONGenerator:
    """JSON生成器"""

    def generate(
        self,
        data: Dict[str, Any],
        template: ReportTemplate,
        output_path: str
    ) -> Tuple[bool, str]:
        """生成JSON报告"""
        try:
            output = {
                'report': {
                    'name': template.name,
                    'type': template.report_type.value,
                    "generated_at": datetime.now().isoformat()
                },
                'data': data
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

            return True, 'JSON生成成功'
        except Exception as e:
            logger.error(f"JSON生成失败: {e}")
            return False, str(e)


# ==================== 报表服务 ====================

class ReportExportService:
    """报表导出服务"""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        self.requests: Dict[str, ReportRequest] = {}
        self.user_requests: Dict[int, List[str]] = defaultdict(list)

        self.data_generator = ReportDataGenerator()
        self.pdf_generator = PDFGenerator()
        self.excel_generator = ExcelGenerator()
        self.csv_generator = CSVGenerator()
        self.json_generator = JSONGenerator()

        self.templates = self._init_templates()

        # 确保输出目录存在
        import os
        os.makedirs(output_dir, exist_ok=True)

    def _init_templates(self) -> Dict[ReportType, ReportTemplate]:
        """初始化报表模板"""
        templates = {}

        templates[ReportType.HEALTH_SUMMARY] = ReportTemplate(
            template_id="tpl_health_summary",
            name='健康摘要报告',
            report_type=ReportType.HEALTH_SUMMARY,
            sections=[
                {'type': 'header', 'title': '健康摘要报告'},
                {'type': 'period', 'title': '报告周期'},
                {'type': 'vital_signs', 'title': '生命体征'},
                {'type': 'activity', 'title': '活动统计'},
                {'type': 'recommendations', 'title': "健康建议"}
            ]
        )

        templates[ReportType.HEALTH_DETAILED] = ReportTemplate(
            template_id="tpl_health_detailed",
            name='健康详细报告',
            report_type=ReportType.HEALTH_DETAILED,
            sections=[
                {'type': 'header', 'title': '健康详细报告'},
                {'type': 'summary', 'title': '健康概览'},
                {'type': 'vital_signs_chart', 'title': '生命体征趋势'},
                {'type': 'analysis', 'title': '数据分析'},
                {'type': 'recommendations', 'title': "医疗建议"}
            ]
        )

        templates[ReportType.FAMILY_REPORT] = ReportTemplate(
            template_id="tpl_family_report",
            name='家庭健康报告',
            report_type=ReportType.FAMILY_REPORT,
            sections=[
                {'type': 'header', 'title': '家庭健康报告'},
                {'type': 'overview', 'title': '健康概览'},
                {'type': 'alerts', 'title': '健康预警'},
                {'type': 'activity', 'title': '活动情况'},
                {'type': 'suggestions', 'title': "关怀建议"}
            ]
        )

        return templates

    def get_available_reports(self) -> List[Dict[str, Any]]:
        """获取可用报表类型"""
        return [config.to_dict() for config in REPORT_CONFIGS.values()]

    def create_report_request(
        self,
        user_id: int,
        report_type: ReportType,
        export_format: ExportFormat,
        start_date: date,
        end_date: date,
        parameters: Dict[str, Any] = None
    ) -> ReportRequest:
        """创建报表请求"""
        request_id = f"rpt_{user_id}_{secrets.token_hex(6)}"

        request = ReportRequest(
            request_id=request_id,
            user_id=user_id,
            report_type=report_type,
            export_format=export_format,
            start_date=start_date,
            end_date=end_date,
            parameters=parameters or {}
        )

        self.requests[request_id] = request
        self.user_requests[user_id].append(request_id)

        return request

    def generate_report(self, request_id: str) -> Tuple[bool, str]:
        """生成报表"""
        request = self.requests.get(request_id)
        if not request:
            return False, "报表请求不存在"

        request.status = ReportStatus.GENERATING

        try:
            # 生成数据
            data = self._generate_data(request)

            # 获取模板
            template = self.templates.get(request.report_type)
            if not template:
                template = ReportTemplate(
                    template_id=f"tpl_{request.report_type.value}",
                    name=REPORT_CONFIGS[request.report_type].title,
                    report_type=request.report_type,
                    sections=[]
                )

            # 确定输出文件
            ext = {
                ExportFormat.PDF: '.txt',  # 简化实现
                ExportFormat.EXCEL: '.csv',  # 简化实现
                ExportFormat.CSV: '.csv',
                ExportFormat.JSON: ".json"
            }[request.export_format]

            output_path = f"{self.output_dir}/{request_id}{ext}"

            # 生成文件
            generator = {
                ExportFormat.PDF: self.pdf_generator,
                ExportFormat.EXCEL: self.excel_generator,
                ExportFormat.CSV: self.csv_generator,
                ExportFormat.JSON: self.json_generator
            }[request.export_format]

            success, message = generator.generate(data, template, output_path)

            if success:
                import os
                request.status = ReportStatus.COMPLETED
                request.file_path = output_path
                request.file_size = os.path.getsize(output_path)
                request.completed_at = datetime.now()
                return True, '报表生成成功'
            else:
                request.status = ReportStatus.FAILED
                request.error_message = message
                return False, message

        except Exception as e:
            logger.error(f"报表生成失败: {e}")
            request.status = ReportStatus.FAILED
            request.error_message = str(e)
            return False, str(e)

    def _generate_data(self, request: ReportRequest) -> Dict[str, Any]:
        """根据报表类型生成数据"""
        if request.report_type == ReportType.HEALTH_SUMMARY:
            return self.data_generator.generate_health_summary(
                request.user_id, request.start_date, request.end_date
            )
        elif request.report_type == ReportType.HEALTH_DETAILED:
            return self.data_generator.generate_health_summary(
                request.user_id, request.start_date, request.end_date
            )
        elif request.report_type == ReportType.MEDICATION_RECORD:
            return self.data_generator.generate_medication_record(
                request.user_id, request.start_date, request.end_date
            )
        elif request.report_type == ReportType.EXERCISE_RECORD:
            return self.data_generator.generate_exercise_record(
                request.user_id, request.start_date, request.end_date
            )
        elif request.report_type == ReportType.FAMILY_REPORT:
            return self.data_generator.generate_family_report(
                request.user_id, request.start_date, request.end_date
            )
        else:
            return {'message': "数据生成未实现", "report_type": request.report_type.value}

    def get_report_status(self, request_id: str) -> Optional[ReportRequest]:
        """获取报表状态"""
        return self.requests.get(request_id)

    def get_user_reports(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[ReportRequest]:
        """获取用户的报表列表"""
        request_ids = self.user_requests.get(user_id, [])
        requests = [self.requests[rid] for rid in request_ids if rid in self.requests]
        return sorted(requests, key=lambda x: x.created_at, reverse=True)[:limit]

    def delete_report(self, request_id: str, user_id: int) -> Tuple[bool, str]:
        """删除报表"""
        request = self.requests.get(request_id)
        if not request:
            return False, '报表不存在'

        if request.user_id != user_id:
            return False, '无权删除'

        # 删除文件
        if request.file_path:
            try:
                import os
                if os.path.exists(request.file_path):
                    os.remove(request.file_path)
            except Exception as e:
                logger.warning(f'删除报表文件失败: {e}')

        # 删除记录
        del self.requests[request_id]
        if request_id in self.user_requests[user_id]:
            self.user_requests[user_id].remove(request_id)

        return True, "报表已删除"

    def cleanup_expired_reports(self) -> int:
        """清理过期报表"""
        now = datetime.now()
        expired_ids = [
            rid for rid, req in self.requests.items()
            if req.expires_at < now
        ]

        for rid in expired_ids:
            req = self.requests.get(rid)
            if req:
                self.delete_report(rid, req.user_id)

        return len(expired_ids)


# ==================== 全局实例 ====================

report_service = ReportExportService()
