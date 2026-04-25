"""老人主动给子女留语音（破子女通知疲劳）

Revision ID: 004_elder_voice_messages
Revises: 003_companion_points
Create Date: 2026-04-25

设计依据：PRODUCT_INSIGHTS_V2.md Insight #12

无数据回填，懒创建。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004_elder_voice_messages"
down_revision: Union[str, None] = "003_companion_points"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "elder_voice_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("sender_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("recipient_user_auth_id", sa.Integer(), sa.ForeignKey("user_auth.id"), nullable=False),
        sa.Column("audio_url", sa.String(500), nullable=False),
        sa.Column("duration_sec", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("ai_caption", sa.String(200), nullable=True),
        sa.Column("emotion", sa.String(20), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("reply_voice_message_id", sa.Integer(),
                  sa.ForeignKey("elder_voice_messages.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_voice_msg_sender_time", "elder_voice_messages",
                    ["sender_user_id", "created_at"])
    op.create_index("idx_voice_msg_recipient_unread", "elder_voice_messages",
                    ["recipient_user_auth_id", "read_at"])


def downgrade() -> None:
    op.drop_index("idx_voice_msg_recipient_unread", table_name="elder_voice_messages")
    op.drop_index("idx_voice_msg_sender_time", table_name="elder_voice_messages")
    op.drop_table("elder_voice_messages")
