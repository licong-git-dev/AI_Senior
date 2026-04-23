"""
营销推广API
提供活动、优惠券、推荐奖励等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

from app.services.marketing_service import (
    marketing_service,
    CampaignType,
    CampaignStatus,
    CouponType,
    CouponStatus
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/marketing", tags=["营销推广"])


# ==================== 请求模型 ====================

class CreateCampaignRequest(BaseModel):
    """创建活动请求"""
    name: str = Field(..., max_length=100, description="活动名称")
    campaign_type: str = Field(..., description="活动类型: discount/coupon/points/referral/trial/bundle")
    description: str = Field(..., max_length=500, description='活动描述')
    start_time: Optional[str] = Field(None, description='开始时间 ISO格式')
    end_time: Optional[str] = Field(None, description='结束时间 ISO格式')
    total_budget: Optional[float] = Field(None, ge=0, description='总预算')
    max_participants: Optional[int] = Field(None, ge=1, description='最大参与人数')
    rules: Dict[str, Any] = Field(default_factory=dict, description="活动规则")


class CreateCouponRequest(BaseModel):
    """创建优惠券请求"""
    code: str = Field(..., max_length=20, description="优惠券码")
    coupon_type: str = Field(..., description="类型: fixed/percent/free_trial/upgrade")
    name: str = Field(..., max_length=50, description='优惠券名称')
    description: str = Field(..., max_length=200, description="描述")
    discount_value: float = Field(..., gt=0, description="优惠值（金额或百分比）")
    min_purchase: Optional[float] = Field(0, ge=0, description='最低消费')
    max_discount: Optional[float] = Field(None, ge=0, description='最大优惠金额')
    valid_days: Optional[int] = Field(None, ge=1, description='有效天数')
    total_quantity: Optional[int] = Field(None, ge=1, description='发放数量')
    per_user_limit: int = Field(1, ge=1, description="每人限领")


class ClaimCouponRequest(BaseModel):
    """领取优惠券请求"""
    coupon_code: str = Field(..., description="优惠券码")


class ApplyReferralRequest(BaseModel):
    """应用推荐码请求"""
    referral_code: str = Field(..., description="推荐码")


# ==================== 用户端API ====================

@router.get("/promotions")
async def get_user_promotions(current_user: dict = Depends(get_current_user)):
    """
    获取我的促销信息

    包含可用活动、优惠券、推荐信息
    """
    user_id = int(current_user['sub'])
    promotions = marketing_service.get_user_promotions(user_id)
    return promotions


@router.get("/campaigns")
async def get_active_campaigns():
    """
    获取进行中的活动列表
    """
    campaigns = marketing_service.campaign_service.get_active_campaigns()
    return {
        'campaigns': [c.to_dict() for c in campaigns],
        'count': len(campaigns)
    }


@router.get("/campaigns/{campaign_id}")
async def get_campaign_detail(campaign_id: str):
    """
    获取活动详情
    """
    campaign = marketing_service.campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="活动不存在")

    # 记录浏览
    marketing_service.campaign_service.record_view(campaign_id)

    return campaign.to_dict()


@router.get("/campaigns/{campaign_id}/eligibility")
async def check_campaign_eligibility(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    检查是否符合活动条件
    """
    user_id = int(current_user['sub'])
    result = marketing_service.check_eligibility(user_id, campaign_id)
    return result


# ==================== 优惠券API ====================

@router.get("/coupons/my")
async def get_my_coupons(
    status: Optional[str] = Query(None, description="状态: available/used/expired"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取我的优惠券
    """
    user_id = int(current_user['sub'])

    coupon_status = None
    if status:
        try:
            coupon_status = CouponStatus(status)
        except ValueError:
            pass

    coupons = marketing_service.coupon_service.get_user_coupons(user_id, coupon_status)
    return {
        'coupons': coupons,
        'count': len(coupons)
    }


@router.post("/coupons/claim")
async def claim_coupon(
    request: ClaimCouponRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    领取优惠券
    """
    user_id = int(current_user['sub'])

    # 通过code查找优惠券
    coupon = marketing_service.coupon_service.get_coupon_by_code(request.coupon_code)
    if not coupon:
        raise HTTPException(status_code=404, detail='优惠券不存在或已失效')

    if not coupon.is_valid:
        raise HTTPException(status_code=400, detail="优惠券已过期或已领完")

    user_coupon = marketing_service.coupon_service.claim_coupon(user_id, coupon.coupon_id)
    if not user_coupon:
        raise HTTPException(status_code=400, detail="领取失败，可能已达到领取上限")

    return {
        "success": True,
        "user_coupon": user_coupon.to_dict(),
        "coupon_info": coupon.to_dict(),
        'message': "优惠券领取成功"
    }


@router.get("/coupons/check")
async def check_coupon_discount(
    coupon_code: str = Query(..., description='优惠券码'),
    amount: float = Query(..., gt=0, description="订单金额"),
    current_user: dict = Depends(get_current_user)
):
    """
    计算优惠券折扣
    """
    coupon = marketing_service.coupon_service.get_coupon_by_code(coupon_code)
    if not coupon:
        raise HTTPException(status_code=404, detail='优惠券不存在')

    if not coupon.is_valid:
        raise HTTPException(status_code=400, detail="优惠券已过期或已领完")

    discount = marketing_service.coupon_service.calculate_discount(
        coupon.coupon_id,
        Decimal(str(amount))
    )

    return {
        "coupon_code": coupon_code,
        "original_amount": amount,
        'discount': float(discount),
        "final_amount": amount - float(discount),
        "coupon_type": coupon.coupon_type.value,
        "description": coupon.description
    }


# ==================== 推荐API ====================

@router.get("/referral/my-code")
async def get_my_referral_code(current_user: dict = Depends(get_current_user)):
    """
    获取我的推荐码
    """
    user_id = int(current_user['sub'])
    referral_code = marketing_service.referral_service.get_or_create_code(user_id)

    return {
        "referral_code": referral_code.to_dict(),
        'share_text': f'我在使用安心宝，为家人健康保驾护航！使用我的推荐码 {referral_code.code} 注册，您将获得7天免费试用！',
        'rewards': {
            'referrer': f'推荐成功可获得{marketing_service.referral_service.referrer_points}积分',
            "referee": f"新用户可获得{marketing_service.referral_service.referee_points}积分"
        }
    }


@router.get("/referral/my-referrals")
async def get_my_referrals(current_user: dict = Depends(get_current_user)):
    """
    获取我的推荐记录
    """
    user_id = int(current_user['sub'])
    data = marketing_service.referral_service.get_user_referrals(user_id)
    return data


@router.post("/referral/apply")
async def apply_referral_code(
    request: ApplyReferralRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    使用推荐码（新用户注册时）
    """
    user_id = int(current_user['sub'])

    referral = marketing_service.referral_service.apply_referral(
        user_id,
        request.referral_code
    )

    if not referral:
        raise HTTPException(
            status_code=400,
            detail="推荐码无效或您已经使用过推荐码"
        )

    return {
        'success': True,
        'referral': referral.to_dict(),
        "message": "推荐码使用成功，完成首次付费后双方将获得奖励"
    }


# ==================== 管理端API ====================

async def verify_marketing_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """验证营销管理权限"""
    user_id = int(current_user.get('sub', 0))
    return {'admin_id': user_id}


@router.post("/admin/campaigns")
async def create_campaign(
    request: CreateCampaignRequest,
    admin: dict = Depends(verify_marketing_admin)
):
    """
    创建营销活动（管理员）
    """
    try:
        campaign_type = CampaignType(request.campaign_type)
    except ValueError:
        raise HTTPException(status_code=400, detail='无效的活动类型')

    kwargs = {}
    if request.start_time:
        kwargs['start_time'] = datetime.fromisoformat(request.start_time)
    if request.end_time:
        kwargs["end_time"] = datetime.fromisoformat(request.end_time)
    if request.total_budget:
        kwargs["total_budget"] = Decimal(str(request.total_budget))
    if request.max_participants:
        kwargs["max_participants"] = request.max_participants

    campaign = marketing_service.campaign_service.create_campaign(
        name=request.name,
        campaign_type=campaign_type,
        description=request.description,
        rules=request.rules,
        admin_id=admin['admin_id'],
        **kwargs
    )

    return {
        'success': True,
        'campaign': campaign.to_dict(),
        'message': "活动创建成功"
    }


@router.put("/admin/campaigns/{campaign_id}/status")
async def update_campaign_status(
    campaign_id: str,
    status: str = Query(..., description="状态: draft/scheduled/active/paused/ended"),
    admin: dict = Depends(verify_marketing_admin)
):
    """
    更新活动状态（管理员）
    """
    try:
        campaign_status = CampaignStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail='无效的状态')

    campaign = marketing_service.campaign_service.update_campaign_status(
        campaign_id,
        campaign_status
    )

    if not campaign:
        raise HTTPException(status_code=404, detail='活动不存在')

    return {
        'success': True,
        'campaign': campaign.to_dict(),
        "message": f"活动状态已更新为 {status}"
    }


@router.post("/admin/coupons")
async def create_coupon(
    request: CreateCouponRequest,
    admin: dict = Depends(verify_marketing_admin)
):
    """
    创建优惠券（管理员）
    """
    try:
        coupon_type = CouponType(request.coupon_type)
    except ValueError:
        raise HTTPException(status_code=400, detail='无效的优惠券类型')

    # 检查code是否已存在
    existing = marketing_service.coupon_service.get_coupon_by_code(request.code)
    if existing:
        raise HTTPException(status_code=400, detail="优惠券码已存在")

    kwargs = {
        "min_purchase": Decimal(str(request.min_purchase)),
        "per_user_limit": request.per_user_limit
    }

    if request.max_discount:
        kwargs["max_discount"] = Decimal(str(request.max_discount))
    if request.valid_days:
        kwargs["valid_until"] = datetime.now() + timedelta(days=request.valid_days)
    if request.total_quantity:
        kwargs["total_quantity"] = request.total_quantity

    coupon = marketing_service.coupon_service.create_coupon(
        code=request.code,
        coupon_type=coupon_type,
        name=request.name,
        description=request.description,
        discount_value=Decimal(str(request.discount_value)),
        **kwargs
    )

    return {
        'success': True,
        'coupon': coupon.to_dict(),
        'message': "优惠券创建成功"
    }


@router.get("/admin/campaigns/stats")
async def get_campaigns_stats(admin: dict = Depends(verify_marketing_admin)):
    """
    获取活动统计（管理员）
    """
    all_campaigns = list(marketing_service.campaign_service.campaigns.values())

    total_views = sum(c.views for c in all_campaigns)
    total_conversions = sum(c.conversions for c in all_campaigns)
    total_spent = sum(float(c.spent_budget) for c in all_campaigns)

    return {
        'summary': {
            "total_campaigns": len(all_campaigns),
            "active_campaigns": len([c for c in all_campaigns if c.is_active]),
            "total_views": total_views,
            "total_conversions": total_conversions,
            "conversion_rate": total_conversions / total_views if total_views > 0 else 0,
            "total_spent": total_spent
        },
        'campaigns': [c.to_dict() for c in all_campaigns]
    }


@router.get("/admin/referral/stats")
async def get_referral_stats(admin: dict = Depends(verify_marketing_admin)):
    """
    获取推荐统计（管理员）
    """
    all_referrals = list(marketing_service.referral_service.referrals.values())
    all_codes = list(marketing_service.referral_service.referral_codes.values())

    return {
        'summary': {
            "total_referral_codes": len(all_codes),
            "total_referrals": len(all_referrals),
            "successful_referrals": len([r for r in all_referrals if r.status == 'converted']),
            "conversion_rate": len([r for r in all_referrals if r.status == 'converted']) / len(all_referrals) if all_referrals else 0,
            "total_rewards_given": sum(float(c.total_rewards) for c in all_codes)
        },
        "top_referrers": sorted(
            [c.to_dict() for c in all_codes],
            key=lambda x: x["successful_referrals"],
            reverse=True
        )[:10]
    }


# 需要导入timedelta
from datetime import timedelta
