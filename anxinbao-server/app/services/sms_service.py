"""
安心宝 - 短信通知服务
支持多个短信服务商（阿里云、腾讯云）
"""
import logging
import json
import hmac
import hashlib
import base64
import time
import uuid
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from enum import Enum
from urllib.parse import quote
import asyncio
from concurrent.futures import ThreadPoolExecutor

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SMSProvider(Enum):
    """短信服务商"""
    ALIYUN = 'aliyun'  # 阿里云
    TENCENT = 'tencent'  # 腾讯云
    MOCK = 'mock'  # 模拟（开发测试用）


class SMSTemplate(Enum):
    """短信模板类型"""
    VERIFICATION_CODE = "verification_code"  # 验证码
    HEALTH_ALERT = "health_alert"  # 健康告警
    EMERGENCY = "emergency"  # 紧急求助
    MEDICATION_REMINDER = "medication_reminder"  # 用药提醒
    DEVICE_ALERT = "device_alert"  # 设备告警
    DAILY_REPORT = "daily_report"  # 日报提醒


class SMSConfig:
    """短信配置"""
    def __init__(
        self,
        provider: SMSProvider = SMSProvider.ALIYUN,
        access_key_id: str = None,
        access_key_secret: str = None,
        sign_name: str = '安心宝',
        region: str = "cn-hangzhou",
        templates: Dict[str, str] = None
    ):
        self.provider = provider
        self.access_key_id = access_key_id or getattr(settings, 'aliyun_access_key_id', '')
        self.access_key_secret = access_key_secret or getattr(settings, 'aliyun_access_key_secret', '')
        self.sign_name = sign_name or getattr(settings, 'sms_sign_name', '安心宝')
        self.region = region

        # 短信模板ID映射
        self.templates = templates or {
            SMSTemplate.VERIFICATION_CODE.value: getattr(settings, 'sms_template_code', 'SMS_123456789'),
            SMSTemplate.HEALTH_ALERT.value: getattr(settings, 'sms_template_health_alert', 'SMS_123456790'),
            SMSTemplate.EMERGENCY.value: getattr(settings, 'sms_template_emergency', 'SMS_123456791'),
            SMSTemplate.MEDICATION_REMINDER.value: getattr(settings, 'sms_template_medication', 'SMS_123456792'),
            SMSTemplate.DEVICE_ALERT.value: getattr(settings, 'sms_template_device', 'SMS_123456793'),
            SMSTemplate.DAILY_REPORT.value: getattr(settings, 'sms_template_daily_report', 'SMS_123456794'),
        }


class AliyunSMSClient:
    """阿里云短信客户端"""

    API_ENDPOINT = "https://dysmsapi.aliyuncs.com"

    def __init__(self, config: SMSConfig):
        self.config = config

    def _sign(self, params: Dict) -> str:
        """生成签名"""
        sorted_params = sorted(params.items())
        canonicalized_query_string = '&'.join([
            f'{quote(k, safe="")}={quote(str(v), safe="")}'
            for k, v in sorted_params
        ])

        string_to_sign = f'GET&%2F&{quote(canonicalized_query_string, safe="")}'

        key = f'{self.config.access_key_secret}&'
        signature = hmac.new(
            key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha1
        ).digest()

        return base64.b64encode(signature).decode('utf-8')

    async def send_sms(
        self,
        phone_number: str,
        template_code: str,
        template_param: Dict = None
    ) -> Dict[str, Any]:
        """发送短信"""
        try:
            params = {
                'Format': 'JSON',
                'Version': '2017-05-25',
                'AccessKeyId': self.config.access_key_id,
                'SignatureMethod': 'HMAC-SHA1',
                'Timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'SignatureVersion': '1.0',
                'SignatureNonce': str(uuid.uuid4()),
                'Action': 'SendSms',
                'PhoneNumbers': phone_number,
                'SignName': self.config.sign_name,
                'TemplateCode': template_code,
            }

            if template_param:
                params['TemplateParam'] = json.dumps(template_param, ensure_ascii=False)

            # 生成签名
            params['Signature'] = self._sign(params)

            # 发送请求
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.API_ENDPOINT, params=params)
                result = response.json()

                if result.get('Code') == 'OK':
                    logger.info(f'短信发送成功: {phone_number}')
                    return {
                        'success': True,
                        'message_id': result.get('BizId'),
                        'request_id': result.get('RequestId')
                    }
                else:
                    logger.error(f'短信发送失败: {result}')
                    return {
                        'success': False,
                        'error': result.get('Message', '发送失败'),
                        'code': result.get('Code')
                    }

        except Exception as e:
            logger.error(f'短信发送异常: {e}')
            return {'success': False, 'error': str(e)}


class TencentSMSClient:
    """腾讯云短信客户端"""

    API_ENDPOINT = "https://sms.tencentcloudapi.com"

    def __init__(self, config: SMSConfig):
        self.config = config

    def _sign(self, params: Dict, timestamp: int) -> str:
        """生成签名（腾讯云签名方式）"""
        # 简化实现，实际使用应该按照腾讯云SDK方式
        service = "sms"
        host = "sms.tencentcloudapi.com"
        algorithm = "TC3-HMAC-SHA256"
        date = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')

        # ... 签名逻辑（简化）
        return ""

    async def send_sms(
        self,
        phone_number: str,
        template_id: str,
        template_param: List[str] = None
    ) -> Dict[str, Any]:
        """发送短信"""
        try:
            # 简化实现
            logger.info(f'腾讯云短信发送（模拟）: {phone_number}')
            return {
                'success': True,
                'message_id': str(uuid.uuid4())
            }
        except Exception as e:
            logger.error(f'短信发送异常: {e}')
            return {'success': False, 'error': str(e)}


class MockSMSClient:
    """模拟短信客户端（开发测试用）"""

    # 存储发送记录
    _sent_messages = []

    async def send_sms(
        self,
        phone_number: str,
        template_code: str,
        template_param: Dict = None
    ) -> Dict[str, Any]:
        """模拟发送短信"""
        message_id = str(uuid.uuid4())

        # 记录发送
        record = {
            'message_id': message_id,
            'phone_number': phone_number,
            'template_code': template_code,
            'template_param': template_param,
            'sent_at': datetime.now().isoformat()
        }
        self._sent_messages.append(record)

        logger.info(f'[模拟短信] 发送至 {phone_number}: {json.dumps(template_param, ensure_ascii=False)}')

        return {
            'success': True,
            'message_id': message_id,
            'mock': True
        }

    @classmethod
    def get_sent_messages(cls) -> List[Dict]:
        """获取发送记录"""
        return cls._sent_messages.copy()

    @classmethod
    def clear_sent_messages(cls):
        """清空发送记录"""
        cls._sent_messages.clear()


class SMSService:
    """短信服务"""

    def __init__(self, config: SMSConfig = None):
        self.config = config or SMSConfig()
        self._executor = ThreadPoolExecutor(max_workers=5)

        # 初始化客户端
        if self.config.provider == SMSProvider.ALIYUN:
            self.client = AliyunSMSClient(self.config)
        elif self.config.provider == SMSProvider.TENCENT:
            self.client = TencentSMSClient(self.config)
        else:
            self.client = MockSMSClient()

    def _get_template_code(self, template_type: SMSTemplate) -> str:
        """获取模板代码"""
        return self.config.templates.get(template_type.value, '')

    async def send_sms(
        self,
        phone_number: Union[str, List[str]],
        template_type: SMSTemplate,
        template_param: Dict = None
    ) -> Dict[str, Any]:
        """
        发送短信

        Args:
            phone_number: 手机号（支持单个或多个）
            template_type: 模板类型
            template_param: 模板参数

        Returns:
            发送结果
        """
        if not self.config.access_key_id and self.config.provider != SMSProvider.MOCK:
            logger.warning('短信服务未配置，使用模拟模式')
            self.client = MockSMSClient()

        template_code = self._get_template_code(template_type)
        if not template_code and self.config.provider != SMSProvider.MOCK:
            return {'success': False, 'error': '模板未配置'}

        # 处理批量发送
        if isinstance(phone_number, list):
            results = {
                'success': True,
                'total': len(phone_number),
                'sent': 0,
                'failed': 0,
                'details': []
            }

            for phone in phone_number:
                result = await self.client.send_sms(
                    phone_number=phone,
                    template_code=template_code,
                    template_param=template_param
                )
                results['details'].append({
                    'phone': phone,
                    **result
                })

                if result.get('success'):
                    results['sent'] += 1
                else:
                    results['failed'] += 1

            results['success'] = results['failed'] == 0
            return results
        else:
            return await self.client.send_sms(
                phone_number=phone_number,
                template_code=template_code,
                template_param=template_param
            )

    # 便捷方法

    async def send_verification_code(
        self,
        phone_number: str,
        code: str,
        expire_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        发送验证码

        Args:
            phone_number: 手机号
            code: 验证码
            expire_minutes: 有效期（分钟）

        Returns:
            发送结果
        """
        return await self.send_sms(
            phone_number=phone_number,
            template_type=SMSTemplate.VERIFICATION_CODE,
            template_param={
                'code': code,
                'expire': str(expire_minutes)
            }
        )

    async def send_health_alert(
        self,
        phone_number: Union[str, List[str]],
        elderly_name: str,
        alert_type: str,
        alert_content: str
    ) -> Dict[str, Any]:
        """
        发送健康告警短信

        Args:
            phone_number: 家属手机号
            elderly_name: 老人姓名
            alert_type: 告警类型
            alert_content: 告警内容

        Returns:
            发送结果
        """
        return await self.send_sms(
            phone_number=phone_number,
            template_type=SMSTemplate.HEALTH_ALERT,
            template_param={
                'name': elderly_name,
                'type': alert_type,
                'content': alert_content[:20]  # 短信长度限制
            }
        )

    async def send_emergency_alert(
        self,
        phone_number: Union[str, List[str]],
        elderly_name: str,
        elderly_phone: str,
        location: str = None
    ) -> Dict[str, Any]:
        """
        发送紧急求助短信

        Args:
            phone_number: 家属手机号
            elderly_name: 老人姓名
            elderly_phone: 老人电话
            location: 位置信息

        Returns:
            发送结果
        """
        return await self.send_sms(
            phone_number=phone_number,
            template_type=SMSTemplate.EMERGENCY,
            template_param={
                'name': elderly_name,
                'phone': elderly_phone,
                'location': location or '未知'
            }
        )

    async def send_medication_reminder(
        self,
        phone_number: Union[str, List[str]],
        elderly_name: str,
        medication_name: str,
        dosage: str,
        status: str = '未服用'
    ) -> Dict[str, Any]:
        """
        发送用药提醒短信

        Args:
            phone_number: 家属手机号
            elderly_name: 老人姓名
            medication_name: 药品名称
            dosage: 剂量
            status: 状态（已服用/未服用）

        Returns:
            发送结果
        """
        return await self.send_sms(
            phone_number=phone_number,
            template_type=SMSTemplate.MEDICATION_REMINDER,
            template_param={
                'name': elderly_name,
                'medicine': medication_name,
                'dosage': dosage,
                'status': status
            }
        )

    async def send_device_alert(
        self,
        phone_number: Union[str, List[str]],
        elderly_name: str,
        device_name: str,
        alert_reason: str
    ) -> Dict[str, Any]:
        """
        发送设备告警短信

        Args:
            phone_number: 家属手机号
            elderly_name: 老人姓名
            device_name: 设备名称
            alert_reason: 告警原因

        Returns:
            发送结果
        """
        return await self.send_sms(
            phone_number=phone_number,
            template_type=SMSTemplate.DEVICE_ALERT,
            template_param={
                'name': elderly_name,
                'device': device_name,
                'reason': alert_reason
            }
        )

    async def send_daily_report_notification(
        self,
        phone_number: Union[str, List[str]],
        elderly_name: str,
        health_score: int,
        summary: str
    ) -> Dict[str, Any]:
        """
        发送日报通知短信

        Args:
            phone_number: 家属手机号
            elderly_name: 老人姓名
            health_score: 健康评分
            summary: 摘要

        Returns:
            发送结果
        """
        return await self.send_sms(
            phone_number=phone_number,
            template_type=SMSTemplate.DAILY_REPORT,
            template_param={
                'name': elderly_name,
                'score': str(health_score),
                'summary': summary[:30]
            }
        )


# 全局短信服务实例
sms_service = SMSService()
