"""
SafetyAgent V1 · 安全守护（24/7 watchdog）· Phase 4 第 1 轮

职责:
- 检测进行中的紧急事件（emergency_service 已上报 → critical）
- 检测特殊模式（crisis/hospital/bereavement → 提示 Hermes 改基调）
- 检测长时间静默（4h+ → warning；24h+ → critical 但不当 SOS）

设计原则:
- 只读，不主动触发 SOS（防误报）
- 当 severity=critical 时 Hermes 会"短路"绕过 LLM 用紧急安抚语
- "长时间静默"是真实信号但不当作 SOS（区分主动求助 vs 被动失联）
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from app.services.agents.base import AgentReport, BaseAgent

logger = logging.getLogger(__name__)


class SafetyAgent(BaseAgent):
    name = "safety"

    SILENCE_WARNING_HOURS = 4
    SILENCE_CRITICAL_HOURS = 24

    async def evaluate(self, user_id: int, context: Dict[str, Any]) -> AgentReport:
        # 1) 优先：检查是否有进行中的紧急事件
        active_alert = self._check_active_emergency(user_id)
        if active_alert:
            return AgentReport(
                self.name,
                severity="critical",
                summary=f"进行中的紧急事件: {active_alert['type']}",
                details=active_alert,
                suggested_actions=["Hermes 用关切+鼓励语气，避免追问细节"],
            )

        # 2) 其次：检查 special_mode（如 crisis/hospital）
        mode_info = self._check_special_mode(user_id)
        if mode_info and mode_info["mode"] != "normal":
            severity = "warning" if mode_info["mode"] in ("hospital", "bereavement") else "info"
            return AgentReport(
                self.name,
                severity=severity,
                summary=f"老人当前处于 {mode_info['mode']} 模式",
                details=mode_info,
                suggested_actions=[f"Hermes 对话基调应匹配 {mode_info['mode']}"],
            )

        # 3) 最后：检查长时间静默
        return self._check_silence(user_id)

    def _check_active_emergency(self, user_id: int) -> Dict[str, Any]:
        """检查 emergency_service 是否有未结束的事件"""
        try:
            from app.services.emergency_service import emergency_service
            if hasattr(emergency_service, "active_alerts"):
                alerts = getattr(emergency_service, "active_alerts", {}) or {}
                for alert_id, alert in alerts.items():
                    if getattr(alert, "user_id", None) == user_id:
                        status_v = getattr(alert, "status", None)
                        status_str = status_v.value if hasattr(status_v, "value") else str(status_v)
                        if status_str in ("triggered", "in_progress", "active"):
                            type_v = getattr(alert, "alert_type", None) or getattr(alert, "type", None)
                            type_str = type_v.value if hasattr(type_v, "value") else str(type_v)
                            return {
                                "alert_id": alert_id,
                                "type": type_str,
                                "status": status_str,
                            }
        except Exception as exc:
            logger.debug(f"[safety_agent] emergency_service 探测失败: {exc}")
        return {}

    def _check_special_mode(self, user_id: int) -> Dict[str, Any]:
        """读 proactive_engagement 的 dnd_configs.special_mode"""
        try:
            from app.services.proactive_engagement import get_store
            cfg = get_store().get_dnd(user_id)
            mode = cfg.get("special_mode")
            if mode and mode != "normal":
                return {
                    "mode": mode,
                    "started_at": cfg.get("special_mode_started_at"),
                }
        except Exception as exc:
            logger.debug(f"[safety_agent] special_mode 读取失败: {exc}")
        return {}

    def _check_silence(self, user_id: int) -> AgentReport:
        """通过 Conversation 表估算最后一次互动时间"""
        try:
            from app.models.database import Conversation, SessionLocal
        except ImportError:
            return AgentReport(self.name, severity="info", summary="无法访问对话表")

        db = SessionLocal()
        try:
            last_conv = (
                db.query(Conversation)
                .filter(Conversation.user_id == user_id)
                .order_by(Conversation.created_at.desc())
                .first()
            )
        finally:
            db.close()

        if last_conv is None:
            return AgentReport(
                self.name,
                severity="info",
                summary="尚无对话记录（首次使用？）",
            )

        elapsed = datetime.now() - last_conv.created_at
        hours = elapsed.total_seconds() / 3600.0

        if hours >= self.SILENCE_CRITICAL_HOURS:
            return AgentReport(
                self.name,
                severity="critical",
                summary=f"老人已 {int(hours)}h 没互动（关切但不报警）",
                details={"hours_silent": int(hours), "last_seen": last_conv.created_at.isoformat()},
                suggested_actions=[
                    "Hermes 用温和+关切语气主动开口，不追问；",
                    "若 24h 后仍无回应，触发 family_absence 通知子女",
                ],
            )
        if hours >= self.SILENCE_WARNING_HOURS:
            return AgentReport(
                self.name,
                severity="warning",
                summary=f"老人已 {hours:.1f}h 没说话",
                details={"hours_silent": round(hours, 1)},
            )
        return AgentReport(
            self.name,
            severity="info",
            summary=f"近期活跃（{hours:.1f}h 前刚说过话）",
            details={"hours_since_last": round(hours, 1)},
        )
