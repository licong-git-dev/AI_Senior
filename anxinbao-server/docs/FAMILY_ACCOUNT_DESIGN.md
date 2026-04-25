# 家庭账户设计（r18）

> 解决 [`PRODUCT_INSIGHTS.md`](../../PRODUCT_INSIGHTS.md) **Insight #1: 付费者 ≠ 使用者** 悖论。
> 本文档是 r18 实施快照 + 后续 r19/r20 路线图。

## 一、为什么需要家庭账户

旧模型：订阅、套餐挂在 `UserAuth` 上 → 一个账号一个订阅。问题：

- 子女付钱给父母用，但**支付主体和使用主体不是同一账号**
- 多个子女想一起关注父母，需要多个独立订阅
- 父母去世/迁移护理重心时，订阅没法在家庭间转移
- 政府补贴/团购的"按家庭计费"无法落地

## 二、新模型（r18）

```
                    ┌──────────────────┐
                    │  FamilyAccount   │ ←── 计费/订阅主体
                    └─────────┬────────┘
                              │
              ┌───────────────┼────────────────┐
              │               │                │
        beneficiary    primary_payer        members (1-N)
        ─────────────  ────────────         ─────────────
              ↓               ↓                  ↓
        User (老人)      UserAuth         FamilyAccountMember
                         (主付费人)        ┌──────────────┐
                                          │ user_auth_id │
                                          │ role         │ (payer/caretaker/observer)
                                          │ permission_l │
                                          └──────────────┘
```

### 三张新表

| 表 | 职责 |
|---|---|
| `family_accounts` | 家庭账户主表（订阅、积分、套餐挂这里）|
| `family_account_members` | 多对多 UserAuth ↔ FamilyAccount，含 role/permission |
| `family_account_invites` | 邀请码 6 位、7 天默认过期、单次有效 |

### 角色权限矩阵

| 操作 | payer | caretaker | observer |
|---|---|---|---|
| 账单/订阅 | ✅ | ❌ | ❌ |
| 邀请新成员 | ✅ | ❌ | ❌ |
| 转让 payer | 仅自己 | ❌ | ❌ |
| 查完整日报 | ✅ | ✅ | ❌ |
| 查聚合安心指数 | ✅ | ✅ | ✅ |
| 设 DND/触发器 | ✅ | ✅ | ❌ |
| 代老人触发 SOS | ✅ | ✅ | ❌ |
| 退出账户 | 需先转让 | 直接退 | 直接退 |

## 三、典型场景

### 场景 A：子女主动建账户（推荐获客路径）
```
1. 子女小军注册 → 创建"妈妈的家庭"账户 (POST /api/family-account/)
2. 自动成为 payer，permission_level=5
3. 邀请妹妹小红 (POST /api/family-account/{id}/invite role=caretaker)
4. 给妈妈办账号 → 关联到 beneficiary_user_id
```

### 场景 B：老人先用，子女后入
```
1. 老人由社区/活动现场注册（独立 UserAuth role=elder）
2. 老人/工作人员发邀请码给子女
3. 子女注册后 POST /api/family-account/accept-invite
4. 后续 BD 逐步把 payer 角色往子女转
```

### 场景 C：双子女同等关注，分摊订阅
```
1. 大儿子建账户 → 邀请大女儿为 payer 角色
   (POST .../invite invited_role=payer)
2. 两人都能看账单、改订阅
3. 任意一方刷卡续费即可
```

### 场景 D：转移护理重心（受益人变更）
```
1. 父母离世 / 接力护理岳父母
2. payer 调用 PUT .../beneficiary
3. 该账户的所有数据 / 订阅延续到新受益人
```

## 四、迁移策略（已实施）

`alembic/versions/002_family_accounts.py` 中：
- 升级时遍历所有 `UserAuth(role='family')`，为每个家属创建 solo 账户
- beneficiary 关联到对应 `family_members.user_id`
- 创建者自动 role=payer

**回滚（downgrade）**：直接 drop 三张新表（数据丢失，慎用）。

## 五、API 端点速查

| Method | Path | 角色 | 用途 |
|---|---|---|---|
| POST | `/api/family-account/` | 任意登录 | 创建账户 |
| GET | `/api/family-account/` | 任意登录 | 我所属的全部账户 |
| GET | `/api/family-account/{id}/members` | 成员 | 成员列表 |
| POST | `/api/family-account/{id}/invite` | payer | 创建邀请码 |
| POST | `/api/family-account/accept-invite` | 任意登录 | 接受邀请 |
| POST | `/api/family-account/{id}/transfer-payer` | payer | 转让主付费人 |
| PUT | `/api/family-account/{id}/beneficiary` | payer | 变更受益老人 |
| DELETE | `/api/family-account/{id}/leave` | 成员 | 退出（payer 需先转让）|

错误码：
- 403 NotAMember / InsufficientPermission
- 409 CannotRemoveLastPayer
- 410 InviteExpiredOrUsed
- 400 其他业务错误

## 六、后续路线（r19 / r20）

### r19：订阅 ↔ 家庭账户挂接（替代既有 SubscriptionService）

```python
# 旧
class Subscription:
    user_auth_id: int   # 单账号订阅

# 新
class Subscription:
    family_account_id: int   # 家庭账户订阅
    payer_snapshot_user_auth_id: int  # 实付者快照（账单展示）
```

需要：
- 新建 `subscriptions` ORM 表（当前是 dataclass，挂内存）
- `payment_service` 调用方携带 `family_account_id`
- 账单查询按家庭维度聚合

### r20：礼品卡 / 团购 SKU（落地 Insight #9）

```python
class GiftCard(Base):
    """子女送父母的礼品卡（一次买断 12 个月）"""
    code: str
    sku: str  # annual_588 / annual_999
    paid_by_user_auth_id: int  # 谁买的
    redeemed_by_family_account_id: int  # 兑换到哪个家庭
    expires_at: datetime
```

获客流程：
- 子女在落地页买 ¥588 礼品卡 → 系统生成 code
- 子女发给父母 → 父母扫码注册或登录
- 兑换后自动开通该家庭账户的年订阅

### 距离生产可用的剩余工程

- [ ] r19: Subscription ORM 化 + 接通 payment
- [ ] r20: 礼品卡 SKU + 兑换流程
- [ ] r21: 子女端家庭账户 UI（成员列表 / 邀请页 / 转让页）
- [ ] r22: 老人端"我家有谁在关注"卡片（透明度 UI）

## 七、安全与合规

- 所有越权场景（非成员查看 / 非 payer 操作）已单测覆盖（[`test_family_account.py`](../tests/unit/test_family_account.py)）
- 邀请码 6 位 32 字符表（去掉 O/I/0/1 防混淆）= 1B 量级，防爆破
- 单次有效（accept 即标 used）
- 7 天默认过期，最多 30 天
- payer 转让会留 audit log（待 r19 接入 audit_service）

## 八、对应 PRODUCT_INSIGHTS

| Insight | r18 实施 | 后续 |
|---|---|---|
| #1 付费者≠使用者 | ✅ FamilyAccount 三表 + 8 端点 | r19 接订阅 |
| #2 ¥588 年卡 / ¥199 团购 | 🟡 schema 已能承载 | r20 礼品卡 SKU |
| #7 多边家庭关怀 | ✅ 多 caretaker 模型 | r21 关怀分担可视化 |
| #9 子女送礼礼品卡 | 🟡 schema 已能承载 | r20 兑换流程 |
