"""
营销推广服务
提供活动管理、优惠券、推荐奖励、精准推送等功能
"""
import logging
import secrets
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from decimal import Decimal

logger = logging.getLogger(__name__)


class CampaignType(Enum):
    """活动类型"""
    DISCOUNT = 'discount'  # 折扣活动
    COUPON = 'coupon'  # 优惠券
    POINTS = 'points'  # 积分活动
    REFERRAL = 'referral'  # 推荐有礼
    TRIAL = 'trial'  # 免费试用
    BUNDLE = "bundle"  # 套餐优惠


class CampaignStatus(Enum):
    """活动状态"""
    DRAFT = 'draft'  # 草稿
    SCHEDULED = 'scheduled'  # 已排期
    ACTIVE = 'active'  # 进行中
    PAUSED = 'paused'  # 已暂停
    ENDED = "ended"  # 已结束


class CouponType(Enum):
    """优惠券类型"""
    FIXED = 'fixed'  # 固定金额
    PERCENT = 'percent'  # 百分比折扣
    FREE_TRIAL = 'free_trial'  # 免费试用
    UPGRADE = "upgrade"  # 升级优惠


class CouponStatus(Enum):
    """优惠券状态"""
    AVAILABLE = 'available'  # 可用
    USED = 'used'  # 已使用
    EXPIRED = 'expired'  # 已过期
    REVOKED = "revoked"  # 已撤销


@dataclass
class Campaign:
    """营销活动"""
    campaign_id: str
    name: str
    campaign_type: CampaignType
    description: str
    status: CampaignStatus = CampaignStatus.DRAFT

    # 时间范围
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # 预算和限制
    total_budget: Optional[Decimal] = None
    spent_budget: Decimal = Decimal("0")
    max_participants: Optional[int] = None
    current_participants: int = 0

    # 目标人群
    target_segments: List[str] = field(default_factory=list)
    target_tiers: List[str] = field(default_factory=list)

    # 活动规则
    rules: Dict[str, Any] = field(default_factory=dict)

    # 统计
    views: int = 0
    conversions: int = 0

    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            'name': self.name,
            'type': self.campaign_type.value,
            "description": self.description,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            "total_budget": float(self.total_budget) if self.total_budget else None,
            "spent_budget": float(self.spent_budget),
            "max_participants": self.max_participants,
            "current_participants": self.current_participants,
            "target_segments": self.target_segments,
            "target_tiers": self.target_tiers,
            'rules': self.rules,
            'views': self.views,
            "conversions": self.conversions,
            "conversion_rate": self.conversions / self.views if self.views > 0 else 0,
            'created_at': self.created_at.isoformat()
        }

    @property
    def is_active(self) -> bool:
        if self.status != CampaignStatus.ACTIVE:
            return False
        now = datetime.now()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return True


@dataclass
class Coupon:
    """优惠券"""
    coupon_id: str
    code: str
    coupon_type: CouponType
    name: str
    description: str

    # 优惠内容
    discount_value: Decimal = Decimal("0")  # 金额或百分比
    min_purchase: Decimal = Decimal('0')  # 最低消费
    max_discount: Optional[Decimal] = None  # 最大优惠金额

    # 适用范围
    applicable_plans: List[str] = field(default_factory=list)  # 适用计划

    # 有效期
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    # 使用限制
    total_quantity: Optional[int] = None
    used_quantity: int = 0
    per_user_limit: int = 1

    # 关联活动
    campaign_id: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'coupon_id': self.coupon_id,
            'code': self.code,
            'type': self.coupon_type.value,
            "name": self.name,
            "description": self.description,
            "discount_value": float(self.discount_value),
            "min_purchase": float(self.min_purchase),
            "max_discount": float(self.max_discount) if self.max_discount else None,
            "applicable_plans": self.applicable_plans,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "total_quantity": self.total_quantity,
            "remaining_quantity": self.total_quantity - self.used_quantity if self.total_quantity else None,
            "per_user_limit": self.per_user_limit,
            'is_valid': self.is_valid
        }

    @property
    def is_valid(self) -> bool:
        now = datetime.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.total_quantity and self.used_quantity >= self.total_quantity:
            return False
        return True


@dataclass
class UserCoupon:
    """用户优惠券"""
    user_coupon_id: str
    user_id: int
    coupon_id: str
    status: CouponStatus = CouponStatus.AVAILABLE
    received_at: datetime = field(default_factory=datetime.now)
    used_at: Optional[datetime] = None
    order_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_coupon_id": self.user_coupon_id,
            'coupon_id': self.coupon_id,
            'status': self.status.value,
            "received_at": self.received_at.isoformat(),
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'order_id': self.order_id
        }


@dataclass
class ReferralCode:
    """推荐码"""
    code: str
    user_id: int
    total_referrals: int = 0
    successful_referrals: int = 0
    total_rewards: Decimal = Decimal("0")
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            "total_referrals": self.total_referrals,
            "successful_referrals": self.successful_referrals,
            "total_rewards": float(self.total_rewards),
            'created_at': self.created_at.isoformat()
        }


@dataclass
class Referral:
    """推荐记录"""
    referral_id: str
    referrer_id: int
    referee_id: int
    referral_code: str
    status: str = 'pending'  # pending/converted/expired
    referrer_reward: Decimal = Decimal("0")
    referee_reward: Decimal = Decimal('0')
    created_at: datetime = field(default_factory=datetime.now)
    converted_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "referral_id": self.referral_id,
            "referrer_id": self.referrer_id,
            'referee_id': self.referee_id,
            'status': self.status,
            "referrer_reward": float(self.referrer_reward),
            "referee_reward": float(self.referee_reward),
            'created_at': self.created_at.isoformat(),
            "converted_at": self.converted_at.isoformat() if self.converted_at else None
        }


# ==================== 活动管理服务 ====================

class CampaignService:
    """活动管理服务"""

    def __init__(self):
        self.campaigns: Dict[str, Campaign] = {}
        self._init_default_campaigns()

    def _init_default_campaigns(self):
        """初始化默认活动"""
        # 新用户首月优惠
        campaign1 = Campaign(
            campaign_id="camp_new_user",
            name="新用户首月5折",
            campaign_type=CampaignType.DISCOUNT,
            description="新注册用户首月订阅享5折优惠",
            status=CampaignStatus.ACTIVE,
            start_time=datetime.now() - timedelta(days=30),
            end_time=datetime.now() + timedelta(days=60),
            target_segments=['new_user'],
            rules={'discount_percent': 50, "applicable_months": 1}
        )
        self.campaigns[campaign1.campaign_id] = campaign1

        # 推荐有礼
        campaign2 = Campaign(
            campaign_id="camp_referral",
            name="推荐有礼",
            campaign_type=CampaignType.REFERRAL,
            description="推荐好友注册，双方各得30天会员",
            status=CampaignStatus.ACTIVE,
            start_time=datetime.now() - timedelta(days=60),
            rules={'referrer_reward_days': 30, "referee_reward_days": 30}
        )
        self.campaigns[campaign2.campaign_id] = campaign2

    def create_campaign(
        self,
        name: str,
        campaign_type: CampaignType,
        description: str,
        rules: Dict,
        admin_id: int,
        **kwargs
    ) -> Campaign:
        """创建活动"""
        campaign_id = f"camp_{secrets.token_hex(8)}"

        campaign = Campaign(
            campaign_id=campaign_id,
            name=name,
            campaign_type=campaign_type,
            description=description,
            rules=rules,
            created_by=admin_id,
            **kwargs
        )

        self.campaigns[campaign_id] = campaign
        logger.info(f"创建活动: {campaign_id} - {name}")
        return campaign

    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """获取活动"""
        return self.campaigns.get(campaign_id)

    def get_active_campaigns(self) -> List[Campaign]:
        """获取进行中的活动"""
        return [c for c in self.campaigns.values() if c.is_active]

    def update_campaign_status(
        self,
        campaign_id: str,
        status: CampaignStatus
    ) -> Optional[Campaign]:
        """更新活动状态"""
        campaign = self.campaigns.get(campaign_id)
        if campaign:
            campaign.status = status
            logger.info(f"活动 {campaign_id} 状态更新为 {status.value}")
        return campaign

    def record_view(self, campaign_id: str):
        """记录活动浏览"""
        campaign = self.campaigns.get(campaign_id)
        if campaign:
            campaign.views += 1

    def record_conversion(self, campaign_id: str, amount: Decimal = Decimal("0")):
        """记录活动转化"""
        campaign = self.campaigns.get(campaign_id)
        if campaign:
            campaign.conversions += 1
            campaign.current_participants += 1
            campaign.spent_budget += amount


# ==================== 优惠券服务 ====================

class CouponService:
    """优惠券服务"""

    def __init__(self):
        self.coupons: Dict[str, Coupon] = {}
        self.user_coupons: Dict[str, UserCoupon] = {}
        self.user_coupon_index: Dict[int, List[str]] = {}  # user_id -> [user_coupon_ids]
        self._init_default_coupons()

    def _init_default_coupons(self):
        """初始化默认优惠券"""
        # 新用户优惠券
        coupon1 = Coupon(
            coupon_id="coupon_new_user",
            code="NEWUSER2024",
            coupon_type=CouponType.PERCENT,
            name='新用户专享',
            description='新用户首单9折优惠',
            discount_value=Decimal('10'),  # 10%折扣
            min_purchase=Decimal("29.9"),
            valid_until=datetime.now() + timedelta(days=365),
            total_quantity=10000,
            per_user_limit=1
        )
        self.coupons[coupon1.coupon_id] = coupon1

        # 免费试用券
        coupon2 = Coupon(
            coupon_id="coupon_free_trial",
            code='FREETRIAL7',
            coupon_type=CouponType.FREE_TRIAL,
            name='7天免费试用',
            description='高级版7天免费体验',
            discount_value=Decimal("7"),  # 7天
            valid_until=datetime.now() + timedelta(days=180),
            total_quantity=5000
        )
        self.coupons[coupon2.coupon_id] = coupon2

    def create_coupon(
        self,
        code: str,
        coupon_type: CouponType,
        name: str,
        description: str,
        discount_value: Decimal,
        **kwargs
    ) -> Coupon:
        """创建优惠券"""
        coupon_id = f"coupon_{secrets.token_hex(6)}"

        coupon = Coupon(
            coupon_id=coupon_id,
            code=code.upper(),
            coupon_type=coupon_type,
            name=name,
            description=description,
            discount_value=discount_value,
            **kwargs
        )

        self.coupons[coupon_id] = coupon
        logger.info(f"创建优惠券: {coupon_id} - {code}")
        return coupon

    def get_coupon_by_code(self, code: str) -> Optional[Coupon]:
        """通过code获取优惠券"""
        code = code.upper()
        for coupon in self.coupons.values():
            if coupon.code == code:
                return coupon
        return None

    def claim_coupon(self, user_id: int, coupon_id: str) -> Optional[UserCoupon]:
        """领取优惠券"""
        coupon = self.coupons.get(coupon_id)
        if not coupon or not coupon.is_valid:
            return None

        # 检查用户领取限制
        user_count = sum(
            1 for uc in self.user_coupons.values()
            if uc.user_id == user_id and uc.coupon_id == coupon_id
        )
        if user_count >= coupon.per_user_limit:
            return None

        user_coupon_id = f"uc_{user_id}_{coupon_id}_{int(datetime.now().timestamp())}"

        user_coupon = UserCoupon(
            user_coupon_id=user_coupon_id,
            user_id=user_id,
            coupon_id=coupon_id
        )

        self.user_coupons[user_coupon_id] = user_coupon

        if user_id not in self.user_coupon_index:
            self.user_coupon_index[user_id] = []
        self.user_coupon_index[user_id].append(user_coupon_id)

        coupon.used_quantity += 1
        logger.info(f"用户 {user_id} 领取优惠券 {coupon_id}")
        return user_coupon

    def get_user_coupons(
        self,
        user_id: int,
        status: Optional[CouponStatus] = None
    ) -> List[Dict]:
        """获取用户优惠券"""
        user_coupon_ids = self.user_coupon_index.get(user_id, [])
        result = []

        for uc_id in user_coupon_ids:
            uc = self.user_coupons.get(uc_id)
            if not uc:
                continue
            if status and uc.status != status:
                continue

            coupon = self.coupons.get(uc.coupon_id)
            if coupon:
                result.append({
                    **uc.to_dict(),
                    "coupon_info": coupon.to_dict()
                })

        return result

    def use_coupon(
        self,
        user_coupon_id: str,
        order_id: str
    ) -> Optional[UserCoupon]:
        """使用优惠券"""
        user_coupon = self.user_coupons.get(user_coupon_id)
        if not user_coupon or user_coupon.status != CouponStatus.AVAILABLE:
            return None

        user_coupon.status = CouponStatus.USED
        user_coupon.used_at = datetime.now()
        user_coupon.order_id = order_id

        logger.info(f"优惠券 {user_coupon_id} 已使用于订单 {order_id}")
        return user_coupon

    def calculate_discount(
        self,
        coupon_id: str,
        original_price: Decimal
    ) -> Decimal:
        """计算优惠金额"""
        coupon = self.coupons.get(coupon_id)
        if not coupon or not coupon.is_valid:
            return Decimal("0")

        if original_price < coupon.min_purchase:
            return Decimal('0')

        if coupon.coupon_type == CouponType.FIXED:
            discount = coupon.discount_value
        elif coupon.coupon_type == CouponType.PERCENT:
            discount = original_price * coupon.discount_value / 100
            if coupon.max_discount:
                discount = min(discount, coupon.max_discount)
        else:
            discount = Decimal('0')

        return min(discount, original_price)


# ==================== 推荐奖励服务 ====================

class ReferralService:
    """推荐奖励服务"""

    def __init__(self):
        self.referral_codes: Dict[str, ReferralCode] = {}
        self.referrals: Dict[str, Referral] = {}
        self.user_referral_code: Dict[int, str] = {}  # user_id -> code

        # 奖励配置
        self.referrer_reward_days = 30  # 推荐人奖励天数
        self.referee_reward_days = 7  # 被推荐人奖励天数
        self.referrer_points = 100  # 推荐人积分
        self.referee_points = 50  # 被推荐人积分

    def get_or_create_code(self, user_id: int) -> ReferralCode:
        """获取或创建推荐码"""
        if user_id in self.user_referral_code:
            code = self.user_referral_code[user_id]
            return self.referral_codes[code]

        # 生成新推荐码
        code = self._generate_code()
        while code in self.referral_codes:
            code = self._generate_code()

        referral_code = ReferralCode(code=code, user_id=user_id)
        self.referral_codes[code] = referral_code
        self.user_referral_code[user_id] = code

        logger.info(f"用户 {user_id} 创建推荐码 {code}")
        return referral_code

    def _generate_code(self) -> str:
        """生成推荐码"""
        return f"AXB{secrets.token_hex(3).upper()}"

    def apply_referral(
        self,
        referee_id: int,
        referral_code: str
    ) -> Optional[Referral]:
        """应用推荐码"""
        code_obj = self.referral_codes.get(referral_code)
        if not code_obj:
            return None

        # 不能自己推荐自己
        if code_obj.user_id == referee_id:
            return None

        # 检查是否已被推荐
        for ref in self.referrals.values():
            if ref.referee_id == referee_id:
                return None

        referral_id = f"ref_{code_obj.user_id}_{referee_id}_{int(datetime.now().timestamp())}"

        referral = Referral(
            referral_id=referral_id,
            referrer_id=code_obj.user_id,
            referee_id=referee_id,
            referral_code=referral_code
        )

        self.referrals[referral_id] = referral
        code_obj.total_referrals += 1

        logger.info(f"用户 {referee_id} 使用推荐码 {referral_code}")
        return referral

    def convert_referral(self, referee_id: int) -> Optional[Referral]:
        """转化推荐（被推荐人完成付费）"""
        for referral in self.referrals.values():
            if referral.referee_id == referee_id and referral.status == 'pending':
                referral.status = "converted"
                referral.converted_at = datetime.now()
                referral.referrer_reward = Decimal(str(self.referrer_points))
                referral.referee_reward = Decimal(str(self.referee_points))

                code_obj = self.referral_codes.get(referral.referral_code)
                if code_obj:
                    code_obj.successful_referrals += 1
                    code_obj.total_rewards += referral.referrer_reward

                logger.info(f"推荐转化成功: {referral.referral_id}")
                return referral

        return None

    def get_user_referrals(self, user_id: int) -> Dict[str, Any]:
        """获取用户的推荐数据"""
        code_obj = self.referral_codes.get(self.user_referral_code.get(user_id))

        referrals = [
            r.to_dict() for r in self.referrals.values()
            if r.referrer_id == user_id
        ]

        return {
            "referral_code": code_obj.to_dict() if code_obj else None,
            'referrals': referrals,
            "total_referrals": len(referrals),
            "successful_referrals": sum(1 for r in referrals if r['status'] == "converted"),
            'total_rewards': sum(r['referrer_reward'] for r in referrals)
        }


# ==================== 统一营销服务 ====================

class MarketingService:
    """营销推广服务"""

    def __init__(self):
        self.campaign_service = CampaignService()
        self.coupon_service = CouponService()
        self.referral_service = ReferralService()

    def get_user_promotions(self, user_id: int) -> Dict[str, Any]:
        """获取用户可用的促销信息"""
        active_campaigns = self.campaign_service.get_active_campaigns()
        user_coupons = self.coupon_service.get_user_coupons(
            user_id,
            CouponStatus.AVAILABLE
        )
        referral_info = self.referral_service.get_user_referrals(user_id)

        return {
            'campaigns': [c.to_dict() for c in active_campaigns],
            'coupons': user_coupons,
            'referral': referral_info
        }

    def check_eligibility(
        self,
        user_id: int,
        campaign_id: str
    ) -> Dict[str, Any]:
        """检查用户是否符合活动条件"""
        campaign = self.campaign_service.get_campaign(campaign_id)
        if not campaign:
            return {'eligible': False, 'reason': '活动不存在'}

        if not campaign.is_active:
            return {'eligible': False, 'reason': '活动未开始或已结束'}

        if campaign.max_participants and campaign.current_participants >= campaign.max_participants:
            return {'eligible': False, 'reason': '活动名额已满'}

        # TODO: 检查用户分群条件
        return {'eligible': True, "campaign": campaign.to_dict()}


# 全局服务实例
marketing_service = MarketingService()
