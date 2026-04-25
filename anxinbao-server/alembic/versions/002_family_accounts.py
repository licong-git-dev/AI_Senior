"""家庭账户三表（解耦付费者≠使用者悖论）

Revision ID: 002_family_accounts
Revises: 001_initial
Create Date: 2026-04-25

设计依据：PRODUCT_INSIGHTS.md Insight #1
- family_accounts: 计费/订阅主体
- family_account_members: 多对多（一户多家属共关注一老人）
- family_account_invites: 邀请链路（payer 邀请其他成员）

回填策略（数据迁移）：
- 每个现有 UserAuth(role=family) 自动创建一个 solo FamilyAccount
- payer/caretaker 角色都设给该 user_auth
- beneficiary 关联到对应 user_id（如有）
- 这样订阅迁移（r19 计划）只要把 subscription.user_auth_id → family_account_id 即可
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002_family_accounts"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==================== family_accounts ====================
    op.create_table(
        "family_accounts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("account_name", sa.String(100), nullable=False, server_default="未命名家庭"),
        sa.Column("beneficiary_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("primary_payer_user_auth_id", sa.Integer(), sa.ForeignKey("user_auth.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_family_accounts_beneficiary", "family_accounts", ["beneficiary_user_id"])
    op.create_index("idx_family_accounts_payer", "family_accounts", ["primary_payer_user_auth_id"])

    # ==================== family_account_members ====================
    op.create_table(
        "family_account_members",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("family_account_id", sa.Integer(), sa.ForeignKey("family_accounts.id"), nullable=False),
        sa.Column("user_auth_id", sa.Integer(), sa.ForeignKey("user_auth.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="caretaker"),
        sa.Column("permission_level", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("invited_by_user_auth_id", sa.Integer(), sa.ForeignKey("user_auth.id"), nullable=True),
        sa.Column("joined_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "idx_family_members_unique",
        "family_account_members",
        ["family_account_id", "user_auth_id"],
        unique=True,
    )
    op.create_index(
        "idx_family_members_role",
        "family_account_members",
        ["family_account_id", "role"],
    )

    # ==================== family_account_invites ====================
    op.create_table(
        "family_account_invites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("invite_code", sa.String(16), nullable=False, unique=True),
        sa.Column("family_account_id", sa.Integer(), sa.ForeignKey("family_accounts.id"), nullable=False),
        sa.Column("invited_role", sa.String(20), nullable=False, server_default="caretaker"),
        sa.Column("inviter_user_auth_id", sa.Integer(), sa.ForeignKey("user_auth.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("used_by_user_auth_id", sa.Integer(), sa.ForeignKey("user_auth.id"), nullable=True),
        sa.Column("note", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "idx_family_account_invites_active",
        "family_account_invites",
        ["family_account_id", "expires_at"],
    )

    # ==================== 回填：每个现有 family role UserAuth 创建 solo 账户 ====================
    # 注意：家属端账号 UserAuth.role='family' 才需要建账户；老人/管理员/设备 跳过
    conn = op.get_bind()
    family_auths = conn.execute(sa.text(
        "SELECT id, family_id, username FROM user_auth WHERE role = 'family'"
    )).fetchall()

    for row in family_auths:
        ua_id, family_id, username = row[0], row[1], row[2]
        # 找到老人 user_id（通过 family_members 表）
        bene_user_id = None
        if family_id:
            bene = conn.execute(sa.text(
                "SELECT user_id FROM family_members WHERE id = :fid"
            ), {"fid": family_id}).fetchone()
            if bene:
                bene_user_id = bene[0]

        # 创建 family_account
        result = conn.execute(sa.text(
            """INSERT INTO family_accounts
               (account_name, beneficiary_user_id, primary_payer_user_auth_id, status)
               VALUES (:name, :bene, :payer, 'active')"""
        ), {
            "name": f"{username}的家庭",
            "bene": bene_user_id,
            "payer": ua_id,
        })
        # 拿回新插入的 id（兼容 SQLite 与 PostgreSQL）
        fa_id = result.lastrowid if hasattr(result, "lastrowid") else None
        if fa_id is None:
            fa_id = conn.execute(sa.text(
                "SELECT id FROM family_accounts WHERE primary_payer_user_auth_id = :p ORDER BY id DESC LIMIT 1"
            ), {"p": ua_id}).fetchone()[0]

        # 写一行 member（同一 user_auth 既是 payer 也是 caretaker）
        conn.execute(sa.text(
            """INSERT INTO family_account_members
               (family_account_id, user_auth_id, role, permission_level)
               VALUES (:fa, :ua, 'payer', 5)"""
        ), {"fa": fa_id, "ua": ua_id})


def downgrade() -> None:
    op.drop_index("idx_family_account_invites_active", table_name="family_account_invites")
    op.drop_table("family_account_invites")

    op.drop_index("idx_family_members_role", table_name="family_account_members")
    op.drop_index("idx_family_members_unique", table_name="family_account_members")
    op.drop_table("family_account_members")

    op.drop_index("idx_family_accounts_payer", table_name="family_accounts")
    op.drop_index("idx_family_accounts_beneficiary", table_name="family_accounts")
    op.drop_table("family_accounts")
