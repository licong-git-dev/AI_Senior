# `/api/users/*` 废弃迁移指南

> 本文给出 [`anxinbao-server/app/api/users.py`](../app/api/users.py) 已废弃端点的逐项替代代码。前端、第三方调用方、测试代码可按此 1:1 替换。

## 为什么废弃

`users.py` 自始至终用进程内 dict（`elders_store`、`family_store`）存储老人/家属档案，**服务一重启数据全丢**。在生产环境上线即等于事故。该模块已废弃：

- DEBUG=True：返回 404，并在日志中记录"调用了已废弃端点"告警
- DEBUG=False：返回 410 Gone，body 含 `use_instead` 字段直接告知替代接口

本文档把前端/调用方的迁移做成可复制粘贴的代码片段。

---

## 1. 创建老人档案

### ❌ 旧代码（已废弃）
```typescript
// 前端
const resp = await fetch('/api/users/elder/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: '张妈妈',
    age: 70,
    gender: 'female',
    phone: '13800138000',
    health_conditions: ['高血压'],
    medications: ['降压药'],
    dialect: 'wuhan',
  }),
});
const { elder_id } = await resp.json();
```

### ✅ 新代码（注册 + 老人档案一步完成）
```typescript
import { authFetch } from '../lib/api';

const resp = await authFetch('/api/auth/register', {
  method: 'POST',
  body: JSON.stringify({
    username: 'zhang_mama_01',          // 必填，唯一
    password: '至少6位密码',
    role: 'elder',                       // 关键：标识为老人账号
    name: '张妈妈',
    age: 70,
    gender: 'female',
    phone: '13800138000',
    address: '武汉市江岸区...',
    dialect: 'wuhan',
    health_conditions: ['高血压'],
    medications: ['降压药'],
  }),
});

const { access_token, user_id, elder_id } = await resp.json();
// access_token 用于后续认证；elder_id 是老人 User 表的主键
```

**关键变化**：
- 不再有"无认证创建老人"的入口；必须走标准 `/api/auth/register`
- 返回值新增 `access_token` 与 `user_id`（UserAuth.id）
- `elder_id` 是 `User.id`（老人信息表主键），与 JWT 中的 `user_id` 不同（详见 [CLAUDE.md](../../CLAUDE.md#关键身份模型容易踩坑)）

---

## 2. 添加家属

### ❌ 旧代码
```typescript
const resp = await fetch('/api/users/family/create', {
  method: 'POST',
  body: JSON.stringify({
    elder_id,
    name: '小王',
    relationship: '儿子',
    phone: '13900139000',
    is_primary: true,
  }),
});
```

### ✅ 新代码（家庭组邀请码模型）
```typescript
import {
  getMyFamilyGroups,
  createFamilyGroup,
  createBindingRequest,
} from '../lib/api';

// 1) 获取或创建家庭组
const { groups } = await getMyFamilyGroups();
let groupId: string;
if (groups.length > 0) {
  groupId = getFamilyGroupId(groups[0]);
} else {
  const { group } = await createFamilyGroup('张妈妈的家庭', '张妈妈');
  groupId = getFamilyGroupId(group);
}

// 2) 生成邀请码（家属用此码或邀请链接完成绑定）
const { invite_code } = await createBindingRequest(groupId);

// 3) 通过子女端用邀请码完成绑定（或扫描邀请链接）
//    POST /api/family/bind { invite_code: 'ABCD1234' }
```

**为什么换成邀请码模型**：
- 老旧接口让创建者直接填家属手机号，没有家属授权 → 容易被滥用
- 新模型由家属主动用邀请码完成绑定，符合 GDPR/隐私法的"自愿入会"原则
- 邀请码 7 天有效，到期自动失效

---

## 3. 列出家属

### ❌ 旧代码
```typescript
const resp = await fetch(`/api/users/family/${elder_id}`);
const { family_members } = await resp.json();
```

### ✅ 新代码
```typescript
import { getMyFamilyGroups } from '../lib/api';

const { groups } = await getMyFamilyGroups();
// groups[0].members 即家属列表，结构包含 name / role / phone / bound_at
```

---

## 4. 绑定设备

### ❌ 旧代码
```typescript
const resp = await fetch(
  `/api/users/elder/${elder_id}/bind-device?device_id=AXB-001`
);
```

### ✅ 新代码
```typescript
const resp = await authFetch('/api/iot/bind', {
  method: 'POST',
  body: JSON.stringify({
    device_id: 'AXB-001',
    device_type: 'smart_speaker',  // 或 'health_bracelet' / 'fall_detector'
  }),
});
```

设备绑定关系存储在 `Device` / `DeviceAuth` 表，可永久持久化。

---

## 5. 通过设备 ID 反查老人

### ❌ 旧代码
```typescript
const resp = await fetch(`/api/users/device/AXB-001`);
```

### ✅ 新代码
```typescript
const resp = await authFetch('/api/iot/devices/AXB-001');
const { device, elder } = await resp.json();
// elder.id 即 User.id；elder.user_auth_id 即 UserAuth.id（与 JWT sub 一致）
```

---

## 6. 测试代码迁移

### ❌ 旧测试
```python
# tests/api/test_endpoints.py
def test_get_user_profile(self, client, auth_headers):
    response = client.get('/api/users/me', headers=auth_headers)
    assert response.status_code in [200, 404]  # 既有的防御性断言
```

### ✅ 新测试
```python
def test_get_user_profile(self, client, auth_headers):
    response = client.get('/api/auth/me', headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert 'user_id' in body and 'role' in body
```

---

## 7. 完整迁移检查清单

针对你的代码库执行：

```bash
# 1. 找出所有调用方
grep -rn '/api/users/elder' anxinbao-pwa/src/  anxinbao-server/tests/
grep -rn '/api/users/family' anxinbao-pwa/src/ anxinbao-server/tests/
grep -rn '/api/users/device' anxinbao-pwa/src/ anxinbao-server/tests/
grep -rn '/api/users/bind-device' anxinbao-pwa/src/

# 2. 确认替换覆盖
# 把每个命中改为本文档给出的"新代码"

# 3. 验证废弃端点的行为
curl -s http://localhost:8000/api/users/elder/test-id | jq .
# 期望：DEBUG=true → 404；DEBUG=false → 410，detail.use_instead 给出新接口
```

---

## 8. 已知例外

`tests/api/test_endpoints.py` 中三处对 `/api/users/me` 与 `/api/users/family` 的请求**保留**（防御性 `assert in [200, 404]`），因为：

1. 这些端点 **从未存在** 在 users.py 中（被废弃前也没有）
2. 测试本意是"如果某天加上了能跑通"，对 404 默认接受
3. 当前 users.py 的 `_gone()` 在 DEBUG 模式返回 404 → 测试继续通过

**结论**：测试无需修改，废弃过程零回归。

---

## 9. 时间线建议

| 阶段 | 动作 |
|---|---|
| 2026-04（已完成） | users.py 全量端点 deprecated；生产环境 410 Gone |
| 2026-05 | 全部前端调用方迁移完成；监控 `/api/users/*` 调用量降为 0 |
| 2026-06 | 删除 users.py 文件；从 main.py 卸载 router |
| 2026-07 | 从 OpenAPI schema 与文档中彻底移除条目 |

---

> 任何疑问见 [CLAUDE.md](../../CLAUDE.md) 中"关键身份模型（容易踩坑）"章节，或 [auth.py](../app/api/auth.py)、[family.py](../app/api/family.py) 的真实端点实现。
