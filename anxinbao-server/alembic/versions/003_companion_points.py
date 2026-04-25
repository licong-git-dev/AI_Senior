"""陪伴值养成系统两表（D30 留存抓手）

Revision ID: 003_companion_points
Revises: 002_family_accounts
Create Date: 2026-04-25

设计依据：PRODUCT_INSIGHTS.md Insight #3

无数据回填 —— 老人首次产生互动时由 service 懒创建 CompanionPoints 行。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003_companion_points"
down_revision: Union[str, None] = "002_family_accounts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companion_points",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lifetime_earned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lifetime_spent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_earned_at", sa.DateTime(), nullable=True),
        sa.Column("streak_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_streak_check_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_companion_points_user_id", "companion_points", ["user_id"], unique=True)

    op.create_table(
        "points_ledger",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("note", sa.String(200), nullable=True),
        sa.Column("related_object_type", sa.String(40), nullable=True),
        sa.Column("related_object_id", sa.String(100), nullable=True),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_points_ledger_user_time", "points_ledger", ["user_id", "created_at"])
    op.create_index("idx_points_ledger_user_type", "points_ledger", ["user_id", "type"])


def downgrade() -> None:
    op.drop_index("idx_points_ledger_user_type", table_name="points_ledger")
    op.drop_index("idx_points_ledger_user_time", table_name="points_ledger")
    op.drop_table("points_ledger")
    op.drop_index("ix_companion_points_user_id", table_name="companion_points")
    op.drop_table("companion_points")
