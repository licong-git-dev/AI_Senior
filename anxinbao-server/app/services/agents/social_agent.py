"""
SocialAgent V1 · 家庭关系图谱与子女联系频率追踪 · Phase 4 第 1 轮

职责:
- 读 family_members + family_account_members 拉关系图
- 检测"子女多久没联系老人"（用 audit_logs 当代理指标）
- 输出 severity（家属若 7 天未活动 → warning；30 天 → critical）

设计原则:
- 只读，不写
- 不暴露具体子女姓名给 Hermes（隐私），只传聚合数字
- 用代理指标（audit_log 中家属账号活动）拼凑"互动证据"
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from app.services.agents.base import AgentReport, BaseAgent

logger = logging.getLogger(__name__)


class SocialAgent(BaseAgent):
    name = "social"

    SILENCE_WARNING_DAYS = 7
    SILENCE_CRITICAL_DAYS = 30

    async def evaluate(self, user_id: int, context: Dict[str, Any]) -> AgentReport:
        try:
            from app.models.database import (
                AuditLog,
                FamilyMember,
                SessionLocal,
                UserAuth,
            )
        except ImportError:
            return AgentReport(self.name, severity="info", summary="社交模型不可用")

        db = SessionLocal()
        try:
            family_members = (
                db.query(FamilyMember).filter(FamilyMember.user_id == user_id).all()
            )

            if not family_members:
                return AgentReport(
                    self.name,
                    severity="info",
                    summary="尚未绑定家属。建议邀请家人。",
                    suggested_actions=["生成邀请码：POST /api/family-account/{id}/invite"],
                )

            family_phones = [fm.phone for fm in family_members if fm.phone]
            if not family_phones:
                return AgentReport(
                    self.name,
                    severity="info",
                    summary=f"已绑定 {len(family_members)} 位家属，但缺手机号无法追踪互动",
                    details={"total_family_members": len(family_members)},
                )

            family_auths = (
                db.query(UserAuth)
                .filter(UserAuth.username.in_(family_phones))
                .all()
            )
            family_auth_ids = [str(a.id) for a in family_auths]

            if not family_auth_ids:
                return AgentReport(
                    self.name,
                    severity="info",
                    summary=f"已绑定 {len(family_members)} 位家属，但他们尚未注册账号",
                )

            cutoff_critical = datetime.now() - timedelta(days=self.SILENCE_CRITICAL_DAYS)
            cutoff_warning = datetime.now() - timedelta(days=self.SILENCE_WARNING_DAYS)

            # 各家属最后一次审计活动时间
            last_seen_by_family: Dict[str, datetime] = {}
            recent_logs = (
                db.query(AuditLog.user_id, AuditLog.created_at)
                .filter(AuditLog.user_id.in_(family_auth_ids))
                .filter(AuditLog.created_at >= cutoff_critical)
                .all()
            )
            for ua_id, ts in recent_logs:
                cur = last_seen_by_family.get(ua_id)
                if cur is None or ts > cur:
                    last_seen_by_family[ua_id] = ts

            silent_warning = 0
            silent_critical = 0
            active = 0
            for ua_id in family_auth_ids:
                last = last_seen_by_family.get(ua_id)
                if last is None:
                    silent_critical += 1
                elif last < cutoff_warning:
                    silent_warning += 1
                else:
                    active += 1
        except Exception as exc:
            return AgentReport(
                self.name,
                severity="error",
                summary=f"读家庭关系失败: {exc}",
            )
        finally:
            db.close()

        # 决定 severity
        if silent_critical > 0:
            severity = "warning"  # 不直接 critical，避免每天告警
            summary = (
                f"{silent_critical} 位家属超过 30 天没活动；"
                f"{silent_warning} 位 7-30 天没活动；{active} 位活跃"
            )
            suggestions = ["建议老人主动跟安心宝说想哪个孩子，AI 会代为发起联系"]
        elif silent_warning > 0:
            severity = "info"
            summary = f"{silent_warning} 位家属超过 7 天没活动；{active} 位最近有互动"
            suggestions = []
        else:
            severity = "info"
            summary = f"全部 {len(family_auth_ids)} 位家属近期都有活动"
            suggestions = []

        return AgentReport(
            self.name,
            severity=severity,
            summary=summary,
            details={
                "total_family_members": len(family_members),
                "registered_family_auths": len(family_auth_ids),
                "active_recent": active,
                "silent_warning": silent_warning,
                "silent_critical": silent_critical,
                # 故意**不返回具体姓名**，保护隐私
            },
            suggested_actions=suggestions,
        )
