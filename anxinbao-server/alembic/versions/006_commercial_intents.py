"""GMV 商业意图识别表（不卖商品先攒数据）

Revision ID: 006_commercial_intents
Revises: 005_user_onboarding_fields
Create Date: 2026-04-25

设计依据：MONETIZATION_BEYOND_SUBSCRIPTION.md A 层第 1 步
"先识别意图 + 标记，6 个月后看分布再决定 SKU 上架"
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "006_commercial_intents"
down_revision: Union[str, None] = "005_user_onboarding_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "commercial_intents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("intent_type", sa.String(40), nullable=False),
        sa.Column("raw_content", sa.String(500), nullable=False),
        sa.Column("matched_keywords", sa.String(200), nullable=True),
        sa.Column("confidence", sa.String(10), nullable=False, server_default="low"),
        sa.Column("suggested_sku", sa.String(200), nullable=True),
        sa.Column("suggested_action", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
        sa.Column("family_acted_at", sa.DateTime(), nullable=True),
        sa.Column("family_action_note", sa.String(500), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_intents_user_type_time", "commercial_intents",
                    ["user_id", "intent_type", "created_at"])
    op.create_index("idx_intents_user_status", "commercial_intents",
                    ["user_id", "status"])
    op.create_index("ix_commercial_intents_user_id", "commercial_intents", ["user_id"])
    op.create_index("ix_commercial_intents_intent_type", "commercial_intents", ["intent_type"])
    op.create_index("ix_commercial_intents_expires_at", "commercial_intents", ["expires_at"])
    op.create_index("ix_commercial_intents_created_at", "commercial_intents", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_commercial_intents_created_at", table_name="commercial_intents")
    op.drop_index("ix_commercial_intents_expires_at", table_name="commercial_intents")
    op.drop_index("ix_commercial_intents_intent_type", table_name="commercial_intents")
    op.drop_index("ix_commercial_intents_user_id", table_name="commercial_intents")
    op.drop_index("idx_intents_user_status", table_name="commercial_intents")
    op.drop_index("idx_intents_user_type_time", table_name="commercial_intents")
    op.drop_table("commercial_intents")
