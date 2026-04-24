# 安心宝 · 验收检查清单

> 目的：把 15 轮自治的每个关键声明都变成**可验证命令 + 可观察输出**。
> 适用场景：QA 上线前、内部审计、新人熟悉代码、投资人技术尽调。
> 全部命令均**无需启动服务**即可跑（低内存机器友好）。

---

## 一、基础环境（3 项）

### ✅ 1.1 Python / Node 版本就绪
```bash
python3 --version   # 期望：Python 3.12.x（PEP 701 要求）
node --version      # 期望：v18+ 或 v20+
```

### ✅ 1.2 Git 状态干净
```bash
git status
# 期望：nothing to commit, working tree clean
```

### ✅ 1.3 所有新/改 Python 文件语法 OK
```bash
cd anxinbao-server
python3 -c "
import ast
from pathlib import Path
errors = 0
for p in Path('app').rglob('*.py'):
    try:
        ast.parse(open(p).read())
    except SyntaxError as e:
        print(f'ERR {p}: {e}')
        errors += 1
print(f'扫描完成: {errors} 个语法错')
"
# 期望：扫描完成: 0 个语法错
```

---

## 二、三色灯真实性验证（5 项）

### ✅ 2.1 🔴 红色就绪度模块为 0
```bash
# 手动对照 FEATURE_STATUS.md 第三节 "v3 整体快照"
grep -c "🔴" FEATURE_STATUS.md
# 期望：**看 v3 增量之后的行数**，不是全文计数
# FEATURE_STATUS.md 仍含 v1/v2 历史 🔴 记录用于对照
```

### ✅ 2.2 admin/analytics 生产环境从 OpenAPI 隐藏
```bash
grep -n "_RED_ROUTERS_HIDE_IN_PROD" anxinbao-server/main.py
# 期望：集合含 "users", "admin", "analytics", "ai"

grep -n "_include_router_safely" anxinbao-server/main.py
# 期望：所有红色 router 走此函数注册
```

### ✅ 2.3 用户敏感字段递归脱敏
```bash
grep -A3 "_SENSITIVE_KEY_HINTS" anxinbao-server/app/services/audit_service.py | head -15
# 期望：包含 password, phone, id_card, address, medical_record 等 22 字段
```

### ✅ 2.4 9 个工具全部有 handler
```bash
cd anxinbao-server && python3 -c "
import sys; sys.path.insert(0, '.')
from app.services.companion_tools import list_tools, _REGISTRY
tools = list_tools()
bound = [n for n, t in _REGISTRY.items() if t.handler is not None]
print(f'工具池 {len(tools)} 个，{len(bound)} 个 handler 已绑定')
assert len(tools) == 9, f'期望 9 个工具，实际 {len(tools)}'
assert len(bound) == 9, f'期望 9 个 handler 绑定，实际 {len(bound)}'
print('✅')
"
```

### ✅ 2.5 所有 fix_*.py dev 残骸已清理
```bash
ls anxinbao-server/fix_*.py 2>/dev/null | wc -l
# 期望：0
```

---

## 三、安全门验证（6 项）

### ✅ 3.1 启动安全门拦截缺凭据生产配置
```bash
cd anxinbao-server
DEBUG=false DATABASE_URL=sqlite:// python scripts/check_integrations.py --strict
echo "exit code: $?"
# 期望：exit code: 1（拦住了）+ 打印 critical_missing 清单
```

### ✅ 3.2 齐凭据时 strict 模式通过
```bash
cd anxinbao-server
DEBUG=false DATABASE_URL=sqlite:// \
JWT_SECRET_KEY="ci-fixture-jwt-secret-min-32-chars-long-for-gate-validation" \
ENCRYPTION_KEY="ci-fixture-encryption-key-base64-format-strong-random-here" \
DASHSCOPE_API_KEY="ci-fixture-dashscope-key" \
XFYUN_APPID="ci-fixture" XFYUN_API_KEY="x" XFYUN_API_SECRET="y" \
ALIYUN_ACCESS_KEY_ID="ci-fixture-aliyun-key" \
SMS_TEMPLATE_EMERGENCY="SMS_CIFIX_001" \
JPUSH_APP_KEY="x" \
ALIPAY_APP_ID="x" \
python scripts/check_integrations.py --strict
echo "exit code: $?"
# 期望：exit code: 0（通过）
```

### ✅ 3.3 SOS 短信调用参数名修复（r1 核心 bug）
```bash
grep -A6 "sms_service.send_emergency_alert" anxinbao-server/app/services/emergency_service.py | head -10
# 期望：phone_number= / elderly_name= / elderly_phone= / location=
# NOT: phone_numbers= / user_name= / phone= / location_address=
```

### ✅ 3.4 隐私防线 —— key_quotes 已脱敏
```bash
grep -B2 -A5 "key_quotes" anxinbao-server/app/services/daily_report.py | head -30
# 期望：能看到 _SENSITIVE_KEYWORDS 过滤 + "和安心宝聊到了「XX」" 脱敏模板
```

### ✅ 3.5 admin 路由强鉴权（r4 修提权）
```bash
grep -A5 "async def verify_admin" anxinbao-server/app/api/admin.py | head -15
# 期望：current_user: UserInfo = Depends(get_current_admin)
# NOT: get_current_user（弱）
# NOT: "为演示目的，允许任何登录用户访问"
```

### ✅ 3.6 CORS 生产守卫
```bash
grep -A20 "CORS 守卫" anxinbao-server/main.py | head -30
# 期望：检查 * / localhost / 127.x / http:// 都会 fatal
```

---

## 四、数字生命陪伴验证（8 项）

### ✅ 4.1 Persona 不可变
```bash
cd anxinbao-server && python3 -c "
import sys; sys.path.insert(0, '.')
from app.services.persona import ANXINBAO_PERSONA
try:
    ANXINBAO_PERSONA.warmth = 0.1
    print('❌ 应不可变但可改')
except Exception:
    print('✅ frozen dataclass，不可运行时修改')
print(f'  - 名字：{ANXINBAO_PERSONA.name}')
print(f'  - 方言：{ANXINBAO_PERSONA.accent}')
print(f'  - 耐心度：{ANXINBAO_PERSONA.patience}（应 >= 0.9）')
assert ANXINBAO_PERSONA.patience >= 0.9
"
```

### ✅ 4.2 武汉话 500+ 模板
```bash
cd anxinbao-server && python3 -c "
import sys; sys.path.insert(0, '.')
from app.services.dialect_companion import dialect_companion
stats = dialect_companion.stats()
total_wuhan = sum(s.get('wuhan', 0) for s in stats.values())
print(f'武汉话总数: {total_wuhan}')
assert total_wuhan >= 500, f'应 >= 500，实际 {total_wuhan}'
print('✅')
"
```

### ✅ 4.3 system prompt 体积健康（< 1500 字符）
```bash
cd anxinbao-server && python3 -c "
import sys; sys.path.insert(0, '.')
from app.services.persona import ANXINBAO_PERSONA, PersonaContext, build_system_prompt
ctx = PersonaContext(elder_name='张妈妈', elder_dialect='wuhan',
                     elder_mood_recent='lonely', health_status='血压偏高',
                     family_status='小军昨天回家',
                     last_chat_summary='聊到了孙子',
                     time_of_day='morning')
p = build_system_prompt(ANXINBAO_PERSONA, ctx)
print(f'system prompt 长度: {len(p)} chars')
assert len(p) < 1500, f'过长: {len(p)}'
print('✅')
"
```

### ✅ 4.4 记忆引擎 CRUD + 隐私默认
```bash
cd anxinbao-server && python3 -c "
import sys, tempfile, os
sys.path.insert(0, '.')
from app.services.memory_engine import MemoryEngine, MemoryRecord, MemoryType, MemoryVisibility

fd, p = tempfile.mkstemp(suffix='.db'); os.close(fd)
eng = MemoryEngine(db_path=p)
rec = MemoryRecord(user_id=1, type=MemoryType.FACT, content='测试事实', keywords=['测试'])
assert rec.visibility == MemoryVisibility.SELF_ONLY, '默认 visibility 必须 SELF_ONLY'
new_id = eng.save(rec)
assert new_id > 0
items = eng.recall(user_id=1, query='测试')
assert len(items) == 1
# 跨用户越权
assert not eng.forget(new_id, user_id=2), '越权应失败'
os.unlink(p)
print('✅')
"
```

### ✅ 4.5 6 个情境触发器全部注册
```bash
cd anxinbao-server && python3 -c "
import sys; sys.path.insert(0, '.')
from app.services.companion_triggers import ALL_TRIGGERS
names = {t.name for t in ALL_TRIGGERS}
expected = {'silence', 'health_anomaly', 'family_absence',
            'festival', 'memorial', 'weather'}
assert names == expected, f'期望 {expected}, 实际 {names}'
print('✅ 6 个触发器全部注册')
"
```

### ✅ 4.6 DND 默认配置 + push_proactive
```bash
cd anxinbao-server && python3 -c "
import sys, tempfile, os
sys.path.insert(0, '.')
from app.services.proactive_engagement import ProactiveStore
fd, p = tempfile.mkstemp(suffix='.db'); os.close(fd)
store = ProactiveStore(db_path=p)
cfg = store.get_dnd(user_id=999)
assert cfg['dnd_start'] == '22:00'
assert cfg['dnd_end'] == '07:00'
assert cfg['daily_quota'] == 4
assert bool(cfg.get('push_proactive', True)) is True
os.unlink(p)
print('✅ DND 默认 22-07 + quota 4 + push 开')
"
```

### ✅ 4.7 weather_service 解析正确
```bash
cd anxinbao-server && python3 -c "
import sys; sys.path.insert(0, '.')
from app.services.weather_service import _parse_wttr_response
fake = {'weather': [
  {'date': 'a', 'maxtempC': '30', 'mintempC': '20', 'hourly': []},
  {'date': 'b', 'maxtempC': '22', 'mintempC': '15', 'hourly': [
    {'lang_zh': [{'value': '晴'}], 'weatherDesc': [{'value': 'Sunny'}]}
  ]},
]}
f = _parse_wttr_response('Wuhan', fake)
assert f.temp_drop == 8, f'期望 8，实际 {f.temp_drop}'
assert f.heat_wave is False
print('✅ weather 解析正确')
"
```

### ✅ 4.8 Companion 模块独立可 import（零新依赖）
```bash
cd anxinbao-server && python3 -c "
import sys; sys.path.insert(0, '.')
# 5 大 Companion 模块应全部可 import
from app.services import persona, memory_engine, memory_consolidator
from app.services import companion_tools, companion_triggers, proactive_engagement, weather_service
from app.services.agents import hermes, health_agent, social_agent, memory_agent, safety_agent, schedule_agent
from app.api import companion
print('✅ Companion 全部模块 import 成功')
"
```

---

## 五、测试覆盖验证（3 项）

### ✅ 5.1 原有测试 272+ case
```bash
cd anxinbao-server
pytest tests/ -q --collect-only 2>&1 | tail -3
# 期望：collected 370+ items
```

### ✅ 5.2 Companion 单测全通过
```bash
cd anxinbao-server
pytest tests/unit/test_companion_*.py tests/unit/test_weather_service.py -v --tb=short
# 期望：所有 89 case passed（具体数可能因 conftest 差异略异）
```

### ✅ 5.3 E2E 集成测试可运行（不启动 uvicorn）
```bash
cd anxinbao-server
COMPANION_ENABLED=true pytest tests/integration/test_companion_e2e.py -v --tb=short
# 期望：23 case passed（全部 scenarios 通过）
```

---

## 六、文档完整性验证（2 项）

### ✅ 6.1 18 份运维文档存在
```bash
find . -name "*.md" -not -path "*/node_modules/*" -not -path "*/.git/*" \
  -not -path "*/senior/*" -not -path "*/.omc/*" -not -path "*/.specstory/*" \
  -not -path "*/.claude/*" | wc -l
# 期望：>= 25 份（含 README / CHANGELOG / FEATURE_STATUS / 各 docs/*.md）
```

### ✅ 6.2 RFC / COST / RISKS / DEMO / CHECKLIST 都可访问
```bash
for f in \
  anxinbao-server/docs/DIGITAL_COMPANION_RFC.md \
  anxinbao-server/docs/DIGITAL_COMPANION_COST.md \
  anxinbao-server/docs/DIGITAL_COMPANION_RISKS.md \
  anxinbao-server/docs/DATABASE_MIGRATION.md \
  anxinbao-server/docs/PAYMENT_ALIPAY_SETUP.md \
  anxinbao-server/docs/VIDEO_CALL_SETUP.md \
  anxinbao-server/docs/MIGRATION_users_api.md \
  anxinbao-pwa/docs/BUNDLE_OPTIMIZATION.md \
  anxinbao-pwa/docs/PWA_MANIFEST.md \
  ROADSHOW_SUMMARY.md \
  DEMO_SCRIPT.md \
  VERIFICATION_CHECKLIST.md \
  CHANGELOG.md \
  FEATURE_STATUS.md \
  CONTRIBUTING.md
do
  [ -f "$f" ] && echo "✅ $f" || echo "❌ $f 缺失"
done
```

---

## 七、生产就绪 Gate（上线前必过）

以下任一项失败，**禁止上线**：

| # | 验证 | 命令 |
|---|---|---|
| G1 | 所有 P0 凭据已配置 | `make integrations` 全绿 |
| G2 | CI 守卫启用 | `.github/workflows/integration-self-check.yml` 存在且可执行 |
| G3 | Companion 关闭时服务正常 | `COMPANION_ENABLED=false` 下 `/api/chat` 正常响应 |
| G4 | 生产模式启动守卫生效 | `DEBUG=false` 缺凭据启动被拒 |
| G5 | 所有数据库迁移已跑 | `alembic current` 输出 head |
| G6 | TURN 服务器已部署（如开放视频） | `curl -I $TURN_URL` 返 200 |
| G7 | 监控告警已配置 | `/metrics` + `/health/integrations` 可被监控系统拉取 |
| G8 | 红队测试已通过（100 道医疗陷阱题） | 内部报告 |
| G9 | 产品责任险已投保 | 法务确认 |
| G10 | 网信办大模型备案已提交 | 法务确认 |

**通过 10 项即具备生产就绪条件**。

---

## 八、上线后监控

每天晨会检查：

```bash
# 1. DLQ 积压
curl -s https://prod.anxinbao.com/health/integrations | jq .dead_letter_queue

# 2. 生产守卫状态
curl -s https://prod.anxinbao.com/health/integrations | jq .production_ready
# 必须 true

# 3. Scheduler 异常计数
curl -s https://prod.anxinbao.com/health/integrations | jq .scheduler.metrics
# jobs_errored / jobs_missed 均应 = 0 或非常小

# 4. 关键 API 延迟（依赖 Prometheus）
# 看 /metrics 中 http_request_duration_seconds 分布
```

---

## 九、验收签字

| 角色 | 验证项 | 签字 |
|---|---|---|
| 后端 TL | 一-五 章全部 ✅ | ____________ |
| 前端 TL | FEATURE_STATUS 前端相关绿色项 | ____________ |
| QA | 五、七章全部 ✅ | ____________ |
| 安全 | 三、七章 G8 ✅ | ____________ |
| 法务 | 七章 G9、G10 ✅ | ____________ |
| 产品 | [`DIGITAL_COMPANION_RFC.md`](anxinbao-server/docs/DIGITAL_COMPANION_RFC.md) 评审通过 | ____________ |
| CEO | 整体上线决策 | ____________ |

**未全部签字前，代码可推进但不得对外正式发布。**
