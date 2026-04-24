"""
Companion 数字生命陪伴 · 端到端集成测试（Phase 1-3 全链路）

覆盖场景：
- Phase 1: 对话 → persona 注入 → 长期记忆召回 → 异步抽取
- Phase 2: 触发器评估 → DND/quota/cooldown → Hermes 生成 → 推送（mock 通道）
- Phase 3: 工具调用 LOW（直接） / MEDIUM（confirm_token） / CRITICAL（双重确认）

设计原则：
- 用 FastAPI TestClient 跑全链路（不实际启动 uvicorn）
- mock qwen_service / notification_service 等外部依赖（避免真 API 调用）
- 用临时 SQLite 隔离 memory_engine 与 proactive_store（测试间不污染）
- 必须 COMPANION_ENABLED=true（在 conftest 中已设 DEBUG=true，本文件单独覆盖）

不测试：
- LLM 真实输出（属于 Anthropic / Qwen 产品的 SLA，非我们职责）
- 真实推送链路到达（依赖外部账号；DLQ 兜底已有 r9 单测）
"""
from __future__ import annotations

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest


# ============ 全局开关：必须在导入业务代码前打开 Companion ============
os.environ["COMPANION_ENABLED"] = "true"


@pytest.fixture
def isolated_companion(monkeypatch):
    """
    每个 e2e 测试用独立临时 DB（memory + proactive）+ 重置 _SafeRandom 等单例。
    避免测试间记忆污染、配额计数串味。
    """
    fd1, mem_db = tempfile.mkstemp(suffix=".db", prefix="e2e_mem_")
    os.close(fd1)
    fd2, proa_db = tempfile.mkstemp(suffix=".db", prefix="e2e_proa_")
    os.close(fd2)

    monkeypatch.setenv("COMPANION_MEMORY_DB", mem_db)
    monkeypatch.setenv("COMPANION_PROACTIVE_DB", proa_db)

    # 重置全局单例（让其用新 DB）
    import app.services.memory_engine as me
    import app.services.proactive_engagement as pe
    me._engine = None
    pe._store = None

    yield {"mem_db": mem_db, "proa_db": proa_db}

    # 清理
    me._engine = None
    pe._store = None
    for p in (mem_db, proa_db):
        try:
            os.unlink(p)
        except OSError:
            pass


@pytest.fixture
def mock_qwen():
    """mock qwen_service.chat_async 返回固定回复，避免真 API 调用"""
    async def fake_chat_async(user_id, message, system_prompt=None, **kwargs):
        # 给一个简单的"听到了"风格回复，包含老人姓名（如果 system_prompt 含）
        return f"[mock] 我听到了：{message[:30]}"

    with patch(
        "app.services.qwen_service.qwen_service.chat_async",
        new=fake_chat_async,
    ):
        yield


@pytest.fixture
def mock_notification():
    """mock notification_service.send_notification，避免触发真推送"""
    async def fake_send(user_id, template, content, extra_data=None):
        return {"success": True, "sent_count": 1, "failed_count": 0, "details": []}

    with patch(
        "app.services.notification_service.notification_service.send_notification",
        new=fake_send,
    ):
        yield


# ===================== 场景 1：Phase 1 全链路 =====================


class TestPhase1FullChat:
    """对话 → persona → 长期记忆召回 → 异步抽取"""

    @pytest.mark.integration
    def test_chat_endpoint_returns_text(
        self, client, auth_headers, isolated_companion, mock_qwen,
    ):
        resp = client.post(
            "/api/companion/chat",
            headers=auth_headers,
            json={"message": "我今天有点想小军", "elder_name": "张妈妈"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "text" in body
        assert isinstance(body["text"], str)
        assert "agent_reports" in body
        # 5 个 agent 全部返回
        assert len(body["agent_reports"]) == 5

    @pytest.mark.integration
    def test_memory_save_and_recall(
        self, client, auth_headers, isolated_companion,
    ):
        # 先存一条事实
        save = client.post(
            "/api/companion/memory/save",
            headers=auth_headers,
            json={
                "type": "fact",
                "content": "老人有 3 个孙子",
                "keywords": ["孙子"],
            },
        )
        assert save.status_code == 200
        mem_id = save.json()["memory_id"]
        assert mem_id > 0

        # 列出应能拿到
        lst = client.get("/api/companion/memory/list", headers=auth_headers)
        assert lst.status_code == 200
        items = lst.json()["items"]
        assert any(item["content"] == "老人有 3 个孙子" for item in items)

        # stats 计数应 +1
        stats = client.get("/api/companion/memory/stats", headers=auth_headers)
        assert stats.status_code == 200
        assert stats.json()["by_type"]["fact"] >= 1

    @pytest.mark.integration
    def test_persona_endpoint(
        self, client, auth_headers, isolated_companion,
    ):
        resp = client.get("/api/companion/persona", headers=auth_headers)
        assert resp.status_code == 200
        p = resp.json()
        assert p["name"] == "安心宝"
        assert "personality" in p

    @pytest.mark.integration
    def test_forget_all_clears_memory(
        self, client, auth_headers, isolated_companion,
    ):
        # 先存几条
        for i in range(3):
            client.post(
                "/api/companion/memory/save",
                headers=auth_headers,
                json={"type": "preference", "content": f"喜欢 {i}", "keywords": []},
            )
        # 不带 confirm 应被拒
        resp = client.delete("/api/companion/memory/all/clear", headers=auth_headers)
        assert resp.status_code == 400
        # 带 confirm 才执行
        resp = client.delete(
            "/api/companion/memory/all/clear?confirm=true",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["deleted_count"] >= 3


# ===================== 场景 2：Phase 2 主动开口 =====================


class TestPhase2Proactive:
    """触发器评估 → DND/quota/cooldown → 主动消息 → 推送（mock）"""

    @pytest.mark.integration
    def test_dnd_default_and_update(
        self, client, auth_headers, isolated_companion,
    ):
        # 默认 DND 配置
        resp = client.get("/api/companion/dnd", headers=auth_headers)
        assert resp.status_code == 200
        cfg = resp.json()
        assert cfg["dnd_start"] == "22:00"
        assert cfg["daily_quota"] == 4

        # 更新部分字段（push_proactive=False）
        resp = client.put(
            "/api/companion/dnd",
            headers=auth_headers,
            json={"push_proactive": False, "daily_quota": 2},
        )
        assert resp.status_code == 200
        cfg = resp.json()
        assert int(cfg["push_proactive"]) == 0
        assert cfg["daily_quota"] == 2
        # dnd_start 不应被覆盖
        assert cfg["dnd_start"] == "22:00"

    @pytest.mark.integration
    def test_run_now_generates_at_least_one_message(
        self, client, auth_headers, isolated_companion, mock_qwen, mock_notification,
    ):
        """
        手动触发评估 —— 因为是新用户（无 last_activity），
        SilenceTrigger 会 fired（"首次使用引导"）→ 应至少生成 1 条
        """
        resp = client.post(
            "/api/companion/proactive/run-now",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["evaluated"] is True
        assert data["generated"] >= 1
        # 收件箱应有同样数量的消息
        inbox = client.get("/api/companion/proactive/inbox", headers=auth_headers)
        assert inbox.status_code == 200
        assert inbox.json()["total"] >= 1

    @pytest.mark.integration
    def test_proactive_inbox_ack_flow(
        self, client, auth_headers, isolated_companion, mock_qwen, mock_notification,
    ):
        client.post("/api/companion/proactive/run-now", headers=auth_headers)
        inbox = client.get("/api/companion/proactive/inbox", headers=auth_headers)
        items = inbox.json()["items"]
        assert items
        msg_id = items[0]["id"]

        # 标记 delivered
        d = client.post(
            f"/api/companion/proactive/{msg_id}/delivered",
            headers=auth_headers,
        )
        assert d.status_code == 200

        # 标记 acknowledged
        a = client.post(
            f"/api/companion/proactive/{msg_id}/ack",
            headers=auth_headers,
        )
        assert a.status_code == 200


# ===================== 场景 3：Phase 3 工具调用安全网关 =====================


class TestPhase3ToolSafetyGate:
    """LOW 直接 / MEDIUM 二次确认 / CRITICAL 双重确认"""

    @pytest.mark.integration
    def test_low_safety_tool_direct_execution(
        self, client, auth_headers, isolated_companion,
    ):
        """log_mood (LOW) 应一次调用即执行"""
        resp = client.post(
            "/api/companion/tools/call",
            headers=auth_headers,
            json={
                "name": "log_mood",
                "params": {"mood": "happy", "note": "今天阳光好"},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["safety_level"] == "low"
        assert body["result"]["ok"] is True

    @pytest.mark.integration
    def test_medium_safety_tool_requires_confirmation(
        self, client, auth_headers, isolated_companion,
    ):
        """video_call_family (MEDIUM) 第一次应返 confirm_token，不真执行"""
        resp = client.post(
            "/api/companion/tools/call",
            headers=auth_headers,
            json={
                "name": "video_call_family",
                "params": {"family_member_id": "fam_99", "family_member_name": "小军"},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("requires_confirmation") is True
        assert body["safety_level"] == "medium"
        assert body["confirm_token"].startswith("conf_")

    @pytest.mark.integration
    def test_medium_safety_tool_executes_with_token(
        self, client, auth_headers, isolated_companion,
    ):
        """带 confirm_token 二次调用应真正执行"""
        # 第一步
        first = client.post(
            "/api/companion/tools/call",
            headers=auth_headers,
            json={
                "name": "video_call_family",
                "params": {"family_member_id": "fam_99"},
            },
        )
        token = first.json()["confirm_token"]

        # 第二步
        second = client.post(
            "/api/companion/tools/call",
            headers=auth_headers,
            json={
                "name": "video_call_family",
                "params": {"family_member_id": "fam_99"},
                "confirm_token": token,
            },
        )
        assert second.status_code == 200
        body = second.json()
        assert body["result"]["ok"] is True
        assert "call_session_id" in body["result"]["result"]

    @pytest.mark.integration
    def test_confirm_token_single_use(
        self, client, auth_headers, isolated_companion,
    ):
        """已用过的 confirm_token 不能再用"""
        first = client.post(
            "/api/companion/tools/call",
            headers=auth_headers,
            json={"name": "video_call_family", "params": {"family_member_id": "x"}},
        )
        token = first.json()["confirm_token"]
        # 第一次成功
        client.post(
            "/api/companion/tools/call",
            headers=auth_headers,
            json={
                "name": "video_call_family",
                "params": {"family_member_id": "x"},
                "confirm_token": token,
            },
        )
        # 第二次应失败
        retry = client.post(
            "/api/companion/tools/call",
            headers=auth_headers,
            json={
                "name": "video_call_family",
                "params": {"family_member_id": "x"},
                "confirm_token": token,
            },
        )
        assert retry.status_code == 400

    @pytest.mark.integration
    def test_unknown_tool_returns_404(
        self, client, auth_headers, isolated_companion,
    ):
        resp = client.post(
            "/api/companion/tools/call",
            headers=auth_headers,
            json={"name": "no_such_tool", "params": {}},
        )
        assert resp.status_code == 404

    @pytest.mark.integration
    def test_pending_confirmations_listing(
        self, client, auth_headers, isolated_companion,
    ):
        """创建 2 个 MEDIUM 调用 → list_pending 应返回 2 条"""
        for i in range(2):
            client.post(
                "/api/companion/tools/call",
                headers=auth_headers,
                json={
                    "name": "video_call_family",
                    "params": {"family_member_id": f"fam_{i}"},
                },
            )
        resp = client.get("/api/companion/confirmations", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 2


# ===================== 场景 4：Phase 2 限流（DND/quota）=====================


class TestPhase2RateLimits:
    """DND / quota / cooldown 三道闸是否真生效"""

    @pytest.mark.integration
    def test_low_quota_caps_messages(
        self, client, auth_headers, isolated_companion, mock_qwen, mock_notification,
    ):
        """配额设 1 → 多次手动评估也只生成 1 条"""
        # 配额降到 1
        client.put(
            "/api/companion/dnd",
            headers=auth_headers,
            json={"daily_quota": 1},
        )
        # 评估两次（第一次 fired silence，第二次 cooldown 应阻止）
        client.post("/api/companion/proactive/run-now", headers=auth_headers)
        client.post("/api/companion/proactive/run-now", headers=auth_headers)

        inbox = client.get("/api/companion/proactive/inbox", headers=auth_headers)
        # 收件箱总条数不应超过 quota（1）
        assert inbox.json()["total"] <= 1

    @pytest.mark.integration
    def test_dnd_disabled_allows_all(
        self, client, auth_headers, isolated_companion, mock_qwen, mock_notification,
    ):
        """关闭 DND 后所有时段都能触发（推送链路 mock）"""
        client.put(
            "/api/companion/dnd",
            headers=auth_headers,
            json={"enabled": False, "daily_quota": 5},
        )
        client.post("/api/companion/proactive/run-now", headers=auth_headers)
        inbox = client.get("/api/companion/proactive/inbox", headers=auth_headers)
        assert inbox.json()["total"] >= 1


# ===================== 场景 5：服务关闭时端点降级 =====================


class TestCompanionDisabled:
    """COMPANION_ENABLED=false 时所有端点应返 503"""

    @pytest.mark.integration
    def test_endpoint_503_when_disabled(self, client, auth_headers, monkeypatch):
        # 临时关闭
        monkeypatch.setenv("COMPANION_ENABLED", "false")
        resp = client.get("/api/companion/persona", headers=auth_headers)
        assert resp.status_code == 503
        body = resp.json()
        assert "companion_disabled" in str(body)
