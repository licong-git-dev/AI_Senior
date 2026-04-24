# 贡献指南

> 用最少的协议成本保证代码质量。本文档约束开发者（也包括 AI 协作者）的最低工程门槛。

## 三条铁律

1. **任何对外宣传只能引用 🟢 绿色就绪度的功能**（参见 [FEATURE_STATUS.md](FEATURE_STATUS.md)）。
2. **不要让"看起来是真的，其实是假的"代码上线**：random 业务数据 / mock 信心值 / 空 router / 占位密钥 → 提 PR 前必须用 `_SafeRandom` 门控、抛 `*NotImplemented`、生产 410，或者从入口下线。
3. **禁止直推 main**：本地完成后 → 推 feature 分支 → 自检通过 → PR → 至少 1 人 review → squash merge。

## 提交前自检（一行）

```bash
make verify          # 集成真实性 + 后端测试
make verify-prod     # 模拟生产环境（DEBUG=false），验证守卫真生效
make doctor          # 综合诊断 Python/Node/Git/.env/集成
```

详见 [Makefile](Makefile) 与 [`anxinbao-server/scripts/check_integrations.py`](anxinbao-server/scripts/check_integrations.py)。

## 分支命名

| 前缀 | 用途 | 例 |
|---|---|---|
| `feat/` | 新功能 | `feat/medication-reminder-tts` |
| `fix/` | 修 bug | `fix/sos-sms-kwargs` |
| `safety/` | 安全/合规修复 | `safety/admin-rbac` |
| `docs/` | 仅文档 | `docs/alipay-sandbox-guide` |
| `chore/` | 杂项（依赖、CI、清理）| `chore/remove-fix-scripts` |
| `refactor/` | 重构 | `refactor/dialect-companion-stats` |

## Commit Message 风格

参考 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/v1.0.0/)：

```
<type>(<scope>): <一句话总结>

<具体改动 1：原因 + 做了什么>
<具体改动 2：原因 + 做了什么>
...
```

`type` 与分支前缀一一对应。`scope` 可选，如 `safety`、`devx`、`backend`、`frontend`。中英文都可以，**业务描述用中文**。

实例（本仓库已有的好范例）：
- `fix(safety): 修复 SOS 短信调用参数名 bug（生产阻断）`
- `feat: 第二轮自治优化 — 凭据自检/方言扩库/行动入口/三色灯看板`

## PR Checklist

提 PR 前自查：

- [ ] `make verify` 通过
- [ ] 涉及 API 改动：`/health/integrations` 与 [FEATURE_STATUS.md](FEATURE_STATUS.md) 已同步
- [ ] 涉及第三方凭据/配置：[`.env.example`](anxinbao-server/.env.example) 已同步
- [ ] 涉及前端 UI：截图贴在 PR 描述
- [ ] 涉及废弃端点：[`docs/MIGRATION_*.md`](anxinbao-server/docs/) 加入迁移指引
- [ ] 涉及方言库扩展：`dialect_companion.stats()` 数量增加在 PR 描述里写明
- [ ] 涉及生产风险（鉴权 / 加密 / 支付 / 短信）：另请一名 reviewer

## 红黄绿三色升级标准

| 颜色 | 升级到下一级需要 |
|---|---|
| 🔴 → 🟡 | 拿掉所有 random 业务数据、生产环境抛 NotImplemented 或返回 410；或加入 `_SafeRandom` 门控 |
| 🟡 → 🟢 | 关键路径有真实 DB 写或真 HTTP 调用、配齐生产凭据、`/health/integrations` 显示 `production_ready=true`、至少 1 个端到端测试覆盖 |

参见 [FEATURE_STATUS.md "维护方式"](FEATURE_STATUS.md#八维护方式)。

## 关键开发模式

### 限流装饰器（必须按此顺序）

```python
@router.post("/endpoint")
@limiter.limit("5/minute")            # 紧跟在 router 装饰器后
async def handler(
    request: Request,                 # 第一个参数必须命名 request
    body: SomeRequest,                # Pydantic body 用其他名称
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ...
```

### 角色守卫

```python
from app.core.deps import get_current_admin, get_current_elder, get_current_family

# admin 接口
async def admin_only(current = Depends(get_current_admin)): ...

# 老人本人
async def elder_only(current = Depends(get_current_elder)): ...

# 家属
async def family_only(current = Depends(get_current_family)): ...
```

### 业务模拟数据守卫（避免伪 ✅）

模块顶部包装 random：

```python
class _SafeRandom:
    """生产环境（DEBUG=False）所有 random 返回 0/0.0/首项；DEBUG=True 保持原行为"""
    def randint(self, a, b):
        from app.core.config import get_settings
        return _real_random.randint(a, b) if get_settings().debug else 0
    # ... uniform / choice 类似

random = _SafeRandom()
```

或者抛业务异常：

```python
class FeatureNotImplemented(NotImplementedError): pass

def my_method(self):
    from app.core.config import get_settings
    if not get_settings().debug:
        raise FeatureNotImplemented("此能力尚未接入真实数据源")
    # ... mock 实现
```

API 层捕获并返回 HTTP 501（[life.py 装饰器](anxinbao-server/app/api/life.py) 是范例）。

### 字符串与 f-string

- **不要在 f-string 内嵌套同款引号**（PEP 701 仅 Python 3.12+ 支持）
- 反例：`f"{news["title"]}"` ❌
- 正例：先 `title = news["title"]` 再 `f"{title}"` ✅

## 隐私与安全

- 老人对 AI 说的话默认**不展示给家属**：仅基于已抽取的 topics 做脱敏摘要（参见 [`daily_report.py:392-426`](anxinbao-server/app/services/daily_report.py#L392-L426)）
- 任何展示给家属的"摘要"必须经过敏感词过滤
- 不要把 `key_quotes` 或类似字段直接 echo 老人原话给第三方

## 依赖

- Python ≥ 3.12（必须！PEP 701 / pydantic v2）
- Node.js ≥ 18
- 新加 Python 依赖：写入 `anxinbao-server/requirements.txt`，**注明用途**
- 新加前端依赖：`anxinbao-pwa/package.json`，避免引入大型库（PWA 体积重要）

## 行为准则

- 评审时只对**事实**严苛，不对**人**严苛
- 拒绝 PR 时给出"如何改正"的具体建议
- 文档/注释/commit 用中文，但代码标识符用英文（除非业务术语）
- 遇到不确定的事 → 在 PR 描述里写"open question"，不要默默实现

---

> 项目目标见 [README.md](README.md) "项目简介"，三色灯标准见 [FEATURE_STATUS.md](FEATURE_STATUS.md)。
