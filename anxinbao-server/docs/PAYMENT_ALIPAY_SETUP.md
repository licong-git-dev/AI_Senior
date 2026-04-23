# 支付宝订阅付费接入指南（沙箱 → 生产）

> 当前 [`payment_service.py:222-225`](../app/services/payment_service.py#L222-L225) 用的是 `'alipay_test_app_id'` / `'test_private_key'` 占位符。本文给出**最快接通沙箱、再切生产**的分步指南，以及代码改造清单。

---

## 一、整体路径（约 90 分钟跑通沙箱）

```
1. 注册支付宝开放平台账号           (~10 min)
2. 创建沙箱应用 + 生成 RSA2 密钥对  (~15 min)
3. 把密钥写入 .env                  (~5 min)
4. 升级 payment_service.py 到真签名 (~30 min)
5. 沙箱 App 端调用 + 回调验证       (~20 min)
6. 切生产环境（提交资质审核约 1-3 天）
```

---

## 二、Step 1：开通沙箱

### 2.1 注册并实名

1. 访问 [open.alipay.com](https://open.alipay.com/)
2. 用支付宝账号登录 → 完成开发者实名（个人或企业，安心宝建议**企业**）
3. 个人账号也能开沙箱，但生产环境必须企业资质，建议直接走企业路径

### 2.2 进入沙箱

1. [open.alipay.com/develop/sandbox/app](https://open.alipay.com/develop/sandbox/app)
2. "沙箱应用" tab 中获取以下三个关键值：
   - **APPID**（沙箱专用，类似 `2021000122xxxxxx`）
   - **支付宝公钥**（沙箱）
   - **支付宝网关**：`https://openapi.alipaydev.com/gateway.do`（注意是 `alipaydev.com` 不是生产的 `alipay.com`）

### 2.3 沙箱测试买家账号

1. 同页面 "沙箱账号" tab
2. 提供两组测试账号：买家、卖家。**记下买家账号和登录密码**，后面 App 端测试用

---

## 三、Step 2：生成 RSA2 密钥对

支付宝官方工具可一键生成：

### 方式 A：用支付宝官方密钥工具（推荐）

1. 下载 [Alipay 开发助手](https://opendocs.alipay.com/common/02kipl)
2. 打开 → "生成密钥" → 选 RSA2 (PKCS1) 2048 位
3. 工具输出：
   - **应用私钥**（`xxx.txt` 一长串）→ 写入 `.env` 的 `ALIPAY_PRIVATE_KEY`
   - **应用公钥**（另一段）→ 上传到沙箱应用页"接口加签方式 → 公钥"

### 方式 B：用 openssl 命令行

```bash
# 生成应用私钥（PKCS1 格式，2048 位）
openssl genrsa -out app_private_key.pem 2048

# 转 PKCS8 格式（支付宝部分 SDK 需要 PKCS8）
openssl pkcs8 -topk8 -inform PEM -in app_private_key.pem -outform PEM -nocrypt -out app_private_key_pkcs8.pem

# 提取应用公钥
openssl rsa -in app_private_key.pem -pubout -out app_public_key.pem

# 把 app_public_key.pem 内容（去掉 BEGIN/END 行）粘贴到沙箱应用配置页
```

### 2.3 上传公钥并取回支付宝公钥

1. 沙箱应用配置 → "接口加签方式" → 选 "公钥"
2. 把你的应用公钥贴进去 → 保存
3. 系统会回填一个**支付宝公钥**（这个不同于第一步的"沙箱公钥"，是用应用公钥换取的）→ 写入 `.env` 的 `ALIPAY_PUBLIC_KEY`

---

## 四、Step 3：写入 .env

```bash
# anxinbao-server/.env
ALIPAY_APP_ID=2021000122xxxxxx                  # 沙箱 APPID
ALIPAY_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
MIIEvQIBADAN...（一长串多行）...
-----END PRIVATE KEY-----"
ALIPAY_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
MIIBIjANB...（一长串多行）...
-----END PUBLIC KEY-----"
PAYMENT_NOTIFY_URL=https://your-test-tunnel.example.com/payment/notify/alipay
```

**关于 NOTIFY_URL**：
- 沙箱测试时本机不能直接被支付宝服务器回调 → 用 [ngrok](https://ngrok.com) 或 [frp](https://github.com/fatedier/frp) 把本地 8000 端口暴露成公网域名
- 例如 `ngrok http 8000` → 用生成的 `https://xxxx.ngrok.io/payment/notify/alipay` 填到 NOTIFY_URL

**验证**：
```bash
cd anxinbao-server && python scripts/check_integrations.py
# 期望 alipay 行从 🔴 missing/placeholder → 🟢 real
```

---

## 五、Step 4：升级 payment_service.py 到真签名

当前实现 [`payment_service.py:274-280`](../app/services/payment_service.py#L274-L280) 用的是 `base64(sorted_params)`，**不是 RSA2 签名**——支付宝服务端会拒签。改造方案：

### 5.1 装 SDK（推荐用官方）

```bash
pip install python-alipay-sdk
```

加到 `requirements.txt`：
```
python-alipay-sdk>=3.3.0
```

### 5.2 替换 AlipayService 实现

新建 `app/services/alipay_real.py`：

```python
"""真实支付宝服务（替代 payment_service.py 中占位的 AlipayService）"""
from alipay import AliPay
from app.core.config import get_settings


def get_alipay_client(sandbox: bool = True) -> AliPay:
    s = get_settings()
    return AliPay(
        appid=s.alipay_app_id,
        app_notify_url=s.payment_notify_url,
        app_private_key_string=s.alipay_private_key,
        alipay_public_key_string=s.alipay_public_key,
        sign_type='RSA2',
        debug=sandbox,  # True → 网关切到 alipaydev.com
    )


def create_app_pay_order(
    out_trade_no: str,
    total_amount: float,
    subject: str = '安心宝订阅',
    sandbox: bool = True,
) -> str:
    """返回 App 端调起支付宝所需的 order_string"""
    client = get_alipay_client(sandbox=sandbox)
    order_string = client.api_alipay_trade_app_pay(
        out_trade_no=out_trade_no,
        total_amount=total_amount,
        subject=subject,
    )
    return order_string


def verify_notify(post_data: dict, sandbox: bool = True) -> bool:
    """支付宝异步回调验签"""
    client = get_alipay_client(sandbox=sandbox)
    sign = post_data.pop('sign', None)
    sign_type = post_data.pop('sign_type', None)
    if not sign:
        return False
    return client.verify(post_data, sign)
```

### 5.3 在 payment_service.py 中替换调用

```python
# payment_service.py
from app.services.alipay_real import create_app_pay_order, verify_notify

class AlipayService:
    def create_trade(self, order: PaymentOrder, product_code: str = 'QUICK_MSECURITY_PAY'):
        order_string = create_app_pay_order(
            out_trade_no=order.order_id,
            total_amount=float(order.amount),
            subject=order.description or '安心宝服务',
            sandbox=getattr(get_settings(), 'alipay_sandbox', True),
        )
        return {'code': '10000', 'msg': 'Success', 'order_string': order_string}

    def verify_notify(self, params: Dict[str, Any]) -> bool:
        return verify_notify(params, sandbox=getattr(get_settings(), 'alipay_sandbox', True))
```

### 5.4 加 sandbox 配置

`app/core/config.py`：
```python
alipay_sandbox: bool = True  # 上线前改 False
```

`.env`：
```
ALIPAY_SANDBOX=true
```

---

## 六、Step 5：联调测试

### 6.1 启动后端
```bash
cd anxinbao-server
python main.py    # DEBUG=true，监听 8000
```

### 6.2 ngrok 暴露回调
```bash
ngrok http 8000
# Forwarding 行例如 https://abcd.ngrok.io -> http://localhost:8000
# 把这个 URL 更新到 .env 的 PAYMENT_NOTIFY_URL，重启后端
```

### 6.3 创建一笔测试订单
```bash
curl -X POST http://localhost:8000/api/payment/alipay/create \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "subscription_id": "monthly_basic",
    "amount": 0.01
  }'
# 返回 order_string，例如 "alipay_sdk=python-alipay-sdk&app_id=..."
```

### 6.4 沙箱 App 端调起
- 安装 [支付宝沙箱版 App](https://opendocs.alipay.com/common/02kovz)
- 用 Step 2.3 的买家账号登录
- 把 order_string 通过 App 端调用 `AlipaySDK.payV2(orderString)` → 进入支付宝支付页 → 输入支付密码（沙箱默认 `111111`）

### 6.5 验证回调
- 后端日志应能看到 ngrok 转发过来的 POST `/payment/notify/alipay`
- `verify_notify` 返回 True → 订单状态改为 paid
- `/api/subscription/me` 应能查到该用户的有效订阅

---

## 七、Step 6：切生产环境

### 7.1 生产应用申请

1. [open.alipay.com/develop/manage](https://open.alipay.com/develop/manage) → "网页&移动应用" → 创建应用
2. 选择 "App 支付" 能力
3. 提交营业执照、ICP 备案、域名所有权证明（约 1-3 天审核）

### 7.2 生产密钥配置

1. 重新走 Step 2 生成一对**全新**的 RSA2 密钥（不要复用沙箱）
2. 上传应用公钥到生产应用配置页
3. 取回支付宝公钥
4. 更新 `.env`：
   ```
   ALIPAY_APP_ID=<生产 APPID>
   ALIPAY_PRIVATE_KEY="<生产应用私钥>"
   ALIPAY_PUBLIC_KEY="<生产支付宝公钥>"
   PAYMENT_NOTIFY_URL=https://api.anxinbao.com/payment/notify/alipay
   ALIPAY_SANDBOX=false
   ```
5. 重启后端，跑 `python scripts/check_integrations.py --strict` 应通过

### 7.3 上线前 checklist

- [ ] 生产应用审核通过
- [ ] 生产 RSA2 密钥与沙箱完全独立
- [ ] PAYMENT_NOTIFY_URL 是 HTTPS 公网地址，且服务器能接收
- [ ] 服务端有幂等机制（同一 `out_trade_no` 不能重复入账）
- [ ] 异常订单告警（如 verify_notify 失败 > 5%/小时）
- [ ] 退款流程演练通过
- [ ] 用真实小额（¥0.01）走通端到端

---

## 八、安全须知（不能省）

1. **私钥永远不进 git**。`.env` 已在 [.gitignore](../../.gitignore) 第 2 行排除
2. **回调一定要验签**。否则攻击者可以伪造支付成功通知白嫖订阅
3. **金额校验**。回调里的 `total_amount` 必须与本地订单 `amount` 严格相等
4. **订单状态机**。已支付的订单不能被再次更新；退款独立流转
5. **超时处理**。订单超过 30 分钟未支付应自动关闭
6. **日志脱敏**。不要把完整签名写入日志（黑客拿到能反推签名规则）

---

## 九、常见错误对照

| 错误码 | 含义 | 解决 |
|---|---|---|
| `ACQ.SIGN_ERROR` | 签名错误 | 私钥/公钥配错；或 PKCS1 vs PKCS8 不匹配 |
| `ACQ.INVALID_PARAMETER` | 参数错误 | 比对官方文档必填字段；money 格式两位小数 |
| `ACQ.MERCHANT_AGREEMENT_NOT_EXIST` | 商户未签约 | 沙箱默认已签约；生产环境需签 App 支付协议 |
| 回调没收到 | 回调地址不通 | ngrok URL 改了忘更新；或防火墙挡了 |

---

## 十、为什么不直接用聚合支付（如 Stripe / Ping++）

| 维度 | 直连支付宝 | 聚合支付 |
|---|---|---|
| 接入复杂度 | 高 | 低 |
| 手续费 | 0.6% | 0.6% + 平台抽佣 |
| 流水到账 | T+1 直接到对公 | 经过聚合方账户 |
| 资质门槛 | 普通商户即可 | 部分聚合方要求年流水 |
| 监管风险 | 低 | 中（部分平台风控严） |

**安心宝建议直连**（金额小、用户基数小阶段，省手续费 + 资金链路清晰）。后续如果接微信支付，再考虑聚合方案。

---

> 完成 Step 1-5 后，[`/health/integrations`](../main.py) 中的 `alipay` 行会从 🔴 → 🟢，[`FEATURE_STATUS.md`](../../FEATURE_STATUS.md) 中 `payment_service` 可从 🟡 升到 🟢。
