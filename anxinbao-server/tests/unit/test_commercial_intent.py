"""单元测试 · 商业意图识别（r27 · Insight #13 GMV 漏斗）"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.database import (
    Base,
    CommercialIntent,
    FamilyAccount,
    FamilyAccountMember,
    User,
    UserAuth,
)
from app.services.commercial_intent_service import (
    CommercialIntentError,
    NotPayerError,
    commercial_intent_service,
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
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mama(db):
    u = User(name="妈妈", dialect="wuhan")
    db.add(u); db.commit(); db.refresh(u)
    return u


@pytest.fixture
def alice_payer(db, mama):
    """alice 是 payer，对应妈妈的家庭账户"""
    ua = UserAuth(username="13800001000", password_hash="x", role="family")
    db.add(ua); db.commit(); db.refresh(ua)
    acc = FamilyAccount(
        account_name="妈妈家",
        beneficiary_user_id=mama.id,
        primary_payer_user_auth_id=ua.id,
    )
    db.add(acc); db.commit(); db.refresh(acc)
    member = FamilyAccountMember(
        family_account_id=acc.id, user_auth_id=ua.id,
        role="payer", permission_level=5,
    )
    db.add(member); db.commit()
    return ua


@pytest.fixture
def stranger(db):
    """局外人，越权测试用"""
    ua = UserAuth(username="13800009999", password_hash="x", role="family")
    db.add(ua); db.commit(); db.refresh(ua)
    return ua


class TestDetectFromText:

    @pytest.mark.unit
    def test_detect_pain_keyword(self):
        results = commercial_intent_service.detect_from_text("我膝盖疼得很")
        assert len(results) >= 1
        top = results[0]
        assert top.category == "pain_relief"
        assert top.keyword == "膝盖疼"
        assert top.confidence >= 0.85

    @pytest.mark.unit
    def test_detect_multiple_intents(self):
        results = commercial_intent_service.detect_from_text(
            "最近睡不好，腰疼也厉害"
        )
        keywords = {r.keyword for r in results}
        assert "睡不好" in keywords
        assert "腰疼" in keywords

    @pytest.mark.unit
    def test_no_match_returns_empty(self):
        results = commercial_intent_service.detect_from_text("今天天气真好")
        assert results == []

    @pytest.mark.unit
    def test_short_text_returns_empty(self):
        assert commercial_intent_service.detect_from_text("") == []
        assert commercial_intent_service.detect_from_text("a") == []

    @pytest.mark.unit
    def test_results_sorted_by_confidence(self):
        # "缺钙" 0.8 < "膝盖疼" 0.9
        results = commercial_intent_service.detect_from_text("膝盖疼，可能缺钙")
        assert results[0].confidence >= results[-1].confidence


class TestDetectAndRecord:

    @pytest.mark.unit
    def test_records_to_db(self, db, mama):
        records = commercial_intent_service.detect_and_record(
            db, mama.id, "我膝盖疼"
        )
        assert len(records) == 1
        # 数据库确实有
        rows = db.query(CommercialIntent).filter(
            CommercialIntent.elder_user_id == mama.id,
        ).all()
        assert len(rows) == 1
        assert rows[0].keyword == "膝盖疼"
        assert rows[0].status == "detected"

    @pytest.mark.unit
    def test_dedup_same_keyword_within_30d(self, db, mama):
        commercial_intent_service.detect_and_record(db, mama.id, "膝盖疼")
        # 第二次说一样的不重复
        records2 = commercial_intent_service.detect_and_record(db, mama.id, "膝盖又疼")
        # 已存在 → 不重复落库
        rows = db.query(CommercialIntent).filter(
            CommercialIntent.elder_user_id == mama.id,
            CommercialIntent.keyword == "膝盖疼",
        ).all()
        assert len(rows) == 1

    @pytest.mark.unit
    def test_max_records_limit(self, db, mama):
        text = "膝盖疼 腰疼 睡不好 缺钙 听不清"  # 5+ 命中
        records = commercial_intent_service.detect_and_record(
            db, mama.id, text, max_records=3,
        )
        assert len(records) <= 3


class TestPermissions:

    @pytest.mark.unit
    def test_payer_can_list(self, db, mama, alice_payer):
        commercial_intent_service.detect_and_record(db, mama.id, "膝盖疼")
        items = commercial_intent_service.list_intents(
            db, mama.id, alice_payer.id,
        )
        assert len(items) == 1

    @pytest.mark.unit
    def test_stranger_cannot_list(self, db, mama, alice_payer, stranger):
        commercial_intent_service.detect_and_record(db, mama.id, "膝盖疼")
        with pytest.raises(NotPayerError):
            commercial_intent_service.list_intents(db, mama.id, stranger.id)

    @pytest.mark.unit
    def test_payer_can_see_stats(self, db, mama, alice_payer):
        commercial_intent_service.detect_and_record(db, mama.id, "膝盖疼 缺钙 睡不好")
        stats = commercial_intent_service.stats(db, mama.id, alice_payer.id)
        assert stats["total_active"] >= 3
        assert "pain_relief" in stats["by_category"]
        assert "nutrition" in stats["by_category"]
        assert "sleep" in stats["by_category"]

    @pytest.mark.unit
    def test_stranger_cannot_see_stats(self, db, mama, alice_payer, stranger):
        with pytest.raises(NotPayerError):
            commercial_intent_service.stats(db, mama.id, stranger.id)


class TestStateMachine:

    @pytest.mark.unit
    def test_mark_reviewed(self, db, mama, alice_payer):
        commercial_intent_service.detect_and_record(db, mama.id, "膝盖疼")
        items = commercial_intent_service.list_intents(db, mama.id, alice_payer.id)
        intent_id = items[0].id

        intent = commercial_intent_service.mark_reviewed(
            db, intent_id, alice_payer.id,
        )
        assert intent.status == "reviewed_by_family"
        assert intent.reviewed_at is not None
        assert intent.reviewed_by_user_auth_id == alice_payer.id

    @pytest.mark.unit
    def test_dismiss(self, db, mama, alice_payer):
        commercial_intent_service.detect_and_record(db, mama.id, "膝盖疼")
        items = commercial_intent_service.list_intents(db, mama.id, alice_payer.id)
        intent_id = items[0].id

        intent = commercial_intent_service.dismiss(db, intent_id, alice_payer.id)
        assert intent.status == "dismissed"

    @pytest.mark.unit
    def test_stranger_cannot_review(self, db, mama, alice_payer, stranger):
        commercial_intent_service.detect_and_record(db, mama.id, "膝盖疼")
        items = commercial_intent_service.list_intents(db, mama.id, alice_payer.id)
        with pytest.raises(NotPayerError):
            commercial_intent_service.mark_reviewed(db, items[0].id, stranger.id)
