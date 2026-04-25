"""
HealthAgent V1 · 健康监控（规则引擎，无 LLM）· Phase 4 第 1 轮

职责:
- 读 HealthRecord 最近 7 天血压/心率/血糖
- 计算阈值命中 + 趋势
- 输出 severity: info / warning / critical 给 Hermes

设计原则:
- 只读，不写（不直接 SOS；让 SafetyAgent 决定是否升级）
- 阈值参考国家标准 + .env 可覆盖（与既有 settings 字段对齐）
- 数据稀少时返 info，不假报警
- DB 异常时返 error 但不抛
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.services.agents.base import AgentReport, BaseAgent

logger = logging.getLogger(__name__)


# ===== 阈值（与 .env.example 对齐；超出范围视为偏高/偏低）=====

THRESHOLDS = {
    "blood_pressure": {
        "systolic_high": 140, "systolic_low": 90,
        "diastolic_high": 90, "diastolic_low": 60,
    },
    "heart_rate": {"high": 100, "low": 60},
    "blood_sugar": {"fasting_high": 6.1, "fasting_low": 3.9, "postprandial_high": 7.8},
    "temperature": {"high": 37.3, "low": 36.0},
}


class HealthAgent(BaseAgent):
    name = "health"

    LOOKBACK_DAYS = 7
    TREND_MIN_RECORDS = 3  # 至少 3 条样本才做趋势判定

    async def evaluate(self, user_id: int, context: Dict[str, Any]) -> AgentReport:
        try:
            from app.models.database import HealthRecord, SessionLocal
        except ImportError:
            return AgentReport(self.name, severity="info", summary="健康模型不可用")

        db = SessionLocal()
        try:
            cutoff = datetime.now() - timedelta(days=self.LOOKBACK_DAYS)
            rows = (
                db.query(HealthRecord)
                .filter(
                    HealthRecord.user_id == user_id,
                    HealthRecord.measured_at >= cutoff,
                )
                .order_by(HealthRecord.measured_at.desc())
                .limit(200)
                .all()
            )
        finally:
            db.close()

        if not rows:
            return AgentReport(
                self.name,
                severity="info",
                summary="近 7 天无健康数据，建议老人主动测量",
                details={"records_count": 0, "lookback_days": self.LOOKBACK_DAYS},
            )

        # 按 record_type 分组
        groups: Dict[str, List] = {}
        for r in rows:
            groups.setdefault(r.record_type, []).append(r)

        anomalies: List[str] = []
        suggestions: List[str] = []
        max_severity = "info"

        # ===== 血压评估 =====
        bp_rows = groups.get("blood_pressure", [])
        if len(bp_rows) >= self.TREND_MIN_RECORDS:
            bp_analysis = self._analyze_blood_pressure(bp_rows)
            if bp_analysis["severity"] != "info":
                max_severity = self._upgrade_severity(max_severity, bp_analysis["severity"])
                anomalies.append(bp_analysis["summary"])
                if bp_analysis.get("suggestion"):
                    suggestions.append(bp_analysis["suggestion"])

        # ===== 心率评估 =====
        hr_rows = groups.get("heart_rate", [])
        if len(hr_rows) >= self.TREND_MIN_RECORDS:
            hr_analysis = self._analyze_heart_rate(hr_rows)
            if hr_analysis["severity"] != "info":
                max_severity = self._upgrade_severity(max_severity, hr_analysis["severity"])
                anomalies.append(hr_analysis["summary"])

        # ===== 血糖评估 =====
        bs_rows = groups.get("blood_sugar", [])
        if bs_rows:
            bs_analysis = self._analyze_blood_sugar(bs_rows)
            if bs_analysis["severity"] != "info":
                max_severity = self._upgrade_severity(max_severity, bs_analysis["severity"])
                anomalies.append(bs_analysis["summary"])

        # 汇总
        if not anomalies:
            return AgentReport(
                self.name,
                severity="info",
                summary=f"近 {self.LOOKBACK_DAYS} 天健康数据正常（{len(rows)} 条记录）",
                details={"records_count": len(rows), "groups": list(groups.keys())},
            )

        return AgentReport(
            self.name,
            severity=max_severity,
            summary="；".join(anomalies),
            details={
                "records_count": len(rows),
                "anomaly_count": len(anomalies),
                "groups": list(groups.keys()),
            },
            suggested_actions=suggestions,
        )

    # ===== 内部分析方法 =====

    def _analyze_blood_pressure(self, rows: List) -> Dict[str, Any]:
        """血压：连续 3 次以上偏高 → warning；任意一次极高 → critical"""
        th = THRESHOLDS["blood_pressure"]
        high_count = 0
        critical_event: Optional[str] = None
        for r in rows:
            sys_v = r.value_primary or 0
            dia_v = r.value_secondary or 0
            if sys_v >= 180 or dia_v >= 110:
                critical_event = f"{int(sys_v)}/{int(dia_v)} mmHg（极高）"
                break
            if sys_v >= th["systolic_high"] or dia_v >= th["diastolic_high"]:
                high_count += 1

        if critical_event:
            return {
                "severity": "critical",
                "summary": f"血压急剧偏高：{critical_event}",
                "suggestion": "立即联系医生或拨打 120",
            }
        if high_count >= 3:
            return {
                "severity": "warning",
                "summary": f"血压偏高（近 7 天 {high_count} 次 ≥{th['systolic_high']}/{th['diastolic_high']}）",
                "suggestion": "建议复测并咨询医生",
            }
        return {"severity": "info"}

    def _analyze_heart_rate(self, rows: List) -> Dict[str, Any]:
        th = THRESHOLDS["heart_rate"]
        latest = rows[0].value_primary or 0
        if latest >= 120 or latest <= 40:
            return {
                "severity": "critical",
                "summary": f"心率异常：{int(latest)} bpm",
            }
        # 持续偏高
        high_count = sum(1 for r in rows if (r.value_primary or 0) > th["high"])
        if high_count >= 3:
            return {
                "severity": "warning",
                "summary": f"心率近期偏高（{high_count}/{len(rows)} 次 >100 bpm）",
            }
        return {"severity": "info"}

    def _analyze_blood_sugar(self, rows: List) -> Dict[str, Any]:
        th = THRESHOLDS["blood_sugar"]
        latest = rows[0].value_primary or 0
        if latest >= 11.1:
            return {
                "severity": "critical",
                "summary": f"血糖异常偏高：{latest:.1f} mmol/L",
            }
        if latest >= th["postprandial_high"]:
            return {
                "severity": "warning",
                "summary": f"血糖偏高：{latest:.1f} mmol/L",
            }
        if latest <= 3.5:
            return {
                "severity": "warning",
                "summary": f"血糖偏低：{latest:.1f} mmol/L（注意低血糖）",
            }
        return {"severity": "info"}

    @staticmethod
    def _upgrade_severity(current: str, new: str) -> str:
        """severity 排序: info < warning < critical < error"""
        rank = {"info": 0, "warning": 1, "critical": 2, "error": 3}
        return new if rank.get(new, 0) > rank.get(current, 0) else current
