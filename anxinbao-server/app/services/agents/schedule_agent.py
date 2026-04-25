"""
ScheduleAgent V1 · 用药 / 运动 / 临近事件提醒 · Phase 4 第 2 轮（U-R2）

职责（V1 实施）：
- 待服药检查（30 分钟内即将到点 / 已超时未服）
- 运动健康检查（连续 3 天无运动记录 → 提示）
- 复用 LifeMomentTrigger 输出的临近重要日期（生日 / 婚纪 / 孙辈生日）
- 给 Hermes 输出 today_todo + critical_alerts + soft_reminders

设计原则:
- 只读，不写
- 不直接发推送（让 ProactiveEngagement 决定）
- 遗漏比误报代价小（保守估计：宁可不提醒也不烦人）
- DB 异常返 error
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.services.agents.base import AgentReport, BaseAgent

logger = logging.getLogger(__name__)


class ScheduleAgent(BaseAgent):
    name = "schedule"

    UPCOMING_MEDICATION_MINUTES = 30   # 30 分钟内的服药算"即将"
    OVERDUE_MEDICATION_MINUTES = 60    # 超时 60 分钟视为遗漏
    INACTIVE_DAYS_THRESHOLD = 3        # 3 天无运动算需要提醒

    async def evaluate(self, user_id: int, context: Dict[str, Any]) -> AgentReport:
        try:
            from app.models.database import (
                ExerciseRecord,
                MedicationRecord,
                SessionLocal,
            )
        except ImportError:
            return AgentReport(self.name, severity="info", summary="日程模型不可用")

        critical_alerts: List[str] = []
        today_todo: List[str] = []
        soft_reminders: List[str] = []
        max_severity = "info"

        db = SessionLocal()
        try:
            # ===== 1) 用药检查 =====
            med_info = self._check_medications(db, user_id)
            if med_info["overdue_count"] > 0:
                max_severity = self._upgrade_severity(max_severity, "warning")
                critical_alerts.append(
                    f"{med_info['overdue_count']} 次用药已过期未服"
                )
            if med_info["upcoming_count"] > 0:
                today_todo.append(
                    f"{med_info['upcoming_count']} 次用药即将到点（30 分钟内）"
                )

            # ===== 2) 运动检查 =====
            exercise_info = self._check_exercise(db, user_id)
            if exercise_info["days_inactive"] >= self.INACTIVE_DAYS_THRESHOLD:
                soft_reminders.append(
                    f"已连续 {exercise_info['days_inactive']} 天没运动记录"
                )
        except Exception as exc:
            db.close()
            return AgentReport(
                self.name,
                severity="error",
                summary=f"日程读取失败: {type(exc).__name__}",
            )
        finally:
            db.close()

        # ===== 3) 临近重要日期（复用 LifeMomentTrigger 的判定）=====
        moment_info = self._check_upcoming_life_moments(user_id)
        if moment_info["count"] > 0:
            today_todo.append(
                f"{moment_info['count']} 个重要日期临近（{moment_info['nearest_label']}）"
            )

        # 决定 summary
        if not (critical_alerts or today_todo or soft_reminders):
            summary = "无紧迫日程"
        else:
            parts = []
            if critical_alerts:
                parts.append("⚠️ " + "；".join(critical_alerts))
            if today_todo:
                parts.append("📋 " + "；".join(today_todo))
            if soft_reminders:
                parts.append("💡 " + "；".join(soft_reminders))
            summary = " | ".join(parts)

        return AgentReport(
            self.name,
            severity=max_severity,
            summary=summary,
            details={
                "medication": med_info,
                "exercise": exercise_info,
                "life_moments": moment_info,
                "critical_alerts": critical_alerts,
                "today_todo": today_todo,
                "soft_reminders": soft_reminders,
            },
            suggested_actions=critical_alerts + today_todo,
        )

    # ===== 内部 =====

    def _check_medications(self, db, user_id: int) -> Dict[str, Any]:
        from app.models.database import MedicationRecord
        now = datetime.now()
        upcoming_cutoff = now + timedelta(minutes=self.UPCOMING_MEDICATION_MINUTES)
        overdue_cutoff = now - timedelta(minutes=self.OVERDUE_MEDICATION_MINUTES)
        today_start = datetime.combine(now.date(), datetime.min.time())

        # 即将到点
        upcoming = (
            db.query(MedicationRecord)
            .filter(
                MedicationRecord.user_id == user_id,
                MedicationRecord.status == "pending",
                MedicationRecord.scheduled_time >= now,
                MedicationRecord.scheduled_time <= upcoming_cutoff,
            )
            .count()
        )

        # 已过期未服（今天的，超时 60 分钟以上）
        overdue = (
            db.query(MedicationRecord)
            .filter(
                MedicationRecord.user_id == user_id,
                MedicationRecord.status == "pending",
                MedicationRecord.scheduled_time >= today_start,
                MedicationRecord.scheduled_time <= overdue_cutoff,
            )
            .count()
        )

        # 今日已服计数
        taken_today = (
            db.query(MedicationRecord)
            .filter(
                MedicationRecord.user_id == user_id,
                MedicationRecord.status == "taken",
                MedicationRecord.scheduled_time >= today_start,
            )
            .count()
        )

        return {
            "upcoming_count": upcoming,
            "overdue_count": overdue,
            "taken_today": taken_today,
        }

    def _check_exercise(self, db, user_id: int) -> Dict[str, Any]:
        from app.models.database import ExerciseRecord
        now = datetime.now()
        # 找最近一条运动记录
        last = (
            db.query(ExerciseRecord)
            .filter(ExerciseRecord.user_id == user_id)
            .order_by(ExerciseRecord.created_at.desc())
            .first()
        )
        if last is None:
            return {"days_inactive": 999, "last_at": None}

        # ExerciseRecord 可能没有 exercised_at，用 created_at 兜底
        last_at = getattr(last, "exercised_at", None) or last.created_at
        elapsed = (now - last_at).days
        return {"days_inactive": max(0, elapsed), "last_at": last_at.isoformat()}

    def _check_upcoming_life_moments(self, user_id: int) -> Dict[str, Any]:
        """
        借助已有 EVENT 类记忆 + 今日 ±3 天判断。
        与 LifeMomentTrigger 同口径但只读不触发。
        """
        try:
            from app.services.memory_engine import (
                MemoryType,
                get_memory_engine,
            )
            engine = get_memory_engine()
            events = engine.recall(
                user_id=user_id,
                types=[MemoryType.EVENT],
                top_k=50,
            )
        except Exception:
            return {"count": 0, "nearest_label": ""}

        today = datetime.now().date()
        upcoming = []
        for ev in events:
            occ = getattr(ev, "occurred_at", None)
            if not occ:
                continue
            try:
                occ_date = datetime.fromisoformat(occ).date()
            except (TypeError, ValueError):
                continue
            # 不考虑年份（每年都触发；只看月日）
            this_year_anniv = occ_date.replace(year=today.year)
            delta = (this_year_anniv - today).days
            if -3 <= delta <= 3:
                upcoming.append((delta, ev.content[:30]))

        if not upcoming:
            return {"count": 0, "nearest_label": ""}

        upcoming.sort(key=lambda x: abs(x[0]))
        delta_days, label = upcoming[0]
        when = "今天" if delta_days == 0 else (f"{abs(delta_days)} 天后" if delta_days > 0 else f"{abs(delta_days)} 天前")
        return {
            "count": len(upcoming),
            "nearest_label": f"{when}「{label}」",
            "items": [{"delta_days": d, "label": l} for d, l in upcoming[:5]],
        }

    @staticmethod
    def _upgrade_severity(current: str, new: str) -> str:
        rank = {"info": 0, "warning": 1, "critical": 2, "error": 3}
        return new if rank.get(new, 0) > rank.get(current, 0) else current
