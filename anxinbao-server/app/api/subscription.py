"""
会员订阅API
提供订阅计划、会员管理、积分系统等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from decimal import Decimal

from app.services.subscription_service import (
    subscription_service,
    MembershipTier,
    SubscriptionStatus,
    PaymentMethod,
    BillingCycle
)
from app.core.security import get_current_user, UserInfo

router = APIRouter(prefix="/api/subscription", tags=["会员订阅"])


def _get_numeric_user_id(current_user: UserInfo) -> int:
    """提取订阅主体的数值型用户ID，拒绝非订阅角色访问。"""
    if current_user.role not in {"elder", "family"}:
        raise HTTPException(status_code=403, detail="当前角色不支持订阅操作")

    try:
        return int(current_user.user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=403, detail="当前角色不支持订阅操作") from exc


# ==================== 请求模型 ====================

class SubscribeRequest(BaseModel):
    """订阅请求"""
    plan_id: str = Field(..., description='计划ID')
    payment_method: str = Field(default="wechat", description="支付方式: wechat/alipay/bank_card")
    is_trial: bool = Field(default=False, description="是否试用")


class CancelSubscriptionRequest(BaseModel):
    """取消订阅请求"""
    reason: Optional[str] = Field(default="", max_length=200, description="取消原因")


class SpendPointsRequest(BaseModel):
    """消费积分请求"""
    amount: int = Field(..., gt=0, description='消费积分数量')
    reason: str = Field(..., description='消费原因')


TIER_ORDER = {
    MembershipTier.FREE: 0,
    MembershipTier.BASIC: 1,
    MembershipTier.PREMIUM: 2,
    MembershipTier.FAMILY: 3,
    MembershipTier.VIP: 4,
}


# ==================== 订阅计划API ====================

@router.get("/plans")
async def get_subscription_plans():
    """
    获取所有订阅计划

    返回可用的订阅计划列表
    """
    plans = subscription_service.get_plans()

    # 按等级和价格排序
    plans.sort(key=lambda p: (TIER_ORDER.get(p.tier, 99), float(p.price)))

    return {
        'plans': [p.to_dict() for p in plans],
        "count": len(plans)
    }


@router.get("/plans/{plan_id}")
async def get_plan_detail(plan_id: str):
    """
    获取订阅计划详情
    """
    plan = subscription_service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")

    return plan.to_dict()


@router.get("/plans/compare")
async def compare_plans():
    """
    对比所有计划

    返回功能对比表
    """
    plans = subscription_service.get_plans()

    # 获取所有可能的权益
    all_benefits = set()
    for plan in plans:
        for benefit in plan.benefits:
            all_benefits.add(benefit.benefit_id)

    comparison = []
    for plan in plans:
        plan_benefits = {b.benefit_id: b.value or '包含' for b in plan.benefits}
        comparison.append({
            'plan_id': plan.plan_id,
            'name': plan.name,
            'tier': plan.tier.value,
            "price": float(plan.price),
            "billing_cycle": plan.billing_cycle.value,
            'benefits': plan_benefits
        })

    return {
        'comparison': comparison,
        "benefit_names": {
            'ai_chat': 'AI对话',
            'health_monitor': '健康监测',
            'health_report': '健康报告',
            'emergency_sos': '紧急求助',
            'family_binding': '家庭绑定',
            'entertainment': '娱乐服务',
            'games': '认知游戏',
            'medication_reminder': '服药提醒',
            'video_call': '视频通话',
            'location_track': '位置追踪',
            'ad_free': '无广告',
            'cloud_storage': '云存储',
            'priority_support': '优先客服'
        }
    }


# ==================== 用户订阅API ====================

@router.get("/my")
async def get_my_subscription(current_user: UserInfo = Depends(get_current_user)):
    """
    获取我的订阅信息
    """
    user_id = _get_numeric_user_id(current_user)
    subscription = subscription_service.get_user_subscription(user_id)

    if not subscription:
        return {
            "has_subscription": False,
            'tier': MembershipTier.FREE.value,
            'message': "您当前是免费用户"
        }

    plan = subscription_service.get_plan(subscription.plan_id)

    return {
        "has_subscription": True,
        "subscription": subscription.to_dict(),
        'plan': plan.to_dict() if plan else None
    }


@router.get("/my/tier")
async def get_my_tier(current_user: UserInfo = Depends(get_current_user)):
    """
    获取我的会员等级
    """
    user_id = _get_numeric_user_id(current_user)
    tier = subscription_service.get_user_tier(user_id)

    tier_info = {
        MembershipTier.FREE: {'name': '免费用户', 'icon': 'user', 'color': '#gray'},
        MembershipTier.BASIC: {'name': '基础会员', 'icon': 'star', 'color': '#blue'},
        MembershipTier.PREMIUM: {'name': '高级会员', 'icon': 'crown', 'color': '#gold'},
        MembershipTier.FAMILY: {'name': '家庭会员', 'icon': 'home', 'color': '#purple'},
        MembershipTier.VIP: {'name': 'VIP会员', 'icon': 'diamond', 'color': '#red'}
    }

    info = tier_info.get(tier, tier_info[MembershipTier.FREE])

    return {
        'tier': tier.value,
        **info
    }


@router.post("/subscribe")
async def subscribe(
    request: SubscribeRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    订阅计划

    创建新订阅或升级现有订阅
    """
    user_id = _get_numeric_user_id(current_user)

    # 验证计划
    plan = subscription_service.get_plan(request.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail='计划不存在')

    if plan.tier == MembershipTier.FREE:
        raise HTTPException(status_code=400, detail='免费计划无需订阅')

    # 验证支付方式
    try:
        payment_method = PaymentMethod(request.payment_method)
    except ValueError:
        valid_methods = [m.value for m in PaymentMethod]
        raise HTTPException(
            status_code=400,
            detail=f'无效的支付方式，可选: {valid_methods}'
        )

    # 检查是否已有订阅
    existing = subscription_service.get_user_subscription(user_id)
    if existing and existing.status == SubscriptionStatus.ACTIVE:
        # 升级处理
        if TIER_ORDER.get(existing.tier, -1) >= TIER_ORDER.get(plan.tier, -1):
            raise HTTPException(
                status_code=400,
                detail='当前会员等级已高于或等于目标等级'
            )

    # 创建订阅
    subscription = subscription_service.create_subscription(
        user_id=user_id,
        plan_id=request.plan_id,
        payment_method=payment_method,
        is_trial=request.is_trial
    )

    if not subscription:
        raise HTTPException(status_code=500, detail='订阅创建失败')

    # 创建支付记录
    payment = subscription_service.create_payment(
        user_id=user_id,
        subscription_id=subscription.subscription_id,
        amount=plan.price,
        payment_method=payment_method
    )

    return {
        "success": True,
        "subscription": subscription.to_dict(),
        'payment': payment.to_dict(),
        'message': '试用已开始' if request.is_trial else '订单已创建，请完成支付后开通会员'
    }


@router.post("/cancel")
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    取消订阅

    取消后服务将在当前周期结束后停止
    """
    user_id = _get_numeric_user_id(current_user)

    subscription = subscription_service.cancel_subscription(user_id, request.reason)
    if not subscription:
        raise HTTPException(status_code=404, detail='未找到有效订阅')

    return {
        "success": True,
        "subscription": subscription.to_dict(),
        'message': f"订阅已取消，服务将持续到 {subscription.end_date.strftime('%Y年%m月%d日') if subscription.end_date else '无限期'}"
    }


@router.post("/renew")
async def renew_subscription(current_user: UserInfo = Depends(get_current_user)):
    """
    续订

    延长当前订阅
    """
    user_id = _get_numeric_user_id(current_user)

    subscription = subscription_service.renew_subscription(user_id)
    if not subscription:
        raise HTTPException(status_code=404, detail='未找到可续订的订阅')

    plan = subscription_service.get_plan(subscription.plan_id)

    # 创建支付记录
    if plan:
        payment = subscription_service.create_payment(
            user_id=user_id,
            subscription_id=subscription.subscription_id,
            amount=plan.price,
            payment_method=subscription.payment_method or PaymentMethod.WECHAT
        )
    else:
        payment = None

    return {
        "success": True,
        "subscription": subscription.to_dict(),
        'payment': payment.to_dict() if payment else None,
        'message': "续订成功"
    }


@router.post("/upgrade/{new_plan_id}")
async def upgrade_subscription(
    new_plan_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    升级订阅
    """
    user_id = _get_numeric_user_id(current_user)

    new_plan = subscription_service.get_plan(new_plan_id)
    if not new_plan:
        raise HTTPException(status_code=404, detail='目标计划不存在')

    subscription = subscription_service.upgrade_subscription(user_id, new_plan_id)
    if not subscription:
        raise HTTPException(status_code=400, detail='升级失败')

    return {
        "success": True,
        "subscription": subscription.to_dict(),
        'message': f"已升级到{new_plan.name}"
    }


@router.get("/check-access/{feature_id}")
async def check_feature_access(
    feature_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    检查功能访问权限

    检查当前用户是否有权使用某功能
    """
    user_id = _get_numeric_user_id(current_user)
    has_access = subscription_service.check_feature_access(user_id, feature_id)

    return {
        'feature_id': feature_id,
        'has_access': has_access,
        'tier': subscription_service.get_user_tier(user_id).value
    }


# ==================== 积分API ====================

@router.get("/points")
async def get_my_points(current_user: UserInfo = Depends(get_current_user)):
    """
    获取我的积分
    """
    user_id = _get_numeric_user_id(current_user)
    points = subscription_service.get_user_points(user_id)

    return {
        'points': points.to_dict(),
        "recent_history": points.history[-10:] if points.history else []
    }


@router.get("/points/history")
async def get_points_history(
    limit: int = Query(50, ge=1, le=100),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取积分历史
    """
    user_id = _get_numeric_user_id(current_user)
    points = subscription_service.get_user_points(user_id)

    history = points.history[-limit:] if points.history else []
    history.reverse()  # 最新的在前

    return {
        'history': history,
        "balance": points.balance
    }


@router.post("/points/spend")
async def spend_points(
    request: SpendPointsRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    消费积分
    """
    user_id = _get_numeric_user_id(current_user)

    points = subscription_service.spend_points(
        user_id=user_id,
        amount=request.amount,
        reason=request.reason
    )

    if not points:
        raise HTTPException(status_code=400, detail='积分余额不足')

    return {
        'success': True,
        'points': points.to_dict(),
        "message": f"消费了{request.amount}积分"
    }


# ==================== 支付记录API ====================

@router.get("/payments")
async def get_my_payments(
    limit: int = Query(20, ge=1, le=100),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    获取支付记录
    """
    user_id = _get_numeric_user_id(current_user)
    payments = subscription_service.get_user_payments(user_id, limit)

    return {
        'payments': [p.to_dict() for p in payments],
        'count': len(payments)
    }


# ==================== 试用API ====================

@router.post("/trial/{plan_id}")
async def start_trial(
    plan_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    开始试用

    部分计划提供7天免费试用
    """
    user_id = _get_numeric_user_id(current_user)

    plan = subscription_service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail='计划不存在')

    if plan.trial_days <= 0:
        raise HTTPException(status_code=400, detail="该计划不支持试用")

    # 检查是否已有订阅
    existing = subscription_service.get_user_subscription(user_id)
    if existing and existing.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]:
        raise HTTPException(status_code=400, detail="您已有有效订阅或正在试用中")

    subscription = subscription_service.create_subscription(
        user_id=user_id,
        plan_id=plan_id,
        payment_method=PaymentMethod.WECHAT,
        is_trial=True
    )

    return {
        "success": True,
        "subscription": subscription.to_dict(),
        'message': f"{plan.trial_days}天试用已开始，试用期结束后需付费继续使用"
    }
