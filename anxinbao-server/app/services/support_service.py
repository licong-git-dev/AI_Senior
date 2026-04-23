"""
客户支持系统服务
提供智能客服、工单系统、FAQ知识库、用户反馈等功能
"""
import logging
import secrets
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


# ==================== 智能客服机器人 ====================

class IntentType(Enum):
    """意图类型"""
    GREETING = 'greeting'  # 问候
    FAREWELL = 'farewell'  # 告别
    HELP = 'help'  # 帮助
    ACCOUNT = "account"  # 账户问题
    SUBSCRIPTION = "subscription"  # 订阅问题
    HEALTH = 'health'  # 健康功能
    DEVICE = 'device'  # 设备问题
    PAYMENT = 'payment'  # 支付问题
    COMPLAINT = 'complaint'  # 投诉
    SUGGESTION = 'suggestion'  # 建议
    UNKNOWN = "unknown"  # 未知


@dataclass
class ChatMessage:
    """聊天消息"""
    message_id: str
    session_id: str
    role: str  # user/bot/agent
    content: str
    intent: Optional[IntentType] = None
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'message_id': self.message_id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'intent': self.intent.value if self.intent else None,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ChatSession:
    """聊天会话"""
    session_id: str
    user_id: int
    status: str = 'active'  # active/transferred/closed
    agent_id: Optional[int] = None
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'status': self.status,
            'agent_id': self.agent_id,
            "message_count": len(self.messages),
            'created_at': self.created_at.isoformat(),
            'closed_at': self.closed_at.isoformat() if self.closed_at else None
        }


class CustomerServiceBot:
    """智能客服机器人"""

    # 意图识别关键词
    INTENT_KEYWORDS = {
        IntentType.GREETING: ['你好', '您好', '早上好', '下午好', '晚上好', '嗨', 'hi', 'hello'],
        IntentType.FAREWELL: ['再见', '拜拜', '谢谢', '感谢', 'bye', 'goodbye'],
        IntentType.HELP: ['帮助', '怎么用', '如何', '教我', '不会', 'help'],
        IntentType.ACCOUNT: ['账号', '登录', '密码', '注册', '修改信息', '个人资料'],
        IntentType.SUBSCRIPTION: ['会员', '订阅', '套餐', '续费', '取消', 'vip'],
        IntentType.HEALTH: ['血压', '心率', '健康', '测量', '提醒', '报告'],
        IntentType.DEVICE: ['设备', '配对', '连接', '蓝牙', '同步', '手表', '血压计'],
        IntentType.PAYMENT: ['支付', '付款', '退款', '扣费', '充值', '发票'],
        IntentType.COMPLAINT: ['投诉', '不满意', '问题严重', '太差', '骗人'],
        IntentType.SUGGESTION: ['建议', '希望', '能不能', '最好', "改进"]
    }

    # 预设回复
    PRESET_RESPONSES = {
        IntentType.GREETING: [
            "您好！我是安心宝智能助手小安，很高兴为您服务。请问有什么可以帮您的？",
            "您好！欢迎使用安心宝客服。我是您的专属助手，请问需要什么帮助？"
        ],
        IntentType.FAREWELL: [
            "感谢您的咨询，祝您身体健康，生活愉快！如有问题随时找我。",
            "再见！如果还有问题，随时联系我们哦。"
        ],
        IntentType.HELP: [
            "好的，我来帮您介绍一下。安心宝提供以下功能：\n1. 健康监测 - 记录血压、心率等健康数据\n2. 智能提醒 - 用药、喝水、运动提醒\n3. 紧急呼叫 - 一键联系家人或急救\n4. 娱乐陪伴 - 听歌、听书、聊天\n\n请问您想了解哪个功能？"
        ],
        IntentType.ACCOUNT: [
            "关于账户问题，您可以：\n1. 在设置中修改个人信息\n2. 点击忘记密码进行密码重置\n3. 联系家人帮助修改\n\n如果仍有困难，我可以帮您转接人工客服。"
        ],
        IntentType.SUBSCRIPTION: [
            "关于会员订阅，我来为您介绍：\n- 基础版：免费，基础健康监测\n- 标准版：29.9元/月，全部功能\n- 尊享版：49.9元/月，专属管家服务\n\n您可以在【我的-会员中心】查看详情。需要帮您办理吗？"
        ],
        IntentType.HEALTH: [
            "关于健康功能，安心宝可以帮您：\n1. 记录每日血压、心率、血糖等数据\n2. 生成健康趋势报告\n3. 异常数据自动预警\n4. 提醒按时测量\n\n请问您具体想了解哪个功能？"
        ],
        IntentType.DEVICE: [
            "设备连接问题，请您尝试：\n1. 确保设备开启且电量充足\n2. 打开手机蓝牙\n3. 在APP中点击添加设备\n4. 按设备说明书操作配对\n\n如果还是无法连接，建议重启设备后再试。"
        ],
        IntentType.PAYMENT: [
            "关于支付问题，请您放心：\n1. 所有支付均有记录可查\n2. 退款一般3-5个工作日到账\n3. 发票可在订单详情中申请\n\n请问您遇到了什么支付问题？"
        ],
        IntentType.COMPLAINT: [
            "非常抱歉给您带来不好的体验！我们非常重视您的反馈。为了更好地帮助您解决问题，建议您：\n1. 描述一下具体问题\n2. 或者我帮您转接人工客服\n\n我们一定会认真处理。"
        ],
        IntentType.SUGGESTION: [
            "感谢您的宝贵建议！我们团队会认真考虑并持续改进产品。您的建议已经记录，如果被采纳我们会通知您。还有其他建议吗？"
        ],
        IntentType.UNKNOWN: [
            "不好意思，我没有完全理解您的问题。您可以：\n1. 换个方式描述\n2. 选择常见问题查看\n3. 转接人工客服\n\n请问需要哪种帮助？"
        ]
    }

    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.user_sessions: Dict[int, List[str]] = defaultdict(list)

    def recognize_intent(self, text: str) -> Tuple[IntentType, float]:
        """识别用户意图"""
        text_lower = text.lower()
        scores = defaultdict(float)

        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[intent] += 1

        if scores:
            best_intent = max(scores.items(), key=lambda x: x[1])
            confidence = min(best_intent[1] / 3, 1.0)
            return best_intent[0], confidence

        return IntentType.UNKNOWN, 0.3

    def create_session(self, user_id: int) -> ChatSession:
        """创建会话"""
        session_id = f"chat_{user_id}_{secrets.token_hex(6)}"

        session = ChatSession(
            session_id=session_id,
            user_id=user_id
        )

        self.sessions[session_id] = session
        self.user_sessions[user_id].append(session_id)

        # 添加欢迎消息
        import random
        welcome = random.choice(self.PRESET_RESPONSES[IntentType.GREETING])
        welcome_msg = ChatMessage(
            message_id=f'msg_{secrets.token_hex(4)}',
            session_id=session_id,
            role="bot",
            content=welcome,
            intent=IntentType.GREETING,
            confidence=1.0
        )
        session.messages.append(welcome_msg)

        return session

    def send_message(
        self,
        session_id: str,
        user_id: int,
        content: str
    ) -> Optional[ChatMessage]:
        """发送消息并获取回复"""
        session = self.sessions.get(session_id)
        if not session or session.user_id != user_id:
            return None

        # 记录用户消息
        intent, confidence = self.recognize_intent(content)
        user_msg = ChatMessage(
            message_id=f"msg_{secrets.token_hex(4)}",
            session_id=session_id,
            role='user',
            content=content,
            intent=intent,
            confidence=confidence
        )
        session.messages.append(user_msg)

        # 生成回复
        import random
        responses = self.PRESET_RESPONSES.get(intent, self.PRESET_RESPONSES[IntentType.UNKNOWN])
        reply_content = random.choice(responses)

        reply_msg = ChatMessage(
            message_id=f'msg_{secrets.token_hex(4)}',
            session_id=session_id,
            role="bot",
            content=reply_content,
            intent=intent,
            confidence=confidence
        )
        session.messages.append(reply_msg)

        return reply_msg

    def transfer_to_agent(self, session_id: str, agent_id: int) -> bool:
        """转接人工客服"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        session.status = "transferred"
        session.agent_id = agent_id

        transfer_msg = ChatMessage(
            message_id=f"msg_{secrets.token_hex(4)}",
            session_id=session_id,
            role='bot',
            content="正在为您转接人工客服，请稍候..."
        )
        session.messages.append(transfer_msg)

        return True

    def close_session(self, session_id: str) -> bool:
        """关闭会话"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        session.status = "closed"
        session.closed_at = datetime.now()
        return True

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取会话"""
        return self.sessions.get(session_id)

    def get_user_sessions(self, user_id: int) -> List[ChatSession]:
        """获取用户会话列表"""
        session_ids = self.user_sessions.get(user_id, [])
        return [self.sessions[sid] for sid in session_ids if sid in self.sessions]


# ==================== 工单系统 ====================

class TicketPriority(Enum):
    """工单优先级"""
    LOW = "low"
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'


class TicketStatus(Enum):
    """工单状态"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = 'resolved'
    CLOSED = 'closed'


class TicketCategory(Enum):
    """工单分类"""
    ACCOUNT = 'account'  # 账户问题
    PAYMENT = 'payment'  # 支付问题
    DEVICE = 'device'  # 设备问题
    FUNCTION = 'function'  # 功能问题
    COMPLAINT = 'complaint'  # 投诉
    OTHER = "other"  # 其他


@dataclass
class TicketComment:
    """工单评论"""
    comment_id: str
    ticket_id: str
    author_id: int
    author_type: str  # user/agent
    content: str
    attachments: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'comment_id': self.comment_id,
            'author_id': self.author_id,
            "author_type": self.author_type,
            'content': self.content,
            "attachments": self.attachments,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class Ticket:
    """工单"""
    ticket_id: str
    user_id: int
    category: TicketCategory
    priority: TicketPriority
    subject: str
    description: str
    status: TicketStatus = TicketStatus.OPEN
    assignee_id: Optional[int] = None
    comments: List[TicketComment] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'category': self.category.value,
            'priority': self.priority.value,
            'subject': self.subject,
            "description": self.description,
            'status': self.status.value,
            "assignee_id": self.assignee_id,
            "comment_count": len(self.comments),
            "attachments": self.attachments,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class TicketService:
    """工单服务"""

    def __init__(self):
        self.tickets: Dict[str, Ticket] = {}
        self.user_tickets: Dict[int, List[str]] = defaultdict(list)
        self.ticket_counter = 0

    def create_ticket(
        self,
        user_id: int,
        category: TicketCategory,
        priority: TicketPriority,
        subject: str,
        description: str,
        attachments: List[str] = None
    ) -> Ticket:
        """创建工单"""
        self.ticket_counter += 1
        ticket_id = f"TK{datetime.now().strftime('%Y%m%d')}{self.ticket_counter:04d}"

        ticket = Ticket(
            ticket_id=ticket_id,
            user_id=user_id,
            category=category,
            priority=priority,
            subject=subject,
            description=description,
            attachments=attachments or []
        )

        self.tickets[ticket_id] = ticket
        self.user_tickets[user_id].append(ticket_id)

        logger.info(f"创建工单 {ticket_id} - 用户 {user_id}")
        return ticket

    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """获取工单"""
        return self.tickets.get(ticket_id)

    def get_user_tickets(
        self,
        user_id: int,
        status: Optional[TicketStatus] = None
    ) -> List[Ticket]:
        """获取用户工单"""
        ticket_ids = self.user_tickets.get(user_id, [])
        tickets = [self.tickets[tid] for tid in ticket_ids if tid in self.tickets]

        if status:
            tickets = [t for t in tickets if t.status == status]

        return sorted(tickets, key=lambda x: x.created_at, reverse=True)

    def add_comment(
        self,
        ticket_id: str,
        author_id: int,
        author_type: str,
        content: str,
        attachments: List[str] = None
    ) -> Optional[TicketComment]:
        """添加评论"""
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return None

        comment = TicketComment(
            comment_id=f"cmt_{secrets.token_hex(4)}",
            ticket_id=ticket_id,
            author_id=author_id,
            author_type=author_type,
            content=content,
            attachments=attachments or []
        )

        ticket.comments.append(comment)
        ticket.updated_at = datetime.now()

        return comment

    def update_status(
        self,
        ticket_id: str,
        status: TicketStatus,
        agent_id: Optional[int] = None
    ) -> bool:
        """更新工单状态"""
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return False

        ticket.status = status
        ticket.updated_at = datetime.now()

        if agent_id:
            ticket.assignee_id = agent_id

        if status == TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.now()

        return True

    def assign_ticket(self, ticket_id: str, agent_id: int) -> bool:
        """分配工单"""
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return False

        ticket.assignee_id = agent_id
        ticket.status = TicketStatus.IN_PROGRESS
        ticket.updated_at = datetime.now()

        return True


# ==================== FAQ知识库 ====================

@dataclass
class FAQItem:
    """FAQ条目"""
    faq_id: str
    category: str
    question: str
    answer: str
    keywords: List[str]
    helpful_count: int = 0
    not_helpful_count: int = 0
    view_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'faq_id': self.faq_id,
            'category': self.category,
            'question': self.question,
            'answer': self.answer,
            'keywords': self.keywords,
            "helpful_count": self.helpful_count,
            "not_helpful_count": self.not_helpful_count,
            'view_count': self.view_count
        }


class FAQService:
    """FAQ知识库服务"""

    def __init__(self):
        self.faqs: Dict[str, FAQItem] = {}
        self.categories: Dict[str, List[str]] = defaultdict(list)
        self._init_default_faqs()

    def _init_default_faqs(self):
        """初始化默认FAQ"""
        default_faqs = [
            # 账户问题
            {
                'category': '账户',
                'question': '如何注册安心宝账号？',
                "answer": "您可以通过以下方式注册：\n1. 下载安心宝APP\n2. 点击'注册'按钮\n3. 输入手机号获取验证码\n4. 设置密码完成注册\n\n也可以请家人帮助注册哦！",
                'keywords': ['注册', '账号', '新用户']
            },
            {
                'category': '账户',
                'question': '忘记密码怎么办？',
                "answer": "忘记密码可以这样找回：\n1. 在登录页点击'忘记密码'\n2. 输入注册手机号\n3. 获取验证码验证\n4. 设置新密码\n\n如有困难可联系客服帮助。",
                'keywords': ['密码', '忘记', '找回', '重置']
            },
            # 健康功能
            {
                'category': '健康',
                'question': '如何测量血压？',
                "answer": "测量血压的步骤：\n1. 确保血压计已连接（蓝牙配对）\n2. 安静休息5分钟\n3. 打开APP点击'测血压'\n4. 按血压计说明操作\n5. 数据会自动同步到APP\n\n建议每天固定时间测量。",
                'keywords': ['血压', '测量', '如何', '怎么']
            },
            {
                'category': '健康',
                'question': '健康报告在哪里查看？',
                "answer": "查看健康报告：\n1. 打开APP首页\n2. 点击'健康报告'或'我的健康'\n3. 可以查看日报/周报/月报\n4. 也可以分享给家人查看\n\n报告会自动生成，无需手动操作。",
                'keywords': ['报告', '健康', '查看', '在哪']
            },
            # 设备问题
            {
                'category': '设备',
                'question': '设备无法连接怎么办？',
                "answer": "设备连接失败请尝试：\n1. 检查设备是否开启\n2. 确认设备电量充足\n3. 打开手机蓝牙\n4. 靠近设备重试连接\n5. 重启APP后再试\n\n如仍无法连接，请联系客服。",
                'keywords': ['连接', '设备', '蓝牙', '失败', '无法']
            },
            {
                'category': '设备',
                'question': '支持哪些智能设备？',
                "answer": "安心宝支持以下设备：\n- 血压计：欧姆龙、鱼跃、小米等\n- 血糖仪：三诺、罗氏、强生等\n- 智能手表：华为、小米、OPPO等\n- 体重秤：华为、小米、云康宝等\n\n具体型号请在APP查看。",
                'keywords': ['支持', '设备', '哪些', '品牌']
            },
            # 会员订阅
            {
                'category': '会员',
                'question': '会员有什么特权？',
                "answer": "会员特权包括：\n- 基础版（免费）：基础健康监测\n- 标准版：全功能、无广告、健康报告\n- 尊享版：专属管家、优先客服、家庭共享\n\n在'我的-会员中心'查看详情。",
                'keywords': ['会员', '特权', '区别', 'vip']
            },
            {
                'category': '会员',
                'question': '如何取消订阅？',
                "answer": "取消订阅步骤：\n1. 打开'我的-会员中心'\n2. 点击'管理订阅'\n3. 选择'取消自动续费'\n4. 确认取消\n\n取消后当期仍可使用，到期后降为免费版。",
                'keywords': ['取消', '订阅', '退订', '不续费']
            },
            # 支付问题
            {
                'category': '支付',
                'question': '支付失败怎么办？',
                "answer": "支付失败请检查：\n1. 网络是否正常\n2. 支付账户余额是否充足\n3. 是否绑定了银行卡\n4. 尝试更换支付方式\n\n如扣款未到账，一般24小时内会退回。",
                'keywords': ['支付', '失败', '付款', '扣款']
            },
            {
                'category': '支付',
                'question': '如何申请退款？',
                "answer": "申请退款流程：\n1. 打开'订单记录'\n2. 找到要退款的订单\n3. 点击'申请退款'\n4. 选择退款原因\n5. 等待审核（1-3个工作日）\n\n退款到账需3-5个工作日。",
                'keywords': ['退款', '申请', '退钱']
            }
        ]

        for i, faq_data in enumerate(default_faqs):
            faq_id = f'faq_{i+1:03d}'
            faq = FAQItem(
                faq_id=faq_id,
                category=faq_data['category'],
                question=faq_data['question'],
                answer=faq_data['answer'],
                keywords=faq_data['keywords']
            )
            self.faqs[faq_id] = faq
            self.categories[faq_data["category"]].append(faq_id)

    def search_faqs(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[FAQItem]:
        """搜索FAQ"""
        results = []
        query_lower = query.lower()

        for faq in self.faqs.values():
            if category and faq.category != category:
                continue

            # 计算匹配分数
            score = 0
            if query_lower in faq.question.lower():
                score += 3
            if query_lower in faq.answer.lower():
                score += 1
            for keyword in faq.keywords:
                if keyword in query_lower or query_lower in keyword:
                    score += 2

            if score > 0:
                results.append((faq, score))

        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:limit]]

    def get_faq(self, faq_id: str) -> Optional[FAQItem]:
        """获取FAQ详情"""
        faq = self.faqs.get(faq_id)
        if faq:
            faq.view_count += 1
        return faq

    def get_categories(self) -> List[Dict[str, Any]]:
        """获取分类列表"""
        return [
            {'name': cat, 'count': len(faq_ids)}
            for cat, faq_ids in self.categories.items()
        ]

    def get_faqs_by_category(self, category: str) -> List[FAQItem]:
        """获取分类下的FAQ"""
        faq_ids = self.categories.get(category, [])
        return [self.faqs[fid] for fid in faq_ids if fid in self.faqs]

    def rate_faq(self, faq_id: str, helpful: bool) -> bool:
        """评价FAQ"""
        faq = self.faqs.get(faq_id)
        if not faq:
            return False

        if helpful:
            faq.helpful_count += 1
        else:
            faq.not_helpful_count += 1

        return True

    def get_popular_faqs(self, limit: int = 10) -> List[FAQItem]:
        """获取热门FAQ"""
        sorted_faqs = sorted(
            self.faqs.values(),
            key=lambda x: x.view_count,
            reverse=True
        )
        return sorted_faqs[:limit]


# ==================== 用户反馈收集 ====================

class FeedbackType(Enum):
    """反馈类型"""
    BUG = 'bug'  # 问题报告
    FEATURE = 'feature'  # 功能建议
    EXPERIENCE = 'experience'  # 体验反馈
    PRAISE = 'praise'  # 好评
    OTHER = "other"  # 其他


@dataclass
class UserFeedback:
    """用户反馈"""
    feedback_id: str
    user_id: int
    feedback_type: FeedbackType
    title: str
    content: str
    rating: Optional[int] = None  # 1-5星
    app_version: Optional[str] = None
    device_info: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    status: str = "pending"  # pending/reviewed/resolved
    admin_reply: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    replied_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            'user_id': self.user_id,
            "feedback_type": self.feedback_type.value,
            'title': self.title,
            'content': self.content,
            'rating': self.rating,
            "screenshots": self.screenshots,
            'status': self.status,
            "admin_reply": self.admin_reply,
            'created_at': self.created_at.isoformat(),
            'replied_at': self.replied_at.isoformat() if self.replied_at else None
        }


@dataclass
class AppRating:
    """应用评分"""
    rating_id: str
    user_id: int
    rating: int  # 1-5
    review: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'rating_id': self.rating_id,
            'rating': self.rating,
            'review': self.review,
            'created_at': self.created_at.isoformat()
        }


class FeedbackService:
    """反馈服务"""

    def __init__(self):
        self.feedbacks: Dict[str, UserFeedback] = {}
        self.user_feedbacks: Dict[int, List[str]] = defaultdict(list)
        self.ratings: Dict[str, AppRating] = {}
        self.user_ratings: Dict[int, str] = {}

    def submit_feedback(
        self,
        user_id: int,
        feedback_type: FeedbackType,
        title: str,
        content: str,
        rating: Optional[int] = None,
        app_version: Optional[str] = None,
        device_info: Optional[str] = None,
        screenshots: List[str] = None
    ) -> UserFeedback:
        """提交反馈"""
        feedback_id = f"fb_{user_id}_{int(datetime.now().timestamp())}"

        feedback = UserFeedback(
            feedback_id=feedback_id,
            user_id=user_id,
            feedback_type=feedback_type,
            title=title,
            content=content,
            rating=rating,
            app_version=app_version,
            device_info=device_info,
            screenshots=screenshots or []
        )

        self.feedbacks[feedback_id] = feedback
        self.user_feedbacks[user_id].append(feedback_id)

        logger.info(f"收到用户反馈 {feedback_id} - 类型 {feedback_type.value}")
        return feedback

    def get_feedback(self, feedback_id: str) -> Optional[UserFeedback]:
        """获取反馈详情"""
        return self.feedbacks.get(feedback_id)

    def get_user_feedbacks(self, user_id: int) -> List[UserFeedback]:
        """获取用户反馈列表"""
        feedback_ids = self.user_feedbacks.get(user_id, [])
        return [self.feedbacks[fid] for fid in feedback_ids if fid in self.feedbacks]

    def reply_feedback(
        self,
        feedback_id: str,
        admin_reply: str
    ) -> bool:
        """回复反馈"""
        feedback = self.feedbacks.get(feedback_id)
        if not feedback:
            return False

        feedback.admin_reply = admin_reply
        feedback.status = "reviewed"
        feedback.replied_at = datetime.now()

        return True

    def submit_rating(
        self,
        user_id: int,
        rating: int,
        review: Optional[str] = None
    ) -> AppRating:
        """提交应用评分"""
        rating_id = f"rate_{user_id}_{int(datetime.now().timestamp())}"

        app_rating = AppRating(
            rating_id=rating_id,
            user_id=user_id,
            rating=max(1, min(5, rating)),
            review=review
        )

        self.ratings[rating_id] = app_rating

        # 覆盖用户之前的评分
        old_rating_id = self.user_ratings.get(user_id)
        if old_rating_id and old_rating_id in self.ratings:
            del self.ratings[old_rating_id]

        self.user_ratings[user_id] = rating_id

        return app_rating

    def get_rating_stats(self) -> Dict[str, Any]:
        """获取评分统计"""
        if not self.ratings:
            return {
                'average': 0,
                'total': 0,
                "distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }

        ratings = [r.rating for r in self.ratings.values()]
        distribution = {i: ratings.count(i) for i in range(1, 6)}

        return {
            'average': round(sum(ratings) / len(ratings), 1),
            'total': len(ratings),
            "distribution": distribution
        }

    def get_feedback_stats(self) -> Dict[str, Any]:
        """获取反馈统计"""
        type_counts = defaultdict(int)
        status_counts = defaultdict(int)

        for feedback in self.feedbacks.values():
            type_counts[feedback.feedback_type.value] += 1
            status_counts[feedback.status] += 1

        return {
            'total': len(self.feedbacks),
            'by_type': dict(type_counts),
            'by_status': dict(status_counts)
        }


# ==================== 统一支持服务 ====================

class SupportService:
    """统一客户支持服务"""

    def __init__(self):
        self.chatbot = CustomerServiceBot()
        self.ticket = TicketService()
        self.faq = FAQService()
        self.feedback = FeedbackService()


# 全局服务实例
support_service = SupportService()
