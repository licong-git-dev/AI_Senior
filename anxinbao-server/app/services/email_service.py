"""
安心宝 - 邮件通知服务
支持SMTP邮件发送，包括健康报告、告警通知等
"""
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailConfig:
    """邮件配置"""
    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        smtp_user: str = None,
        smtp_password: str = None,
        use_tls: bool = True,
        use_ssl: bool = False,
        sender_name: str = '安心宝',
        sender_email: str = None,
        timeout: int = 30
    ):
        self.smtp_host = smtp_host or getattr(settings, 'smtp_host', 'smtp.qq.com')
        self.smtp_port = smtp_port or getattr(settings, 'smtp_port', 587)
        self.smtp_user = smtp_user or getattr(settings, 'smtp_user', '')
        self.smtp_password = smtp_password or getattr(settings, 'smtp_password', '')
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.sender_name = sender_name
        self.sender_email = sender_email or self.smtp_user
        self.timeout = timeout


class EmailTemplate:
    """邮件模板类型"""
    HEALTH_ALERT = "health_alert"
    HEALTH_REPORT = "health_report"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_REPORT = "weekly_report"
    MONTHLY_REPORT = "monthly_report"
    EMERGENCY = "emergency"
    MEDICATION_REMINDER = "medication_reminder"
    DEVICE_ALERT = "device_alert"
    WELCOME = "welcome"
    VERIFICATION_CODE = "verification_code"


# 邮件模板HTML
EMAIL_TEMPLATES = {
    EmailTemplate.HEALTH_ALERT: """
<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <style>
        body { font-family: 'Microsoft YaHei', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; }
        .header p { margin: 10px 0 0; opacity: 0.9; }
        .content { padding: 30px; }
        .alert-box { background: #fef2f2; border-left: 4px solid #ef4444; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .alert-box h3 { color: #dc2626; margin: 0 0 10px; }
        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }
        .info-item { background: #f9fafb; padding: 15px; border-radius: 8px; }
        .info-item label { color: #6b7280; font-size: 12px; display: block; margin-bottom: 5px; }
        .info-item value { color: #111827; font-size: 16px; font-weight: bold; }
        .btn { display: inline-block; background: #ef4444; color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none; margin-top: 20px; }
        .footer { background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; font-size: 12px; }
    </style>
</head>
<body>
    <div class='container'>
        <div class='header'>
            <h1>健康告警通知</h1>
            <p>{{ elderly_name }}的健康状况需要您的关注</p>
        </div>
        <div class='content'>
            <div class='alert-box'>
                <h3>{{ alert_title }}</h3>
                <p>{{ alert_content }}</p>
            </div>
            <div class='info-grid'>
                <div class='info-item'>
                    <label>告警时间</label>
                    <value>{{ alert_time }}</value>
                </div>
                <div class='info-item'>
                    <label>告警级别</label>
                    <value>{{ alert_level }}</value>
                </div>
                <div class='info-item'>
                    <label>风险评分</label>
                    <value>{{ risk_score }}/10</value>
                </div>
                <div class='info-item'>
                    <label>建议措施</label>
                    <value>{{ suggestion }}</value>
                </div>
            </div>
            <p>请尽快登录安心宝APP查看详情，或联系老人了解情况。</p>
            <a href='{{ app_link }}' class='btn'>查看详情</a>
        </div>
        <div class='footer'>
            <p>此邮件由安心宝系统自动发送，请勿直接回复</p>
            <p>如有疑问，请联系客服：{{ support_phone }}</p>
        </div>
    </div>
</body>
</html>
    """,

    EmailTemplate.HEALTH_REPORT: """
<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <style>
        body { font-family: 'Microsoft YaHei', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; }
        .header p { margin: 10px 0 0; opacity: 0.9; }
        .content { padding: 30px; }
        .score-card { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; border-radius: 16px; text-align: center; margin-bottom: 25px; }
        .score-card .score { font-size: 48px; font-weight: bold; }
        .score-card .label { opacity: 0.9; }
        .stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0; }
        .stat-item { background: #f9fafb; padding: 20px; border-radius: 12px; text-align: center; }
        .stat-item .value { font-size: 24px; font-weight: bold; color: #111827; }
        .stat-item .label { color: #6b7280; font-size: 12px; margin-top: 5px; }
        .section { margin: 25px 0; }
        .section h3 { color: #111827; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #e5e7eb; }
        .trend-item { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #f3f4f6; }
        .trend-item:last-child { border-bottom: none; }
        .trend-up { color: #10b981; }
        .trend-down { color: #ef4444; }
        .btn { display: inline-block; background: #3b82f6; color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none; margin-top: 20px; }
        .footer { background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; font-size: 12px; }
    </style>
</head>
<body>
    <div class='container'>
        <div class='header'>
            <h1>{{ report_type }}健康报告</h1>
            <p>{{ elderly_name }} · {{ report_period }}</p>
        </div>
        <div class='content'>
            <div class='score-card'>
                <div class='score'>{{ health_score }}</div>
                <div class='label'>综合健康评分</div>
            </div>

            <div class='stats-grid'>
                <div class='stat-item'>
                    <div class='value'>{{ bp_avg }}</div>
                    <div class='label'>平均血压 (mmHg)</div>
                </div>
                <div class='stat-item'>
                    <div class='value'>{{ hr_avg }}</div>
                    <div class='label'>平均心率 (次/分)</div>
                </div>
                <div class='stat-item'>
                    <div class='value'>{{ steps_total }}</div>
                    <div class='label'>累计步数</div>
                </div>
                <div class='stat-item'>
                    <div class='value'>{{ medication_rate }}%</div>
                    <div class='label'>服药依从性</div>
                </div>
            </div>

            <div class='section'>
                <h3>健康趋势</h3>
                {% for item in trends %}
                <div class='trend-item'>
                    <span>{{ item.name }}</span>
                    <span class="{{ item.trend_class }}">{{ item.value }} {{ item.trend_icon }}</span>
                </div>
                {% endfor %}
            </div>

            <div class='section'>
                <h3>健康建议</h3>
                <ul>
                {% for advice in advices %}
                    <li>{{ advice }}</li>
                {% endfor %}
                </ul>
            </div>

            <a href='{{ report_link }}' class='btn'>查看完整报告</a>
        </div>
        <div class='footer'>
            <p>报告生成时间：{{ generated_at }}</p>
            <p>安心宝 - 您的家庭健康守护者</p>
        </div>
    </div>
</body>
</html>
    """,

    EmailTemplate.EMERGENCY: """
<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <style>
        body { font-family: 'Microsoft YaHei', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 28px; animation: pulse 1s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        .content { padding: 30px; }
        .emergency-box { background: #fef2f2; border: 2px solid #dc2626; padding: 25px; border-radius: 12px; margin-bottom: 20px; }
        .emergency-box h2 { color: #dc2626; margin: 0 0 15px; }
        .info-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #fee2e2; }
        .info-row:last-child { border-bottom: none; }
        .location-box { background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .btn-emergency { display: block; background: #dc2626; color: white; padding: 15px 30px; border-radius: 8px; text-decoration: none; text-align: center; font-size: 18px; font-weight: bold; margin-top: 20px; }
        .footer { background: #fef2f2; padding: 20px; text-align: center; color: #991b1b; font-size: 14px; font-weight: bold; }
    </style>
</head>
<body>
    <div class='container'>
        <div class='header'>
            <h1>紧急求助</h1>
            <p>{{ elderly_name }}触发了SOS紧急求助</p>
        </div>
        <div class='content'>
            <div class='emergency-box'>
                <h2>请立即联系老人或采取行动！</h2>
                <div class='info-row'>
                    <span>触发时间</span>
                    <strong>{{ trigger_time }}</strong>
                </div>
                <div class='info-row'>
                    <span>紧急类型</span>
                    <strong>{{ emergency_type }}</strong>
                </div>
                <div class='info-row'>
                    <span>联系电话</span>
                    <strong>{{ elderly_phone }}</strong>
                </div>
            </div>

            {% if location %}
            <div class="location-box">
                <strong>最后位置：</strong>
                <p>{{ location.address }}</p>
                <p style="color: #6b7280; font-size: 12px;">
                    经度: {{ location.longitude }} | 纬度: {{ location.latitude }}
                </p>
            </div>
            {% endif %}

            <a href='tel:{{ elderly_phone }}' class='btn-emergency'>立即拨打电话</a>
            <a href='{{ app_link }}' class='btn-emergency' style="background: #f97316; margin-top: 10px;">打开安心宝APP</a>
        </div>
        <div class='footer'>
            <p>如无法联系老人，请立即拨打120或前往老人所在位置！</p>
        </div>
    </div>
</body>
</html>
    """,

    EmailTemplate.VERIFICATION_CODE: """
<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <style>
        body { font-family: 'Microsoft YaHei', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 500px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #FF6B35 0%, #f97316 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; }
        .content { padding: 30px; text-align: center; }
        .code-box { background: #f9fafb; padding: 25px; border-radius: 12px; margin: 25px 0; }
        .code { font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #FF6B35; }
        .expire { color: #6b7280; font-size: 14px; margin-top: 10px; }
        .warning { background: #fef3c7; color: #92400e; padding: 15px; border-radius: 8px; margin-top: 20px; font-size: 13px; }
        .footer { background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; font-size: 12px; }
    </style>
</head>
<body>
    <div class='container'>
        <div class='header'>
            <h1>验证码</h1>
        </div>
        <div class='content'>
            <p>您正在进行{{ action }}操作，验证码如下：</p>
            <div class='code-box'>
                <div class='code'>{{ code }}</div>
                <div class='expire'>验证码有效期{{ expire_minutes }}分钟</div>
            </div>
            <div class='warning'>
                如非本人操作，请忽略此邮件。请勿将验证码告知他人。
            </div>
        </div>
        <div class='footer'>
            <p>安心宝 - 您的家庭健康守护者</p>
        </div>
    </div>
</body>
</html>
    """
}


class EmailService:
    """邮件服务"""

    def __init__(self, config: EmailConfig = None):
        self.config = config or EmailConfig()
        self._executor = ThreadPoolExecutor(max_workers=5)
        self._template_env = Environment(
            autoescape=select_autoescape(['html', 'xml'])
        )

    def _get_template(self, template_type: str) -> str:
        """获取邮件模板"""
        return EMAIL_TEMPLATES.get(template_type, "")

    def _render_template(self, template_type: str, context: Dict) -> str:
        """渲染邮件模板"""
        template_str = self._get_template(template_type)
        if not template_str:
            return ""

        template = self._template_env.from_string(template_str)
        return template.render(**context)

    def _send_email_sync(
        self,
        to_email: Union[str, List[str]],
        subject: str,
        html_content: str,
        text_content: str = None,
        attachments: List[Dict] = None,
        cc: List[str] = None,
        bcc: List[str] = None
    ) -> Dict[str, Any]:
        """同步发送邮件"""
        try:
            # 创建邮件
            msg = MIMEMultipart("alternative")
            msg['Subject'] = subject
            msg['From'] = f'{self.config.sender_name} <{self.config.sender_email}>'

            if isinstance(to_email, list):
                msg['To'] = ', '.join(to_email)
                recipients = to_email.copy()
            else:
                msg['To'] = to_email
                recipients = [to_email]

            if cc:
                msg['Cc'] = ', '.join(cc)
                recipients.extend(cc)

            if bcc:
                recipients.extend(bcc)

            # 添加纯文本内容
            if text_content:
                part_text = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part_text)

            # 添加HTML内容
            part_html = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part_html)

            # 添加附件
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)

            # 发送邮件
            if self.config.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    self.config.smtp_host,
                    self.config.smtp_port,
                    context=context,
                    timeout=self.config.timeout
                )
            else:
                server = smtplib.SMTP(
                    self.config.smtp_host,
                    self.config.smtp_port,
                    timeout=self.config.timeout
                )
                if self.config.use_tls:
                    server.starttls()

            server.login(self.config.smtp_user, self.config.smtp_password)
            server.sendmail(self.config.sender_email, recipients, msg.as_string())
            server.quit()

            logger.info(f'邮件发送成功: {to_email} - {subject}')
            return {
                'success': True,
                'message': '邮件发送成功',
                'recipients': recipients
            }

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f'SMTP认证失败: {e}')
            return {'success': False, 'error': '邮件认证失败，请检查配置'}

        except smtplib.SMTPException as e:
            logger.error(f'SMTP错误: {e}')
            return {'success': False, 'error': f'邮件发送失败: {str(e)}'}

        except Exception as e:
            logger.error(f'邮件发送异常: {e}')
            return {'success': False, 'error': str(e)}

    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict):
        """添加附件"""
        try:
            file_path = attachment.get('path')
            file_name = attachment.get('name') or Path(file_path).name

            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{file_name}"'
                )
                msg.attach(part)

        except Exception as e:
            logger.error(f'添加附件失败: {e}')

    async def send_email(
        self,
        to_email: Union[str, List[str]],
        subject: str,
        html_content: str,
        text_content: str = None,
        attachments: List[Dict] = None,
        cc: List[str] = None,
        bcc: List[str] = None
    ) -> Dict[str, Any]:
        """
        异步发送邮件

        Args:
            to_email: 收件人邮箱（支持单个或列表）
            subject: 邮件主题
            html_content: HTML内容
            text_content: 纯文本内容（可选）
            attachments: 附件列表 [{'path': '/path/to/file', 'name': 'filename'}]
            cc: 抄送列表
            bcc: 密送列表

        Returns:
            发送结果
        """
        if not self.config.smtp_user or not self.config.smtp_password:
            logger.warning('邮件服务未配置')
            return {'success': False, 'error': '邮件服务未配置'}

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._send_email_sync,
            to_email,
            subject,
            html_content,
            text_content,
            attachments,
            cc,
            bcc
        )

    async def send_template_email(
        self,
        to_email: Union[str, List[str]],
        template_type: str,
        context: Dict,
        subject: str = None,
        attachments: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        发送模板邮件

        Args:
            to_email: 收件人邮箱
            template_type: 模板类型
            context: 模板上下文数据
            subject: 邮件主题（可选，会自动生成）
            attachments: 附件列表

        Returns:
            发送结果
        """
        # 渲染模板
        html_content = self._render_template(template_type, context)
        if not html_content:
            return {'success': False, 'error': '模板渲染失败'}

        # 默认主题
        default_subjects = {
            EmailTemplate.HEALTH_ALERT: f"【安心宝】{context.get('elderly_name', '')}健康告警通知",
            EmailTemplate.HEALTH_REPORT: f"【安心宝】{context.get('elderly_name', '')}{context.get('report_type', '')}健康报告",
            EmailTemplate.EMERGENCY: f"【紧急】{context.get('elderly_name', '')}触发SOS求助！",
            EmailTemplate.VERIFICATION_CODE: '【安心宝】您的验证码',
            EmailTemplate.MEDICATION_REMINDER: f"【安心宝】{context.get('elderly_name', '')}用药提醒",
            EmailTemplate.DEVICE_ALERT: '【安心宝】设备状态提醒',
        }

        email_subject = subject or default_subjects.get(template_type, '【安心宝】通知')

        return await self.send_email(
            to_email=to_email,
            subject=email_subject,
            html_content=html_content,
            attachments=attachments
        )

    # 便捷方法

    async def send_health_alert(
        self,
        to_email: Union[str, List[str]],
        elderly_name: str,
        alert_title: str,
        alert_content: str,
        alert_level: str,
        risk_score: float,
        suggestion: str = '请及时关注'
    ) -> Dict[str, Any]:
        """发送健康告警邮件"""
        context = {
            "elderly_name": elderly_name,
            "alert_title": alert_title,
            "alert_content": alert_content,
            "alert_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "alert_level": alert_level,
            "risk_score": risk_score,
            "suggestion": suggestion,
            "app_link": getattr(settings, 'app_download_url', 'https://anxinbao.com/app'),
            "support_phone": getattr(settings, 'support_phone', '400-123-4567')
        }

        return await self.send_template_email(
            to_email=to_email,
            template_type=EmailTemplate.HEALTH_ALERT,
            context=context
        )

    async def send_health_report(
        self,
        to_email: Union[str, List[str]],
        elderly_name: str,
        report_type: str,
        report_period: str,
        health_score: int,
        stats: Dict,
        trends: List[Dict],
        advices: List[str],
        report_link: str = None
    ) -> Dict[str, Any]:
        """发送健康报告邮件"""
        context = {
            "elderly_name": elderly_name,
            "report_type": report_type,
            "report_period": report_period,
            "health_score": health_score,
            "bp_avg": stats.get('bp_avg', 'N/A'),
            "hr_avg": stats.get('hr_avg', 'N/A'),
            "steps_total": stats.get('steps_total', 'N/A'),
            "medication_rate": stats.get('medication_rate', 'N/A'),
            "trends": trends,
            "advices": advices,
            "report_link": report_link or getattr(settings, 'app_download_url', 'https://anxinbao.com/app'),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return await self.send_template_email(
            to_email=to_email,
            template_type=EmailTemplate.HEALTH_REPORT,
            context=context
        )

    async def send_emergency_alert(
        self,
        to_email: Union[str, List[str]],
        elderly_name: str,
        elderly_phone: str,
        emergency_type: str,
        location: Dict = None
    ) -> Dict[str, Any]:
        """发送紧急求助邮件"""
        context = {
            "elderly_name": elderly_name,
            "elderly_phone": elderly_phone,
            "trigger_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "emergency_type": emergency_type,
            "location": location,
            "app_link": getattr(settings, 'app_download_url', 'https://anxinbao.com/app')
        }

        return await self.send_template_email(
            to_email=to_email,
            template_type=EmailTemplate.EMERGENCY,
            context=context
        )

    async def send_verification_code(
        self,
        to_email: str,
        code: str,
        action: str = '账号验证',
        expire_minutes: int = 5
    ) -> Dict[str, Any]:
        """发送验证码邮件"""
        context = {
            'code': code,
            'action': action,
            "expire_minutes": expire_minutes
        }

        return await self.send_template_email(
            to_email=to_email,
            template_type=EmailTemplate.VERIFICATION_CODE,
            context=context,
            subject=f'【安心宝】{action}验证码'
        )


# 全局邮件服务实例
email_service = EmailService()
