"""
支付API
提供支付订单创建、查询、回调等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from decimal import Decimal

from app.services.payment_service import (
    payment_service,
    PaymentChannel,
    PaymentStatus
)
from app.services.subscription_service import subscription_service
from app.core.security import get_current_user

router = APIRouter(prefix="/api/payment", tags=["支付"])


# ==================== 请求模型 ====================

class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    amount: float = Field(..., gt=0, description='支付金额')
    channel: str = Field(default="wechat", description="支付渠道: wechat/alipay")
    business_type: str = Field(..., description="业务类型: subscription/recharge")
    business_id: str = Field(..., description="业务ID")
    description: Optional[str] = Field(default="", description="订单描述")


class GetPayParamsRequest(BaseModel):
    """获取支付参数请求"""
    order_id: str = Field(..., description="订单号")
    openid: Optional[str] = Field(default=None, description="微信openid（JSAPI支付需要）")


class RefundRequest(BaseModel):
    """退款请求"""
    order_id: str = Field(..., description="原订单号")
    amount: Optional[float] = Field(default=None, gt=0, description="退款金额，默认全额退款")
    reason: Optional[str] = Field(default="", max_length=200, description='退款原因')


# ==================== 订单API ====================

@router.post("/orders")
async def create_order(
    request: CreateOrderRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    创建支付订单

    业务类型:
    - subscription: 订阅会员
    - recharge: 余额充值
    """
    user_id = int(current_user['sub'])

    # 验证支付渠道
    try:
        channel = PaymentChannel(request.channel)
    except ValueError:
        valid_channels = [c.value for c in PaymentChannel]
        raise HTTPException(
            status_code=400,
            detail=f"无效的支付渠道，可选: {valid_channels}"
        )

    # 验证业务类型
    if request.business_type not in ['subscription', 'recharge', 'purchase']:
        raise HTTPException(status_code=400, detail='无效的业务类型')

    # 创建订单
    order = payment_service.create_order(
        user_id=user_id,
        amount=Decimal(str(request.amount)),
        channel=channel,
        business_type=request.business_type,
        business_id=request.business_id,
        description=request.description
    )

    return {
        'success': True,
        'order': order.to_dict(),
        "message": "订单创建成功，请在30分钟内完成支付"
    }


@router.post("/orders/pay-params")
async def get_pay_params(
    request: GetPayParamsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    获取支付参数

    微信JSAPI支付需要提供openid
    """
    user_id = int(current_user['sub'])

    order = payment_service.query_order(request.order_id)
    if not order:
        raise HTTPException(status_code=404, detail='订单不存在')

    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail='无权访问此订单')

    if order.is_expired:
        raise HTTPException(status_code=400, detail='订单已过期')

    if order.status == PaymentStatus.SUCCESS:
        raise HTTPException(status_code=400, detail='订单已支付')

    params = payment_service.get_pay_params(request.order_id, request.openid)

    if not params:
        raise HTTPException(status_code=500, detail='获取支付参数失败')

    return {
        "success": True,
        **params
    }


@router.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    查询订单详情
    """
    user_id = int(current_user['sub'])

    order = payment_service.query_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail='订单不存在')

    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail='无权访问此订单')

    return order.to_dict()


@router.get('/orders')
async def list_orders(
    status: Optional[str] = Query(None, description="订单状态筛选"),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    获取我的订单列表
    """
    user_id = int(current_user['sub'])

    payment_status = None
    if status:
        try:
            payment_status = PaymentStatus(status)
        except ValueError:
            pass

    orders = payment_service.get_user_orders(user_id, payment_status, limit)

    return {
        'orders': [o.to_dict() for o in orders],
        'count': len(orders)
    }


@router.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    取消订单
    """
    user_id = int(current_user['sub'])

    order = payment_service.query_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail='订单不存在')

    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail='无权操作此订单')

    success = payment_service.cancel_order(order_id)
    if not success:
        raise HTTPException(status_code=400, detail='无法取消订单')

    return {
        'success': True,
        'message': "订单已取消"
    }


@router.get("/statistics")
async def get_statistics(current_user: dict = Depends(get_current_user)):
    """
    获取支付统计
    """
    user_id = int(current_user['sub'])
    stats = payment_service.get_order_statistics(user_id)
    return stats


# ==================== 退款API ====================

@router.post("/refund")
async def request_refund(
    request: RefundRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    申请退款
    """
    user_id = int(current_user['sub'])

    order = payment_service.query_order(request.order_id)
    if not order:
        raise HTTPException(status_code=404, detail='订单不存在')

    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail='无权操作此订单')

    if order.status != PaymentStatus.SUCCESS:
        raise HTTPException(status_code=400, detail='订单状态不支持退款')

    refund_amount = Decimal(str(request.amount)) if request.amount else None

    refund = payment_service.create_refund(
        order_id=request.order_id,
        amount=refund_amount,
        reason=request.reason
    )

    if not refund:
        raise HTTPException(status_code=400, detail='退款申请失败')

    return {
        'success': True,
        'refund': refund.to_dict(),
        'message': "退款申请已提交"
    }


# ==================== 支付回调API ====================

@router.post("/notify/wechat")
async def wechat_notify(request: Request, background_tasks: BackgroundTasks):
    """
    微信支付回调

    此接口由微信服务器调用，无需认证
    """
    try:
        body = await request.body()
        # 实际实现需要解析XML
        data = {'result_code': "SUCCESS"}  # 模拟解析结果

        order = payment_service.handle_notify(PaymentChannel.WECHAT, data)

        if order and order.status == PaymentStatus.SUCCESS:
            # 后台处理业务逻辑
            background_tasks.add_task(
                _process_payment_success,
                order.order_id,
                order.business_type,
                order.business_id
            )

        # 返回微信要求的格式
        return PlainTextResponse(
            content="<xml><return_code><![CDATA[SUCCESS]]></return_code></xml>",
            media_type="application/xml"
        )

    except Exception as e:
        return PlainTextResponse(
            content="<xml><return_code><![CDATA[FAIL]]></return_code></xml>",
            media_type="application/xml"
        )


@router.post("/notify/alipay")
async def alipay_notify(request: Request, background_tasks: BackgroundTasks):
    """
    支付宝回调

    此接口由支付宝服务器调用，无需认证
    """
    try:
        form_data = await request.form()
        data = dict(form_data)

        order = payment_service.handle_notify(PaymentChannel.ALIPAY, data)

        if order and order.status == PaymentStatus.SUCCESS:
            background_tasks.add_task(
                _process_payment_success,
                order.order_id,
                order.business_type,
                order.business_id
            )

        return PlainTextResponse(content="success")

    except Exception as e:
        return PlainTextResponse(content='fail')


# ==================== 测试API ====================

@router.post("/test/simulate-success/{order_id}")
async def simulate_payment_success(
    order_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    模拟支付成功（仅用于测试环境）
    """
    user_id = int(current_user['sub'])

    order = payment_service.query_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail='订单不存在')

    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail='无权操作此订单')

    success = payment_service.simulate_payment_success(order_id)
    if not success:
        raise HTTPException(status_code=400, detail='模拟支付失败')

    # 处理业务逻辑
    background_tasks.add_task(
        _process_payment_success,
        order.order_id,
        order.business_type,
        order.business_id
    )

    return {
        'success': True,
        'order': payment_service.query_order(order_id).to_dict(),
        'message': '模拟支付成功'
    }


# ==================== 支付渠道信息 ====================

@router.get("/channels")
async def get_available_channels():
    """
    获取可用支付渠道
    """
    return {
        'channels': [
            {
                'id': 'wechat',
                'name': '微信支付',
                'icon': 'wechat',
                'description': '使用微信扫码或直接支付',
                'enabled': True
            },
            {
                'id': 'alipay',
                'name': '支付宝',
                'icon': 'alipay',
                'description': '使用支付宝扫码或直接支付',
                "enabled": True
            }
        ]
    }


# ==================== 辅助函数 ====================

async def _process_payment_success(order_id: str, business_type: str, business_id: str):
    """处理支付成功后的业务逻辑"""
    try:
        if business_type == "subscription":
            # 激活订阅
            order = payment_service.query_order(order_id)
            if order:
                payment = subscription_service.complete_payment(
                    payment_id=business_id,
                    transaction_id=order.transaction_id
                )
                if payment:
                    # 赠送积分等操作
                    pass

        elif business_type == "recharge":
            # 充值到余额
            pass

    except Exception as e:
        import logging
        logging.error(f"处理支付成功业务失败: {e}")
