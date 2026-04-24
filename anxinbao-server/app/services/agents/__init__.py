"""
多智能体目录（Phase 4 · Hermes 完全体）

架构：
- Hermes 协调者：唯一对外人格，整合其他 agent 的输出
- HealthAgent：监控数据流，异常向 Hermes 上报（无 LLM，规则引擎）
- SocialAgent：维护家庭关系图谱、节日提醒、子女互动
- MemoryAgent：长期记忆管理；每天"睡眠"做记忆整合
- SafetyAgent：SOS / 跌倒 / 长时间静默（无 LLM，规则引擎）
- ScheduleAgent：用药 / 服务 / 出行规划

详见 docs/DIGITAL_COMPANION_RFC.md 第 4 章 Phase 4。
"""

from app.services.agents.base import AgentReport, BaseAgent
from app.services.agents.hermes import Hermes

__all__ = ["BaseAgent", "AgentReport", "Hermes"]
