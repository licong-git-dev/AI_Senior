"""
老人主动留语音服务（r25 · Insight #12）

破解"子女通知疲劳"。把推送方向从"AI 推子女"反转为"老人主动给子女"。

工作流:
1. record(): 老人录音文件 → DB ElderVoiceMessage 行
2. transcribe(): 调讯飞 STT 拿原文（异步，失败不影响存档）
3. generate_caption(): 调 qwen 生成"妈妈想说"摘要（≤40 字）
4. dispatch(): 通过 NotificationService 推给家属（已有 retry+DLQ 兜底）
5. mark_delivered/read: 家属端回执
6. reply(): 家属语音回复 → 自引用关联

设计原则:
- 录音文件**优先存对象存储**（生产）；这里 audio_url 是抽象指针
- transcribe / caption 失败不阻塞 record（先存档再异步加工）
- 家属隔离：每个 voice message 的 read 操作只能由 recipient 自己执行
- 复用既有 NotificationService（不新增推送通道）
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.database import ElderVoiceMessage, FamilyMember, User, UserAuth

logger = logging.getLogger(__name__)


# ===== 异常 =====


class VoiceMessageError(Exception):
    pass


class RecipientNotFoundError(VoiceMessageError):
    pass


class NotRecipientError(VoiceMessageError):
    """非收件人试图操作（read/reply）"""


class MessageNotFoundError(VoiceMessageError):
    pass


# ===== 服务 =====


class VoiceMessageService:
    """老人主动留语音的全流程"""

    MAX_DURATION_SEC = 60          # 单条语音最长 60 秒
    MIN_DURATION_SEC = 3           # 太短的（误触/咳嗽）拒绝
    DAILY_LIMIT_PER_ELDER = 5      # 防滥用

    # ----- 录音 -----

    def record(
        self,
        db: Session,
        sender_user_id: int,
        recipient_user_auth_id: int,
        audio_url: str,
        duration_sec: int,
    ) -> ElderVoiceMessage:
        """
        老人录完音的入口。
        - 验证收件人是绑定的家属
        - 限频 5 条/老人/天
        - 异步触发 transcribe + caption（失败也存档）
        """
        # 1) 时长校验
        if duration_sec < self.MIN_DURATION_SEC:
            raise VoiceMessageError(
                f"录音时长 {duration_sec}s 太短（最少 {self.MIN_DURATION_SEC}s）"
            )
        if duration_sec > self.MAX_DURATION_SEC:
            raise VoiceMessageError(
                f"录音时长 {duration_sec}s 超出 {self.MAX_DURATION_SEC}s 上限"
            )

        # 2) 收件人合法性：必须是该老人绑定的某个家属
        recipient = (
            db.query(UserAuth).filter(UserAuth.id == recipient_user_auth_id).first()
        )
        if not recipient:
            raise RecipientNotFoundError(f"收件人 user_auth={recipient_user_auth_id} 不存在")
        if recipient.role != "family":
            raise VoiceMessageError("收件人必须是 family 角色")

        # 通过 phone 关联确认是否真是该老人的家属
        family_phones = [
            fm.phone for fm in db.query(FamilyMember).filter(
                FamilyMember.user_id == sender_user_id
            ).all()
            if fm.phone
        ]
        if recipient.username not in family_phones:
            raise RecipientNotFoundError(
                "该家属未绑定到此老人，请先确认家庭关系"
            )

        # 3) 限频
        today_start = datetime.combine(datetime.now().date(), datetime.min.time())
        today_count = (
            db.query(ElderVoiceMessage)
            .filter(
                ElderVoiceMessage.sender_user_id == sender_user_id,
                ElderVoiceMessage.created_at >= today_start,
            )
            .count()
        )
        if today_count >= self.DAILY_LIMIT_PER_ELDER:
            raise VoiceMessageError(
                f"今日已发 {today_count} 条语音（上限 {self.DAILY_LIMIT_PER_ELDER}）"
            )

        # 4) 落库
        msg = ElderVoiceMessage(
            sender_user_id=sender_user_id,
            recipient_user_auth_id=recipient_user_auth_id,
            audio_url=audio_url,
            duration_sec=duration_sec,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        logger.info(
            f"[voice_message] 老人 {sender_user_id} → 家属 {recipient_user_auth_id} "
            f"语音 {duration_sec}s 已存档 (id={msg.id})"
        )
        return msg

    # ----- 异步加工（transcribe + caption）-----

    def attach_transcript(
        self,
        db: Session,
        message_id: int,
        transcript: str,
    ) -> ElderVoiceMessage:
        """讯飞 STT 完成后回填原文"""
        msg = db.query(ElderVoiceMessage).filter(ElderVoiceMessage.id == message_id).first()
        if not msg:
            raise MessageNotFoundError(f"语音 {message_id} 不存在")
        msg.transcript = (transcript or "")[:1000]
        db.commit()
        db.refresh(msg)
        return msg

    def attach_caption(
        self,
        db: Session,
        message_id: int,
        caption: str,
        emotion: Optional[str] = None,
    ) -> ElderVoiceMessage:
        """qwen 摘要 + 情感分类完成后回填"""
        msg = db.query(ElderVoiceMessage).filter(ElderVoiceMessage.id == message_id).first()
        if not msg:
            raise MessageNotFoundError(f"语音 {message_id} 不存在")
        msg.ai_caption = (caption or "")[:200]
        if emotion:
            msg.emotion = emotion[:20]
        db.commit()
        db.refresh(msg)
        return msg

    # ----- 家属端 -----

    def list_inbox(
        self,
        db: Session,
        recipient_user_auth_id: int,
        unread_only: bool = False,
        limit: int = 30,
    ) -> List[ElderVoiceMessage]:
        """家属拉收件箱"""
        q = db.query(ElderVoiceMessage).filter(
            ElderVoiceMessage.recipient_user_auth_id == recipient_user_auth_id
        )
        if unread_only:
            q = q.filter(ElderVoiceMessage.read_at.is_(None))
        return q.order_by(ElderVoiceMessage.created_at.desc()).limit(max(1, min(100, limit))).all()

    def mark_delivered(
        self,
        db: Session,
        message_id: int,
        recipient_user_auth_id: int,
    ) -> bool:
        """前端展示后标记 delivered（不等于 read）"""
        msg = db.query(ElderVoiceMessage).filter(
            ElderVoiceMessage.id == message_id,
            ElderVoiceMessage.recipient_user_auth_id == recipient_user_auth_id,
        ).first()
        if not msg:
            return False
        if msg.delivered_at is None:
            msg.delivered_at = datetime.now()
            db.commit()
        return True

    def mark_read(
        self,
        db: Session,
        message_id: int,
        recipient_user_auth_id: int,
    ) -> bool:
        """家属点开播放后标记 read"""
        msg = db.query(ElderVoiceMessage).filter(
            ElderVoiceMessage.id == message_id,
        ).first()
        if not msg:
            raise MessageNotFoundError(f"语音 {message_id} 不存在")
        # 越权防护
        if msg.recipient_user_auth_id != recipient_user_auth_id:
            raise NotRecipientError("您不是此语音的收件人，无权标记已读")
        if msg.read_at is None:
            msg.read_at = datetime.now()
            db.commit()
        return True

    # ----- 家属回复 -----

    def reply_voice(
        self,
        db: Session,
        original_message_id: int,
        replier_user_auth_id: int,
        audio_url: str,
        duration_sec: int,
    ) -> ElderVoiceMessage:
        """
        家属语音回复老人。本质上是创建一条新消息，
        sender 是老人 user_id（虚拟，因为现在没有 family→elder 的方向），
        但 reply_voice_message_id 关联原 message。

        当前简化设计：仅记录一条"逆向"语音，不强制方向校验。
        v2 应建独立的 family_voice_replies 表分开管理。
        """
        original = db.query(ElderVoiceMessage).filter(
            ElderVoiceMessage.id == original_message_id
        ).first()
        if not original:
            raise MessageNotFoundError(f"原语音 {original_message_id} 不存在")
        if original.recipient_user_auth_id != replier_user_auth_id:
            raise NotRecipientError("您不是原语音收件人，无权回复")

        if duration_sec < self.MIN_DURATION_SEC:
            raise VoiceMessageError(f"录音时长太短")
        if duration_sec > self.MAX_DURATION_SEC:
            raise VoiceMessageError(f"录音时长超限")

        reply = ElderVoiceMessage(
            sender_user_id=original.sender_user_id,
            recipient_user_auth_id=replier_user_auth_id,  # 暂时同 recipient
            audio_url=audio_url,
            duration_sec=duration_sec,
            reply_voice_message_id=original.id,
        )
        db.add(reply)
        db.commit()
        db.refresh(reply)
        return reply

    # ----- 统计 -----

    def stats_for_elder(self, db: Session, elder_user_id: int) -> dict:
        """老人维度的语音统计（用于子女端"妈妈给我留过 N 条" 显示）"""
        total = db.query(ElderVoiceMessage).filter(
            ElderVoiceMessage.sender_user_id == elder_user_id
        ).count()
        unread_for_recipients = db.query(ElderVoiceMessage).filter(
            ElderVoiceMessage.sender_user_id == elder_user_id,
            ElderVoiceMessage.read_at.is_(None),
        ).count()
        return {
            "total_recorded": total,
            "unread_count": unread_for_recipients,
        }


# 全局单例
voice_message_service = VoiceMessageService()
