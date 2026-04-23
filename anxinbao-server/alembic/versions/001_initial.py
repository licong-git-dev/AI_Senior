"""初始化数据库表

Revision ID: 001_initial
Revises:
Create Date: 2024-01-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==================== 1. users ====================
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('device_id', sa.String(100), unique=True, nullable=True),
        sa.Column('dialect', sa.String(20), nullable=True, server_default='mandarin'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_device_id', 'users', ['device_id'])

    # ==================== 2. family_members (FK to users) ====================
    # Created early because user_auth.family_id references family_members.id
    op.create_table(
        'family_members',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('openid', sa.String(100), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_family_members_id', 'family_members', ['id'])

    # ==================== 3. user_auth (FK to users, family_members) ====================
    op.create_table(
        'user_auth',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='family'),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('family_id', sa.Integer(), sa.ForeignKey('family_members.id'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_user_auth_id', 'user_auth', ['id'])
    op.create_index('ix_user_auth_username', 'user_auth', ['username'])

    # ==================== 4. device_auth (FK to users) ====================
    op.create_table(
        'device_auth',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('device_id', sa.String(100), unique=True, nullable=False),
        sa.Column('device_secret', sa.String(255), nullable=False),
        sa.Column('device_type', sa.String(50), nullable=True, server_default='speaker'),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('last_active', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_device_auth_id', 'device_auth', ['id'])
    op.create_index('ix_device_auth_device_id', 'device_auth', ['device_id'])

    # ==================== 5. refresh_tokens (FK to user_auth, device_auth) ====================
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('token_hash', sa.String(255), unique=True, nullable=False),
        sa.Column('user_auth_id', sa.Integer(), sa.ForeignKey('user_auth.id'), nullable=True),
        sa.Column('device_auth_id', sa.Integer(), sa.ForeignKey('device_auth.id'), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_refresh_tokens_id', 'refresh_tokens', ['id'])
    op.create_index('ix_refresh_tokens_token_hash', 'refresh_tokens', ['token_hash'])
    op.create_index('idx_refresh_tokens_expires', 'refresh_tokens', ['expires_at'])

    # ==================== 6. audit_logs ====================
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.String(50), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource', sa.String(100), nullable=True),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, server_default='success'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_audit_logs_user_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('idx_audit_logs_created', 'audit_logs', ['created_at'])

    # ==================== 7. conversations (FK to users) ====================
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('role', sa.String(20), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True, server_default=sa.text('0')),
        sa.Column('category', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_conversations_id', 'conversations', ['id'])
    op.create_index('ix_conversations_session_id', 'conversations', ['session_id'])

    # ==================== 8. health_notifications (FK to users) ====================
    op.create_table(
        'health_notifications',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('conversation_summary', sa.Text(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('risk_reason', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('is_handled', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_health_notifications_id', 'health_notifications', ['id'])

    # ==================== 9. health_records (FK to users) ====================
    op.create_table(
        'health_records',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('record_type', sa.String(30), nullable=False),
        sa.Column('value_primary', sa.Float(), nullable=True),
        sa.Column('value_secondary', sa.Float(), nullable=True),
        sa.Column('value_tertiary', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(20), nullable=True),
        sa.Column('source', sa.String(20), nullable=True, server_default='manual'),
        sa.Column('device_id', sa.String(100), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('alert_level', sa.String(20), nullable=True, server_default='normal'),
        sa.Column('is_abnormal', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('measured_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_health_records_id', 'health_records', ['id'])
    op.create_index('ix_health_records_user_id', 'health_records', ['user_id'])
    op.create_index('ix_health_records_record_type', 'health_records', ['record_type'])
    op.create_index('ix_health_records_measured_at', 'health_records', ['measured_at'])
    op.create_index('idx_health_records_user_type', 'health_records', ['user_id', 'record_type'])
    op.create_index('idx_health_records_measured', 'health_records', ['measured_at'])

    # ==================== 10. health_alerts (FK to users, health_records) ====================
    op.create_table(
        'health_alerts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('record_id', sa.Integer(), sa.ForeignKey('health_records.id'), nullable=True),
        sa.Column('alert_type', sa.String(30), nullable=False),
        sa.Column('level', sa.String(20), nullable=False),
        sa.Column('title', sa.String(100), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('record_type', sa.String(30), nullable=True),
        sa.Column('record_value', sa.String(100), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('is_handled', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('handled_at', sa.DateTime(), nullable=True),
        sa.Column('handled_by', sa.String(50), nullable=True),
        sa.Column('handle_notes', sa.Text(), nullable=True),
        sa.Column('notified_family', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('notification_channels', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_health_alerts_id', 'health_alerts', ['id'])
    op.create_index('ix_health_alerts_user_id', 'health_alerts', ['user_id'])
    op.create_index('ix_health_alerts_created_at', 'health_alerts', ['created_at'])
    op.create_index('idx_health_alerts_user_level', 'health_alerts', ['user_id', 'level'])
    op.create_index('idx_health_alerts_status', 'health_alerts', ['is_handled', 'created_at'])

    # ==================== 11. health_reports (FK to users) ====================
    op.create_table(
        'health_reports',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('report_type', sa.String(20), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('overall_score', sa.Integer(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('stats_data', sa.Text(), nullable=True),
        sa.Column('is_sent', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_health_reports_id', 'health_reports', ['id'])
    op.create_index('ix_health_reports_user_id', 'health_reports', ['user_id'])
    op.create_index('idx_health_reports_user_type', 'health_reports', ['user_id', 'report_type'])

    # ==================== 12. medications (FK to users) ====================
    op.create_table(
        'medications',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('generic_name', sa.String(100), nullable=True),
        sa.Column('dosage', sa.String(50), nullable=False),
        sa.Column('medication_type', sa.String(30), nullable=True, server_default='tablet'),
        sa.Column('frequency', sa.String(30), nullable=False),
        sa.Column('times', sa.String(200), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('side_effects', sa.Text(), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('prescriber', sa.String(50), nullable=True),
        sa.Column('pharmacy', sa.String(100), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('low_stock_threshold', sa.Integer(), nullable=True, server_default=sa.text('7')),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_medications_id', 'medications', ['id'])
    op.create_index('ix_medications_user_id', 'medications', ['user_id'])
    op.create_index('idx_medications_user_active', 'medications', ['user_id', 'is_active'])

    # ==================== 13. medication_records (FK to users, medications) ====================
    op.create_table(
        'medication_records',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('medication_id', sa.Integer(), sa.ForeignKey('medications.id'), nullable=False),
        sa.Column('scheduled_time', sa.DateTime(), nullable=False),
        sa.Column('taken_time', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('skip_reason', sa.String(200), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('reminder_sent', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('reminder_count', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_medication_records_id', 'medication_records', ['id'])
    op.create_index('ix_medication_records_user_id', 'medication_records', ['user_id'])
    op.create_index('ix_medication_records_medication_id', 'medication_records', ['medication_id'])
    op.create_index('idx_medication_records_user_time', 'medication_records', ['user_id', 'scheduled_time'])
    op.create_index('idx_medication_records_status', 'medication_records', ['status', 'scheduled_time'])

    # ==================== 14. exercise_records (FK to users) ====================
    op.create_table(
        'exercise_records',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('exercise_type', sa.String(30), nullable=False),
        sa.Column('intensity', sa.String(20), nullable=True, server_default='moderate'),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('calories_burned', sa.Integer(), nullable=True),
        sa.Column('steps', sa.Integer(), nullable=True),
        sa.Column('distance_meters', sa.Integer(), nullable=True),
        sa.Column('heart_rate_avg', sa.Integer(), nullable=True),
        sa.Column('heart_rate_max', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('source', sa.String(20), nullable=True, server_default='manual'),
        sa.Column('device_id', sa.String(100), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_exercise_records_id', 'exercise_records', ['id'])
    op.create_index('ix_exercise_records_user_id', 'exercise_records', ['user_id'])
    op.create_index('idx_exercise_records_user_time', 'exercise_records', ['user_id', 'started_at'])

    # ==================== 15. exercise_plans (FK to users) ====================
    op.create_table(
        'exercise_plans',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('exercise_type', sa.String(30), nullable=False),
        sa.Column('target_duration_minutes', sa.Integer(), nullable=False),
        sa.Column('intensity', sa.String(20), nullable=True, server_default='moderate'),
        sa.Column('schedule_days', sa.String(50), nullable=True),
        sa.Column('schedule_time', sa.String(10), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('reminder_enabled', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('reminder_minutes_before', sa.Integer(), nullable=True, server_default=sa.text('15')),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_exercise_plans_id', 'exercise_plans', ['id'])
    op.create_index('ix_exercise_plans_user_id', 'exercise_plans', ['user_id'])

    # ==================== 16. meal_records (FK to users) ====================
    op.create_table(
        'meal_records',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('meal_type', sa.String(20), nullable=False),
        sa.Column('meal_time', sa.DateTime(), nullable=False),
        sa.Column('total_calories', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('total_carbohydrates', sa.Float(), nullable=True, server_default=sa.text('0')),
        sa.Column('total_protein', sa.Float(), nullable=True, server_default=sa.text('0')),
        sa.Column('total_fat', sa.Float(), nullable=True, server_default=sa.text('0')),
        sa.Column('total_fiber', sa.Float(), nullable=True, server_default=sa.text('0')),
        sa.Column('foods', sa.Text(), nullable=True),
        sa.Column('photo_url', sa.String(500), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_meal_records_id', 'meal_records', ['id'])
    op.create_index('ix_meal_records_user_id', 'meal_records', ['user_id'])
    op.create_index('idx_meal_records_user_time', 'meal_records', ['user_id', 'meal_time'])

    # ==================== 17. water_intake (FK to users) ====================
    op.create_table(
        'water_intake',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('amount_ml', sa.Integer(), nullable=False),
        sa.Column('beverage_type', sa.String(30), nullable=True, server_default='water'),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_water_intake_id', 'water_intake', ['id'])
    op.create_index('ix_water_intake_user_id', 'water_intake', ['user_id'])

    # ==================== 18. nutrition_targets (FK to users) ====================
    op.create_table(
        'nutrition_targets',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('daily_calories', sa.Integer(), nullable=True, server_default=sa.text('1800')),
        sa.Column('daily_carbohydrates', sa.Float(), nullable=True, server_default=sa.text('250')),
        sa.Column('daily_protein', sa.Float(), nullable=True, server_default=sa.text('60')),
        sa.Column('daily_fat', sa.Float(), nullable=True, server_default=sa.text('60')),
        sa.Column('daily_fiber', sa.Float(), nullable=True, server_default=sa.text('25')),
        sa.Column('daily_water_ml', sa.Integer(), nullable=True, server_default=sa.text('2000')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_nutrition_targets_id', 'nutrition_targets', ['id'])

    # ==================== 19. mood_records (FK to users) ====================
    op.create_table(
        'mood_records',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('mood_type', sa.String(20), nullable=False),
        sa.Column('intensity', sa.Integer(), nullable=True, server_default=sa.text('5')),
        sa.Column('triggers', sa.String(500), nullable=True),
        sa.Column('activities', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_mood_records_id', 'mood_records', ['id'])
    op.create_index('ix_mood_records_user_id', 'mood_records', ['user_id'])
    op.create_index('idx_mood_records_user_time', 'mood_records', ['user_id', 'recorded_at'])

    # ==================== 20. psych_assessments (FK to users) ====================
    op.create_table(
        'psych_assessments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('assessment_type', sa.String(30), nullable=False),
        sa.Column('total_score', sa.Integer(), nullable=False),
        sa.Column('max_score', sa.Integer(), nullable=False),
        sa.Column('severity_level', sa.String(30), nullable=True),
        sa.Column('answers', sa.Text(), nullable=True),
        sa.Column('interpretation', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_psych_assessments_id', 'psych_assessments', ['id'])
    op.create_index('ix_psych_assessments_user_id', 'psych_assessments', ['user_id'])
    op.create_index('idx_psych_assessments_user_type', 'psych_assessments', ['user_id', 'assessment_type'])

    # ==================== 21. sleep_records (FK to users) ====================
    op.create_table(
        'sleep_records',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('bedtime', sa.DateTime(), nullable=False),
        sa.Column('wake_time', sa.DateTime(), nullable=False),
        sa.Column('total_sleep_minutes', sa.Integer(), nullable=True),
        sa.Column('deep_sleep_minutes', sa.Integer(), nullable=True),
        sa.Column('light_sleep_minutes', sa.Integer(), nullable=True),
        sa.Column('rem_minutes', sa.Integer(), nullable=True),
        sa.Column('awake_times', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('quality', sa.String(20), nullable=True),
        sa.Column('quality_score', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(20), nullable=True, server_default='manual'),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_sleep_records_id', 'sleep_records', ['id'])
    op.create_index('ix_sleep_records_user_id', 'sleep_records', ['user_id'])
    op.create_index('idx_sleep_records_user_time', 'sleep_records', ['user_id', 'bedtime'])

    # ==================== 22. social_interactions (FK to users) ====================
    op.create_table(
        'social_interactions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('interaction_type', sa.String(30), nullable=False),
        sa.Column('participant_id', sa.Integer(), nullable=True),
        sa.Column('participant_name', sa.String(50), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('satisfaction_score', sa.Integer(), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('interaction_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_social_interactions_id', 'social_interactions', ['id'])
    op.create_index('ix_social_interactions_user_id', 'social_interactions', ['user_id'])

    # ==================== 23. message_conversations ====================
    op.create_table(
        'message_conversations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('conversation_type', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('avatar', sa.String(500), nullable=True),
        sa.Column('participant_ids', sa.Text(), nullable=False),
        sa.Column('last_message_id', sa.Integer(), nullable=True),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('last_message_preview', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_message_conversations_id', 'message_conversations', ['id'])

    # ==================== 24. messages (FK to message_conversations, self-ref) ====================
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('message_conversations.id'), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('message_type', sa.String(20), nullable=False, server_default='text'),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('media_url', sa.String(500), nullable=True),
        sa.Column('media_duration', sa.Integer(), nullable=True),
        sa.Column('media_size', sa.Integer(), nullable=True),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('reply_to_id', sa.Integer(), sa.ForeignKey('messages.id'), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, server_default='sent'),
        sa.Column('is_recalled', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('recalled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_messages_id', 'messages', ['id'])
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_sender_id', 'messages', ['sender_id'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])
    op.create_index('idx_messages_conversation_time', 'messages', ['conversation_id', 'created_at'])

    # ==================== 25. message_read_status (FK to message_conversations) ====================
    op.create_table(
        'message_read_status',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('message_conversations.id'), nullable=False),
        sa.Column('last_read_message_id', sa.Integer(), nullable=True),
        sa.Column('last_read_at', sa.DateTime(), nullable=True),
        sa.Column('unread_count', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('is_muted', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('is_pinned', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_message_read_status_id', 'message_read_status', ['id'])
    op.create_index('ix_message_read_status_user_id', 'message_read_status', ['user_id'])
    op.create_index('ix_message_read_status_conversation_id', 'message_read_status', ['conversation_id'])
    op.create_index('idx_message_read_user_conv', 'message_read_status', ['user_id', 'conversation_id'], unique=True)

    # ==================== 26. emergency_events (FK to users) ====================
    op.create_table(
        'emergency_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('emergency_type', sa.String(30), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default='high'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('trigger_source', sa.String(30), nullable=True, server_default='manual'),
        sa.Column('device_id', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='triggered'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(50), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('is_false_alarm', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('first_response_at', sa.DateTime(), nullable=True),
        sa.Column('response_time_seconds', sa.Integer(), nullable=True),
        sa.Column('triggered_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_emergency_events_id', 'emergency_events', ['id'])
    op.create_index('ix_emergency_events_user_id', 'emergency_events', ['user_id'])
    op.create_index('idx_emergency_events_user_status', 'emergency_events', ['user_id', 'status'])
    op.create_index('idx_emergency_events_time', 'emergency_events', ['triggered_at'])

    # ==================== 27. emergency_notifications (FK to emergency_events, family_members) ====================
    op.create_table(
        'emergency_notifications',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('emergency_events.id'), nullable=False),
        sa.Column('contact_id', sa.Integer(), sa.ForeignKey('family_members.id'), nullable=True),
        sa.Column('contact_name', sa.String(50), nullable=False),
        sa.Column('contact_phone', sa.String(20), nullable=False),
        sa.Column('notification_method', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('response_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_emergency_notifications_id', 'emergency_notifications', ['id'])
    op.create_index('ix_emergency_notifications_event_id', 'emergency_notifications', ['event_id'])

    # ==================== 28. emergency_contacts (FK to users) ====================
    op.create_table(
        'emergency_contacts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('relation_type', sa.String(30), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('notify_order', sa.Integer(), nullable=True, server_default=sa.text('1')),
        sa.Column('notification_enabled', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_emergency_contacts_id', 'emergency_contacts', ['id'])
    op.create_index('ix_emergency_contacts_user_id', 'emergency_contacts', ['user_id'])

    # ==================== 29. notifications ====================
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(30), nullable=False),
        sa.Column('priority', sa.String(20), nullable=True, server_default='normal'),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('data', sa.Text(), nullable=True),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('sent_channels', sa.String(100), nullable=True),
        sa.Column('delivery_status', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_notifications_id', 'notifications', ['id'])
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('idx_notifications_user_read', 'notifications', ['user_id', 'is_read'])
    op.create_index('idx_notifications_type', 'notifications', ['notification_type', 'created_at'])

    # ==================== 30. user_settings (FK to users) ====================
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('font_size', sa.String(20), nullable=True, server_default='large'),
        sa.Column('theme', sa.String(20), nullable=True, server_default='light'),
        sa.Column('language', sa.String(10), nullable=True, server_default='zh-CN'),
        sa.Column('voice_enabled', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('voice_speed', sa.Float(), nullable=True, server_default=sa.text('1.0')),
        sa.Column('voice_volume', sa.Float(), nullable=True, server_default=sa.text('1.0')),
        sa.Column('dialect', sa.String(20), nullable=True, server_default='mandarin'),
        sa.Column('notification_enabled', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('notification_sound', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('notification_vibrate', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('quiet_hours_start', sa.String(10), nullable=True),
        sa.Column('quiet_hours_end', sa.String(10), nullable=True),
        sa.Column('location_sharing', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('health_data_sharing', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_user_settings_id', 'user_settings', ['id'])

    # ==================== 31. proactive_greetings (FK to users) ====================
    op.create_table(
        'proactive_greetings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('greeting_type', sa.String(30), nullable=False),
        sa.Column('schedule_time', sa.String(10), nullable=False),
        sa.Column('schedule_days', sa.String(50), nullable=True, server_default='[1,2,3,4,5,6,7]'),
        sa.Column('greeting_template', sa.Text(), nullable=True),
        sa.Column('include_weather', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('include_health_tip', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('include_medication_reminder', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_proactive_greetings_id', 'proactive_greetings', ['id'])
    op.create_index('ix_proactive_greetings_user_id', 'proactive_greetings', ['user_id'])

    # ==================== 32. proactive_reminders (FK to users) ====================
    op.create_table(
        'proactive_reminders',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('reminder_type', sa.String(30), nullable=False),
        sa.Column('title', sa.String(100), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('trigger_type', sa.String(20), nullable=False),
        sa.Column('schedule_time', sa.String(10), nullable=True),
        sa.Column('interval_minutes', sa.Integer(), nullable=True),
        sa.Column('behavior_trigger', sa.String(50), nullable=True),
        sa.Column('min_interval_minutes', sa.Integer(), nullable=True, server_default=sa.text('60')),
        sa.Column('quiet_during_sleep', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('skip_if_interacted', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('trigger_count', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_proactive_reminders_id', 'proactive_reminders', ['id'])
    op.create_index('ix_proactive_reminders_user_id', 'proactive_reminders', ['user_id'])

    # ==================== 33. user_behavior_patterns (FK to users) ====================
    op.create_table(
        'user_behavior_patterns',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('pattern_type', sa.String(30), nullable=False),
        sa.Column('pattern_value', sa.String(100), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True, server_default=sa.text('0.5')),
        sa.Column('sample_count', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('last_occurrence', sa.DateTime(), nullable=True),
        sa.Column('stats_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_user_behavior_patterns_id', 'user_behavior_patterns', ['id'])
    op.create_index('ix_user_behavior_patterns_user_id', 'user_behavior_patterns', ['user_id'])
    op.create_index('idx_behavior_patterns_user_type', 'user_behavior_patterns', ['user_id', 'pattern_type'])

    # ==================== 34. proactive_interaction_logs (FK to users) ====================
    op.create_table(
        'proactive_interaction_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('interaction_type', sa.String(30), nullable=False),
        sa.Column('trigger_source', sa.String(30), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('user_response', sa.Text(), nullable=True),
        sa.Column('response_type', sa.String(20), nullable=True),
        sa.Column('triggered_at', sa.DateTime(), nullable=False),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_proactive_interaction_logs_id', 'proactive_interaction_logs', ['id'])
    op.create_index('ix_proactive_interaction_logs_user_id', 'proactive_interaction_logs', ['user_id'])
    op.create_index('idx_proactive_logs_user_time', 'proactive_interaction_logs', ['user_id', 'triggered_at'])

    # ==================== 35. user_profiles (FK to users) ====================
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('nickname', sa.String(50), nullable=True),
        sa.Column('birth_date', sa.DateTime(), nullable=True),
        sa.Column('zodiac', sa.String(20), nullable=True),
        sa.Column('constellation', sa.String(20), nullable=True),
        sa.Column('hometown', sa.String(100), nullable=True),
        sa.Column('current_city', sa.String(100), nullable=True),
        sa.Column('family_info', sa.Text(), nullable=True),
        sa.Column('hobbies', sa.Text(), nullable=True),
        sa.Column('favorite_music', sa.Text(), nullable=True),
        sa.Column('favorite_foods', sa.Text(), nullable=True),
        sa.Column('disliked_foods', sa.Text(), nullable=True),
        sa.Column('chronic_conditions', sa.Text(), nullable=True),
        sa.Column('allergies', sa.Text(), nullable=True),
        sa.Column('dietary_restrictions', sa.Text(), nullable=True),
        sa.Column('personality_traits', sa.Text(), nullable=True),
        sa.Column('communication_style', sa.String(30), nullable=True),
        sa.Column('preferred_topics', sa.Text(), nullable=True),
        sa.Column('ai_persona', sa.String(50), nullable=True, server_default='caring_companion'),
        sa.Column('response_speed', sa.String(20), nullable=True, server_default='normal'),
        sa.Column('verbosity', sa.String(20), nullable=True, server_default='moderate'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_user_profiles_id', 'user_profiles', ['id'])

    # ==================== 36. user_memories (FK to users) ====================
    op.create_table(
        'user_memories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('memory_type', sa.String(30), nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('source_conversation_id', sa.Integer(), nullable=True),
        sa.Column('extracted_at', sa.DateTime(), nullable=False),
        sa.Column('importance', sa.Integer(), nullable=True, server_default=sa.text('5')),
        sa.Column('confidence', sa.Float(), nullable=True, server_default=sa.text('0.8')),
        sa.Column('last_referenced_at', sa.DateTime(), nullable=True),
        sa.Column('reference_count', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('is_verified', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_user_memories_id', 'user_memories', ['id'])
    op.create_index('ix_user_memories_user_id', 'user_memories', ['user_id'])
    op.create_index('idx_user_memories_user_type', 'user_memories', ['user_id', 'memory_type'])
    op.create_index('idx_user_memories_key', 'user_memories', ['user_id', 'key'])

    # ==================== 37. important_dates (FK to users) ====================
    op.create_table(
        'important_dates',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('date_type', sa.String(30), nullable=False),
        sa.Column('title', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('day', sa.Integer(), nullable=False),
        sa.Column('is_lunar', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('reminder_days_before', sa.Integer(), nullable=True, server_default=sa.text('1')),
        sa.Column('reminder_enabled', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('related_person', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_important_dates_id', 'important_dates', ['id'])
    op.create_index('ix_important_dates_user_id', 'important_dates', ['user_id'])

    # ==================== 38. life_stories (FK to users) ====================
    op.create_table(
        'life_stories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(30), nullable=True),
        sa.Column('era', sa.String(50), nullable=True),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('related_people', sa.Text(), nullable=True),
        sa.Column('audio_url', sa.String(500), nullable=True),
        sa.Column('photo_urls', sa.Text(), nullable=True),
        sa.Column('emotion_tags', sa.Text(), nullable=True),
        sa.Column('source', sa.String(20), nullable=True, server_default='conversation'),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_life_stories_id', 'life_stories', ['id'])
    op.create_index('ix_life_stories_user_id', 'life_stories', ['user_id'])
    op.create_index('idx_life_stories_user_category', 'life_stories', ['user_id', 'category'])

    # ==================== 39. drug_info ====================
    op.create_table(
        'drug_info',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('generic_name', sa.String(100), nullable=True),
        sa.Column('brand_names', sa.Text(), nullable=True),
        sa.Column('barcode', sa.String(50), nullable=True),
        sa.Column('specification', sa.String(100), nullable=True),
        sa.Column('dosage_form', sa.String(30), nullable=True),
        sa.Column('manufacturer', sa.String(100), nullable=True),
        sa.Column('approval_number', sa.String(50), nullable=True),
        sa.Column('drug_category', sa.String(30), nullable=True),
        sa.Column('therapeutic_category', sa.String(100), nullable=True),
        sa.Column('indications', sa.Text(), nullable=True),
        sa.Column('dosage_instructions', sa.Text(), nullable=True),
        sa.Column('contraindications', sa.Text(), nullable=True),
        sa.Column('side_effects', sa.Text(), nullable=True),
        sa.Column('interactions', sa.Text(), nullable=True),
        sa.Column('precautions', sa.Text(), nullable=True),
        sa.Column('storage', sa.String(200), nullable=True),
        sa.Column('elderly_precautions', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_drug_info_id', 'drug_info', ['id'])
    op.create_index('ix_drug_info_name', 'drug_info', ['name'])
    op.create_index('ix_drug_info_barcode', 'drug_info', ['barcode'])
    op.create_index('idx_drug_info_name', 'drug_info', ['name'])
    op.create_index('idx_drug_info_generic', 'drug_info', ['generic_name'])

    # ==================== 40. drug_recognition_logs (FK to users, drug_info) ====================
    op.create_table(
        'drug_recognition_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('recognized_text', sa.Text(), nullable=True),
        sa.Column('barcode', sa.String(50), nullable=True),
        sa.Column('drug_info_id', sa.Integer(), sa.ForeignKey('drug_info.id'), nullable=True),
        sa.Column('matched_name', sa.String(100), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('manual_correction', sa.String(100), nullable=True),
        sa.Column('added_to_medication', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('medication_id', sa.Integer(), nullable=True),
        sa.Column('recognized_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_drug_recognition_logs_id', 'drug_recognition_logs', ['id'])
    op.create_index('ix_drug_recognition_logs_user_id', 'drug_recognition_logs', ['user_id'])
    op.create_index('idx_drug_recognition_user_time', 'drug_recognition_logs', ['user_id', 'recognized_at'])

    # ==================== 41. drug_interactions (FK to drug_info x2) ====================
    op.create_table(
        'drug_interactions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('drug_a_id', sa.Integer(), sa.ForeignKey('drug_info.id'), nullable=False),
        sa.Column('drug_b_id', sa.Integer(), sa.ForeignKey('drug_info.id'), nullable=False),
        sa.Column('interaction_type', sa.String(30), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_drug_interactions_id', 'drug_interactions', ['id'])
    op.create_index('idx_drug_interactions', 'drug_interactions', ['drug_a_id', 'drug_b_id'])

    # ==================== 42. cognitive_games ====================
    op.create_table(
        'cognitive_games',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('game_type', sa.String(30), nullable=False),
        sa.Column('difficulty_levels', sa.Integer(), nullable=True, server_default=sa.text('3')),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('benefits', sa.Text(), nullable=True),
        sa.Column('config', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_cognitive_games_id', 'cognitive_games', ['id'])

    # ==================== 43. cognitive_game_sessions (FK to users, cognitive_games) ====================
    op.create_table(
        'cognitive_game_sessions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('game_id', sa.Integer(), sa.ForeignKey('cognitive_games.id'), nullable=False),
        sa.Column('difficulty', sa.Integer(), nullable=True, server_default=sa.text('1')),
        sa.Column('score', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('max_score', sa.Integer(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('completion_time_seconds', sa.Integer(), nullable=True),
        sa.Column('game_data', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, server_default='completed'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_cognitive_game_sessions_id', 'cognitive_game_sessions', ['id'])
    op.create_index('ix_cognitive_game_sessions_user_id', 'cognitive_game_sessions', ['user_id'])
    op.create_index('idx_game_sessions_user_time', 'cognitive_game_sessions', ['user_id', 'started_at'])

    # ==================== 44. cognitive_assessments (FK to users) ====================
    op.create_table(
        'cognitive_assessments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('assessment_type', sa.String(30), nullable=False),
        sa.Column('assessment_date', sa.DateTime(), nullable=False),
        sa.Column('dimension_scores', sa.Text(), nullable=True),
        sa.Column('total_score', sa.Integer(), nullable=False),
        sa.Column('max_score', sa.Integer(), nullable=False),
        sa.Column('percentile', sa.Float(), nullable=True),
        sa.Column('cognitive_level', sa.String(30), nullable=True),
        sa.Column('trend', sa.String(20), nullable=True),
        sa.Column('raw_data', sa.Text(), nullable=True),
        sa.Column('analysis', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('notified_family', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('notification_level', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_cognitive_assessments_id', 'cognitive_assessments', ['id'])
    op.create_index('ix_cognitive_assessments_user_id', 'cognitive_assessments', ['user_id'])
    op.create_index('idx_cognitive_assessments_user_date', 'cognitive_assessments', ['user_id', 'assessment_date'])

    # ==================== 45. cognitive_training_plans (FK to users) ====================
    op.create_table(
        'cognitive_training_plans',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_dimensions', sa.Text(), nullable=True),
        sa.Column('weekly_sessions', sa.Integer(), nullable=True, server_default=sa.text('3')),
        sa.Column('session_duration_minutes', sa.Integer(), nullable=True, server_default=sa.text('15')),
        sa.Column('games_config', sa.Text(), nullable=True),
        sa.Column('schedule_days', sa.String(50), nullable=True),
        sa.Column('schedule_time', sa.String(10), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('reminder_enabled', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_cognitive_training_plans_id', 'cognitive_training_plans', ['id'])
    op.create_index('ix_cognitive_training_plans_user_id', 'cognitive_training_plans', ['user_id'])


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table('cognitive_training_plans')
    op.drop_table('cognitive_assessments')
    op.drop_table('cognitive_game_sessions')
    op.drop_table('cognitive_games')
    op.drop_table('drug_interactions')
    op.drop_table('drug_recognition_logs')
    op.drop_table('drug_info')
    op.drop_table('life_stories')
    op.drop_table('important_dates')
    op.drop_table('user_memories')
    op.drop_table('user_profiles')
    op.drop_table('proactive_interaction_logs')
    op.drop_table('user_behavior_patterns')
    op.drop_table('proactive_reminders')
    op.drop_table('proactive_greetings')
    op.drop_table('user_settings')
    op.drop_table('notifications')
    op.drop_table('emergency_contacts')
    op.drop_table('emergency_notifications')
    op.drop_table('emergency_events')
    op.drop_table('message_read_status')
    op.drop_table('messages')
    op.drop_table('message_conversations')
    op.drop_table('social_interactions')
    op.drop_table('sleep_records')
    op.drop_table('psych_assessments')
    op.drop_table('mood_records')
    op.drop_table('nutrition_targets')
    op.drop_table('water_intake')
    op.drop_table('meal_records')
    op.drop_table('exercise_plans')
    op.drop_table('exercise_records')
    op.drop_table('medication_records')
    op.drop_table('medications')
    op.drop_table('health_reports')
    op.drop_table('health_alerts')
    op.drop_table('health_records')
    op.drop_table('health_notifications')
    op.drop_table('conversations')
    op.drop_table('audit_logs')
    op.drop_table('refresh_tokens')
    op.drop_table('device_auth')
    op.drop_table('user_auth')
    op.drop_table('family_members')
    op.drop_table('users')
