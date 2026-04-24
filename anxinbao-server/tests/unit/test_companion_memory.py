"""单元测试 · MemoryEngine（Phase 1 长期记忆）"""
import os
import tempfile
from datetime import datetime, timedelta

import pytest

from app.services.memory_engine import (
    MemoryEngine,
    MemoryRecord,
    MemoryType,
    MemoryVisibility,
)


@pytest.fixture
def engine():
    """每个测试用独立临时 SQLite，互不污染"""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="memtest_")
    os.close(fd)
    yield MemoryEngine(db_path=path)
    try:
        os.unlink(path)
    except OSError:
        pass


class TestMemoryEngineCRUD:

    @pytest.mark.unit
    def test_save_and_recall(self, engine):
        rec = MemoryRecord(
            user_id=1,
            type=MemoryType.FACT,
            content="老人有 3 个孙子",
            keywords=["孙子"],
        )
        new_id = engine.save(rec)
        assert new_id > 0

        # 召回
        items = engine.recall(user_id=1, query="孙子")
        assert len(items) == 1
        assert items[0].content == "老人有 3 个孙子"

    @pytest.mark.unit
    def test_user_isolation(self, engine):
        """不同 user_id 的记忆严格隔离"""
        engine.save(MemoryRecord(user_id=1, type=MemoryType.FACT, content="A 的事实"))
        engine.save(MemoryRecord(user_id=2, type=MemoryType.FACT, content="B 的事实"))
        items_1 = engine.list_all(user_id=1)
        items_2 = engine.list_all(user_id=2)
        assert len(items_1) == 1
        assert len(items_2) == 1
        assert items_1[0].content == "A 的事实"

    @pytest.mark.unit
    def test_forget_requires_user_id(self, engine):
        """forget 必须校验 user_id 防越权（用户 1 不能删用户 2 的记忆）"""
        new_id = engine.save(MemoryRecord(
            user_id=2, type=MemoryType.FACT, content="B 的隐私"
        ))
        # 用户 1 试图删除用户 2 的记忆 → 失败
        ok = engine.forget(memory_id=new_id, user_id=1)
        assert ok is False
        # 用户 2 自己删 → 成功
        ok = engine.forget(memory_id=new_id, user_id=2)
        assert ok is True

    @pytest.mark.unit
    def test_forget_all(self, engine):
        for i in range(5):
            engine.save(MemoryRecord(
                user_id=1, type=MemoryType.MOOD, content=f"心境 {i}"
            ))
        n = engine.forget_all(user_id=1)
        assert n == 5
        assert engine.list_all(user_id=1) == []


class TestMemoryRecallScoring:

    @pytest.mark.unit
    def test_keyword_match_boosts_score(self, engine):
        """召回打分应让关键词命中的记忆排在前"""
        engine.save(MemoryRecord(user_id=1, type=MemoryType.FACT,
                                 content="无关事实", keywords=[]))
        engine.save(MemoryRecord(user_id=1, type=MemoryType.FACT,
                                 content="老伴喜欢散步", keywords=["老伴"]))
        items = engine.recall(user_id=1, query="老伴")
        assert items[0].content == "老伴喜欢散步"

    @pytest.mark.unit
    def test_fact_always_high_priority(self, engine):
        """FACT 类应有持久召回优先级（不被时间衰减）"""
        engine.save(MemoryRecord(user_id=1, type=MemoryType.FACT,
                                 content="名字叫张三", importance=0.5))
        # 即使无关键词，FACT 也应被召回
        items = engine.recall(user_id=1, query="hello")
        assert len(items) >= 1


class TestMemoryStats:

    @pytest.mark.unit
    def test_stats_count_by_type(self, engine):
        engine.save(MemoryRecord(user_id=1, type=MemoryType.FACT, content="A"))
        engine.save(MemoryRecord(user_id=1, type=MemoryType.FACT, content="B"))
        engine.save(MemoryRecord(user_id=1, type=MemoryType.MOOD, content="C"))
        stats = engine.stats(user_id=1)
        assert stats["total"] == 3
        assert stats["by_type"]["fact"] == 2
        assert stats["by_type"]["mood"] == 1


class TestMemoryVisibility:
    """关键安全：SELF_ONLY 不可被外部召回（隐私防线）"""

    @pytest.mark.unit
    def test_visibility_default_is_self_only(self):
        rec = MemoryRecord(user_id=1, type=MemoryType.FACT, content="x")
        assert rec.visibility == MemoryVisibility.SELF_ONLY

    @pytest.mark.unit
    def test_visibility_can_be_family(self):
        rec = MemoryRecord(
            user_id=1, type=MemoryType.FACT, content="x",
            visibility=MemoryVisibility.FAMILY,
        )
        assert rec.visibility == MemoryVisibility.FAMILY


class TestMemoryExpiration:
    """带 expires_at 的记忆（如临时心境）应自动从召回中消失"""

    @pytest.mark.unit
    def test_expired_record_not_recalled(self, engine):
        past = (datetime.now() - timedelta(hours=1)).isoformat()
        engine.save(MemoryRecord(
            user_id=1, type=MemoryType.MOOD, content="过期心境",
            expires_at=past,
        ))
        engine.save(MemoryRecord(
            user_id=1, type=MemoryType.MOOD, content="还在的心境",
        ))
        items = engine.recall(user_id=1)
        # 只应召回未过期的
        contents = [i.content for i in items]
        assert "过期心境" not in contents
        assert "还在的心境" in contents
