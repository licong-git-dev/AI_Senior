"""老人个性化激活字段（前 3 分钟决定一切）

Revision ID: 005_user_onboarding_fields
Revises: 004_elder_voice_messages
Create Date: 2026-04-25

设计依据：PRODUCT_INSIGHTS_V2.md Insight #11 + ACTIVATION_FIRST_3_MIN.md

不破坏现有 User 字段，全部新增。downgrade 时只 drop 新字段。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "005_user_onboarding_fields"
down_revision: Union[str, None] = "004_elder_voice_messages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NEW_COLUMNS = [
    sa.Column("family_name", sa.String(20), nullable=True),
    sa.Column("addressed_as", sa.String(20), nullable=True),
    sa.Column("closest_child_name", sa.String(50), nullable=True),
    sa.Column("favorite_tv_show", sa.String(100), nullable=True),
    sa.Column("health_focus", sa.String(50), nullable=True),
    sa.Column("onboarded_at", sa.DateTime(), nullable=True),
    sa.Column("onboarding_d1_at", sa.DateTime(), nullable=True),
    sa.Column("onboarding_d3_at", sa.DateTime(), nullable=True),
    sa.Column("onboarding_d7_at", sa.DateTime(), nullable=True),
]


def upgrade() -> None:
    # SQLite 兼容：用 batch_alter_table（PostgreSQL 也支持）
    with op.batch_alter_table("users") as batch:
        for col in _NEW_COLUMNS:
            batch.add_column(col)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        for col in _NEW_COLUMNS:
            batch.drop_column(col.name)
