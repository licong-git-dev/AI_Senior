"""单元测试 · 老人主动语音服务（r25 · Insight #12）"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.database import (
    Base,
    ElderVoiceMessage,
    FamilyMember,
    User,
    UserAuth,
)
from app.services.voice_message_service import (
    MessageNotFoundError,
    NotRecipientError,
    RecipientNotFoundError,
    VoiceMessageError,
    voice_message_service,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    s = SessionLocal()
    yield s
    s.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mama(db):
    u = User(name="妈妈", dialect="wuhan")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def small_jun(db, mama):
    """小军：mama 的家属 + 对应 user_auth"""
    fm = FamilyMember(user_id=mama.id, name="小军", phone="13800001000", is_primary=True)
    db.add(fm)
    db.commit()
    ua = UserAuth(username="13800001000", password_hash="x", role="family")
    db.add(ua)
    db.commit()
    db.refresh(ua)
    return ua


@pytest.fixture
def stranger(db):
    """局外人：未绑定 mama 的另一个 family"""
    ua = UserAuth(username="13900009999", password_hash="x", role="family")
    db.add(ua)
    db.commit()
    db.refresh(ua)
    return ua


# ===== record =====


class TestRecord:

    @pytest.mark.unit
    def test_normal_record(self, db, mama, small_jun):
        msg = voice_message_service.record(
            db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
            audio_url="oss://test/x.m4a", duration_sec=15,
        )
        assert msg.id is not None
        assert msg.duration_sec == 15
        assert msg.transcript is None  # 异步加工
        assert msg.read_at is None

    @pytest.mark.unit
    def test_too_short_rejected(self, db, mama, small_jun):
        with pytest.raises(VoiceMessageError, match="太短"):
            voice_message_service.record(
                db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
                audio_url="oss://test/x.m4a", duration_sec=2,
            )

    @pytest.mark.unit
    def test_too_long_rejected(self, db, mama, small_jun):
        with pytest.raises(VoiceMessageError, match="超出"):
            voice_message_service.record(
                db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
                audio_url="oss://test/x.m4a", duration_sec=120,
            )

    @pytest.mark.unit
    def test_unbound_recipient_rejected(self, db, mama, stranger):
        """局外家属不在 family_members 绑定中 → 拒绝"""
        with pytest.raises(RecipientNotFoundError, match="未绑定"):
            voice_message_service.record(
                db=db, sender_user_id=mama.id, recipient_user_auth_id=stranger.id,
                audio_url="oss://test/x.m4a", duration_sec=15,
            )

    @pytest.mark.unit
    def test_daily_limit(self, db, mama, small_jun):
        for _ in range(5):
            voice_message_service.record(
                db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
                audio_url="oss://test/x.m4a", duration_sec=10,
            )
        # 第 6 条触发限频
        with pytest.raises(VoiceMessageError, match="上限"):
            voice_message_service.record(
                db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
                audio_url="oss://test/x.m4a", duration_sec=10,
            )


# ===== 异步加工 =====


class TestAsyncEnrichment:

    @pytest.mark.unit
    def test_attach_transcript(self, db, mama, small_jun):
        msg = voice_message_service.record(
            db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
            audio_url="oss://test/x.m4a", duration_sec=10,
        )
        msg2 = voice_message_service.attach_transcript(db, msg.id, "想您了小军")
        assert msg2.transcript == "想您了小军"

    @pytest.mark.unit
    def test_attach_caption_with_emotion(self, db, mama, small_jun):
        msg = voice_message_service.record(
            db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
            audio_url="oss://test/x.m4a", duration_sec=10,
        )
        msg2 = voice_message_service.attach_caption(
            db, msg.id, "妈妈想您了，提到您小时候的事", emotion="lonely",
        )
        assert msg2.ai_caption.startswith("妈妈想您了")
        assert msg2.emotion == "lonely"

    @pytest.mark.unit
    def test_caption_truncated_to_200(self, db, mama, small_jun):
        msg = voice_message_service.record(
            db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
            audio_url="oss://test/x.m4a", duration_sec=10,
        )
        long = "妈妈想您了" * 200  # > 200 字符
        msg2 = voice_message_service.attach_caption(db, msg.id, long)
        assert len(msg2.ai_caption) <= 200

    @pytest.mark.unit
    def test_attach_to_unknown_message(self, db):
        with pytest.raises(MessageNotFoundError):
            voice_message_service.attach_transcript(db, 99999, "x")


# ===== 家属端 =====


class TestRecipientActions:

    @pytest.mark.unit
    def test_inbox_lists_recent_first(self, db, mama, small_jun):
        for i in range(3):
            voice_message_service.record(
                db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
                audio_url=f"oss://x/{i}.m4a", duration_sec=10,
            )
        items = voice_message_service.list_inbox(db, small_jun.id)
        assert len(items) == 3
        # 创建时间倒序
        assert items[0].created_at >= items[-1].created_at

    @pytest.mark.unit
    def test_inbox_unread_only(self, db, mama, small_jun):
        m1 = voice_message_service.record(
            db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
            audio_url="oss://x/1.m4a", duration_sec=10,
        )
        m2 = voice_message_service.record(
            db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
            audio_url="oss://x/2.m4a", duration_sec=10,
        )
        voice_message_service.mark_read(db, m1.id, small_jun.id)
        unread = voice_message_service.list_inbox(db, small_jun.id, unread_only=True)
        assert len(unread) == 1
        assert unread[0].id == m2.id

    @pytest.mark.unit
    def test_mark_read_idempotent(self, db, mama, small_jun):
        msg = voice_message_service.record(
            db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
            audio_url="oss://x.m4a", duration_sec=10,
        )
        ok1 = voice_message_service.mark_read(db, msg.id, small_jun.id)
        ok2 = voice_message_service.mark_read(db, msg.id, small_jun.id)
        assert ok1 is True
        assert ok2 is True
        # read_at 不会被覆盖（保留首次时间）
        first_read = db.query(ElderVoiceMessage).get(msg.id).read_at
        ok3 = voice_message_service.mark_read(db, msg.id, small_jun.id)
        assert db.query(ElderVoiceMessage).get(msg.id).read_at == first_read

    @pytest.mark.unit
    def test_cross_user_cannot_mark_read(self, db, mama, small_jun, stranger):
        msg = voice_message_service.record(
            db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
            audio_url="oss://x.m4a", duration_sec=10,
        )
        # stranger 不能标记小军的语音已读
        with pytest.raises(NotRecipientError):
            voice_message_service.mark_read(db, msg.id, stranger.id)

    @pytest.mark.unit
    def test_inbox_user_isolation(self, db, mama, small_jun, stranger):
        voice_message_service.record(
            db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
            audio_url="oss://x.m4a", duration_sec=10,
        )
        small_jun_box = voice_message_service.list_inbox(db, small_jun.id)
        stranger_box = voice_message_service.list_inbox(db, stranger.id)
        assert len(small_jun_box) == 1
        assert len(stranger_box) == 0


# ===== Reply =====


class TestReply:

    @pytest.mark.unit
    def test_normal_reply(self, db, mama, small_jun):
        original = voice_message_service.record(
            db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
            audio_url="oss://orig.m4a", duration_sec=15,
        )
        reply = voice_message_service.reply_voice(
            db=db, original_message_id=original.id,
            replier_user_auth_id=small_jun.id,
            audio_url="oss://reply.m4a", duration_sec=10,
        )
        assert reply.reply_voice_message_id == original.id

    @pytest.mark.unit
    def test_non_recipient_cannot_reply(self, db, mama, small_jun, stranger):
        original = voice_message_service.record(
            db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
            audio_url="oss://orig.m4a", duration_sec=10,
        )
        with pytest.raises(NotRecipientError):
            voice_message_service.reply_voice(
                db=db, original_message_id=original.id,
                replier_user_auth_id=stranger.id,
                audio_url="oss://reply.m4a", duration_sec=10,
            )


# ===== Stats =====


class TestStats:

    @pytest.mark.unit
    def test_stats_counts(self, db, mama, small_jun):
        for _ in range(3):
            voice_message_service.record(
                db=db, sender_user_id=mama.id, recipient_user_auth_id=small_jun.id,
                audio_url="oss://x.m4a", duration_sec=10,
            )
        # 标记 1 条已读
        items = voice_message_service.list_inbox(db, small_jun.id)
        voice_message_service.mark_read(db, items[0].id, small_jun.id)
        stats = voice_message_service.stats_for_elder(db, mama.id)
        assert stats["total_recorded"] == 3
        assert stats["unread_count"] == 2
