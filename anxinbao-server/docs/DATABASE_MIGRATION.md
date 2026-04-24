# 数据库迁移指南（Alembic）

> 安心宝使用 [Alembic](https://alembic.sqlalchemy.org) 管理数据库 schema 变更。
> 任何 [`app/models/database.py`](../app/models/database.py) 的修改都必须配套迁移脚本，否则生产环境 `init_db()` 不会自动同步（[`init_db`](../app/models/database.py) 只 create_all 不修改既有表）。

## 工作流（90% 场景）

```bash
cd anxinbao-server

# 1. 改 app/models/database.py（增/改/删字段或表）

# 2. 自动生成迁移脚本（diff Base.metadata vs 当前 DB）
alembic revision --autogenerate -m "add medication_dose_unit"

# 3. 打开 alembic/versions/<新文件>.py 复核
#    ⚠️ 必看：autogenerate 不能识别的场景见下文"已知缺陷"

# 4. 本地预演（先备份再跑）
cp anxinbao.db anxinbao.db.bak
alembic upgrade head

# 5. 验证
sqlite3 anxinbao.db ".schema medications"  # 或 psql 等价命令

# 6. 想回退？
alembic downgrade -1
```

## 一图看懂状态

```
alembic current      → 当前 DB 应用到了哪个 revision
alembic history      → 全部迁移链条
alembic heads        → 顶部（应只有 1 个，多个 = 出现分支需 merge）
alembic show <rev>   → 显示某次迁移的详情
```

## 多环境

[`alembic/env.py:23-25`](../alembic/env.py#L23) 优先读 `DATABASE_URL` 环境变量，因此：

```bash
# 开发（默认 SQLite）
alembic upgrade head

# 生产（外置 PostgreSQL）
DATABASE_URL=postgresql://user:pass@db.internal:5432/anxinbao alembic upgrade head

# 测试（内存 SQLite，CI 用）
DATABASE_URL=sqlite:// alembic upgrade head
```

`alembic.ini` 里的 `sqlalchemy.url=sqlite:///./anxinbao.db` 仅是 fallback，**生产环境必须由 env 覆盖**。

## 创建新迁移的两条路径

### A. autogenerate（推荐 90% 场景）

适合：加字段、加索引、加表、改 nullable。

```bash
alembic revision --autogenerate -m "<描述>"
```

### B. 手写迁移（剩余 10% 场景必须）

autogenerate **不能识别**这些场景：
- 字段重命名（会被识别为 drop + add，会丢数据）
- 数据迁移（如：把 `text` 字段拆成 `first_name` / `last_name`）
- 自定义索引（GIN / partial index 等）
- check constraint 修改
- 表分区

手写时：

```bash
alembic revision -m "rename medications.dose_unit to dose_unit_text"
# 然后编辑生成的空 migration 文件，手填 upgrade() 和 downgrade()
```

## 已知缺陷与陷阱

### 1. SQLite 不支持 ALTER COLUMN

SQLite 的 `ALTER TABLE` 极其有限（不能改类型、不能加 NOT NULL）。Alembic 用 batch 模式绕开：

```python
def upgrade():
    with op.batch_alter_table('medications') as batch_op:
        batch_op.alter_column('dose', existing_type=sa.String(50), nullable=False)
```

迁移到 PostgreSQL 后这个限制消失，但**为了双环境兼容，所有 alter_column 都用 batch 模式**。

### 2. autogenerate 漏检的常见情况

| 情况 | 必须手写 |
|---|---|
| `Index('ix_user_email', User.email, unique=True)` 增 / 删 | ✅ |
| `CheckConstraint("age >= 0", name='ck_age_nonneg')` | ✅ |
| 字段 `default=` 修改（仅作用于新行） | ✅ |
| 枚举值新增（PostgreSQL ENUM 类型） | ✅ |

### 3. 数据迁移 (Data Migration) 最佳实践

```python
# alembic/versions/xxx_split_name.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Step 1: schema 改动
    op.add_column('users', sa.Column('first_name', sa.String(50)))
    op.add_column('users', sa.Column('last_name', sa.String(50)))

    # Step 2: 数据搬迁（用 SQL 比 ORM 快 10-100 倍）
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE users
        SET first_name = SUBSTR(name, 1, INSTR(name, ' ') - 1),
            last_name  = SUBSTR(name, INSTR(name, ' ') + 1)
        WHERE name LIKE '% %'
    """))

    # Step 3: 旧字段在下个迁移再 drop（先观察 1-2 周）
    # op.drop_column('users', 'name')   # 这里先不做

def downgrade():
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
```

**关键**：data migration 与 column drop **分两个迁移**做，给 rollback 留余地。

### 4. 多人协作冲突（branch heads）

两个 PR 同时基于 `001_initial` 各自生成 `002_xxx` 和 `002_yyy` → 合并时出现两个 head：

```bash
alembic heads
# 输出：
#   abc123 (head)
#   def456 (head)
```

合并：
```bash
alembic merge -m "merge xxx and yyy" abc123 def456
# 生成 003_merge_xxx_and_yyy.py
git add alembic/versions/
git commit -m "chore: alembic merge"
```

### 5. 生产环境上线前检查

- [ ] `alembic upgrade head` 在 staging 库跑通
- [ ] `alembic downgrade -1 && alembic upgrade head` 跑通（rollback 演练）
- [ ] 大表 ALTER 评估锁表时间（PostgreSQL 用 `EXPLAIN` 查执行计划）
- [ ] 生产前停服 / 灰度策略已沟通
- [ ] DBA 已审核 SQL（>50 万行表的迁移必须做）

## 与 init_db() 的关系

[`init_db()`](../app/models/database.py) 只在**全新空库**用 `Base.metadata.create_all` 拉起 schema。

老库 / 生产环境：**绝不能依赖 init_db**，必须用 alembic upgrade。否则：
- 已有数据被 silently 跳过（create_all 是 IF NOT EXISTS 行为）
- 字段类型 / 约束变更不会被同步
- 索引 / FK 不会更新

main.py 的 `init_db()` 调用建议生产环境改为 `alembic upgrade head`：

```python
# 生产环境推荐
import subprocess
subprocess.run(["alembic", "upgrade", "head"], check=True)
```

或者在 docker-entrypoint.sh 里跑：

```bash
#!/bin/sh
alembic upgrade head
exec uvicorn main:app --host 0.0.0.0 --port 8000
```

## 备份与回滚 SOP

1. **每次升级前必须备份**
   ```bash
   # SQLite
   cp anxinbao.db anxinbao.db.$(date +%Y%m%d_%H%M%S).bak

   # PostgreSQL
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **回滚顺序**（从严重到温和）：
   - 先 `alembic downgrade -1`（如果 downgrade 完整）
   - 再 `pg_restore`（数据完整性优先）
   - 最后 `git revert` migration 文件并重写

3. **绝对不要**：
   - 直接修改已 push 的 migration 文件（破坏链）
   - 在生产手 SQL `DROP COLUMN`（应走 alembic）
   - 跳版本（必须 head → head-1 → head-2 顺序回退）

---

> 当前 `alembic/versions/` 共 1 个迁移：`001_initial.py`。增量迁移积累后建议每季度回顾一次合并冗余 migration。
