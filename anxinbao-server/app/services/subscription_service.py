"""
会员订阅服务
提供会员等级、订阅计划、权益管理等功能
"""
import logging
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
import secrets

logger = logging.getLogger(__name__)


class MembershipTier(Enum):
    """会员等级"""
    FREE = 'free'  # 免费版
    BASIC = 'basic'  # 基础版
    PREMIUM = 'premium'  # 高级版
    FAMILY = 'family'  # 家庭版
    VIP = 'vip'  # VIP版


class SubscriptionStatus(Enum):
    """订阅状态"""
    ACTIVE = 'active'  # 生效中
    EXPIRED = 'expired'  # 已过期
    CANCELLED = 'cancelled'  # 已取消
    PENDING = 'pending'  # 待支付
    TRIAL = 'trial'  # 试用中


class BillingCycle(Enum):
    """计费周期"""
    MONTHLY = 'monthly'  # 月付
    QUARTERLY = 'quarterly'  # 季付
    YEARLY = 'yearly'  # 年付
    LIFETIME = 'lifetime'  # 终身


class PaymentMethod(Enum):
    """支付方式"""
    WECHAT = 'wechat'  # 微信支付
    ALIPAY = 'alipay'  # 支付宝
    BANK_CARD = 'bank_card'  # 银行卡
    POINTS = 'points'  # 积分兑换


@dataclass
class PlanBenefit:
    """权益项"""
    benefit_id: str
    name: str
    description: str
    icon: str
    value: Optional[str] = None  # 如'100次/月'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'benefit_id': self.benefit_id,
            'name': self.name,
            "description": self.description,
            'icon': self.icon,
            'value': self.value
        }


@dataclass
class SubscriptionPlan:
    """订阅计划"""
    plan_id: str
    name: str
    tier: MembershipTier
    billing_cycle: BillingCycle
    price: Decimal
    original_price: Optional[Decimal] = None  # 原价（用于显示折扣）
    description: str = ''
    benefits: List[PlanBenefit] = field(default_factory=list)
    max_family_members: int = 1  # 家庭版可绑定人数
    is_popular: bool = False
    is_available: bool = True
    trial_days: int = 0  # 试用天数

    def to_dict(self) -> Dict[str, Any]:
        return {
            'plan_id': self.plan_id,
            'name': self.name,
            'tier': self.tier.value,
            "billing_cycle": self.billing_cycle.value,
            'price': float(self.price),
            "original_price": float(self.original_price) if self.original_price else None,
            "discount_percent": self._calculate_discount(),
            "description": self.description,
            'benefits': [b.to_dict() for b in self.benefits],
            "max_family_members": self.max_family_members,
            'is_popular': self.is_popular,
            'trial_days': self.trial_days
        }

    def _calculate_discount(self) -> Optional[int]:
        if self.original_price and self.original_price > 0:
            return int((1 - self.price / self.original_price) * 100)
        return None


@dataclass
class Subscription:
    """用户订阅"""
    subscription_id: str
    user_id: int
    plan_id: str
    tier: MembershipTier
    status: SubscriptionStatus
    start_date: datetime
    end_date: Optional[datetime] = None
    auto_renew: bool = True
    payment_method: Optional[PaymentMethod] = None
    created_at: datetime = field(default_factory=datetime.now)
    cancelled_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subscription_id": self.subscription_id,
            'plan_id': self.plan_id,
            'tier': self.tier.value,
            'status': self.status.value,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            "days_remaining": self._days_remaining(),
            'auto_renew': self.auto_renew,
            "payment_method": self.payment_method.value if self.payment_method else None,
            'is_active': self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
        }

    def _days_remaining(self) -> int:
        if not self.end_date:
            return -1  # 无限期
        delta = self.end_date - datetime.now()
        return max(0, delta.days)


@dataclass
class PaymentRecord:
    """支付记录"""
    payment_id: str
    user_id: int
    subscription_id: str
    amount: Decimal
    payment_method: PaymentMethod
    status: str  # pending/success/failed/refunded
    transaction_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'payment_id': self.payment_id,
            "subscription_id": self.subscription_id,
            'amount': float(self.amount),
            "payment_method": self.payment_method.value,
            'status': self.status,
            "transaction_id": self.transaction_id,
            'created_at': self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class UserPoints:
    """用户积分"""
    user_id: int
    balance: int = 0
    total_earned: int = 0
    total_spent: int = 0
    history: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'balance': self.balance,
            "total_earned": self.total_earned,
            "total_spent": self.total_spent
        }


# ==================== 预定义订阅计划 ====================

# 权益定义
BENEFITS = {
    'ai_chat': PlanBenefit('ai_chat', 'AI智能对话', '24小时陪伴聊天', 'chat', '无限次'),
    "ai_chat_limited": PlanBenefit('ai_chat', 'AI智能对话', '基础对话功能', 'chat', '100次/天'),
    "health_monitor": PlanBenefit('health_monitor', '健康监测', '实时健康数据监测', 'heart'),
    'health_report': PlanBenefit('health_report', '健康报告', '周度/月度健康分析报告', 'chart'),
    'emergency_sos': PlanBenefit('emergency_sos', '紧急求助', '一键SOS，快速响应', 'alert'),
    'family_binding': PlanBenefit('family_binding', '家庭绑定', '绑定家人，远程监护', 'home'),
    'family_binding_5': PlanBenefit('family_binding', '家庭绑定', '最多绑定5位家人', 'home', '5人'),
    'entertainment': PlanBenefit('entertainment', '娱乐服务', '音乐、戏曲、新闻等', 'music'),
    'games': PlanBenefit('games', '认知游戏', '记忆、注意力训练', 'game'),
    "priority_support": PlanBenefit('priority_support', '优先客服', '专属客服，快速响应', 'headset'),
    'ad_free': PlanBenefit('ad_free', '无广告', '纯净使用体验', 'block'),
    "cloud_storage": PlanBenefit('cloud_storage', '云存储', '健康数据云端备份', 'cloud', '10GB'),
    'video_call': PlanBenefit('video_call', '视频通话', '高清视频通话', 'video'),
    "medication_reminder": PlanBenefit('medication_reminder', '智能服药提醒', '智能服药提醒', 'pill'),
    'location_track': PlanBenefit('location_track', '位置追踪', '实时位置查看', 'map'),
}

# 订阅计划
SUBSCRIPTION_PLANS = {
    'free': SubscriptionPlan(
        plan_id='free',
        name='免费版',
        tier=MembershipTier.FREE,
        billing_cycle=BillingCycle.MONTHLY,
        price=Decimal('0'),
        description='基础功能，永久免费',
        benefits=[
            BENEFITS["ai_chat_limited"],
            BENEFITS["emergency_sos"],
            BENEFITS['games']
        ],
        max_family_members=1
    ),

    "basic_monthly": SubscriptionPlan(
        plan_id="basic_monthly",
        name='基础版 - 月付',
        tier=MembershipTier.BASIC,
        billing_cycle=BillingCycle.MONTHLY,
        price=Decimal('29.9'),
        original_price=Decimal('39.9'),
        description='解锁更多功能',
        benefits=[
            BENEFITS['ai_chat'],
            BENEFITS["health_monitor"],
            BENEFITS["emergency_sos"],
            BENEFITS["entertainment"],
            BENEFITS['games'],
            BENEFITS["medication_reminder"]
        ],
        max_family_members=2,
        trial_days=7
    ),

    "basic_yearly": SubscriptionPlan(
        plan_id="basic_yearly",
        name='基础版 - 年付',
        tier=MembershipTier.BASIC,
        billing_cycle=BillingCycle.YEARLY,
        price=Decimal('299'),
        original_price=Decimal('478.8'),
        description='年付更优惠，省179元',
        benefits=[
            BENEFITS['ai_chat'],
            BENEFITS["health_monitor"],
            BENEFITS["emergency_sos"],
            BENEFITS["entertainment"],
            BENEFITS['games'],
            BENEFITS["medication_reminder"]
        ],
        max_family_members=2,
        is_popular=True
    ),

    "premium_monthly": SubscriptionPlan(
        plan_id="premium_monthly",
        name='高级版 - 月付',
        tier=MembershipTier.PREMIUM,
        billing_cycle=BillingCycle.MONTHLY,
        price=Decimal('59.9'),
        original_price=Decimal('79.9'),
        description='全功能体验',
        benefits=[
            BENEFITS['ai_chat'],
            BENEFITS["health_monitor"],
            BENEFITS["health_report"],
            BENEFITS["emergency_sos"],
            BENEFITS["entertainment"],
            BENEFITS['games'],
            BENEFITS["medication_reminder"],
            BENEFITS['video_call'],
            BENEFITS["location_track"],
            BENEFITS['ad_free'],
            BENEFITS["cloud_storage"]
        ],
        max_family_members=3
    ),

    "premium_yearly": SubscriptionPlan(
        plan_id="premium_yearly",
        name='高级版 - 年付',
        tier=MembershipTier.PREMIUM,
        billing_cycle=BillingCycle.YEARLY,
        price=Decimal('599'),
        original_price=Decimal('958.8'),
        description='年付更优惠，省359元',
        benefits=[
            BENEFITS['ai_chat'],
            BENEFITS["health_monitor"],
            BENEFITS["health_report"],
            BENEFITS["emergency_sos"],
            BENEFITS["entertainment"],
            BENEFITS['games'],
            BENEFITS["medication_reminder"],
            BENEFITS['video_call'],
            BENEFITS["location_track"],
            BENEFITS['ad_free'],
            BENEFITS["cloud_storage"]
        ],
        max_family_members=3,
        is_popular=True
    ),

    "family_yearly": SubscriptionPlan(
        plan_id="family_yearly",
        name='家庭版 - 年付',
        tier=MembershipTier.FAMILY,
        billing_cycle=BillingCycle.YEARLY,
        price=Decimal('899'),
        original_price=Decimal('1198'),
        description='全家共享，多人守护',
        benefits=[
            BENEFITS['ai_chat'],
            BENEFITS["health_monitor"],
            BENEFITS["health_report"],
            BENEFITS["emergency_sos"],
            BENEFITS["family_binding_5"],
            BENEFITS["entertainment"],
            BENEFITS['games'],
            BENEFITS["medication_reminder"],
            BENEFITS['video_call'],
            BENEFITS["location_track"],
            BENEFITS['ad_free'],
            BENEFITS["cloud_storage"],
            BENEFITS["priority_support"]
        ],
        max_family_members=5
    )
}


# ==================== 会员服务 ====================

class SubscriptionService:
    """订阅服务"""

    def __init__(self):
        self.plans = SUBSCRIPTION_PLANS
        self.subscriptions: Dict[str, Subscription] = {}
        self.user_subscriptions: Dict[int, str] = {}  # user_id -> subscription_id
        self.payments: Dict[str, PaymentRecord] = {}
        self.user_points: Dict[int, UserPoints] = {}

    def get_plans(self, include_unavailable: bool = False) -> List[SubscriptionPlan]:
        """获取所有订阅计划"""
        plans = list(self.plans.values())
        if not include_unavailable:
            plans = [p for p in plans if p.is_available]
        return plans

    def get_plan(self, plan_id: str) -> Optional[SubscriptionPlan]:
        """获取指定计划"""
        return self.plans.get(plan_id)

    def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """获取用户当前订阅"""
        sub_id = self.user_subscriptions.get(user_id)
        if sub_id:
            sub = self.subscriptions.get(sub_id)
            if sub:
                # 检查是否过期
                if sub.end_date and datetime.now() > sub.end_date:
                    sub.status = SubscriptionStatus.EXPIRED
                return sub
        return None

    def get_user_tier(self, user_id: int) -> MembershipTier:
        """获取用户会员等级"""
        sub = self.get_user_subscription(user_id)
        if sub and sub.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]:
            return sub.tier
        return MembershipTier.FREE

    def create_subscription(
        self,
        user_id: int,
        plan_id: str,
        payment_method: PaymentMethod,
        is_trial: bool = False
    ) -> Optional[Subscription]:
        """创建订阅"""
        plan = self.get_plan(plan_id)
        if not plan:
            return None

        subscription_id = f"sub_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 计算结束日期
        start_date = datetime.now()
        if plan.billing_cycle == BillingCycle.MONTHLY:
            end_date = start_date + timedelta(days=30)
        elif plan.billing_cycle == BillingCycle.QUARTERLY:
            end_date = start_date + timedelta(days=90)
        elif plan.billing_cycle == BillingCycle.YEARLY:
            end_date = start_date + timedelta(days=365)
        else:
            end_date = None  # 终身

        # 试用期可立即生效；非试用订阅必须等待支付成功后再激活
        status = SubscriptionStatus.TRIAL if is_trial else SubscriptionStatus.PENDING
        if is_trial and plan.trial_days > 0:
            end_date = start_date + timedelta(days=plan.trial_days)

        subscription = Subscription(
            subscription_id=subscription_id,
            user_id=user_id,
            plan_id=plan_id,
            tier=plan.tier,
            status=status,
            start_date=start_date,
            end_date=end_date,
            payment_method=payment_method
        )

        self.subscriptions[subscription_id] = subscription
        self.user_subscriptions[user_id] = subscription_id

        logger.info(f'用户 {user_id} 订阅了 {plan_id}')
        return subscription

    def cancel_subscription(
        self,
        user_id: int,
        reason: str = ""
    ) -> Optional[Subscription]:
        """取消订阅"""
        sub = self.get_user_subscription(user_id)
        if not sub:
            return None

        sub.status = SubscriptionStatus.CANCELLED
        sub.cancelled_at = datetime.now()
        sub.cancel_reason = reason
        sub.auto_renew = False

        logger.info(f'用户 {user_id} 取消了订阅')
        return sub

    def renew_subscription(self, user_id: int) -> Optional[Subscription]:
        """续订"""
        sub = self.get_user_subscription(user_id)
        if not sub:
            return None

        plan = self.get_plan(sub.plan_id)
        if not plan:
            return None

        # 延长结束日期
        if sub.end_date:
            base_date = max(sub.end_date, datetime.now())
            if plan.billing_cycle == BillingCycle.MONTHLY:
                sub.end_date = base_date + timedelta(days=30)
            elif plan.billing_cycle == BillingCycle.QUARTERLY:
                sub.end_date = base_date + timedelta(days=90)
            elif plan.billing_cycle == BillingCycle.YEARLY:
                sub.end_date = base_date + timedelta(days=365)

        sub.status = SubscriptionStatus.ACTIVE

        logger.info(f"用户 {user_id} 续订成功")
        return sub

    def upgrade_subscription(
        self,
        user_id: int,
        new_plan_id: str
    ) -> Optional[Subscription]:
        """升级订阅"""
        new_plan = self.get_plan(new_plan_id)
        if not new_plan:
            return None

        current_sub = self.get_user_subscription(user_id)
        if current_sub:
            # 取消旧订阅
            current_sub.status = SubscriptionStatus.CANCELLED
            current_sub.cancelled_at = datetime.now()
            current_sub.cancel_reason = f"升级到 {new_plan_id}"

        # 创建新订阅
        return self.create_subscription(user_id, new_plan_id, PaymentMethod.WECHAT)

    def check_feature_access(
        self,
        user_id: int,
        feature_id: str
    ) -> bool:
        """检查用户是否有权访问某功能"""
        sub = self.get_user_subscription(user_id)
        if not sub or sub.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]:
            # 免费用户的权限
            free_features = ['ai_chat_limited', 'emergency_sos', 'games']
            return feature_id in free_features

        plan = self.get_plan(sub.plan_id)
        if not plan:
            return False

        benefit_ids = [b.benefit_id for b in plan.benefits]
        return feature_id in benefit_ids

    # ==================== 积分系统 ====================

    def get_user_points(self, user_id: int) -> UserPoints:
        """获取用户积分"""
        if user_id not in self.user_points:
            self.user_points[user_id] = UserPoints(user_id=user_id)
        return self.user_points[user_id]

    def add_points(
        self,
        user_id: int,
        amount: int,
        reason: str
    ) -> UserPoints:
        """添加积分"""
        points = self.get_user_points(user_id)
        points.balance += amount
        points.total_earned += amount
        points.history.append({
            'type': 'earn',
            'amount': amount,
            'reason': reason,
            'time': datetime.now().isoformat()
        })

        # 保留最近100条记录
        if len(points.history) > 100:
            points.history = points.history[-100:]

        return points

    def spend_points(
        self,
        user_id: int,
        amount: int,
        reason: str
    ) -> Optional[UserPoints]:
        """消费积分"""
        points = self.get_user_points(user_id)
        if points.balance < amount:
            return None

        points.balance -= amount
        points.total_spent += amount
        points.history.append({
            'type': 'spend',
            'amount': amount,
            'reason': reason,
            'time': datetime.now().isoformat()
        })

        return points

    # ==================== 支付相关 ====================

    def create_payment(
        self,
        user_id: int,
        subscription_id: str,
        amount: Decimal,
        payment_method: PaymentMethod
    ) -> PaymentRecord:
        """创建支付记录"""
        payment_id = f"pay_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        payment = PaymentRecord(
            payment_id=payment_id,
            user_id=user_id,
            subscription_id=subscription_id,
            amount=amount,
            payment_method=payment_method,
            status='pending'
        )

        self.payments[payment_id] = payment
        return payment

    def complete_payment(
        self,
        payment_id: str,
        transaction_id: str
    ) -> Optional[PaymentRecord]:
        """完成支付"""
        payment = self.payments.get(payment_id)
        if not payment:
            return None

        payment.status = 'success'
        payment.transaction_id = transaction_id
        payment.completed_at = datetime.now()

        # 赠送积分（消费1元=1积分）
        self.add_points(
            payment.user_id,
            int(payment.amount),
            f'订阅支付赠送积分'
        )

        return payment

    def get_user_payments(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[PaymentRecord]:
        """获取用户支付记录"""
        payments = [p for p in self.payments.values() if p.user_id == user_id]
        payments.sort(key=lambda p: p.created_at, reverse=True)
        return payments[:limit]


# 全局服务实例
subscription_service = SubscriptionService()
