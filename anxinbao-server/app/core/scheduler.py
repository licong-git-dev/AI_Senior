"""
定时任务调度器
负责主动关怀推送、健康检查提醒、数据清理等定时任务
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, List, Any
from functools import wraps
import threading

logger = logging.getLogger(__name__)

# 尝试导入APScheduler
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.jobstores.memory import MemoryJobStore
    from apscheduler.events import (
        EVENT_JOB_ERROR,
        EVENT_JOB_MISSED,
        EVENT_JOB_MAX_INSTANCES,
    )
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    logger.warning("APScheduler未安装，定时任务功能将被禁用")


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self.enabled = SCHEDULER_AVAILABLE
        self.scheduler = None
        self._started = False
        # 任务执行计数（错过/失败/超额），便于运维和 Prometheus 拉取
        self.metrics = {"jobs_errored": 0, "jobs_missed": 0, "jobs_max_instances": 0}

        if self.enabled:
            jobstores = {
                'default': MemoryJobStore()
            }
            # 全局 job defaults：单任务异常不影响其他；过期 5 分钟内仍可补跑；
            # 单任务最多 1 个并发实例（避免重复推送 / 写入冲突）
            job_defaults = {
                "coalesce": True,
                "misfire_grace_time": 300,
                "max_instances": 1,
            }
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                timezone="Asia/Shanghai",
                job_defaults=job_defaults,
            )

    # ===== 任务异常监听器 =====
    # APScheduler 默认对 job 抛异常仅 log，不会让 scheduler 死，但运维看不到。
    # 这里把异常 / 错过 / 超额并发统一记到本对象 metrics 里，
    # 下游 Prometheus 中间件能 pull 出来（参见 app/core/metrics.py）。

    def _on_job_error(self, event):
        self.metrics["jobs_errored"] += 1
        logger.exception(
            f"[scheduler] 定时任务异常: job_id={event.job_id} "
            f"scheduled_run_time={event.scheduled_run_time} "
            f"exception={event.exception}"
        )

    def _on_job_missed(self, event):
        self.metrics["jobs_missed"] += 1
        logger.warning(
            f"[scheduler] 定时任务错过执行（超过 misfire_grace_time）: "
            f"job_id={event.job_id} scheduled_run_time={event.scheduled_run_time}"
        )

    def _on_job_max_instances(self, event):
        self.metrics["jobs_max_instances"] += 1
        logger.warning(
            f"[scheduler] 定时任务并发达到上限被跳过: job_id={event.job_id}"
        )

    def start(self):
        """启动调度器"""
        if not self.enabled or self._started:
            return

        # 注册异常监听器（必须在 start 之前或之后立即注册）
        self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
        self.scheduler.add_listener(self._on_job_missed, EVENT_JOB_MISSED)
        self.scheduler.add_listener(self._on_job_max_instances, EVENT_JOB_MAX_INSTANCES)

        self.scheduler.start()
        self._started = True
        logger.info("任务调度器已启动（含异常监听器）")

    def shutdown(self):
        """关闭调度器"""
        if not self.enabled or not self._started:
            return

        self.scheduler.shutdown(wait=True)
        self._started = False
        logger.info("任务调度器已关闭")

    def add_job(
        self,
        func: Callable,
        trigger: str,
        job_id: str,
        **trigger_args
    ):
        """
        添加定时任务

        Args:
            func: 任务函数
            trigger: 触发器类型 ('cron', 'interval', "date")
            job_id: 任务ID
            **trigger_args: 触发器参数
        """
        if not self.enabled:
            logger.warning(f'调度器未启用，任务 {job_id} 未添加')
            return

        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            **trigger_args
        )
        logger.info(f"任务已添加: {job_id}")

    def remove_job(self, job_id: str):
        """移除任务"""
        if not self.enabled:
            return

        try:
            self.scheduler.remove_job(job_id)
            logger.info(f'任务已移除: {job_id}')
        except Exception as e:
            logger.error(f"移除任务失败: {job_id} - {e}")

    def get_jobs(self) -> List[Dict]:
        """获取所有任务"""
        if not self.enabled:
            return []

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': str(job.next_run_time) if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs


# 全局调度器实例
scheduler = TaskScheduler()


# ==================== 主动关怀任务 ====================

class ProactiveCareScheduler:
    """主动关怀调度器"""

    def __init__(self):
        self.scheduler = scheduler

    async def morning_greeting(self):
        """早间问候（每天8:00）"""
        logger.info('执行早间问候任务')
        try:
            from app.models.database import SessionLocal, User
            from app.services.qwen_service import chat_service
            from app.core.cache import conversation_store

            db = SessionLocal()
            try:
                # 获取所有活跃用户
                users = db.query(User).all()

                for user in users:
                    # 获取用户画像
                    profile = self._get_user_profile(user)

                    # 获取天气等上下文
                    context = await self._get_morning_context()

                    # 生成问候消息
                    message = chat_service.generate_proactive_care(
                        user_profile=profile,
                        context=f'现在是早上好时间。{context}'
                    )

                    if message:
                        # 存储为系统消息
                        await conversation_store.add_message(
                            user_id=str(user.id),
                            session_id=f"proactive-{datetime.now().strftime('%Y%m%d')}",
                            role='assistant',
                            content=message,
                            metadata={'type': 'proactive_care', 'trigger': 'morning_greeting'}
                        )
                        logger.info(f'早间问候已发送给用户 {user.id}')

            finally:
                db.close()

        except Exception as e:
            logger.error(f"早间问候任务失败: {e}")

    async def medication_reminder(self):
        """用药提醒（每天特定时间）"""
        logger.info('执行用药提醒任务')
        try:
            from app.models.database import SessionLocal, User
            from app.core.cache import conversation_store

            db = SessionLocal()
            try:
                users = db.query(User).all()

                for user in users:
                    # 检查用户是否设置了用药提醒
                    # 这里需要扩展数据模型来存储用药计划
                    reminder_message = f'您好，现在是吃药时间了。记得按时服药，身体健康最重要。'

                    await conversation_store.add_message(
                        user_id=str(user.id),
                        session_id=f"reminder-{datetime.now().strftime('%Y%m%d')}",
                        role='assistant',
                        content=reminder_message,
                        metadata={"type": "medication_reminder"}
                    )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"用药提醒任务失败: {e}")

    async def evening_check(self):
        """晚间关怀检查（每天20:00）"""
        logger.info("执行晚间关怀任务")
        try:
            from app.models.database import SessionLocal, User, Conversation
            from app.services.qwen_service import chat_service
            from app.core.cache import conversation_store
            from sqlalchemy import func

            db = SessionLocal()
            try:
                users = db.query(User).all()
                today = datetime.now().date()

                for user in users:
                    # 检查今天是否有对话
                    today_conversations = db.query(Conversation).filter(
                        Conversation.user_id == user.id,
                        func.date(Conversation.created_at) == today
                    ).count()

                    profile = self._get_user_profile(user)

                    if today_conversations == 0:
                        # 今天没有对话，发送关怀消息
                        message = chat_service.generate_proactive_care(
                            user_profile=profile,
                            context="今天一整天都没有聊天了，主动关心一下。"
                        )
                    else:
                        # 有对话，发送晚安消息
                        message = f'晚上好！今天过得怎么样？早点休息，祝您做个好梦。'

                    if message:
                        await conversation_store.add_message(
                            user_id=str(user.id),
                            session_id=f"proactive-{datetime.now().strftime('%Y%m%d')}",
                            role='assistant',
                            content=message,
                            metadata={'type': 'proactive_care', 'trigger': 'evening_check'}
                        )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"晚间关怀任务失败: {e}")

    async def inactivity_check(self):
        """不活跃用户检查（每小时）"""
        logger.info('执行不活跃用户检查')
        try:
            from app.models.database import SessionLocal, User, Conversation, HealthNotification
            from sqlalchemy import func

            db = SessionLocal()
            try:
                # 查找超过48小时没有对话的用户
                threshold = datetime.now() - timedelta(hours=48)

                inactive_users = db.query(User).outerjoin(
                    Conversation
                ).group_by(User.id).having(
                    func.max(Conversation.created_at) < threshold
                ).all()

                for user in inactive_users:
                    # 创建提醒通知给家属
                    notification = HealthNotification(
                        user_id=user.id,
                        conversation_summary=f'{user.name}已超过48小时没有与安心宝交流',
                        risk_score=5,
                        risk_reason='长时间未活跃，建议关注',
                        is_read=False,
                        is_handled=False
                    )
                    db.add(notification)

                    logger.warning(f'用户 {user.id} 超过48小时未活跃')

                db.commit()

            finally:
                db.close()

        except Exception as e:
            logger.error(f"不活跃检查任务失败: {e}")

    async def birthday_check(self):
        """生日检查（每天凌晨检查当天生日）"""
        logger.info('执行生日检查任务')
        try:
            from app.models.database import SessionLocal, User
            from app.services.qwen_service import chat_service
            from app.core.cache import conversation_store

            db = SessionLocal()
            try:
                today = datetime.now()
                today_str = f'-{today.month:02d}-{today.day:02d}'

                users = db.query(User).all()

                for user in users:
                    profile = self._get_user_profile(user)
                    important_dates = profile.get('important_dates', {})

                    # 检查是否有今天的重要日期
                    for event, date_str in important_dates.items():
                        if date_str.endswith(today_str):
                            message = chat_service.generate_proactive_care(
                                user_profile=profile,
                                context=f'今天是{event}！'
                            )

                            if message:
                                await conversation_store.add_message(
                                    user_id=str(user.id),
                                    session_id=f"special-{datetime.now().strftime('%Y%m%d')}",
                                    role='assistant',
                                    content=message,
                                    metadata={'type': 'special_day', 'event': event}
                                )
                                logger.info(f'特殊日期提醒已发送给用户 {user.id}: {event}')

            finally:
                db.close()

        except Exception as e:
            logger.error(f"生日检查任务失败: {e}")

    def _get_user_profile(self, user) -> Dict:
        """获取用户画像"""
        return {
            'name': user.name,
            'age': getattr(user, 'age', ''),
            "health_conditions": [],
            'interests': [],
            "family_members": [],
            "important_dates": {},
            'preferences': ""
        }

    async def _get_morning_context(self) -> str:
        """获取早间上下文（天气等）"""
        # 这里可以集成天气API
        return "今天天气不错，适合出门散步。"

    def setup_jobs(self):
        """设置所有主动关怀任务"""
        if not scheduler.enabled:
            logger.warning("调度器未启用，主动关怀任务未设置")
            return

        # 早间问候 - 每天8:00
        scheduler.add_job(
            self.morning_greeting,
            'cron',
            job_id='morning_greeting',
            hour=8,
            minute=0
        )

        # 晚间关怀 - 每天20:00
        scheduler.add_job(
            self.evening_check,
            'cron',
            job_id='evening_check',
            hour=20,
            minute=0
        )

        # 不活跃检查 - 每小时
        scheduler.add_job(
            self.inactivity_check,
            'interval',
            job_id='inactivity_check',
            hours=1
        )

        # 生日/特殊日期检查 - 每天凌晨1:00
        scheduler.add_job(
            self.birthday_check,
            'cron',
            job_id="birthday_check",
            hour=1,
            minute=0
        )

        logger.info("主动关怀任务已设置完成")


# ==================== 系统维护任务 ====================

class MaintenanceScheduler:
    """系统维护调度器"""

    def __init__(self):
        self.scheduler = scheduler

    async def cleanup_expired_tokens(self):
        """清理过期令牌"""
        logger.info('执行令牌清理任务')
        try:
            from app.models.database import SessionLocal, RefreshToken
            from datetime import datetime

            db = SessionLocal()
            try:
                # 删除过期超过7天的令牌
                threshold = datetime.now() - timedelta(days=7)
                deleted = db.query(RefreshToken).filter(
                    RefreshToken.expires_at < threshold
                ).delete()

                db.commit()
                logger.info(f'已清理 {deleted} 个过期令牌')

            finally:
                db.close()

        except Exception as e:
            logger.error(f"令牌清理任务失败: {e}")

    async def cleanup_old_conversations(self):
        """清理旧对话记录（保留90天）"""
        logger.info('执行对话清理任务')
        try:
            from app.models.database import SessionLocal, Conversation

            db = SessionLocal()
            try:
                threshold = datetime.now() - timedelta(days=90)
                deleted = db.query(Conversation).filter(
                    Conversation.created_at < threshold
                ).delete()

                db.commit()
                logger.info(f'已清理 {deleted} 条旧对话记录')

            finally:
                db.close()

        except Exception as e:
            logger.error(f"对话清理任务失败: {e}")

    async def cleanup_audit_logs(self):
        """清理审计日志（保留90天）"""
        logger.info('执行审计日志清理任务')
        try:
            from app.models.database import SessionLocal, AuditLog

            db = SessionLocal()
            try:
                threshold = datetime.now() - timedelta(days=90)
                deleted = db.query(AuditLog).filter(
                    AuditLog.created_at < threshold
                ).delete()

                db.commit()
                logger.info(f'已清理 {deleted} 条审计日志')

            finally:
                db.close()

        except Exception as e:
            logger.error(f"审计日志清理任务失败: {e}")

    async def generate_daily_report(self):
        """生成每日报告"""
        logger.info('执行每日报告生成任务')
        try:
            from app.models.database import SessionLocal, User, Conversation, HealthNotification
            from sqlalchemy import func

            db = SessionLocal()
            try:
                yesterday = datetime.now().date() - timedelta(days=1)

                # 统计数据
                total_users = db.query(User).count()
                active_users = db.query(Conversation.user_id).filter(
                    func.date(Conversation.created_at) == yesterday
                ).distinct().count()

                total_conversations = db.query(Conversation).filter(
                    func.date(Conversation.created_at) == yesterday
                ).count()

                high_risk_alerts = db.query(HealthNotification).filter(
                    func.date(HealthNotification.created_at) == yesterday,
                    HealthNotification.risk_score >= 7
                ).count()

                report = {
                    "date": str(yesterday),
                    "total_users": total_users,
                    "active_users": active_users,
                    "total_conversations": total_conversations,
                    "high_risk_alerts": high_risk_alerts,
                    "activity_rate": round(active_users / total_users * 100, 2) if total_users > 0 else 0
                }

                logger.info(f'每日报告: {report}')

                # 可以在这里发送报告到管理员

            finally:
                db.close()

        except Exception as e:
            logger.error(f"每日报告生成失败: {e}")

    def setup_jobs(self):
        """设置所有维护任务"""
        if not scheduler.enabled:
            return

        # 令牌清理 - 每天凌晨3:00
        scheduler.add_job(
            self.cleanup_expired_tokens,
            'cron',
            job_id='cleanup_tokens',
            hour=3,
            minute=0
        )

        # 对话清理 - 每周日凌晨4:00
        scheduler.add_job(
            self.cleanup_old_conversations,
            'cron',
            job_id='cleanup_conversations',
            day_of_week='sun',
            hour=4,
            minute=0
        )

        # 审计日志清理 - 每月1日凌晨4:30
        scheduler.add_job(
            self.cleanup_audit_logs,
            'cron',
            job_id='cleanup_audit_logs',
            day=1,
            hour=4,
            minute=30
        )

        # 每日报告 - 每天凌晨6:00
        scheduler.add_job(
            self.generate_daily_report,
            'cron',
            job_id="daily_report",
            hour=6,
            minute=0
        )

        logger.info("系统维护任务已设置完成")


# ==================== 新主动交互系统集成 ====================

class EnhancedProactiveScheduler:
    """
    增强的主动交互调度器
    基于新的数据模型：ProactiveGreeting, ProactiveReminder, UserBehaviorPattern, ImportantDate
    """

    def __init__(self):
        self.scheduler = scheduler

    async def process_scheduled_greetings(self):
        """处理用户配置的定时问候"""
        logger.info('执行定时问候处理任务')
        try:
            from app.models.database import SessionLocal, ProactiveGreeting, UserProfile, User
            from datetime import datetime
            import json

            db = SessionLocal()
            try:
                current_time = datetime.now().strftime('%H:%M')
                current_hour = datetime.now().hour

                # 确定问候类型
                if 5 <= current_hour < 12:
                    greeting_type = 'morning'
                elif 12 <= current_hour < 18:
                    greeting_type = 'afternoon'
                else:
                    greeting_type = 'evening'

                # 查找匹配当前时间的活跃问候配置
                greetings = db.query(ProactiveGreeting).filter(
                    ProactiveGreeting.is_active == True,
                    ProactiveGreeting.schedule_time == current_time
                ).all()

                for greeting in greetings:
                    user = db.query(User).filter(User.id == greeting.user_id).first()
                    if not user:
                        continue

                    # 获取用户画像
                    profile = db.query(UserProfile).filter(
                        UserProfile.user_id == greeting.user_id
                    ).first()

                    # 构建问候内容
                    content_parts = []

                    # 基础问候
                    greet_text = self._get_greeting_text(greeting_type, user.name)
                    content_parts.append(greet_text)

                    # 天气信息
                    if greeting.include_weather:
                        weather_info = await self._get_weather_info()
                        if weather_info:
                            content_parts.append(weather_info)

                    # 用药提醒
                    if greeting.include_medication_reminder:
                        med_reminder = await self._get_medication_reminder(greeting.user_id, db)
                        if med_reminder:
                            content_parts.append(med_reminder)

                    # 健康提示
                    if greeting.include_health_tip:
                        health_tip = self._get_health_tip(profile)
                        content_parts.append(health_tip)

                    # 今日日程
                    if greeting.include_schedule:
                        schedule = await self._get_today_schedule(greeting.user_id, db)
                        if schedule:
                            content_parts.append(schedule)

                    # 发送问候
                    full_content = ' '.join(content_parts)
                    await self._send_proactive_message(
                        user_id=greeting.user_id,
                        content=full_content,
                        interaction_type='greeting',
                        trigger_source='scheduled',
                        db=db
                    )

                    # 更新最后触发时间
                    greeting.last_triggered = datetime.now()
                    db.commit()

                    logger.info(f'问候已发送给用户 {greeting.user_id}')

            finally:
                db.close()

        except Exception as e:
            logger.error(f"定时问候处理失败: {e}")

    async def process_scheduled_reminders(self):
        """处理用户配置的定时提醒"""
        logger.info('执行定时提醒处理任务')
        try:
            from app.models.database import SessionLocal, ProactiveReminder, User
            from datetime import datetime
            import json

            db = SessionLocal()
            try:
                current_time = datetime.now().strftime('%H:%M')

                # 查找时间触发的提醒
                reminders = db.query(ProactiveReminder).filter(
                    ProactiveReminder.is_active == True,
                    ProactiveReminder.trigger_type == "time_based",
                    ProactiveReminder.trigger_time == current_time
                ).all()

                for reminder in reminders:
                    user = db.query(User).filter(User.id == reminder.user_id).first()
                    if not user:
                        continue

                    # 检查触发条件
                    conditions = json.loads(reminder.trigger_conditions) if reminder.trigger_conditions else {}

                    # 检查星期几
                    days = conditions.get("days_of_week", [])
                    if days and datetime.now().weekday() not in days:
                        continue

                    # 生成提醒内容
                    content = self._generate_reminder_content(reminder, user.name)

                    # 发送提醒
                    await self._send_proactive_message(
                        user_id=reminder.user_id,
                        content=content,
                        interaction_type='reminder',
                        trigger_source="scheduled",
                        metadata={"reminder_type": reminder.reminder_type},
                        db=db
                    )

                    # 更新最后触发时间
                    reminder.last_triggered = datetime.now()
                    db.commit()

                    logger.info(f'提醒已发送给用户 {reminder.user_id}: {reminder.reminder_type}')

            finally:
                db.close()

        except Exception as e:
            logger.error(f"定时提醒处理失败: {e}")

    async def process_interval_reminders(self):
        """处理间隔触发的提醒（如喝水、起身活动）"""
        logger.info('执行间隔提醒处理任务')
        try:
            from app.models.database import SessionLocal, ProactiveReminder, User
            from datetime import datetime, timedelta
            import json

            db = SessionLocal()
            try:
                now = datetime.now()

                # 查找间隔触发的提醒
                reminders = db.query(ProactiveReminder).filter(
                    ProactiveReminder.is_active == True,
                    ProactiveReminder.trigger_type == "interval"
                ).all()

                for reminder in reminders:
                    conditions = json.loads(reminder.trigger_conditions) if reminder.trigger_conditions else {}
                    interval_minutes = conditions.get("interval_minutes", 60)

                    # 检查是否到达触发时间
                    if reminder.last_triggered:
                        next_trigger = reminder.last_triggered + timedelta(minutes=interval_minutes)
                        if now < next_trigger:
                            continue

                    # 检查当前时间是否在活跃时段内
                    start_time = conditions.get('active_start', '08:00')
                    end_time = conditions.get('active_end', '22:00')
                    current_time_str = now.strftime('%H:%M')
                    if not (start_time <= current_time_str <= end_time):
                        continue

                    user = db.query(User).filter(User.id == reminder.user_id).first()
                    if not user:
                        continue

                    # 生成提醒内容
                    content = self._generate_reminder_content(reminder, user.name)

                    # 发送提醒
                    await self._send_proactive_message(
                        user_id=reminder.user_id,
                        content=content,
                        interaction_type='reminder',
                        trigger_source="interval",
                        metadata={"reminder_type": reminder.reminder_type},
                        db=db
                    )

                    # 更新最后触发时间
                    reminder.last_triggered = now
                    db.commit()

            finally:
                db.close()

        except Exception as e:
            logger.error(f"间隔提醒处理失败: {e}")

    async def check_important_dates(self):
        """检查重要日期（生日、纪念日等）"""
        logger.info('执行重要日期检查任务')
        try:
            from app.models.database import SessionLocal, ImportantDate, User, UserProfile
            from datetime import datetime, timedelta
            import json

            db = SessionLocal()
            try:
                today = datetime.now().date()

                # 查找今天和未来3天的重要日期
                upcoming_dates = db.query(ImportantDate).filter(
                    ImportantDate.reminder_enabled == True
                ).all()

                for imp_date in upcoming_dates:
                    # 计算今年的日期
                    this_year_date = imp_date.date.replace(year=today.year)
                    if this_year_date < today:
                        this_year_date = this_year_date.replace(year=today.year + 1)

                    days_until = (this_year_date - today).days

                    # 检查是否需要提醒
                    should_remind = False
                    if days_until == 0:  # 当天
                        should_remind = True
                        reminder_text = f'今天是{imp_date.title}！'
                    elif days_until == imp_date.reminder_days_before:  # 提前提醒
                        should_remind = True
                        reminder_text = f'还有{days_until}天就是{imp_date.title}了，别忘了准备。'

                    if should_remind:
                        user = db.query(User).filter(User.id == imp_date.user_id).first()
                        if not user:
                            continue

                        # 发送提醒
                        await self._send_proactive_message(
                            user_id=imp_date.user_id,
                            content=reminder_text,
                            interaction_type="reminder",
                            trigger_source="important_date",
                            metadata={'date_type': imp_date.date_type, 'title': imp_date.title},
                            db=db
                        )

                        logger.info(f'重要日期提醒已发送给用户 {imp_date.user_id}: {imp_date.title}')

            finally:
                db.close()

        except Exception as e:
            logger.error(f"重要日期检查失败: {e}")

    async def learn_user_behavior_patterns(self):
        """学习用户行为模式"""
        logger.info("执行用户行为模式学习任务")
        try:
            from app.models.database import SessionLocal, UserBehaviorPattern, User, Conversation
            from sqlalchemy import func
            from datetime import datetime, timedelta
            import json

            db = SessionLocal()
            try:
                # 获取所有用户
                users = db.query(User).all()

                for user in users:
                    # 分析过去30天的对话数据
                    thirty_days_ago = datetime.now() - timedelta(days=30)
                    conversations = db.query(Conversation).filter(
                        Conversation.user_id == user.id,
                        Conversation.created_at >= thirty_days_ago
                    ).all()

                    if len(conversations) < 10:
                        continue  # 数据不足，跳过

                    # 分析活跃时间段
                    hour_counts = {}
                    for conv in conversations:
                        hour = conv.created_at.hour
                        hour_counts[hour] = hour_counts.get(hour, 0) + 1

                    # 找出活跃高峰时段
                    if hour_counts:
                        peak_hour = max(hour_counts, key=hour_counts.get)

                        # 更新或创建行为模式记录
                        pattern = db.query(UserBehaviorPattern).filter(
                            UserBehaviorPattern.user_id == user.id,
                            UserBehaviorPattern.pattern_type == "activity_peak"
                        ).first()

                        if pattern:
                            pattern.pattern_value = json.dumps({'peak_hour': peak_hour, "distribution": hour_counts})
                            pattern.confidence = min(1.0, len(conversations) / 100)
                            pattern.updated_at = datetime.now()
                        else:
                            pattern = UserBehaviorPattern(
                                user_id=user.id,
                                pattern_type="activity_peak",
                                pattern_value=json.dumps({'peak_hour': peak_hour, "distribution": hour_counts}),
                                confidence=min(1.0, len(conversations) / 100),
                                sample_count=len(conversations)
                            )
                            db.add(pattern)

                db.commit()
                logger.info('用户行为模式学习完成')

            finally:
                db.close()

        except Exception as e:
            logger.error(f"用户行为模式学习失败: {e}")

    async def check_cognitive_training_schedules(self):
        """检查认知训练计划提醒"""
        logger.info("执行认知训练计划检查任务")
        try:
            from app.models.database import SessionLocal, CognitiveTrainingPlan, User
            from datetime import datetime
            import json

            db = SessionLocal()
            try:
                current_time = datetime.now().strftime('%H:%M')
                today_weekday = datetime.now().weekday()

                # 查找活跃的训练计划
                plans = db.query(CognitiveTrainingPlan).filter(
                    CognitiveTrainingPlan.is_active == True,
                    CognitiveTrainingPlan.reminder_enabled == True,
                    CognitiveTrainingPlan.schedule_time == current_time
                ).all()

                for plan in plans:
                    # 检查今天是否是训练日
                    schedule_days = json.loads(plan.schedule_days) if plan.schedule_days else list(range(7))
                    if today_weekday not in schedule_days:
                        continue

                    user = db.query(User).filter(User.id == plan.user_id).first()
                    if not user:
                        continue

                    # 发送训练提醒
                    content = f'{user.name}，现在是您的认知训练时间。今天的训练计划是「{plan.name}」，大约需要{plan.session_duration_minutes}分钟。准备好了就开始吧！'

                    await self._send_proactive_message(
                        user_id=plan.user_id,
                        content=content,
                        interaction_type="reminder",
                        trigger_source="training_schedule",
                        metadata={'plan_id': plan.id, 'plan_name': plan.name},
                        db=db
                    )

                    logger.info(f'认知训练提醒已发送给用户 {plan.user_id}')

            finally:
                db.close()

        except Exception as e:
            logger.error(f"认知训练计划检查失败: {e}")

    def _get_greeting_text(self, greeting_type: str, name: str) -> str:
        """生成问候语"""
        import random
        greetings = {
            'morning': [
                f'早上好，{name}！新的一天开始了，希望您今天精神饱满。',
                f'{name}，早安！睡得好吗？新的一天，新的开始。',
                f'早上好呀{name}，阳光明媚的一天，心情也要美美的。'
            ],
            'afternoon': [
                f'下午好，{name}！午休得怎么样？',
                f'{name}，下午好！忙了一上午，记得喝点水休息一下。',
                f'午安，{name}！下午也要保持好心情哦。'
            ],
            'evening': [
                f'晚上好，{name}！今天过得怎么样？',
                f"{name}，晚安！一天辛苦了，好好休息。",
                f"晚上好呀，{name}！放松一下，聊聊天吧。"
            ]
        }
        return random.choice(greetings.get(greeting_type, greetings["morning"]))

    async def _get_weather_info(self) -> str:
        """获取天气信息"""
        # 这里可以集成真实天气API
        import random
        weather_tips = [
            "今天天气晴朗，适合出门散步。",
            "外面有点凉，出门记得加件外套。",
            "今天温度适宜，是个好天气。",
            "可能会下雨，出门记得带伞。"
        ]
        return random.choice(weather_tips)

    async def _get_medication_reminder(self, user_id: int, db) -> str:
        """获取用药提醒"""
        from app.models.database import Medication
        from datetime import datetime

        current_hour = datetime.now().hour
        time_period = '早上' if current_hour < 12 else ('中午' if current_hour < 14 else ('下午' if current_hour < 18 else '晚上'))

        medications = db.query(Medication).filter(
            Medication.user_id == user_id,
            Medication.is_active == True
        ).all()

        if medications:
            return f'别忘了{time_period}的药要按时吃哦。'
        return ""

    def _get_health_tip(self, profile) -> str:
        """获取健康提示"""
        import random
        tips = [
            "记得多喝水，保持身体水分。",
            "适当活动一下，伸展伸展筋骨。",
            "保持心情愉快，对健康很重要。",
            "饮食要规律，少油少盐更健康。"
        ]
        return random.choice(tips)

    async def _get_today_schedule(self, user_id: int, db) -> str:
        """获取今日日程"""
        # 可以集成日历功能
        return ""

    def _generate_reminder_content(self, reminder, name: str) -> str:
        """生成提醒内容"""
        import json
        reminder_templates = {
            'water': f'{name}，该喝水了！保持充足的水分对身体很重要哦。',
            'stand_up': f'{name}，坐久了该起来活动一下了，伸伸腿、扭扭腰。',
            'exercise': f'{name}，是时候做做运动了，简单的活动对身体很有好处。',
            'medication': f'{name}，现在是吃药时间，别忘了按时服药。',
            'meal': f'{name}，该吃饭了，规律饮食很重要。',
            "rest": f"{name}，注意休息，别太累了。"
        }

        base_content = reminder_templates.get(
            reminder.reminder_type,
            f"{name}，{reminder.content or '这是一条提醒'}"
        )

        return base_content

    async def _send_proactive_message(
        self,
        user_id: int,
        content: str,
        interaction_type: str,
        trigger_source: str,
        metadata: dict = None,
        db=None
    ):
        """发送主动交互消息并记录日志"""
        from app.models.database import ProactiveInteractionLog
        from datetime import datetime
        import json

        try:
            # 记录交互日志
            log = ProactiveInteractionLog(
                user_id=user_id,
                interaction_type=interaction_type,
                trigger_source=trigger_source,
                content=content,
                triggered_at=datetime.now(),
                metadata=json.dumps(metadata) if metadata else None
            )
            db.add(log)
            db.commit()

            # 这里可以集成实际的推送服务
            # 如 WebSocket推送、App推送、短信等
            logger.info(f'主动消息已发送: user_id={user_id}, type={interaction_type}')

        except Exception as e:
            logger.error(f"发送主动消息失败: {e}")

    def setup_jobs(self):
        """设置增强的主动交互任务"""
        if not scheduler.enabled:
            logger.warning("调度器未启用，增强主动交互任务未设置")
            return

        # 定时问候检查 - 每分钟
        scheduler.add_job(
            self.process_scheduled_greetings,
            'interval',
            job_id='enhanced_greetings',
            minutes=1
        )

        # 定时提醒检查 - 每分钟
        scheduler.add_job(
            self.process_scheduled_reminders,
            'interval',
            job_id='scheduled_reminders',
            minutes=1
        )

        # 间隔提醒检查 - 每15分钟
        scheduler.add_job(
            self.process_interval_reminders,
            'interval',
            job_id='interval_reminders',
            minutes=15
        )

        # 重要日期检查 - 每天早上7:00
        scheduler.add_job(
            self.check_important_dates,
            'cron',
            job_id='check_important_dates',
            hour=7,
            minute=0
        )

        # 用户行为模式学习 - 每天凌晨2:00
        scheduler.add_job(
            self.learn_user_behavior_patterns,
            'cron',
            job_id='learn_behavior_patterns',
            hour=2,
            minute=0
        )

        # 认知训练计划检查 - 每分钟
        scheduler.add_job(
            self.check_cognitive_training_schedules,
            'interval',
            job_id="cognitive_training_check",
            minutes=1
        )

        logger.info("增强主动交互任务已设置完成")


# ==================== 调度器初始化 ====================

proactive_care = ProactiveCareScheduler()
maintenance = MaintenanceScheduler()
enhanced_proactive = EnhancedProactiveScheduler()


async def push_daily_reports():
    """每日20:00推送安心日报给所有家属"""
    from app.models.database import SessionLocal, UserAuth, FamilyMember, User
    from app.services.daily_report import daily_report_service
    from app.services.notification_service import notification_service

    logger.info("开始推送今日安心日报...")
    db = SessionLocal()
    pushed = 0
    failed = 0

    try:
        # 获取所有活跃老人
        elders = db.query(UserAuth).filter(
            UserAuth.role == "elder",
            UserAuth.is_active == True,
            UserAuth.user_id != None,
        ).all()

        for elder_auth in elders:
            try:
                # 生成日报
                report = daily_report_service.generate_report(db, elder_auth.user_id)

                # 查找绑定的家属
                family_members = db.query(FamilyMember).filter(
                    FamilyMember.user_id == elder_auth.user_id
                ).all()

                if not family_members:
                    continue

                # 推送给每个家属
                for member in family_members:
                    try:
                        elder_name = report.user_name or "爸妈"
                        score = report.anxin_score
                        summary = report.one_line_summary

                        # 推送通知
                        await notification_service.send_notification(
                            user_id=str(member.id),
                            template="DAILY_REPORT",
                            title=f"📋 {elder_name}今日安心日报",
                            content=f"安心指数：{score}/10 · {report.anxin_level}\n{summary}",
                        )
                        pushed += 1
                    except Exception as e:
                        logger.error(f"推送日报给家属 {member.id} 失败: {e}")
                        failed += 1

            except Exception as e:
                logger.error(f"生成老人 {elder_auth.user_id} 日报失败: {e}")
                failed += 1

    finally:
        db.close()

    logger.info(f"安心日报推送完成：成功 {pushed} 条，失败 {failed} 条")


def init_scheduler():
    """初始化所有定时任务"""
    if not scheduler.enabled:
        logger.warning("定时任务调度器未启用")
        return

    # 设置任务
    proactive_care.setup_jobs()
    maintenance.setup_jobs()
    enhanced_proactive.setup_jobs()  # 新增增强主动交互任务

    # 安心日报推送 - 每天20:00
    scheduler.add_job(
        push_daily_reports,
        'cron',
        job_id='push_daily_reports',
        hour=20,
        minute=0
    )

    # 启动调度器
    scheduler.start()

    logger.info("定时任务调度器初始化完成")


def shutdown_scheduler():
    """关闭调度器"""
    scheduler.shutdown()
