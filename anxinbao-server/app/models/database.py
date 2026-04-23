"""
数据库模型
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

from app.core.config import get_settings

settings = get_settings()

# 根据数据库类型配置引擎参数
if settings.database_url.startswith("sqlite"):
    # SQLite配置
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL/MySQL等生产数据库配置
    engine = create_engine(
        settings.database_url,
        pool_size=10,  # 连接池大小
        max_overflow=20,  # 最大溢出连接数
        pool_timeout=30,  # 获取连接的超时时间（秒）
        pool_pre_ping=True,  # 连接前ping检查
        pool_recycle=1800,  # 连接回收时间（秒），避免数据库主动断开空闲连接
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserAuth(Base):
    """用户认证表（存储登录凭据）"""
    __tablename__ = "user_auth"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)  # 用户名/手机号
    password_hash = Column(String(255), nullable=False)  # 密码哈希
    role = Column(String(20), nullable=False, default="family")  # 角色：elder/family/admin
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # 关联的老人ID（老人端）
    family_id = Column(Integer, ForeignKey("family_members.id"), nullable=True)  # 关联的家属ID（家属端）
    is_active = Column(Boolean, default=True)  # 是否激活
    last_login = Column(DateTime, nullable=True)  # 最后登录时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DeviceAuth(Base):
    """设备认证表（音箱等设备）"""
    __tablename__ = "device_auth"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, index=True, nullable=False)  # 设备唯一标识
    device_secret = Column(String(255), nullable=False)  # 设备密钥（哈希后存储）
    device_type = Column(String(50), default="speaker")  # 设备类型：speaker/tablet/watch
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # 绑定的老人ID
    is_active = Column(Boolean, default=True)  # 是否激活
    last_active = Column(DateTime, nullable=True)  # 最后活跃时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = relationship("User", back_populates="devices")


class RefreshToken(Base):
    """刷新令牌表（用于令牌管理和撤销）"""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(255), unique=True, index=True, nullable=False)  # 令牌哈希
    user_auth_id = Column(Integer, ForeignKey("user_auth.id"), nullable=True)
    device_auth_id = Column(Integer, ForeignKey("device_auth.id"), nullable=True)
    expires_at = Column(DateTime, nullable=False)  # 过期时间
    is_revoked = Column(Boolean, default=False)  # 是否已撤销
    created_at = Column(DateTime, default=datetime.now)

    # 索引：用于清理过期令牌
    __table_args__ = (
        Index("idx_refresh_tokens_expires", "expires_at"),
    )


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=True)  # 用户ID
    action = Column(String(100), nullable=False)  # 操作类型
    resource = Column(String(100), nullable=True)  # 资源类型
    resource_id = Column(String(100), nullable=True)  # 资源ID
    ip_address = Column(String(50), nullable=True)  # IP地址
    user_agent = Column(String(500), nullable=True)  # 用户代理
    details = Column(Text, nullable=True)  # 详细信息（JSON）
    status = Column(String(20), default="success")  # 状态：success/failure
    created_at = Column(DateTime, default=datetime.now, index=True)

    # 索引：用于查询和清理
    __table_args__ = (
        Index("idx_audit_logs_user_action", 'user_id', "action"),
        Index("idx_audit_logs_created", "created_at"),
    )


class User(Base):
    """用户表（老人）"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)  # 称呼
    device_id = Column(String(100), unique=True, index=True)  # 设备ID（已弃用，使用DeviceAuth）
    dialect = Column(String(20), default="mandarin")  # 方言偏好
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    conversations = relationship("Conversation", back_populates="user")
    family_members = relationship("FamilyMember", back_populates="user")
    devices = relationship("DeviceAuth", back_populates="user")


class FamilyMember(Base):
    """家属表（子女）"""
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20))
    openid = Column(String(100))  # 微信OpenID，用于推送
    is_primary = Column(Boolean, default=False)  # 是否主要联系人
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", back_populates="family_members")


class FamilyBindingInvite(Base):
    """家庭绑定邀请码持久化表"""
    __tablename__ = "family_binding_invites"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(100), unique=True, index=True, nullable=False)
    invite_code = Column(String(20), unique=True, index=True, nullable=False)
    group_id = Column(String(100), index=True, nullable=False)
    requester_id = Column(Integer, nullable=False, index=True)
    requester_name = Column(String(50), nullable=False)
    target_id = Column(Integer, default=0, index=True)
    relationship = Column(String(50), nullable=False)
    role = Column(String(30), nullable=False)
    permission_level = Column(Integer, nullable=False, default=3)
    status = Column(String(20), nullable=False, default="pending", index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_family_invites_code_status", "invite_code", "status"),
        Index("idx_family_invites_group_status", "group_id", "status"),
    )


class Conversation(Base):
    """对话记录表"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    session_id = Column(String(100), index=True)  # 会话ID
    role = Column(String(20))  # user/assistant
    content = Column(Text)
    risk_score = Column(Float, default=0)
    category = Column(String(20))  # health/daily/chat
    created_at = Column(DateTime, default=datetime.now, index=True)

    # 关系
    user = relationship("User", back_populates="conversations")

    __table_args__ = (
        Index("idx_conversations_user_session", 'user_id', "session_id"),
        Index("idx_conversations_user_created", 'user_id', "created_at"),
    )


class HealthNotification(Base):
    """健康通知表"""
    __tablename__ = "health_notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    conversation_summary = Column(Text)  # 对话摘要
    risk_score = Column(Float)
    risk_reason = Column(Text)
    is_read = Column(Boolean, default=False)
    is_handled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now, index=True)

    __table_args__ = (
        Index("idx_health_notifications_user_read", 'user_id', "is_read"),
    )


# ==================== 健康数据模型 ====================

class HealthRecord(Base):
    """健康记录表 - 存储各类生命体征数据"""
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    record_type = Column(String(30), nullable=False, index=True)  # blood_pressure/heart_rate/blood_sugar/blood_oxygen/temperature/weight

    # 通用数值字段
    value_primary = Column(Float, nullable=True)  # 主数值（如收缩压、心率、血糖值）
    value_secondary = Column(Float, nullable=True)  # 次数值（如舒张压）
    value_tertiary = Column(Float, nullable=True)  # 第三数值（如脉搏）
    unit = Column(String(20), nullable=True)  # 单位

    # 元数据
    source = Column(String(20), default="manual")  # manual/device/import
    device_id = Column(String(100), nullable=True)  # 采集设备ID
    notes = Column(String(500), nullable=True)  # 备注

    # 评估结果
    alert_level = Column(String(20), default="normal")  # normal/low/medium/high/critical
    is_abnormal = Column(Boolean, default=False)  # 是否异常

    measured_at = Column(DateTime, nullable=False, index=True)  # 测量时间
    created_at = Column(DateTime, default=datetime.now)

    # 索引
    __table_args__ = (
        Index("idx_health_records_user_type", 'user_id', "record_type"),
        Index("idx_health_records_measured", 'measured_at'),
    )

    # 关系
    user = relationship("User", backref="health_records")


class HealthAlert(Base):
    """健康告警表"""
    __tablename__ = "health_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    record_id = Column(Integer, ForeignKey("health_records.id"), nullable=True)

    alert_type = Column(String(30), nullable=False)  # blood_pressure_high/heart_rate_abnormal/etc
    level = Column(String(20), nullable=False)  # low/medium/high/critical
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=True)

    # 关联数据
    record_type = Column(String(30), nullable=True)
    record_value = Column(String(100), nullable=True)  # JSON格式的数值

    # 状态
    is_read = Column(Boolean, default=False)
    is_handled = Column(Boolean, default=False)
    handled_at = Column(DateTime, nullable=True)
    handled_by = Column(String(50), nullable=True)  # 处理人
    handle_notes = Column(Text, nullable=True)  # 处理备注

    # 通知状态
    notified_family = Column(Boolean, default=False)
    notification_channels = Column(String(100), nullable=True)  # push,sms,call

    created_at = Column(DateTime, default=datetime.now, index=True)

    # 索引
    __table_args__ = (
        Index("idx_health_alerts_user_level", 'user_id', "level"),
        Index("idx_health_alerts_status", 'is_handled', "created_at"),
    )


class HealthReport(Base):
    """健康报告表"""
    __tablename__ = "health_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    report_type = Column(String(20), nullable=False)  # daily/weekly/monthly
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # 评分和摘要
    overall_score = Column(Integer, nullable=True)  # 0-100
    summary = Column(Text, nullable=True)  # 报告摘要
    recommendations = Column(Text, nullable=True)  # 建议（JSON数组）

    # 统计数据
    stats_data = Column(Text, nullable=True)  # JSON格式的统计数据

    # 状态
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_health_reports_user_type", 'user_id', "report_type"),
    )


# ==================== 用药管理模型 ====================

class Medication(Base):
    """药物信息表"""
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String(100), nullable=False)  # 药物名称
    generic_name = Column(String(100), nullable=True)  # 通用名
    dosage = Column(String(50), nullable=False)  # 剂量，如'1片'、'5ml'
    medication_type = Column(String(30), default="tablet")  # tablet/capsule/liquid/injection/topical

    # 服用安排
    frequency = Column(String(30), nullable=False)  # once_daily/twice_daily/three_times_daily/as_needed
    times = Column(String(200), nullable=True)  # JSON数组：['08:00', '12:00', '18:00']

    # 说明
    instructions = Column(Text, nullable=True)  # 服用说明
    side_effects = Column(Text, nullable=True)  # 副作用说明
    notes = Column(String(500), nullable=True)  # 备注

    # 来源信息
    prescriber = Column(String(50), nullable=True)  # 开药医生
    pharmacy = Column(String(100), nullable=True)  # 购药药店

    # 库存
    quantity = Column(Integer, default=0)  # 当前库存
    low_stock_threshold = Column(Integer, default=7)  # 低库存阈值

    # 时间范围
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)  # 空表示长期服用

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = relationship("User", backref="medications")
    records = relationship("MedicationRecord", back_populates="medication")

    __table_args__ = (
        Index("idx_medications_user_active", 'user_id', "is_active"),
    )


class MedicationRecord(Base):
    """服药记录表"""
    __tablename__ = "medication_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False, index=True)

    scheduled_time = Column(DateTime, nullable=False)  # 计划服药时间
    taken_time = Column(DateTime, nullable=True)  # 实际服药时间

    status = Column(String(20), nullable=False, default="pending")  # pending/taken/missed/skipped
    skip_reason = Column(String(200), nullable=True)  # 跳过原因
    notes = Column(String(500), nullable=True)

    # 提醒状态
    reminder_sent = Column(Boolean, default=False)
    reminder_count = Column(Integer, default=0)  # 提醒次数

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    medication = relationship("Medication", back_populates="records")

    __table_args__ = (
        Index("idx_medication_records_user_time", 'user_id', "scheduled_time"),
        Index("idx_medication_records_status", 'status', "scheduled_time"),
    )


# ==================== 运动管理模型 ====================

class ExerciseRecord(Base):
    """运动记录表"""
    __tablename__ = "exercise_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    exercise_type = Column(String(30), nullable=False)  # walking/running/tai_chi/yoga/stretching/rehabilitation
    intensity = Column(String(20), default="moderate")  # light/moderate/vigorous

    # 运动数据
    duration_minutes = Column(Integer, nullable=False)  # 持续时间（分钟）
    calories_burned = Column(Integer, nullable=True)  # 消耗卡路里
    steps = Column(Integer, nullable=True)  # 步数
    distance_meters = Column(Integer, nullable=True)  # 距离（米）

    # 心率数据
    heart_rate_avg = Column(Integer, nullable=True)
    heart_rate_max = Column(Integer, nullable=True)

    # 时间
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)

    # 来源
    source = Column(String(20), default="manual")  # manual/device/app
    device_id = Column(String(100), nullable=True)

    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", backref="exercise_records")

    __table_args__ = (
        Index("idx_exercise_records_user_time", 'user_id', "started_at"),
    )


class ExercisePlan(Base):
    """运动计划表"""
    __tablename__ = "exercise_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    exercise_type = Column(String(30), nullable=False)

    target_duration_minutes = Column(Integer, nullable=False)
    intensity = Column(String(20), default="moderate")

    # 时间安排
    schedule_days = Column(String(50), nullable=True)  # JSON数组：[1,3,5] 表示周一三五
    schedule_time = Column(String(10), nullable=True)  # '08:00'

    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)

    # 提醒设置
    reminder_enabled = Column(Boolean, default=True)
    reminder_minutes_before = Column(Integer, default=15)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = relationship("User", backref="exercise_plans")


# ==================== 营养管理模型 ====================

class MealRecord(Base):
    """饮食记录表"""
    __tablename__ = "meal_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    meal_type = Column(String(20), nullable=False)  # breakfast/lunch/dinner/snack
    meal_time = Column(DateTime, nullable=False)

    # 营养数据
    total_calories = Column(Integer, default=0)
    total_carbohydrates = Column(Float, default=0)  # 克
    total_protein = Column(Float, default=0)  # 克
    total_fat = Column(Float, default=0)  # 克
    total_fiber = Column(Float, default=0)  # 克

    # 食物列表（JSON数组）
    foods = Column(Text, nullable=True)  # [{'name': '米饭', 'amount': '1碗', 'calories': 200}]

    photo_url = Column(String(500), nullable=True)
    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", backref="meal_records")

    __table_args__ = (
        Index("idx_meal_records_user_time", 'user_id', "meal_time"),
    )


class WaterIntake(Base):
    """饮水记录表"""
    __tablename__ = "water_intake"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    amount_ml = Column(Integer, nullable=False)  # 饮水量（毫升）
    beverage_type = Column(String(30), default="water")  # water/tea/coffee/juice

    recorded_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", backref="water_intakes")

    __table_args__ = (
        Index("idx_water_intake_user_time", 'user_id', "recorded_at"),
    )


class NutritionTarget(Base):
    """营养目标表"""
    __tablename__ = "nutrition_targets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    daily_calories = Column(Integer, default=1800)
    daily_carbohydrates = Column(Float, default=250)  # 克
    daily_protein = Column(Float, default=60)  # 克
    daily_fat = Column(Float, default=60)  # 克
    daily_fiber = Column(Float, default=25)  # 克
    daily_water_ml = Column(Integer, default=2000)  # 毫升

    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = relationship("User", backref="nutrition_target", uselist=False)


# ==================== 心理健康模型 ====================

class MoodRecord(Base):
    """心情记录表"""
    __tablename__ = "mood_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    mood_type = Column(String(20), nullable=False)  # happy/calm/neutral/tired/anxious/sad/angry/lonely
    intensity = Column(Integer, default=5)  # 1-10

    triggers = Column(String(500), nullable=True)  # JSON数组：触发因素
    activities = Column(String(500), nullable=True)  # JSON数组：相关活动
    notes = Column(Text, nullable=True)

    recorded_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", backref="mood_records")

    __table_args__ = (
        Index("idx_mood_records_user_time", 'user_id', "recorded_at"),
    )


class PsychAssessment(Base):
    """心理评估记录表"""
    __tablename__ = "psych_assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    assessment_type = Column(String(30), nullable=False)  # phq9/gad7/loneliness/sleep_quality

    total_score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    severity_level = Column(String(30), nullable=True)  # minimal/mild/moderate/moderately_severe/severe

    answers = Column(Text, nullable=True)  # JSON格式的答案
    interpretation = Column(Text, nullable=True)  # 解读
    recommendations = Column(Text, nullable=True)  # JSON数组：建议

    completed_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", backref="psych_assessments")

    __table_args__ = (
        Index("idx_psych_assessments_user_type", 'user_id', "assessment_type"),
    )


class SleepRecord(Base):
    """睡眠记录表"""
    __tablename__ = "sleep_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    bedtime = Column(DateTime, nullable=False)  # 入睡时间
    wake_time = Column(DateTime, nullable=False)  # 起床时间

    total_sleep_minutes = Column(Integer, nullable=True)  # 总睡眠时长
    deep_sleep_minutes = Column(Integer, nullable=True)  # 深睡时长
    light_sleep_minutes = Column(Integer, nullable=True)  # 浅睡时长
    rem_minutes = Column(Integer, nullable=True)  # REM时长

    awake_times = Column(Integer, default=0)  # 夜醒次数
    quality = Column(String(20), nullable=True)  # very_poor/poor/fair/good/excellent
    quality_score = Column(Integer, nullable=True)  # 0-100

    source = Column(String(20), default="manual")  # manual/device
    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", backref="sleep_records")

    __table_args__ = (
        Index("idx_sleep_records_user_time", 'user_id', "bedtime"),
    )


# ==================== 社交互动模型 ====================

class SocialInteraction(Base):
    """社交互动记录表"""
    __tablename__ = "social_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    interaction_type = Column(String(30), nullable=False)  # family_call/video_call/message/visit/community_activity

    # 参与者
    participant_id = Column(Integer, nullable=True)  # 家属ID或其他用户ID
    participant_name = Column(String(50), nullable=True)

    duration_minutes = Column(Integer, nullable=True)  # 持续时间
    satisfaction_score = Column(Integer, nullable=True)  # 1-5满意度

    notes = Column(String(500), nullable=True)

    interaction_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", backref="social_interactions")

    __table_args__ = (
        Index("idx_social_interactions_user_time", 'user_id', "interaction_at"),
    )


# ==================== 消息模型 ====================

class MessageConversation(Base):
    """消息会话表"""
    __tablename__ = "message_conversations"

    id = Column(Integer, primary_key=True, index=True)

    conversation_type = Column(String(20), nullable=False)  # private/group/system
    name = Column(String(100), nullable=True)  # 群聊名称
    avatar = Column(String(500), nullable=True)

    # 参与者（JSON数组）
    participant_ids = Column(Text, nullable=False)  # [1, 2, 3]

    # 最后消息
    last_message_id = Column(Integer, nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    last_message_preview = Column(String(200), nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """消息表"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("message_conversations.id"), nullable=False, index=True)
    sender_id = Column(Integer, nullable=False, index=True)  # 发送者用户ID

    message_type = Column(String(20), nullable=False, default="text")  # text/image/voice/video/file/location
    content = Column(Text, nullable=True)  # 文本内容

    # 媒体信息
    media_url = Column(String(500), nullable=True)
    media_duration = Column(Integer, nullable=True)  # 语音/视频时长（秒）
    media_size = Column(Integer, nullable=True)  # 文件大小（字节）
    thumbnail_url = Column(String(500), nullable=True)  # 缩略图

    # 回复
    reply_to_id = Column(Integer, ForeignKey("messages.id"), nullable=True)

    # 状态
    status = Column(String(20), default="sent")  # sending/sent/delivered/read/failed
    is_recalled = Column(Boolean, default=False)
    recalled_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.now, index=True)

    # 关系
    conversation = relationship("MessageConversation", back_populates="messages")

    __table_args__ = (
        Index("idx_messages_conversation_time", 'conversation_id', "created_at"),
    )


class MessageReadStatus(Base):
    """消息已读状态表"""
    __tablename__ = "message_read_status"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("message_conversations.id"), nullable=False, index=True)

    last_read_message_id = Column(Integer, nullable=True)
    last_read_at = Column(DateTime, nullable=True)
    unread_count = Column(Integer, default=0)

    is_muted = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)

    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_message_read_user_conv", 'user_id', "conversation_id", unique=True),
    )


# ==================== 紧急服务模型 ====================

class EmergencyEvent(Base):
    """紧急事件表"""
    __tablename__ = "emergency_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    emergency_type = Column(String(30), nullable=False)  # fall/health_crisis/distress/fire/intrusion/gas_leak
    severity = Column(String(20), nullable=False, default="high")  # low/medium/high/critical

    description = Column(Text, nullable=True)

    # 位置信息
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(String(500), nullable=True)

    # 触发信息
    trigger_source = Column(String(30), default="manual")  # manual/device/fall_detection/health_alert
    device_id = Column(String(100), nullable=True)

    # 状态
    status = Column(String(20), nullable=False, default="triggered")  # triggered/notifying/responding/resolved/false_alarm/cancelled

    # 处理信息
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(50), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    is_false_alarm = Column(Boolean, default=False)

    # 响应时间
    first_response_at = Column(DateTime, nullable=True)
    response_time_seconds = Column(Integer, nullable=True)

    triggered_at = Column(DateTime, nullable=False, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", backref="emergency_events")
    notifications = relationship("EmergencyNotification", back_populates="event")

    __table_args__ = (
        Index("idx_emergency_events_user_status", 'user_id', "status"),
        Index("idx_emergency_events_time", 'triggered_at'),
    )


class EmergencyNotification(Base):
    """紧急通知记录表"""
    __tablename__ = "emergency_notifications"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("emergency_events.id"), nullable=False, index=True)

    contact_id = Column(Integer, ForeignKey("family_members.id"), nullable=True)
    contact_name = Column(String(50), nullable=False)
    contact_phone = Column(String(20), nullable=False)

    notification_method = Column(String(20), nullable=False)  # push/sms/call

    # 状态
    status = Column(String(20), nullable=False, default="pending")  # pending/sent/delivered/failed/answered
    error_message = Column(String(500), nullable=True)

    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    response_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.now)

    # 关系
    event = relationship("EmergencyEvent", back_populates="notifications")


class EmergencyContact(Base):
    """紧急联系人表（扩展家属表）"""
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    relation_type = Column(String(30), nullable=True)  # 关系：子女/配偶/邻居/社区

    is_primary = Column(Boolean, default=False)
    notify_order = Column(Integer, default=1)  # 通知顺序

    notification_enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # ORM关系
    user = relationship("User", backref="emergency_contacts")


# ==================== 通知模型 ====================

class Notification(Base):
    """通知表"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # 接收者用户ID

    notification_type = Column(String(30), nullable=False)  # system/health_alert/medication/emergency/family/device
    priority = Column(String(20), default="normal")  # low/normal/high/urgent

    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)

    # 附加数据
    data = Column(Text, nullable=True)  # JSON格式
    action_url = Column(String(500), nullable=True)

    # 状态
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)

    # 发送状态
    sent_channels = Column(String(100), nullable=True)  # push,sms,email
    delivery_status = Column(Text, nullable=True)  # JSON格式

    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)

    __table_args__ = (
        Index("idx_notifications_user_read", 'user_id', "is_read"),
        Index("idx_notifications_type", 'notification_type', "created_at"),
    )


# ==================== 设置模型 ====================

class UserSettings(Base):
    """用户设置表"""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # 显示设置
    font_size = Column(String(20), default="large")  # small/medium/large/xlarge
    theme = Column(String(20), default="light")  # light/dark/auto
    language = Column(String(10), default='zh-CN')

    # 语音设置
    voice_enabled = Column(Boolean, default=True)
    voice_speed = Column(Float, default=1.0)  # 0.5-2.0
    voice_volume = Column(Float, default=1.0)  # 0-1
    dialect = Column(String(20), default="mandarin")

    # 通知设置
    notification_enabled = Column(Boolean, default=True)
    notification_sound = Column(Boolean, default=True)
    notification_vibrate = Column(Boolean, default=True)
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(10), nullable=True)  # '22:00'
    quiet_hours_end = Column(String(10), nullable=True)  # '07:00'

    # 隐私设置
    location_sharing = Column(Boolean, default=True)
    health_data_sharing = Column(Boolean, default=True)

    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = relationship("User", backref="settings", uselist=False)


# ==================== 主动交互系统模型 ====================

class ProactiveGreeting(Base):
    """主动问候配置表"""
    __tablename__ = "proactive_greetings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    greeting_type = Column(String(30), nullable=False)  # morning/afternoon/evening/health_check/care
    schedule_time = Column(String(10), nullable=False)  # '08:00'
    schedule_days = Column(String(50), default="[1,2,3,4,5,6,7]")  # JSON数组，周几

    # 问候内容模板
    greeting_template = Column(Text, nullable=True)  # 自定义问候语模板
    include_weather = Column(Boolean, default=True)  # 是否包含天气
    include_health_tip = Column(Boolean, default=True)  # 是否包含健康提示
    include_medication_reminder = Column(Boolean, default=True)  # 是否包含用药提醒

    is_enabled = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = relationship("User", backref="proactive_greetings")


class ProactiveReminder(Base):
    """主动提醒表"""
    __tablename__ = "proactive_reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    reminder_type = Column(String(30), nullable=False)  # water/stand_up/exercise/rest/medication/custom
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=True)

    # 触发条件
    trigger_type = Column(String(20), nullable=False)  # time_based/interval/behavior_based
    schedule_time = Column(String(10), nullable=True)  # 定时触发 '14:00'
    interval_minutes = Column(Integer, nullable=True)  # 间隔触发（分钟）
    behavior_trigger = Column(String(50), nullable=True)  # 行为触发条件

    # 智能触发设置
    min_interval_minutes = Column(Integer, default=60)  # 最小间隔
    quiet_during_sleep = Column(Boolean, default=True)  # 睡眠时间不提醒
    skip_if_interacted = Column(Boolean, default=True)  # 刚互动过则跳过

    is_enabled = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = relationship("User", backref="proactive_reminders")


class UserBehaviorPattern(Base):
    """用户行为模式表 - 学习用户习惯"""
    __tablename__ = "user_behavior_patterns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    pattern_type = Column(String(30), nullable=False)  # wake_time/sleep_time/meal_time/activity_peak/inactive_period
    pattern_value = Column(String(100), nullable=False)  # 模式值，如 '07:30\" 或 \"14:00-15:00'

    confidence = Column(Float, default=0.5)  # 置信度 0-1
    sample_count = Column(Integer, default=0)  # 样本数量
    last_occurrence = Column(DateTime, nullable=True)  # 最后出现时间

    # 统计数据
    stats_data = Column(Text, nullable=True)  # JSON格式的统计数据

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = relationship("User", backref="behavior_patterns")

    __table_args__ = (
        Index("idx_behavior_patterns_user_type", 'user_id', "pattern_type"),
    )


class ProactiveInteractionLog(Base):
    """主动交互日志表"""
    __tablename__ = "proactive_interaction_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    interaction_type = Column(String(30), nullable=False)  # greeting/reminder/care_inquiry/health_check
    trigger_source = Column(String(30), nullable=True)  # scheduled/behavior/anomaly

    content = Column(Text, nullable=True)  # 主动发起的内容
    user_response = Column(Text, nullable=True)  # 用户回应
    response_type = Column(String(20), nullable=True)  # positive/neutral/negative/no_response

    triggered_at = Column(DateTime, nullable=False)
    responded_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", backref="proactive_interaction_logs")

    __table_args__ = (
        Index("idx_proactive_logs_user_time", 'user_id', "triggered_at"),
    )


# ==================== 情感记忆系统模型 ====================

class UserProfile(Base):
    """用户画像表 - 存储个性化信息"""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # 基本信息
    nickname = Column(String(50), nullable=True)  # 昵称/称呼
    birth_date = Column(DateTime, nullable=True)
    zodiac = Column(String(20), nullable=True)  # 生肖
    constellation = Column(String(20), nullable=True)  # 星座
    hometown = Column(String(100), nullable=True)  # 老家
    current_city = Column(String(100), nullable=True)  # 现居城市

    # 家庭信息（JSON）
    family_info = Column(Text, nullable=True)  # {'spouse': '老伴张阿姨', 'children': [{'name': '小明', 'relation': '儿子'}]}

    # 兴趣爱好（JSON数组）
    hobbies = Column(Text, nullable=True)  # ['听戏', '下棋', '种花']
    favorite_music = Column(Text, nullable=True)  # ['黄梅戏', '京剧']
    favorite_foods = Column(Text, nullable=True)  # ['红烧肉', '清蒸鱼']
    disliked_foods = Column(Text, nullable=True)  # ['辣椒', '芹菜']

    # 健康相关
    chronic_conditions = Column(Text, nullable=True)  # ['高血压', '糖尿病']
    allergies = Column(Text, nullable=True)  # ['青霉素', '海鲜']
    dietary_restrictions = Column(Text, nullable=True)  # ['低盐', '低糖']

    # 性格特点
    personality_traits = Column(Text, nullable=True)  # ['开朗', '健谈']
    communication_style = Column(String(30), nullable=True)  # formal/casual/caring
    preferred_topics = Column(Text, nullable=True)  # ['家庭', '健康', '新闻\"]

    # AI对话风格设置
    ai_persona = Column(String(50), default="caring_companion")  # caring_companion/health_advisor/cheerful_friend
    response_speed = Column(String(20), default="normal")  # slow/normal/fast
    verbosity = Column(String(20), default="moderate")  # brief/moderate/detailed

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = relationship("User", backref="profile", uselist=False)


class UserMemory(Base):
    """用户记忆表 - 存储对话中提取的重要信息"""
    __tablename__ = "user_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    memory_type = Column(String(30), nullable=False)  # family/event/preference/health/emotion/story
    category = Column(String(50), nullable=True)  # 子类别

    # 记忆内容
    key = Column(String(100), nullable=False)  # 记忆键，如 'grandson_name', \"favorite_song\"
    value = Column(Text, nullable=False)  # 记忆值，如 '小明', '女驸马'
    context = Column(Text, nullable=True)  # 上下文信息

    # 来源
    source_conversation_id = Column(Integer, nullable=True)  # 来源对话ID
    extracted_at = Column(DateTime, nullable=False)

    # 重要性和置信度
    importance = Column(Integer, default=5)  # 1-10
    confidence = Column(Float, default=0.8)  # 0-1

    # 使用情况
    last_referenced_at = Column(DateTime, nullable=True)  # 最后引用时间
    reference_count = Column(Integer, default=0)  # 引用次数

    is_verified = Column(Boolean, default=False)  # 是否已验证
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = relationship("User", backref="memories")

    __table_args__ = (
        Index("idx_user_memories_user_type", 'user_id', "memory_type"),
        Index("idx_user_memories_key", 'user_id', "key"),
    )


class ImportantDate(Base):
    """重要日期表"""
    __tablename__ = "important_dates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    date_type = Column(String(30), nullable=False)  # birthday/anniversary/memorial/custom
    title = Column(String(100), nullable=False)  # 如'老伴生日', '孙子生日'
    description = Column(Text, nullable=True)

    # 日期设置
    month = Column(Integer, nullable=False)  # 1-12
    day = Column(Integer, nullable=False)  # 1-31
    is_lunar = Column(Boolean, default=False)  # 是否农历
    year = Column(Integer, nullable=True)  # 具体年份（可选，用于计算周年）

    # 提醒设置
    reminder_days_before = Column(Integer, default=1)  # 提前几天提醒
    reminder_enabled = Column(Boolean, default=True)

    # 关联人物
    related_person = Column(String(50), nullable=True)  # 关联的人

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", backref="important_dates")


class LifeStory(Base):
    """人生故事表 - 记录老人的回忆和故事"""
    __tablename__ = "life_stories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)  # 故事内容

    # 分类
    category = Column(String(30), nullable=True)  # childhood/youth/career/family/travel/custom
    era = Column(String(50), nullable=True)  # 年代，如 '1960年代'
    location = Column(String(100), nullable=True)  # 地点

    # 相关人物（JSON数组）
    related_people = Column(Text, nullable=True)  # ['父亲', '母亲', '老师']

    # 媒体附件
    audio_url = Column(String(500), nullable=True)  # 语音记录URL
    photo_urls = Column(Text, nullable=True)  # JSON数组，照片URLs

    # 情感标签
    emotion_tags = Column(Text, nullable=True)  # ['温馨', '怀念', '自豪\"]

    # 来源
    source = Column(String(20), default="conversation")  # conversation/voice_diary/manual

    recorded_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", backref="life_stories")

    __table_args__ = (
        Index("idx_life_stories_user_category", 'user_id', "category"),
    )


# ==================== 药品识别模块模型 ====================

class DrugInfo(Base):
    """药品信息库表"""
    __tablename__ = "drug_info"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    name = Column(String(100), nullable=False, index=True)  # 药品名称
    generic_name = Column(String(100), nullable=True)  # 通用名
    brand_names = Column(Text, nullable=True)  # JSON数组，品牌名
    barcode = Column(String(50), nullable=True, index=True)  # 条形码

    # 规格
    specification = Column(String(100), nullable=True)  # 规格，如'100mg*30片'
    dosage_form = Column(String(30), nullable=True)  # 剂型：tablet/capsule/liquid/injection
    manufacturer = Column(String(100), nullable=True)  # 生产厂家
    approval_number = Column(String(50), nullable=True)  # 批准文号

    # 分类
    drug_category = Column(String(30), nullable=True)  # otc/prescription/chinese_medicine
    therapeutic_category = Column(String(100), nullable=True)  # 治疗类别

    # 说明
    indications = Column(Text, nullable=True)  # 适应症
    dosage_instructions = Column(Text, nullable=True)  # 用法用量
    contraindications = Column(Text, nullable=True)  # 禁忌
    side_effects = Column(Text, nullable=True)  # 不良反应
    interactions = Column(Text, nullable=True)  # 药物相互作用
    precautions = Column(Text, nullable=True)  # 注意事项
    storage = Column(String(200), nullable=True)  # 储存条件

    # 老年人特别提示
    elderly_precautions = Column(Text, nullable=True)  # 老年人用药注意

    # 图片
    image_url = Column(String(500), nullable=True)  # 药品图片

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_drug_info_name", 'name'),
        Index("idx_drug_info_generic", "generic_name"),
    )


class DrugRecognitionLog(Base):
    """药品识别日志表"""
    __tablename__ = "drug_recognition_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 识别信息
    image_url = Column(String(500), nullable=True)  # 上传的图片
    recognized_text = Column(Text, nullable=True)  # OCR识别的文本
    barcode = Column(String(50), nullable=True)  # 识别到的条形码

    # 识别结果
    drug_info_id = Column(Integer, ForeignKey("drug_info.id"), nullable=True)  # 匹配到的药品
    matched_name = Column(String(100), nullable=True)  # 匹配到的药名
    confidence = Column(Float, nullable=True)  # 识别置信度

    # 状态
    status = Column(String(20), nullable=False)  # success/partial/failed/manual
    manual_correction = Column(String(100), nullable=True)  # 人工更正

    # 后续操作
    added_to_medication = Column(Boolean, default=False)  # 是否添加到用药计划
    medication_id = Column(Integer, nullable=True)  # 关联的用药计划ID

    recognized_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", backref="drug_recognition_logs")
    drug_info = relationship("DrugInfo")

    __table_args__ = (
        Index("idx_drug_recognition_user_time", 'user_id', "recognized_at"),
    )


class DrugInteraction(Base):
    """药物相互作用表"""
    __tablename__ = "drug_interactions"

    id = Column(Integer, primary_key=True, index=True)

    drug_a_id = Column(Integer, ForeignKey("drug_info.id"), nullable=False)
    drug_b_id = Column(Integer, ForeignKey("drug_info.id"), nullable=False)

    interaction_type = Column(String(30), nullable=False)  # contraindicated/major/moderate/minor
    severity = Column(String(20), nullable=False)  # high/medium/low
    description = Column(Text, nullable=True)  # 相互作用描述
    recommendation = Column(Text, nullable=True)  # 建议

    created_at = Column(DateTime, default=datetime.now)

    # 关系
    drug_a = relationship("DrugInfo", foreign_keys=[drug_a_id])
    drug_b = relationship("DrugInfo", foreign_keys=[drug_b_id])

    __table_args__ = (
        Index("idx_drug_interactions", 'drug_a_id', "drug_b_id"),
    )


# ==================== 认知训练模块模型 ====================

class CognitiveGame(Base):
    """认知训练游戏表"""
    __tablename__ = "cognitive_games"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)  # 游戏名称
    game_type = Column(String(30), nullable=False)  # memory/attention/calculation/language/spatial
    difficulty_levels = Column(Integer, default=3)  # 难度级别数

    description = Column(Text, nullable=True)  # 游戏描述
    instructions = Column(Text, nullable=True)  # 游戏说明
    benefits = Column(Text, nullable=True)  # 训练益处

    # 游戏配置（JSON）
    config = Column(Text, nullable=True)  # 游戏参数配置

    icon_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.now)


class CognitiveGameSession(Base):
    """认知训练游戏会话表"""
    __tablename__ = "cognitive_game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    game_id = Column(Integer, ForeignKey("cognitive_games.id"), nullable=False)

    difficulty = Column(Integer, default=1)  # 当前难度

    # 成绩
    score = Column(Integer, default=0)
    max_score = Column(Integer, nullable=True)
    accuracy = Column(Float, nullable=True)  # 正确率
    completion_time_seconds = Column(Integer, nullable=True)  # 完成时间

    # 详细数据（JSON）
    game_data = Column(Text, nullable=True)  # 游戏详细数据

    status = Column(String(20), default="completed")  # in_progress/completed/abandoned

    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", backref="cognitive_game_sessions")
    game = relationship("CognitiveGame")

    __table_args__ = (
        Index("idx_game_sessions_user_time", 'user_id', "started_at"),
    )


class CognitiveAssessment(Base):
    """认知评估表"""
    __tablename__ = "cognitive_assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    assessment_type = Column(String(30), nullable=False)  # mmse/moca/custom/daily
    assessment_date = Column(DateTime, nullable=False)

    # 各维度评分（JSON）
    dimension_scores = Column(Text, nullable=True)  # {'memory': 8, 'attention': 7, 'language': 9}

    # 总分
    total_score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    percentile = Column(Float, nullable=True)  # 百分位

    # 评估结果
    cognitive_level = Column(String(30), nullable=True)  # normal/mild_decline/moderate_decline/severe_decline
    trend = Column(String(20), nullable=True)  # improving/stable/declining

    # 详细数据
    raw_data = Column(Text, nullable=True)  # 原始答题数据
    analysis = Column(Text, nullable=True)  # AI分析
    recommendations = Column(Text, nullable=True)  # 建议（JSON数组）

    # 通知
    notified_family = Column(Boolean, default=False)
    notification_level = Column(String(20), nullable=True)  # info/warning/alert

    created_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User", backref="cognitive_assessments")

    __table_args__ = (
        Index("idx_cognitive_assessments_user_date", 'user_id', "assessment_date"),
    )


class CognitiveTrainingPlan(Base):
    """认知训练计划表"""
    __tablename__ = "cognitive_training_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # 训练目标
    target_dimensions = Column(Text, nullable=True)  # JSON数组: ['memory', 'attention']
    weekly_sessions = Column(Integer, default=3)  # 每周训练次数
    session_duration_minutes = Column(Integer, default=15)  # 每次时长

    # 游戏配置（JSON数组）
    games_config = Column(Text, nullable=True)  # [{'game_id': 1, "difficulty": 2, "repetitions\": 3}]

    # 时间安排
    schedule_days = Column(String(50), nullable=True)  # JSON数组，周几
    schedule_time = Column(String(10), nullable=True)  # \"09:00\"

    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)

    # 提醒
    reminder_enabled = Column(Boolean, default=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    user = relationship("User", backref="cognitive_training_plans")


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
