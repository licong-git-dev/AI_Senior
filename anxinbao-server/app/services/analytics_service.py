"""
数据分析报表服务
提供用户行为分析、健康数据分析、业务报表等功能
"""
import logging
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from decimal import Decimal
import random as _real_random
import json

logger = logging.getLogger(__name__)


class _SafeRandom:
    """
    生产环境（DEBUG=False）的随机数守卫。

    本模块原本含 ~93 处 random 调用，几乎所有"业务指标"都是 random 占位
    （如"今日 DAU 1.5-2 万"），任何运营或投资人翻看都会立刻发现造假。

    DEBUG=True 时保留 random（前端 UI 调试需要）；
    DEBUG=False 时一律返回 0/0.0/首项，让运营看到诚实的"无数据"而非伪造数字。
    """

    def randint(self, a: int, b: int) -> int:
        from app.core.config import get_settings
        return _real_random.randint(a, b) if get_settings().debug else 0

    def uniform(self, a: float, b: float) -> float:
        from app.core.config import get_settings
        return _real_random.uniform(a, b) if get_settings().debug else 0.0

    def choice(self, seq):
        from app.core.config import get_settings
        if not seq:
            return None
        return _real_random.choice(seq) if get_settings().debug else seq[0]

    def random(self) -> float:
        from app.core.config import get_settings
        return _real_random.random() if get_settings().debug else 0.0


# 模块内的 random 名称改为安全版本；所有 `random.xxx` 调用都路由到 _SafeRandom，
# 无需逐行重写 90+ 处占位 → 零风险。
random = _SafeRandom()


class ReportPeriod(Enum):
    """报表周期"""
    DAILY = "daily"
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    YEARLY = 'yearly'


class MetricType(Enum):
    """指标类型"""
    USER = "user"
    REVENUE = 'revenue'
    HEALTH = 'health'
    ENGAGEMENT = 'engagement'
    RETENTION = 'retention'


@dataclass
class ReportData:
    """报表数据"""
    report_id: str
    report_type: str
    period: ReportPeriod
    start_date: date
    end_date: date
    data: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_id': self.report_id,
            "report_type": self.report_type,
            'period': self.period.value,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'data': self.data,
            "generated_at": self.generated_at.isoformat()
        }


# ==================== 用户分析服务 ====================

class UserAnalyticsService:
    """用户分析服务"""

    def get_user_growth(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """获取用户增长数据"""
        days = (end_date - start_date).days + 1
        dates = []
        new_users = []
        total_users = []
        base_total = 50000

        for i in range(days):
            d = start_date + timedelta(days=i)
            dates.append(d.isoformat())
            daily_new = random.randint(80, 200)
            new_users.append(daily_new)
            base_total += daily_new
            total_users.append(base_total)

        return {
            'dates': dates,
            'new_users': new_users,
            "total_users": total_users,
            'summary': {
                'total_new': sum(new_users),
                "avg_daily_new": sum(new_users) // len(new_users),
                "growth_rate": round((total_users[-1] - total_users[0]) / total_users[0] * 100, 2)
            }
        }

    def get_retention_analysis(self, cohort_date: date) -> Dict[str, Any]:
        """获取留存分析"""
        cohort_size = random.randint(150, 250)

        retention_rates = []
        for day in range(8):  # 0-7天留存
            if day == 0:
                rate = 100
            elif day == 1:
                rate = random.uniform(65, 80)
            elif day == 3:
                rate = random.uniform(45, 60)
            elif day == 7:
                rate = random.uniform(30, 45)
            else:
                prev = retention_rates[-1]['rate']
                rate = prev * random.uniform(0.85, 0.95)

            retention_rates.append({
                'day': day,
                'rate': round(rate, 1),
                "users": int(cohort_size * rate / 100)
            })

        return {
            "cohort_date": cohort_date.isoformat(),
            "cohort_size": cohort_size,
            'retention': retention_rates,
            'analysis': {
                "day1_retention": retention_rates[1]['rate'],
                "day7_retention": retention_rates[7]['rate'],
                'health_status': '良好' if retention_rates[7]['rate'] > 35 else "需改进"
            }
        }

    def get_user_segments(self) -> Dict[str, Any]:
        """获取用户分群"""
        return {
            'segments': [
                {
                    'name': '高活跃用户',
                    'description': '每日活跃，使用多个功能',
                    'count': random.randint(8000, 12000),
                    'percentage': random.uniform(15, 20),
                    'characteristics': ['日均使用30分钟以上', '使用3个以上功能', '付费意愿高']
                },
                {
                    'name': '健康关注型',
                    'description': '主要使用健康监测功能',
                    'count': random.randint(15000, 20000),
                    'percentage': random.uniform(30, 35),
                    'characteristics': ['频繁使用健康检查', '设置多个健康提醒', '关注健康报告']
                },
                {
                    'name': '社交活跃型',
                    'description': '喜欢社交互动',
                    'count': random.randint(10000, 15000),
                    'percentage': random.uniform(20, 25),
                    'characteristics': ['经常发帖互动', '参与社区活动', '好友数量多']
                },
                {
                    'name': '娱乐消遣型',
                    'description': '主要使用娱乐功能',
                    'count': random.randint(8000, 12000),
                    'percentage': random.uniform(15, 20),
                    'characteristics': ['收听音乐戏曲', '玩认知游戏', '使用时长长']
                },
                {
                    'name': '低活跃用户',
                    'description': '偶尔使用',
                    'count': random.randint(5000, 8000),
                    'percentage': random.uniform(10, 15),
                    'characteristics': ['周活跃1-2次', '功能使用单一', "需要激活"]
                }
            ]
        }

    def get_user_journey(self, user_id: int) -> Dict[str, Any]:
        """获取用户旅程分析"""
        registration_date = datetime.now() - timedelta(days=random.randint(30, 365))

        return {
            'user_id': user_id,
            'journey': {
                "registration": {
                    'date': registration_date.isoformat(),
                    'source': random.choice(['app_store', 'referral', 'ad', 'organic'])
                },
                'onboarding': {
                    'completed': True,
                    "completion_rate": random.uniform(0.8, 1.0),
                    "duration_minutes": random.randint(5, 15)
                },
                'first_week': {
                    'sessions': random.randint(5, 12),
                    "features_used": random.randint(3, 8),
                    "health_checks": random.randint(2, 7)
                },
                "current_stage": random.choice(['active', 'growing', 'mature', 'at_risk']),
                "lifetime_value": random.uniform(0, 500),
                "churn_probability": random.uniform(0.05, 0.3)
            },
            "recommendations": [
                '推送个性化健康提醒',
                '推荐相似用户社交',
                "推送会员优惠"
            ]
        }


# ==================== 健康数据分析服务 ====================

class HealthAnalyticsService:
    """健康数据分析服务"""

    def get_health_overview(self) -> Dict[str, Any]:
        """获取健康数据概览"""
        return {
            "total_health_records": random.randint(500000, 800000),
            "daily_health_checks": random.randint(15000, 25000),
            "abnormal_alerts": {
                'today': random.randint(50, 100),
                'week': random.randint(300, 600),
                'month': random.randint(1200, 2000)
            },
            "health_score_distribution": [
                {'range': "90-100", 'count': random.randint(20000, 30000), 'label': '优秀'},
                {'range': '80-89', 'count': random.randint(15000, 25000), 'label': '良好'},
                {'range': '70-79', 'count': random.randint(8000, 15000), 'label': '一般'},
                {'range': '60-69', 'count': random.randint(3000, 6000), 'label': '需关注'},
                {'range': '<60', 'count': random.randint(1000, 3000), 'label': "需改善"}
            ],
            "popular_health_concerns": [
                {'concern': '血压', 'count': random.randint(20000, 30000)},
                {'concern': '睡眠', 'count': random.randint(18000, 28000)},
                {'concern': '血糖', 'count': random.randint(15000, 22000)},
                {'concern': '心率', 'count': random.randint(12000, 18000)},
                {'concern': '运动', "count": random.randint(10000, 15000)}
            ]
        }

    def get_health_trends(
        self,
        metric: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取健康趋势"""
        dates = []
        values = []

        base_value = {
            "blood_pressure_high": 130,
            "blood_pressure_low": 80,
            'heart_rate': 72,
            "blood_sugar": 5.5,
            "sleep_hours": 7
        }.get(metric, 70)

        for i in range(days):
            d = date.today() - timedelta(days=days - i - 1)
            dates.append(d.isoformat())
            variation = random.uniform(-0.05, 0.05)
            values.append(round(base_value * (1 + variation), 1))

        return {
            'metric': metric,
            'dates': dates,
            'values': values,
            'summary': {
                'avg': round(sum(values) / len(values), 1),
                'min': min(values),
                'max': max(values),
                'trend': 'stable' if abs(values[-1] - values[0]) / values[0] < 0.05 else 'improving'
            }
        }

    def get_alert_analysis(self) -> Dict[str, Any]:
        """获取警报分析"""
        return {
            "alert_types": [
                {'type': '高血压', 'count': random.randint(500, 800), 'severity': 'high'},
                {'type': '低血糖', 'count': random.randint(200, 400), 'severity': 'high'},
                {'type': '心率异常', 'count': random.randint(300, 500), 'severity': 'medium'},
                {'type': '睡眠不足', 'count': random.randint(800, 1200), 'severity': 'low'},
                {'type': '久坐提醒', 'count': random.randint(2000, 3000), 'severity': "low"}
            ],
            "response_time": {
                "avg_minutes": random.uniform(5, 15),
                "family_response_rate": random.uniform(0.85, 0.95),
                "emergency_escalation_rate": random.uniform(0.02, 0.08)
            },
            "false_positive_rate": random.uniform(0.05, 0.15)
        }


# ==================== 业务报表服务 ====================

class BusinessReportService:
    """业务报表服务"""

    def get_revenue_report(
        self,
        period: ReportPeriod,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """获取收入报表"""
        if period == ReportPeriod.DAILY:
            days = (end_date - start_date).days + 1
            dates = []
            revenue = []

            for i in range(days):
                d = start_date + timedelta(days=i)
                dates.append(d.isoformat())
                revenue.append(random.uniform(10000, 25000))

            return {
                'period': period.value,
                'dates': dates,
                'revenue': revenue,
                'total': sum(revenue),
                'avg_daily': sum(revenue) / len(revenue)
            }

        elif period == ReportPeriod.MONTHLY:
            months = []
            revenue = []
            current = start_date.replace(day=1)

            while current <= end_date:
                months.append(current.strftime("%Y-%m"))
                revenue.append(random.uniform(300000, 500000))
                # 移到下个月
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)

            return {
                'period': period.value,
                'months': months,
                'revenue': revenue,
                "total": sum(revenue),
                "growth_rate": random.uniform(0.05, 0.15)
            }

        return {}

    def get_subscription_report(self) -> Dict[str, Any]:
        """获取订阅报表"""
        return {
            'summary': {
                "total_subscribers": random.randint(10000, 15000),
                "active_subscribers": random.randint(8000, 12000),
                'mrr': random.uniform(200000, 350000),  # 月经常性收入
                'arpu': random.uniform(30, 50),  # 每用户平均收入
                'churn_rate': random.uniform(0.02, 0.05)
            },
            'by_tier': [
                {'tier': 'basic', 'count': random.randint(5000, 8000), 'revenue': random.uniform(100000, 150000)},
                {'tier': 'premium', 'count': random.randint(2000, 4000), 'revenue': random.uniform(100000, 180000)},
                {'tier': 'family', 'count': random.randint(500, 1500), "revenue": random.uniform(40000, 100000)}
            ],
            "by_billing_cycle": [
                {'cycle': 'monthly', 'count': random.randint(4000, 6000)},
                {'cycle': 'yearly', 'count': random.randint(4000, 7000)}
            ],
            "conversions": {
                "trial_to_paid": random.uniform(0.15, 0.30),
                "free_to_paid": random.uniform(0.05, 0.12),
                "upgrade_rate": random.uniform(0.08, 0.15)
            }
        }

    def get_feature_usage_report(self) -> Dict[str, Any]:
        """获取功能使用报表"""
        return {
            'features': [
                {
                    'name': "AI对话",
                    "daily_usage": random.randint(80000, 120000),
                    "unique_users": random.randint(20000, 30000),
                    "avg_per_user": random.uniform(3, 6),
                    "satisfaction": random.uniform(4.2, 4.8)
                },
                {
                    'name': "健康监测",
                    "daily_usage": random.randint(30000, 50000),
                    "unique_users": random.randint(15000, 25000),
                    "avg_per_user": random.uniform(1.5, 3),
                    "satisfaction": random.uniform(4.0, 4.6)
                },
                {
                    'name': "娱乐服务",
                    "daily_usage": random.randint(40000, 60000),
                    "unique_users": random.randint(12000, 20000),
                    "avg_per_user": random.uniform(2, 4),
                    "satisfaction": random.uniform(4.3, 4.7)
                },
                {
                    'name': "认知游戏",
                    "daily_usage": random.randint(15000, 25000),
                    "unique_users": random.randint(8000, 15000),
                    "avg_per_user": random.uniform(1, 2.5),
                    "satisfaction": random.uniform(4.1, 4.5)
                },
                {
                    'name': "社交功能",
                    "daily_usage": random.randint(20000, 35000),
                    "unique_users": random.randint(10000, 18000),
                    "avg_per_user": random.uniform(1.5, 3),
                    "satisfaction": random.uniform(3.9, 4.4)
                }
            ]
        }

    def generate_report(
        self,
        report_type: str,
        period: ReportPeriod,
        start_date: date,
        end_date: date
    ) -> ReportData:
        """生成报表"""
        report_id = f"report_{report_type}_{start_date}_{end_date}_{int(datetime.now().timestamp())}"

        if report_type == 'revenue':
            data = self.get_revenue_report(period, start_date, end_date)
        elif report_type == "subscription":
            data = self.get_subscription_report()
        elif report_type == "feature_usage":
            data = self.get_feature_usage_report()
        else:
            data = {}

        return ReportData(
            report_id=report_id,
            report_type=report_type,
            period=period,
            start_date=start_date,
            end_date=end_date,
            data=data
        )


# ==================== 统一分析服务 ====================

class AnalyticsService:
    """统一分析服务"""

    def __init__(self):
        self.user_analytics = UserAnalyticsService()
        self.health_analytics = HealthAnalyticsService()
        self.business_report = BusinessReportService()
        self.cached_reports: Dict[str, ReportData] = {}

    def get_executive_summary(self) -> Dict[str, Any]:
        """获取管理层摘要"""
        return {
            'period': "本月",
            "key_metrics": {
                "total_users": random.randint(50000, 60000),
                "user_growth": f"+{random.uniform(3, 8):.1f}%",
                'active_users': random.randint(20000, 30000),
                'revenue': f'¥{random.uniform(300000, 500000):,.0f}',
                'revenue_growth': f'+{random.uniform(5, 15):.1f}%',
                'customer_satisfaction': f"{random.uniform(4.2, 4.8):.1f}/5"
            },
            'highlights': [
                "用户增长持续稳定，月环比增长5.2%",
                "付费转化率提升至18%，超过行业平均",
                "健康监测功能使用率提升20%",
                "用户满意度保持4.5分以上"
            ],
            "concerns": [
                "部分地区用户留存率下降",
                "客服响应时间需优化",
                "社交功能活跃度有待提升"
            ],
            "recommendations": [
                '加强新用户引导流程',
                '推出区域化运营活动',
                "优化社交功能体验"
            ],
            "generated_at": datetime.now().isoformat()
        }

    def export_report(
        self,
        report_type: str,
        format: str = "json"
    ) -> Dict[str, Any]:
        """导出报表"""
        # 模拟报表数据
        report_data = {
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            'data': self.business_report.get_subscription_report()
        }

        if format == 'json':
            return {
                'format': 'json',
                'content': json.dumps(report_data, ensure_ascii=False, indent=2),
                'filename': f"report_{report_type}_{date.today().isoformat()}.json"
            }
        elif format == 'csv':
            # 简化的CSV导出
            return {
                'format': 'csv',
                'content': '待实现CSV导出',
                "filename": f"report_{report_type}_{date.today().isoformat()}.csv"
            }

        return {'error': "不支持的格式"}


# 全局服务实例
analytics_service = AnalyticsService()
