"""
支付服务
集成微信支付、支付宝等支付渠道
"""
import logging
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
import base64

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PaymentChannel(Enum):
    """支付渠道"""
    WECHAT = 'wechat'  # 微信支付
    ALIPAY = 'alipay'  # 支付宝
    UNIONPAY = 'unionpay'  # 银联
    APPLE_PAY = "apple_pay"  # Apple Pay


class PaymentStatus(Enum):
    """支付状态"""
    PENDING = 'pending'  # 待支付
    PROCESSING = 'processing'  # 处理中
    SUCCESS = 'success'  # 成功
    FAILED = 'failed'  # 失败
    CANCELLED = 'cancelled'  # 已取消
    REFUNDED = "refunded"  # 已退款
    PARTIAL_REFUND = "partial_refund"  # 部分退款


class RefundStatus(Enum):
    """退款状态"""
    PENDING = "pending"
    PROCESSING = 'processing'
    SUCCESS = 'success'
    FAILED = 'failed'


@dataclass
class PaymentOrder:
    """支付订单"""
    order_id: str
    user_id: int
    amount: Decimal
    currency: str = "CNY"
    channel: PaymentChannel = PaymentChannel.WECHAT
    status: PaymentStatus = PaymentStatus.PENDING
    description: str = ""

    # 业务关联
    business_type: str = ""  # subscription/recharge/purchase
    business_id: str = ""  # 关联的业务ID

    # 支付信息
    prepay_id: Optional[str] = None
    transaction_id: Optional[str] = None
    pay_time: Optional[datetime] = None

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    # 额外数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'user_id': self.user_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'channel': self.channel.value,
            "status": self.status.value,
            "description": self.description,
            "business_type": self.business_type,
            "business_id": self.business_id,
            "transaction_id": self.transaction_id,
            'pay_time': self.pay_time.isoformat() if self.pay_time else None,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired
        }

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at


@dataclass
class RefundOrder:
    """退款订单"""
    refund_id: str
    order_id: str
    user_id: int
    amount: Decimal
    reason: str = ""
    status: RefundStatus = RefundStatus.PENDING

    refund_transaction_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'refund_id': self.refund_id,
            'order_id': self.order_id,
            'amount': float(self.amount),
            'reason': self.reason,
            'status': self.status.value,
            "refund_transaction_id": self.refund_transaction_id,
            'created_at': self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


# ==================== 微信支付服务 ====================

class WeChatPayService:
    """微信支付服务"""

    def __init__(self):
        self.app_id = getattr(settings, 'wechat_app_id', 'wx_test_app_id')
        self.mch_id = getattr(settings, 'wechat_mch_id', 'test_mch_id')
        self.api_key = getattr(settings, 'wechat_api_key', 'test_api_key')
        self.notify_url = getattr(settings, 'payment_notify_url', 'https://api.anxinbao.com/payment/notify/wechat')

    def create_unified_order(
        self,
        order: PaymentOrder,
        trade_type: str = 'JSAPI',
        openid: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建统一下单"""
        # 模拟微信支付统一下单
        nonce_str = secrets.token_hex(16)

        params = {
            'appid': self.app_id,
            'mch_id': self.mch_id,
            'nonce_str': nonce_str,
            'body': order.description or "安心宝服务",
            "out_trade_no": order.order_id,
            'total_fee': int(order.amount * 100),  # 分
            'spbill_create_ip': "127.0.0.1",
            'notify_url': self.notify_url,
            'trade_type': trade_type,
        }

        if trade_type == 'JSAPI' and openid:
            params['openid'] = openid

        # 签名
        params["sign"] = self._generate_sign(params)

        # 模拟返回prepay_id
        prepay_id = f"wx_prepay_{order.order_id}_{int(time.time())}"

        return {
            'return_code': 'SUCCESS',
            'result_code': 'SUCCESS',
            'prepay_id': prepay_id,
            'trade_type': trade_type,
            'code_url': f'weixin://wxpay/bizpayurl?pr={prepay_id}' if trade_type == 'NATIVE' else None
        }

    def get_jsapi_params(self, prepay_id: str) -> Dict[str, Any]:
        """获取JSAPI支付参数"""
        timestamp = str(int(time.time()))
        nonce_str = secrets.token_hex(16)

        params = {
            'appId': self.app_id,
            'timeStamp': timestamp,
            'nonceStr': nonce_str,
            'package': f"prepay_id={prepay_id}",
            'signType': 'MD5'
        }

        params['paySign'] = self._generate_sign(params)

        return params

    def verify_notify(self, data: Dict[str, Any]) -> bool:
        """验证回调签名"""
        if 'sign' not in data:
            return False

        sign = data.pop("sign")
        calculated_sign = self._generate_sign(data)

        return sign == calculated_sign

    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """生成签名"""
        sorted_params = sorted(params.items())
        sign_str = '&'.join([f'{k}={v}' for k, v in sorted_params if v])
        sign_str += f"&key={self.api_key}"

        return hashlib.md5(sign_str.encode()).hexdigest().upper()


# ==================== 支付宝服务 ====================

class AlipayService:
    """支付宝服务"""

    def __init__(self):
        self.app_id = getattr(settings, 'alipay_app_id', 'alipay_test_app_id')
        self.private_key = getattr(settings, 'alipay_private_key', 'test_private_key')
        self.public_key = getattr(settings, 'alipay_public_key', 'test_public_key')
        self.notify_url = getattr(settings, 'payment_notify_url', 'https://api.anxinbao.com/payment/notify/alipay')

    def create_trade(
        self,
        order: PaymentOrder,
        product_code: str = "QUICK_MSECURITY_PAY"
    ) -> Dict[str, Any]:
        """创建支付宝订单"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        biz_content = {
            "out_trade_no": order.order_id,
            "total_amount": str(order.amount),
            'subject': order.description or "安心宝服务",
            "product_code": product_code
        }

        params = {
            'app_id': self.app_id,
            'method': "alipay.trade.app.pay",
            'format': 'JSON',
            'charset': 'utf-8',
            'sign_type': 'RSA2',
            'timestamp': timestamp,
            'version': '1.0',
            'notify_url': self.notify_url,
            "biz_content": json.dumps(biz_content)
        }

        # 签名
        params["sign"] = self._generate_sign(params)

        # 模拟返回支付字符串
        order_string = f"alipay_sdk=python&{self._build_query(params)}"

        return {
            'code': '10000',
            'msg': 'Success',
            "order_string": order_string
        }

    def verify_notify(self, params: Dict[str, Any]) -> bool:
        """验证回调签名"""
        if 'sign' not in params:
            return False

        # 实际实现需要使用RSA验签
        return True

    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """生成签名（简化实现）"""
        sorted_params = sorted(params.items())
        sign_str = '&'.join([f'{k}={v}' for k, v in sorted_params if v])

        # 实际实现需要使用RSA2签名
        return base64.b64encode(sign_str.encode()).decode()

    def _build_query(self, params: Dict[str, Any]) -> str:
        """构建查询字符串"""
        return '&'.join([f'{k}={v}' for k, v in params.items()])


# ==================== 统一支付服务 ====================

class PaymentService:
    """统一支付服务"""

    def __init__(self):
        self.orders: Dict[str, PaymentOrder] = {}
        self.refunds: Dict[str, RefundOrder] = {}
        self.user_orders: Dict[int, List[str]] = {}

        self.wechat_pay = WeChatPayService()
        self.alipay = AlipayService()

        # 支付超时时间（分钟）
        self.order_timeout = 30

    def create_order(
        self,
        user_id: int,
        amount: Decimal,
        channel: PaymentChannel,
        business_type: str,
        business_id: str,
        description: str = ""
    ) -> PaymentOrder:
        """创建支付订单"""
        order_id = self._generate_order_id(user_id)

        order = PaymentOrder(
            order_id=order_id,
            user_id=user_id,
            amount=amount,
            channel=channel,
            description=description,
            business_type=business_type,
            business_id=business_id,
            expires_at=datetime.now() + timedelta(minutes=self.order_timeout)
        )

        self.orders[order_id] = order

        if user_id not in self.user_orders:
            self.user_orders[user_id] = []
        self.user_orders[user_id].append(order_id)

        logger.info(f"创建支付订单: {order_id}, 金额: {amount}, 渠道: {channel.value}")
        return order

    def get_pay_params(
        self,
        order_id: str,
        openid: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """获取支付参数"""
        order = self.orders.get(order_id)
        if not order:
            return None

        if order.is_expired:
            order.status = PaymentStatus.CANCELLED
            return None

        if order.channel == PaymentChannel.WECHAT:
            # 微信支付
            result = self.wechat_pay.create_unified_order(order, "JSAPI", openid)
            if result.get("return_code") == 'SUCCESS':
                order.prepay_id = result.get("prepay_id")
                order.status = PaymentStatus.PROCESSING

                return {
                    'channel': 'wechat',
                    'params': self.wechat_pay.get_jsapi_params(order.prepay_id),
                    'order_id': order_id
                }

        elif order.channel == PaymentChannel.ALIPAY:
            # 支付宝
            result = self.alipay.create_trade(order)
            if result.get('code') == '10000':
                order.status = PaymentStatus.PROCESSING

                return {
                    'channel': "alipay",
                    "order_string": result.get("order_string"),
                    'order_id': order_id
                }

        return None

    def handle_notify(
        self,
        channel: PaymentChannel,
        data: Dict[str, Any]
    ) -> Optional[PaymentOrder]:
        """处理支付回调"""
        if channel == PaymentChannel.WECHAT:
            return self._handle_wechat_notify(data)
        elif channel == PaymentChannel.ALIPAY:
            return self._handle_alipay_notify(data)
        return None

    def _handle_wechat_notify(self, data: Dict[str, Any]) -> Optional[PaymentOrder]:
        """处理微信支付回调"""
        if not self.wechat_pay.verify_notify(data.copy()):
            logger.warning("微信支付回调签名验证失败")
            return None

        order_id = data.get("out_trade_no")
        order = self.orders.get(order_id)

        if not order:
            return None

        if data.get("result_code") == 'SUCCESS':
            order.status = PaymentStatus.SUCCESS
            order.transaction_id = data.get("transaction_id")
            order.pay_time = datetime.now()

            logger.info(f'微信支付成功: {order_id}')
        else:
            order.status = PaymentStatus.FAILED
            logger.warning(f"微信支付失败: {order_id}")

        return order

    def _handle_alipay_notify(self, data: Dict[str, Any]) -> Optional[PaymentOrder]:
        """处理支付宝回调"""
        if not self.alipay.verify_notify(data):
            logger.warning("支付宝回调签名验证失败")
            return None

        order_id = data.get("out_trade_no")
        order = self.orders.get(order_id)

        if not order:
            return None

        trade_status = data.get("trade_status")
        if trade_status in ['TRADE_SUCCESS', 'TRADE_FINISHED']:
            order.status = PaymentStatus.SUCCESS
            order.transaction_id = data.get("trade_no")
            order.pay_time = datetime.now()

            logger.info(f'支付宝支付成功: {order_id}')
        else:
            order.status = PaymentStatus.FAILED
            logger.warning(f"支付宝支付失败: {order_id}")

        return order

    def query_order(self, order_id: str) -> Optional[PaymentOrder]:
        """查询订单"""
        return self.orders.get(order_id)

    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        order = self.orders.get(order_id)
        if not order:
            return False

        if order.status in [PaymentStatus.SUCCESS, PaymentStatus.REFUNDED]:
            return False

        order.status = PaymentStatus.CANCELLED
        logger.info(f'取消支付订单: {order_id}')
        return True

    def create_refund(
        self,
        order_id: str,
        amount: Optional[Decimal] = None,
        reason: str = ""
    ) -> Optional[RefundOrder]:
        """创建退款"""
        order = self.orders.get(order_id)
        if not order:
            return None

        if order.status != PaymentStatus.SUCCESS:
            return None

        refund_amount = amount or order.amount
        if refund_amount > order.amount:
            return None

        refund_id = f"refund_{order_id}_{int(time.time())}"

        refund = RefundOrder(
            refund_id=refund_id,
            order_id=order_id,
            user_id=order.user_id,
            amount=refund_amount,
            reason=reason
        )

        self.refunds[refund_id] = refund

        # 模拟退款处理
        refund.status = RefundStatus.SUCCESS
        refund.refund_transaction_id = f'refund_txn_{refund_id}'
        refund.completed_at = datetime.now()

        # 更新原订单状态
        if refund_amount == order.amount:
            order.status = PaymentStatus.REFUNDED
        else:
            order.status = PaymentStatus.PARTIAL_REFUND

        logger.info(f"退款成功: {refund_id}, 金额: {refund_amount}")
        return refund

    def get_user_orders(
        self,
        user_id: int,
        status: Optional[PaymentStatus] = None,
        limit: int = 20
    ) -> List[PaymentOrder]:
        """获取用户订单列表"""
        order_ids = self.user_orders.get(user_id, [])
        orders = []

        for order_id in reversed(order_ids):
            order = self.orders.get(order_id)
            if order:
                if status is None or order.status == status:
                    orders.append(order)
                    if len(orders) >= limit:
                        break

        return orders

    def get_order_statistics(self, user_id: int) -> Dict[str, Any]:
        """获取用户支付统计"""
        order_ids = self.user_orders.get(user_id, [])

        total_amount = Decimal("0")
        success_count = 0

        for order_id in order_ids:
            order = self.orders.get(order_id)
            if order and order.status == PaymentStatus.SUCCESS:
                total_amount += order.amount
                success_count += 1

        return {
            "total_orders": len(order_ids),
            "success_orders": success_count,
            "total_amount": float(total_amount)
        }

    def _generate_order_id(self, user_id: int) -> str:
        """生成订单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = secrets.token_hex(4).upper()
        return f'AXB{timestamp}{user_id:06d}{random_str}'

    # ==================== 模拟支付（测试用） ====================

    def simulate_payment_success(self, order_id: str) -> bool:
        """模拟支付成功（仅用于测试）"""
        order = self.orders.get(order_id)
        if not order:
            return False

        if order.status not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
            return False

        order.status = PaymentStatus.SUCCESS
        order.transaction_id = f"test_txn_{order_id}"
        order.pay_time = datetime.now()

        logger.info(f"模拟支付成功: {order_id}")
        return True


# 全局服务实例
payment_service = PaymentService()
