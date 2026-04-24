"""
通知推送服务
支持多渠道推送：微信模板消息、App推送、短信等
"""
import logging
import json
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import httpx

from app.core.config import get_settings
from app.core.retry import async_retry
from app.core.dead_letter import dead_letter_queue, DeadLetterRecord

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationChannel(Enum):
    """通知渠道"""
    WECHAT = 'wechat'  # 微信模板消息
    APP_PUSH = 'app_push'  # App推送
    SMS = 'sms'  # 短信
    EMAIL = 'email'  # 邮件
    VOICE_CALL = 'voice_call'  # 语音电话（紧急）


class NotificationPriority(Enum):
    """通知优先级"""
    LOW = 1  # 低优先级（日常提醒）
    NORMAL = 2  # 正常优先级
    HIGH = 3  # 高优先级（健康告警）
    URGENT = 4  # 紧急（需要立即处理）


class NotificationTemplate(Enum):
    """通知模板"""
    HEALTH_ALERT = "health_alert"  # 健康告警
    DAILY_REPORT = "daily_report"  # 每日报告
    PROACTIVE_CARE = "proactive_care"  # 主动关怀
    INACTIVITY_ALERT = "inactivity_alert"  # 不活跃提醒
    EMERGENCY = "emergency"  # 紧急情况


# ==================== 抽象推送器 ====================

class BasePusher(ABC):
    """推送器基类"""

    @abstractmethod
    async def push(
        self,
        recipient: str,
        title: str,
        content: str,
        data: Optional[Dict] = None
    ) -> bool:
        """
        发送推送

        Args:
            recipient: 接收者标识
            title: 标题
            content: 内容
            data: 额外数据

        Returns:
            是否发送成功
        """
        pass


class WeChatPusher(BasePusher):
    """微信模板消息推送"""

    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id or getattr(settings, 'wechat_app_id', '')
        self.app_secret = app_secret or getattr(settings, 'wechat_app_secret', '')
        self._access_token = None
        self._token_expires_at = None

    @async_retry(
        max_attempts=3, backoff_base=0.5, max_delay=4.0,
        retryable=(httpx.TransportError, httpx.TimeoutException),
    )
    async def _get_access_token(self) -> str:
        """获取微信access_token"""
        if self._access_token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return self._access_token

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.weixin.qq.com/cgi-bin/token",
                    params={
                        'grant_type': "client_credential",
                        'appid': self.app_id,
                        'secret': self.app_secret
                    }
                )
                data = response.json()

                if "access_token" in data:
                    self._access_token = data["access_token"]
                    from datetime import timedelta
                    self._token_expires_at = datetime.now() + timedelta(seconds=data.get('expires_in', 7200) - 300)
                    return self._access_token
                else:
                    logger.error(f'获取微信access_token失败: {data}')
                    return None
        except Exception as e:
            logger.error(f'获取微信access_token异常: {e}')
            return None

    @async_retry(
        max_attempts=3, backoff_base=0.5, max_delay=4.0,
        retryable=(httpx.TransportError, httpx.TimeoutException),
    )
    async def push(
        self,
        recipient: str,
        title: str,
        content: str,
        data: Optional[Dict] = None
    ) -> bool:
        """发送微信模板消息（瞬时网络异常会重试 3 次，不可用配置直接返回 False）"""
        if not self.app_id or not self.app_secret:
            logger.warning('微信推送未配置')
            return False

        access_token = await self._get_access_token()
        if not access_token:
            return False

        try:
            template_id = data.get('template_id', '') if data else ""
            template_data = data.get("template_data", {}) if data else {}

            payload = {
                'touser': recipient,  # OpenID
                "template_id": template_id,
                'data': {
                    'first': {'value': title},
                    'keyword1': {'value': content},
                    'keyword2': {'value': datetime.now().strftime("%Y-%m-%d %H:%M")},
                    'remark': {'value': '点击查看详情'},
                    **template_data
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}',
                    json=payload
                )
                result = response.json()

                if result.get('errcode') == 0:
                    logger.info(f'微信消息发送成功: {recipient}')
                    return True
                else:
                    logger.error(f'微信消息发送失败: {result}')
                    return False

        except Exception as e:
            logger.error(f'微信推送异常: {e}')
            return False


class SMSPusher(BasePusher):
    """短信推送（使用阿里云短信服务）"""

    def __init__(self):
        self.access_key_id = getattr(settings, 'aliyun_access_key_id', '')
        self.access_key_secret = getattr(settings, 'aliyun_access_key_secret', '')
        self.sign_name = getattr(settings, 'sms_sign_name', '安心宝')

    async def push(
        self,
        recipient: str,
        title: str,
        content: str,
        data: Optional[Dict] = None
    ) -> bool:
        """发送短信"""
        if not self.access_key_id or not self.access_key_secret:
            logger.warning('短信服务未配置')
            return False

        try:
            # 这里简化实现，实际需要使用阿里云SDK
            template_code = data.get('template_code', '') if data else ""
            template_param = json.dumps(data.get("template_param", {})) if data else '{}'

            logger.info(f'短信发送（模拟）: {recipient} - {content}')
            return True

        except Exception as e:
            logger.error(f'短信发送异常: {e}')
            return False


class AppPushPusher(BasePusher):
    """App推送（使用极光推送）"""

    def __init__(self):
        self.app_key = getattr(settings, 'jpush_app_key', '')
        self.master_secret = getattr(settings, 'jpush_master_secret', '')

    async def push(
        self,
        recipient: str,
        title: str,
        content: str,
        data: Optional[Dict] = None
    ) -> bool:
        """发送App推送"""
        if not self.app_key or not self.master_secret:
            logger.warning('App推送服务未配置')
            return False

        try:
            # 这里简化实现，实际需要使用极光推送SDK
            logger.info(f'App推送（模拟）: {recipient} - {title}: {content}')
            return True

        except Exception as e:
            logger.error(f'App推送异常: {e}')
            return False


# ==================== 通知服务 ====================

class NotificationService:
    """通知服务"""

    def __init__(self):
        self.pushers = {
            NotificationChannel.WECHAT: WeChatPusher(),
            NotificationChannel.SMS: SMSPusher(),
            NotificationChannel.APP_PUSH: AppPushPusher(),
        }

        # 模板配置
        self.templates = {
            NotificationTemplate.HEALTH_ALERT: {
                'title': '健康告警提醒',
                'channels': [NotificationChannel.WECHAT, NotificationChannel.APP_PUSH],
                'priority': NotificationPriority.HIGH
            },
            NotificationTemplate.EMERGENCY: {
                'title': '紧急情况通知',
                'channels': [NotificationChannel.SMS, NotificationChannel.WECHAT, NotificationChannel.APP_PUSH],
                'priority': NotificationPriority.URGENT
            },
            NotificationTemplate.DAILY_REPORT: {
                'title': '每日健康报告',
                'channels': [NotificationChannel.WECHAT],
                'priority': NotificationPriority.LOW
            },
            NotificationTemplate.PROACTIVE_CARE: {
                'title': '主动关怀提醒',
                'channels': [NotificationChannel.APP_PUSH],
                'priority': NotificationPriority.NORMAL
            },
            NotificationTemplate.INACTIVITY_ALERT: {
                'title': '活跃度提醒',
                'channels': [NotificationChannel.WECHAT, NotificationChannel.APP_PUSH],
                'priority': NotificationPriority.NORMAL
            }
        }

    async def send_notification(
        self,
        user_id: int,
        template: NotificationTemplate,
        content: str,
        extra_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发送通知

        Args:
            user_id: 老人用户ID
            template: 通知模板
            content: 通知内容
            extra_data: 额外数据

        Returns:
            发送结果
        """
        try:
            # 获取模板配置
            template_config = self.templates.get(template)
            if not template_config:
                return {'success': False, 'error': '未知模板'}

            # 获取老人的家属信息
            from app.models.database import SessionLocal, FamilyMember
            db = SessionLocal()

            try:
                family_members = db.query(FamilyMember).filter(
                    FamilyMember.user_id == user_id
                ).all()

                if not family_members:
                    return {'success': False, 'error': '没有关联的家属'}

                results = {
                    'success': True,
                    'sent_count': 0,
                    'failed_count': 0,
                    'details': []
                }

                # 根据优先级决定发送给哪些家属
                recipients = family_members
                if template_config['priority'] != NotificationPriority.URGENT:
                    # 非紧急情况只发送给主要联系人
                    primary = [f for f in family_members if f.is_primary]
                    if primary:
                        recipients = primary

                # 紧急模板需要"任一通道成功 = 该家属成功"的逻辑
                # （而不是"所有通道都失败才记 dead letter"），便于运维定位"谁没收到"
                is_critical = template == NotificationTemplate.EMERGENCY

                # 向每个家属发送通知
                for family in recipients:
                    family_any_success = False
                    family_failed_channels: List[Dict[str, Any]] = []

                    for channel in template_config['channels']:
                        pusher = self.pushers.get(channel)
                        if not pusher:
                            continue

                        # 获取接收者标识
                        recipient = self._get_recipient(family, channel)
                        if not recipient:
                            continue

                        # 发送推送（pusher.push 内部已带 retry；这里再补 try/except
                        # 是为了把"重试用尽仍失败"统一翻译为 success=False）
                        try:
                            success = await pusher.push(
                                recipient=recipient,
                                title=template_config['title'],
                                content=content,
                                data=extra_data
                            )
                        except Exception as exc:
                            logger.error(
                                f"通道 {channel.value} 推送异常（重试用尽）: "
                                f"family={family.id} err={exc}"
                            )
                            success = False
                            family_failed_channels.append({
                                "channel": channel.value,
                                "error": str(exc),
                            })

                        result_detail = {
                            'family_id': family.id,
                            'family_name': family.name,
                            'channel': channel.value,
                            'success': success
                        }
                        results['details'].append(result_detail)

                        if success:
                            results['sent_count'] += 1
                            family_any_success = True
                        else:
                            results["failed_count"] += 1
                            family_failed_channels.append({
                                "channel": channel.value,
                                "error": "push returned False",
                            })

                    # 紧急通知 + 该家属所有通道都失败 → 死信记录 + ERROR 日志
                    # （健康告警等非紧急通知失败不入 DLQ，避免噪音）
                    if is_critical and not family_any_success:
                        dead_letter_queue.record(DeadLetterRecord(
                            channel="multi",
                            recipient=str(family.id),
                            template=template.value,
                            payload={
                                "user_id": user_id,
                                "family_name": family.name,
                                "content": content[:200],
                                "failed_channels": family_failed_channels,
                            },
                            error="所有通道均失败",
                            severity="critical",
                            attempts=len(template_config['channels']),
                        ))

                # 记录通知日志
                await self._log_notification(
                    user_id=user_id,
                    template=template,
                    content=content,
                    results=results
                )

                return results

            finally:
                db.close()

        except Exception as e:
            logger.error(f'发送通知失败: {e}')
            return {'success': False, 'error': str(e)}

    def _get_recipient(self, family, channel: NotificationChannel) -> Optional[str]:
        """获取推送接收者标识"""
        if channel == NotificationChannel.WECHAT:
            return family.openid
        elif channel == NotificationChannel.SMS:
            return family.phone
        elif channel == NotificationChannel.APP_PUSH:
            return family.phone  # 使用手机号作为设备标识
        return None

    async def _log_notification(
        self,
        user_id: int,
        template: NotificationTemplate,
        content: str,
        results: Dict
    ):
        """记录通知日志"""
        logger.info(
            f"通知发送: user_id={user_id}, template={template.value}, "
            f"sent={results['sent_count']}, failed={results['failed_count']}"
        )

        # 保存通知记录到数据库
        try:
            from app.models.database import SessionLocal, Notification
            db = SessionLocal()
            try:
                sent_channels = ','.join(
                    detail['channel'] for detail in results.get('details', []) if detail.get('success')
                )
                notification = Notification(
                    user_id=user_id,
                    notification_type=template.value,
                    priority=self.templates.get(template, {}).get('priority', NotificationPriority.NORMAL).name.lower(),
                    title=self.templates.get(template, {}).get('title', ''),
                    content=content,
                    data=json.dumps(results, ensure_ascii=False),
                    sent_channels=sent_channels,
                    delivery_status=json.dumps(results.get('details', []), ensure_ascii=False),
                )
                db.add(notification)
                db.commit()
            except Exception as db_err:
                db.rollback()
                logger.error(f"保存通知记录到数据库失败: {db_err}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"初始化数据库会话失败: {e}")

    async def send_health_alert(
        self,
        user_id: int,
        user_name: str,
        risk_score: float,
        risk_reason: str,
        conversation_summary: str
    ) -> Dict[str, Any]:
        """
        发送健康告警

        Args:
            user_id: 老人用户ID
            user_name: 老人姓名
            risk_score: 风险评分
            risk_reason: 风险原因
            conversation_summary: 对话摘要

        Returns:
            发送结果
        """
        template = NotificationTemplate.EMERGENCY if risk_score >= 9 else NotificationTemplate.HEALTH_ALERT

        content = f"""
{user_name}健康告警

风险等级：{'紧急' if risk_score >= 9 else '高风险'}
风险评分：{risk_score}/10
原因：{risk_reason}

对话摘要：
{conversation_summary[:100]}...

请及时关注老人健康状况。
        """.strip()

        return await self.send_notification(
            user_id=user_id,
            template=template,
            content=content,
            extra_data={
                'risk_score': risk_score,
                "risk_reason": risk_reason,
                'alert_type': 'health'
            }
        )

    async def send_daily_report(
        self,
        user_id: int,
        user_name: str,
        report_data: Dict
    ) -> Dict[str, Any]:
        """
        发送每日报告

        Args:
            user_id: 老人用户ID
            user_name: 老人姓名
            report_data: 报告数据

        Returns:
            发送结果
        """
        content = f"""
{user_name}每日健康报告

日期：{report_data.get('date', '今日')}
对话次数：{report_data.get('conversation_count', 0)}次
平均风险评分：{report_data.get('avg_risk_score', 0):.1f}
情绪状态：{report_data.get('mood', '正常')}

{report_data.get('summary', '')}
        """.strip()

        return await self.send_notification(
            user_id=user_id,
            template=NotificationTemplate.DAILY_REPORT,
            content=content,
            extra_data=report_data
        )

    async def send_inactivity_alert(
        self,
        user_id: int,
        user_name: str,
        inactive_hours: int
    ) -> Dict[str, Any]:
        """
        发送不活跃提醒

        Args:
            user_id: 老人用户ID
            user_name: 老人姓名
            inactive_hours: 不活跃小时数

        Returns:
            发送结果
        """
        content = f"""
{user_name}已有{inactive_hours}小时未与安心宝交流

建议您主动联系老人，了解近况。

如有任何异常，请及时查看或上门探望。
        """.strip()

        return await self.send_notification(
            user_id=user_id,
            template=NotificationTemplate.INACTIVITY_ALERT,
            content=content,
            extra_data={
                'inactive_hours': inactive_hours,
                'alert_type': 'inactivity'
            }
        )


# 全局通知服务实例
notification_service = NotificationService()
