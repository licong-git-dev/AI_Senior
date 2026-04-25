"""
Companion Onboarding Service · 老人冷启动激活（r26 · Insight #11）

设计依据：ACTIVATION_FIRST_3_MIN.md

注：与既有 onboarding_service.py（步骤化新手引导）功能互补。
本 service 专做 "前 3 分钟激活" 这个独立心智路径。

核心：60+ 老人对 AI 的心智模型不是"朋友"，是"比我儿子还聪明的客服"。
首次激活不是"教老人怎么操作"，是"让 AI 一句话就击中老人"。

3 句话激活法（5s + 10s + 15s）:
  1. 建立熟悉感: "{家姓}{addressed_as}，您家伢{closest_child_name}让我来陪您唠两句。"
  2. 给可消费内容: "我晓得您今儿个一个人在家，要不要听我说说{天气}和{节目}？"
  3. 给操作权: "想跟我说话按绿色，想喊我闭嘴按红色。您家慢慢来，我一直在这。"

D1/D3/D7 二次激活（防止首日激活后流失）:
  - D1 早晨: 复用 closest_child_name 提一件具体的事
  - D3 意外惊喜: 召回 EVENT/PREFERENCE 类记忆做跟进
  - D7 总结: 用 7 天对话总数建立"它真的记得我"

设计原则:
- 字段缺失时优雅降级（用通用问候）
- 不依赖 LLM（脚本生成；保证首次永远能渲染）
- 复用 weather_service 拿真天气
- 全部 idempotent（onboarded_at / onboarding_d{N}_at 记录防重复）
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.database import User

logger = logging.getLogger(__name__)


# ===== 默认值兜底 =====

DEFAULT_ADDRESSED_AS = {"wuhan": "妈妈", "ezhou": "妈", "mandarin": "您"}
DEFAULT_HEALTH_INTRO = {
    "高血压": "上回您说血压有点高，我帮您留意着",
    "糖尿病": "上回您说血糖要看着，我记下了",
    "睡眠": "上回您说晚上睡不好，我陪您聊会儿能助眠",
    "关节": "上回您说膝盖疼，今儿个走路慢点",
}


@dataclass
class ActivationScript:
    """3 句话激活脚本输出"""
    line_1: str
    line_2: str
    line_3: str
    estimated_total_seconds: int = 30
    dialect: str = "wuhan"

    def as_full_text(self) -> str:
        return f"{self.line_1}\n\n{self.line_2}\n\n{self.line_3}"


@dataclass
class FollowUpScript:
    """D1/D3/D7 唤回脚本"""
    day_offset: int  # 1 / 3 / 7
    text: str
    trigger_type: str  # morning_recall / memory_followup / weekly_summary


class CompanionOnboardingService:
    """无状态服务，db 注入"""

    # ----- 3 句话激活 -----

    def generate_activation_script(
        self,
        db: Session,
        user_id: int,
        weather_desc: Optional[str] = None,
    ) -> ActivationScript:
        """
        生成 3 句话激活脚本。

        - 字段缺失时降级为通用版（仍可用，但击中率下降）
        - weather_desc 为可选注入；缺则用季节兜底
        - 不调 LLM（保证可用性）
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return self._fallback_script("您", "wuhan")

        dialect = user.dialect or "mandarin"
        addressed_as = user.addressed_as or DEFAULT_ADDRESSED_AS.get(dialect, "您")
        if user.family_name:
            full_address = f"{user.family_name}{addressed_as}"
        else:
            full_address = addressed_as

        child_name = user.closest_child_name

        # ===== 第 1 句 =====
        if child_name:
            line_1 = f"{full_address}，您家伢{child_name}让我来陪您唠两句。"
        else:
            line_1 = f"{full_address}，您家伢让我来陪您唠两句。"
        if dialect == "mandarin":
            line_1 = line_1.replace("您家伢", "您的孩子").replace("唠两句", "陪您聊聊")

        # ===== 第 2 句 =====
        weather_text = weather_desc or self._season_fallback()
        tv_show = user.favorite_tv_show
        if tv_show:
            content_offer = f"今天的天气{weather_text}，和{tv_show}"
        else:
            content_offer = f"今天的天气{weather_text}"

        # 健康关注做"我记得"勾子
        health_hook = ""
        if user.health_focus and user.health_focus in DEFAULT_HEALTH_INTRO:
            health_hook = DEFAULT_HEALTH_INTRO[user.health_focus] + "。"

        if dialect == "wuhan":
            line_2 = f"我晓得您今儿个一个人在家。{health_hook}要不要听我说说{content_offer}？"
        else:
            line_2 = f"我知道您今天一个人在家。{health_hook}要不要听我讲讲{content_offer}？"

        # ===== 第 3 句 =====
        if dialect == "wuhan":
            line_3 = "想跟我说话，按中间的绿色大按钮就行；想喊我闭嘴，按红色按钮。您家慢慢来，我一直在这。"
        else:
            line_3 = "想跟我说话，按中间的绿色大按钮；想让我安静，按红色按钮。您慢慢来，我一直在这。"

        return ActivationScript(
            line_1=line_1, line_2=line_2, line_3=line_3,
            estimated_total_seconds=30, dialect=dialect,
        )

    def mark_onboarded(self, db: Session, user_id: int) -> None:
        """老人首次激活完成后调用（防重复触发）"""
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.onboarded_at is None:
            user.onboarded_at = datetime.now()
            db.commit()
            logger.info(f"[onboarding] user={user_id} 完成首次激活")

    def is_onboarded(self, db: Session, user_id: int) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        return bool(user and user.onboarded_at)

    # ----- D1/D3/D7 唤回 -----

    def generate_followup(
        self,
        db: Session,
        user_id: int,
        day_offset: int,
    ) -> Optional[FollowUpScript]:
        """
        生成 D1/D3/D7 唤回脚本。
        - 已经触发过的（onboarding_d{N}_at not null）→ 返回 None
        - 老人未完成 onboarding → 返回 None
        """
        if day_offset not in (1, 3, 7):
            return None

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.onboarded_at:
            return None

        # 防重复：已触发过则返 None
        attr_name = f"onboarding_d{day_offset}_at"
        if getattr(user, attr_name, None) is not None:
            return None

        dialect = user.dialect or "mandarin"
        addressed_as = user.addressed_as or DEFAULT_ADDRESSED_AS.get(dialect, "您")
        full_address = (
            f"{user.family_name}{addressed_as}" if user.family_name else addressed_as
        )

        if day_offset == 1:
            text = self._d1_morning_recall(full_address, user, dialect)
            trigger_type = "morning_recall"
        elif day_offset == 3:
            text = self._d3_memory_followup(full_address, user, dialect)
            trigger_type = "memory_followup"
        else:  # 7
            text = self._d7_weekly_summary(full_address, user, dialect)
            trigger_type = "weekly_summary"

        # 标记已触发（防重复）
        setattr(user, attr_name, datetime.now())
        db.commit()

        return FollowUpScript(
            day_offset=day_offset, text=text, trigger_type=trigger_type,
        )

    # ----- 内部辅助 -----

    def _d1_morning_recall(self, address: str, user: User, dialect: str) -> str:
        child = user.closest_child_name or "您家伢"
        if dialect == "wuhan":
            return f"{address}，早呀！昨天您跟我提到{child}的事，今儿个想唠点啥？"
        return f"{address}，早上好！昨天您说了{child}的事，今天想聊点什么？"

    def _d3_memory_followup(self, address: str, user: User, dialect: str) -> str:
        try:
            from app.services.memory_engine import MemoryType, get_memory_engine
            memories = get_memory_engine().recall(
                user_id=user.id,
                types=[MemoryType.EVENT, MemoryType.PREFERENCE],
                top_k=3,
            )
            if memories:
                clue = memories[0].content[:30]
                if dialect == "wuhan":
                    return f"{address}，您前几天提到「{clue}」，今儿个咋样啦？我蛮想知道。"
                return f"{address}，您前几天提到「{clue}」，今天怎么样了？"
        except Exception as exc:
            logger.debug(f"[onboarding] D3 召回记忆失败: {exc}")

        if dialect == "wuhan":
            return f"{address}，咱们认识三天了，您家这两天有啥新鲜事？"
        return f"{address}，咱们认识三天了，您这两天过得怎么样？"

    def _d7_weekly_summary(self, address: str, user: User, dialect: str) -> str:
        try:
            from app.services.memory_engine import get_memory_engine
            stats = get_memory_engine().stats(user.id)
            total = stats.get("total", 0)
        except Exception:
            total = 0

        child = user.closest_child_name or "您家伢"
        if dialect == "wuhan":
            return (
                f"{address}，咱们认识一周了。这周您跟我聊了好多关于{child}的事，"
                f"我都记着嘞（{total}条）。今儿个想跟我说点啥？"
            )
        return (
            f"{address}，咱们认识一周了。这周您跟我聊了不少{child}的事，"
            f"我都记得（{total}条）。今天想说点什么？"
        )

    @staticmethod
    def _season_fallback() -> str:
        m = datetime.now().month
        if m in (12, 1, 2):
            return "蛮冷的"
        if m in (3, 4, 5):
            return "暖和咯"
        if m in (6, 7, 8):
            return "热得很"
        return "凉快咯"

    def _fallback_script(self, address: str, dialect: str) -> ActivationScript:
        return ActivationScript(
            line_1=f"{address}，我来陪您唠两句。",
            line_2=f"今儿个一个人在家么？要不要听我讲讲天气和电视节目？",
            line_3="想跟我说话按绿色，想喊我闭嘴按红色。您家慢慢来，我一直在这。",
            dialect=dialect,
        )


# 全局单例
companion_onboarding_service = CompanionOnboardingService()
