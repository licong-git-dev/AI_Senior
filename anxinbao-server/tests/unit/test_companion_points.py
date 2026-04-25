"""单元测试 · CompanionPoints 陪伴值养成系统（r19 · S 选项）"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.database import Base, CompanionPoints, PointsLedger, User
from app.services.companion_points_service import (
    DailyLimitExceededError,
    EARN_RULES,
    InsufficientBalanceError,
    REDEMPTION_CATALOG,
    RedemptionConstraintViolatedError,
    UnknownRedemptionError,
    companion_points_service,
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
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def baba(db):
    u = User(name="爸爸", dialect="wuhan")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


class TestAccount:

    @pytest.mark.unit
    def test_lazy_create(self, db, mama):
        row = companion_points_service.get_or_create(db, mama.id)
        assert row.balance == 0
        assert row.lifetime_earned == 0
        # 二次调用返同一行
        row2 = companion_points_service.get_or_create(db, mama.id)
        assert row.id == row2.id

    @pytest.mark.unit
    def test_balance_starts_at_zero(self, db, mama):
        assert companion_points_service.get_balance(db, mama.id) == 0


class TestEarn:

    @pytest.mark.unit
    def test_earn_chat_message(self, db, mama):
        ledger = companion_points_service.earn(db, mama.id, "earn_chat_message")
        assert ledger.delta == 1
        assert ledger.balance_after == 1
        assert ledger.type == "earn_chat_message"

    @pytest.mark.unit
    def test_earn_save_memory_higher(self, db, mama):
        ledger = companion_points_service.earn(db, mama.id, "earn_save_memory")
        assert ledger.delta == 3

    @pytest.mark.unit
    def test_earn_unknown_type_raises(self, db, mama):
        with pytest.raises(Exception):
            companion_points_service.earn(db, mama.id, "earn_does_not_exist")

    @pytest.mark.unit
    def test_daily_limit_chat_30(self, db, mama):
        # 30 条以内都成功
        for _ in range(30):
            companion_points_service.earn(db, mama.id, "earn_chat_message")
        # 第 31 条触发限频
        with pytest.raises(DailyLimitExceededError):
            companion_points_service.earn(db, mama.id, "earn_chat_message")
        # balance 是 30
        assert companion_points_service.get_balance(db, mama.id) == 30

    @pytest.mark.unit
    def test_safe_earn_swallows_limit(self, db, mama):
        for _ in range(30):
            companion_points_service.safe_earn(db, mama.id, "earn_chat_message")
        # 第 31 不报错（吞了）
        result = companion_points_service.safe_earn(db, mama.id, "earn_chat_message")
        assert result is None

    @pytest.mark.unit
    def test_lifetime_earned_accumulates(self, db, mama):
        companion_points_service.earn(db, mama.id, "earn_save_memory")  # +3
        companion_points_service.earn(db, mama.id, "earn_chat_message")  # +1
        row = companion_points_service.get_or_create(db, mama.id)
        assert row.lifetime_earned == 4
        assert row.balance == 4
        assert row.lifetime_spent == 0


class TestRedemption:

    @pytest.mark.unit
    def test_redeem_unknown_raises(self, db, mama):
        with pytest.raises(UnknownRedemptionError):
            companion_points_service.redeem(db, mama.id, "not_a_real_item")

    @pytest.mark.unit
    def test_redeem_insufficient_balance(self, db, mama):
        # balance=0，但兑换需要 20
        with pytest.raises(InsufficientBalanceError):
            companion_points_service.redeem(db, mama.id, "extend_videocall_5min")

    @pytest.mark.unit
    def test_redeem_videocall_extension(self, db, mama):
        # 攒够 20
        for _ in range(20):
            companion_points_service.earn(db, mama.id, "earn_chat_message")
        ledger = companion_points_service.redeem(db, mama.id, "extend_videocall_5min")
        assert ledger.delta == -20
        assert ledger.balance_after == 0
        # lifetime_spent 增加
        row = companion_points_service.get_or_create(db, mama.id)
        assert row.lifetime_spent == 20

    @pytest.mark.unit
    def test_birthday_egg_constraint(self, db, mama):
        # 攒够 50
        for _ in range(50):
            companion_points_service.earn(db, mama.id, "earn_chat_message")
        # 不在生日 → 拒
        with pytest.raises(RedemptionConstraintViolatedError):
            companion_points_service.redeem(db, mama.id, "birthday_egg",
                                             context={"is_birthday_today": False})
        # 在生日 → OK
        ledger = companion_points_service.redeem(db, mama.id, "birthday_egg",
                                                  context={"is_birthday_today": True})
        assert ledger.delta == -50

    @pytest.mark.unit
    def test_catalog_well_formed(self):
        for k, v in REDEMPTION_CATALOG.items():
            assert "cost" in v and v["cost"] > 0
            assert "title" in v and v["title"]
            assert "ledger_type" in v and v["ledger_type"].startswith("spend_")


class TestSignin:

    @pytest.mark.unit
    def test_first_signin_today(self, db, mama):
        is_new, streak = companion_points_service.daily_signin(db, mama.id)
        assert is_new is True
        assert streak == 1
        # balance +5
        assert companion_points_service.get_balance(db, mama.id) == 5

    @pytest.mark.unit
    def test_second_signin_same_day_idempotent(self, db, mama):
        companion_points_service.daily_signin(db, mama.id)
        is_new2, streak2 = companion_points_service.daily_signin(db, mama.id)
        assert is_new2 is False
        assert streak2 == 1
        # 仍是 5（没重复加分）
        assert companion_points_service.get_balance(db, mama.id) == 5


class TestLedger:

    @pytest.mark.unit
    def test_ledger_records_all(self, db, mama):
        companion_points_service.earn(db, mama.id, "earn_chat_message")
        companion_points_service.earn(db, mama.id, "earn_save_memory")
        rows = companion_points_service.list_ledger(db, mama.id)
        assert len(rows) == 2
        # 最新的在前
        assert rows[0].type == "earn_save_memory"

    @pytest.mark.unit
    def test_ledger_user_isolation(self, db, mama, baba):
        companion_points_service.earn(db, mama.id, "earn_chat_message")
        companion_points_service.earn(db, baba.id, "earn_save_memory")
        mama_rows = companion_points_service.list_ledger(db, mama.id)
        baba_rows = companion_points_service.list_ledger(db, baba.id)
        assert len(mama_rows) == 1
        assert len(baba_rows) == 1
        assert mama_rows[0].user_id == mama.id
        assert baba_rows[0].user_id == baba.id


class TestEarnRules:

    @pytest.mark.unit
    def test_earn_rules_well_formed(self):
        """所有 earn 规则 delta>0 且 daily_limit 合理"""
        for type_, (delta, limit) in EARN_RULES.items():
            assert delta > 0, f"{type_} delta 应 > 0"
            assert type_.startswith("earn_"), f"{type_} 应以 earn_ 开头"
            if limit is not None:
                assert limit > 0, f"{type_} limit 应 > 0"
