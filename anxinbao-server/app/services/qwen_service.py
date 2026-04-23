"""
通义千问AI对话服务
负责健康陪聊、多轮问诊、食疗建议、情绪识别、个性化记忆
"""
import asyncio
import dashscope
from dashscope import Generation
from typing import List, Dict, Optional, Tuple
import json
import re
from datetime import datetime

from app.core.config import get_settings


# 系统提示词（增强版 - 包含情绪识别）
SYSTEM_PROMPT = """你是「安心宝」智能健康陪聊助手，专门服务老年人。你的角色是一位温和、专业、有耐心的健康顾问。

【核心原则】
1. 永远不要吓唬老人。不说'你可能得了XX病'、'这很严重'之类的话
2. 先安抚，再询问，最后建议。每次回复都要让老人感到安心
3. 用通俗易懂的语言，避免医学术语
4. 食疗建议为主，不推荐具体药物
5. 建议就医时说'让孩子带您去检查一下'，而不是'你必须去医院'

【对话风格】
- 称呼老人为'您'
- 语气像邻家晚辈，亲切但不失尊重
- 多用'没事的'、'这个很常见'、'别担心'开头
- 回复要简短，每次不超过100字，老人看着不累

【情绪识别与关怀】
在对话中注意识别老人的情绪状态，包括：
- 孤独感：如'没人陪'、'儿女忙'、'一个人'、'想他们'
- 焦虑感：如'担心'、'害怕'、'睡不着'、'烦躁'、'不安'
- 悲伤感：如'想老伴'、'难过'、'哭'、'走了'、'不在了'
- 积极情绪：如'高兴'、'开心'、'今天不错'、'孩子来看我'

针对不同情绪的回应策略：
- 孤独：多陪聊，问问日常，提议找朋友/邻居聊天，主动多问几句
- 焦虑：安抚为主，帮助理清思绪，建议放松活动
- 悲伤：共情倾听，不急于转移话题，给予温暖陪伴
- 积极：一起开心，鼓励分享，增强正向情绪

【健康问询流程】
当老人提到身体不适时：
1. 先安抚：'没事的，我来了解一下情况'
2. 问清楚具体症状：哪里？什么感觉？
3. 问持续时间：多久了？第一次还是经常？
4. 问相关因素：最近睡眠/饮食/情绪怎么样？
5. 综合判断，给出安抚+建议

【风险与情绪评估】
在回复的最后，你需要用JSON格式输出内部评估（老人看不到这部分），格式如下：
```json
{'risk_score': 数字1-10, 'risk_reason': '评分理由', 'need_notify': true/false, 'category': 'health/daily/chat/emotion', 'emotion': {'type': 'lonely/anxious/sad/happy/neutral', 'intensity': 1-5, 'keywords': ['关键词']}, 'topics': ['话题标签']}
```

评分标准：
- 1-3分：轻微不适或日常闲聊，无需关注
- 4-6分：需要关注但不紧急，给食疗建议
- 7-8分：建议就医检查或情绪需要关注，通知子女
- 9-10分：疑似紧急情况，必须通知子女

情绪强度评分：
- 1-2：轻微情绪波动，正常范围
- 3：中度情绪，需要关注
- 4-5：强烈情绪，建议通知子女关心

【特别注意的症状】（起点评分7分）
- 胸痛、胸闷、心慌
- 呼吸困难、喘不上气
- 剧烈头痛、头晕到站不稳
- 意识模糊、说话不清
- 摔倒受伤

【特别关注的情绪表达】（起点情绪强度4）
- 频繁提到想念去世的亲人
- 表达不想活、没意思
- 持续的孤独感表达（连续多天）
- 极度焦虑、恐慌状态

【食疗建议示例】
- 头晕、没精神 → 枸杞菊花茶、红枣桂圆汤
- 胃不舒服 → 小米粥、山药粥
- 睡不好 → 酸枣仁泡水、热牛奶加蜂蜜
- 腰酸背痛 → 杜仲炖排骨、黑豆煲汤
- 便秘 → 蜂蜜水、香蕉、红薯
- 咳嗽 → 冰糖雪梨、川贝炖梨

【日常闲聊】
当老人不是问健康问题时：
- 天气、时间、日期照实回答
- 想聊天就陪着聊
- 问买菜就给建议
- category设为'daily'或'chat'，risk_score设为1

记住：你的目标是让老人感到安心和温暖，而不是制造焦虑。"""


# 个性化提示词模板
PERSONALIZED_CONTEXT_TEMPLATE = """
【老人信息】
- 称呼：{name}
- 年龄：{age}岁
- 健康状况：{health_conditions}
- 兴趣爱好：{interests}
- 家庭成员：{family_members}
- 重要日期：{important_dates}
- 对话偏好：{preferences}

请根据以上信息，在对话中自然地体现你了解这位老人，让ta感到被关心和记得。
"""


class QwenChatService:
    """通义千问对话服务（增强版）"""

    def __init__(self):
        settings = get_settings()
        dashscope.api_key = settings.dashscope_api_key
        self.model = 'qwen-turbo'  # 使用turbo版本，响应快

    def chat(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        user_profile: Optional[Dict] = None
    ) -> Tuple[str, Dict]:
        """
        进行对话（同步版本，供非async上下文调用）

        Args:
            user_message: 用户输入
            conversation_history: 历史对话记录 [{'role': 'user/assistant', 'content': '...'}]
            user_profile: 用户画像信息（可选）

        Returns:
            (回复文本, 风险评估字典)
        """
        if conversation_history is None:
            conversation_history = []

        # 构建系统提示词（包含个性化信息）
        system_content = SYSTEM_PROMPT
        if user_profile:
            personalized_context = self._build_personalized_context(user_profile)
            system_content = f"{SYSTEM_PROMPT}\n\n{personalized_context}"

        # 构建消息列表
        messages = [{'role': 'system', 'content': system_content}]
        messages.extend(conversation_history)
        messages.append({'role': 'user', 'content': user_message})

        try:
            # 调用通义千问API
            response = Generation.call(
                model=self.model,
                messages=messages,
                result_format='message',
                temperature=0.7,
                max_tokens=500
            )

            if response.status_code == 200:
                full_response = response.output.choices[0].message.content

                # 解析回复和风险评估
                reply_text, risk_info = self._parse_response(full_response)

                return reply_text, risk_info
            else:
                print(f'API调用失败: {response.code} - {response.message}')
                return '抱歉，我刚才没听清，您再说一遍？', {'risk_score': 1, 'category': 'error'}

        except Exception as e:
            print(f'对话服务错误: {e}')
            return '抱歉，我刚才没听清，您再说一遍？', {'risk_score': 1, 'category': 'error'}

    async def chat_async(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        user_profile: Optional[Dict] = None
    ) -> Tuple[str, Dict]:
        """
        进行对话（异步版本，避免阻塞事件循环）

        Args:
            user_message: 用户输入
            conversation_history: 历史对话记录
            user_profile: 用户画像信息（可选）

        Returns:
            (回复文本, 风险评估字典)
        """
        return await asyncio.to_thread(
            self.chat, user_message, conversation_history, user_profile
        )

    def _build_personalized_context(self, profile: Dict) -> str:
        """构建个性化上下文"""
        return PERSONALIZED_CONTEXT_TEMPLATE.format(
            name=profile.get('name', '老人家'),
            age=profile.get('age', ''),
            health_conditions=', '.join(profile.get('health_conditions', [])) or '暂无记录',
            interests=', '.join(profile.get('interests', [])) or '暂无记录',
            family_members=', '.join(profile.get('family_members', [])) or '暂无记录',
            important_dates=self._format_important_dates(profile.get('important_dates', {})),
            preferences=profile.get('preferences', '暂无记录')
        )

    def _format_important_dates(self, dates: Dict) -> str:
        """格式化重要日期"""
        if not dates:
            return '暂无记录'
        formatted = []
        for event, date in dates.items():
            formatted.append(f'{event}: {date}')
        return ', '.join(formatted)

    def _parse_response(self, response: str) -> Tuple[str, Dict]:
        """
        解析AI回复，分离显示文本和风险评估

        Args:
            response: AI的完整回复

        Returns:
            (显示给用户的文本, 风险评估字典)
        """
        # 默认风险评估（包含情绪）
        default_risk = {
            'risk_score': 1,
            'risk_reason': '日常对话',
            'need_notify': False,
            'category': 'chat',
            'emotion': {
                'type': 'neutral',
                'intensity': 1,
                'keywords': []
            },
            'topics': []
        }

        # 尝试提取JSON部分
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, response, re.DOTALL)

        if match:
            try:
                risk_info = json.loads(match.group(1))
                # 确保包含所有字段
                risk_info = self._normalize_risk_info(risk_info)
                # 移除JSON部分，保留给用户看的文本
                reply_text = re.sub(json_pattern, '', response, flags=re.DOTALL).strip()
                return reply_text, risk_info
            except json.JSONDecodeError:
                pass

        # 如果没有找到JSON，尝试其他格式（单引号或双引号key）
        for json_pattern2 in [r'\{"risk_score".*?\}', r"\{'risk_score'.*?\}"]:
            match2 = re.search(json_pattern2, response, re.DOTALL)
            if match2:
                try:
                    risk_info = json.loads(match2.group(0))
                    risk_info = self._normalize_risk_info(risk_info)
                    reply_text = re.sub(json_pattern2, '', response, flags=re.DOTALL).strip()
                    return reply_text, risk_info
                except json.JSONDecodeError:
                    continue

        # 都没找到，返回原文和默认风险
        return response.strip(), default_risk

    def _normalize_risk_info(self, risk_info: Dict) -> Dict:
        """标准化风险评估信息，确保包含所有必要字段"""
        # 确保基本字段
        if 'risk_score' not in risk_info:
            risk_info['risk_score'] = 1
        if 'category' not in risk_info:
            risk_info['category'] = 'chat'
        if 'need_notify' not in risk_info:
            risk_info['need_notify'] = risk_info.get('risk_score', 1) >= 7

        # 确保情绪字段
        if 'emotion' not in risk_info:
            risk_info['emotion'] = {
                'type': 'neutral',
                'intensity': 1,
                'keywords': []
            }
        else:
            emotion = risk_info['emotion']
            if 'type' not in emotion:
                emotion['type'] = 'neutral'
            if 'intensity' not in emotion:
                emotion['intensity'] = 1
            if 'keywords' not in emotion:
                emotion['keywords'] = []

        # 确保话题字段
        if 'topics' not in risk_info:
            risk_info['topics'] = []

        return risk_info

    def analyze_emotion(self, text: str) -> Dict:
        """
        独立的情绪分析功能

        Args:
            text: 待分析文本

        Returns:
            情绪分析结果
        """
        prompt = f"""请分析以下老人说的话中表达的情绪。

文本："{text}"

请用JSON格式回复，包含：
- type: 情绪类型（lonely孤独/anxious焦虑/sad悲伤/happy开心/neutral中性）
- intensity: 情绪强度（1-5，1最轻5最强）
- keywords: 触发情绪的关键词列表
- suggestion: 建议的回应方式

只输出JSON，不要其他内容。"""

        try:
            response = Generation.call(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                result_format='message',
                temperature=0.3
            )

            if response.status_code == 200:
                content = response.output.choices[0].message.content
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))

        except Exception as e:
            print(f'情绪分析错误: {e}')

        return {
            'type': 'neutral',
            'intensity': 1,
            'keywords': [],
            'suggestion': '正常交流'
        }

    def generate_proactive_care(
        self,
        user_profile: Dict,
        last_interaction: Optional[datetime] = None,
        context: str = ""
    ) -> Optional[str]:
        """
        生成主动关怀消息

        Args:
            user_profile: 用户画像
            last_interaction: 上次交互时间
            context: 额外上下文（如天气、节日等）

        Returns:
            主动关怀消息，或None（如果不需要）
        """
        # 构建主动关怀提示
        prompt_parts = [f'你是安心宝，需要主动关心{user_profile.get('name', '老人家')}。']

        # 检查重要日期
        today = datetime.now()
        important_dates = user_profile.get('important_dates', {})
        for event, date_str in important_dates.items():
            try:
                if date_str.endswith(f'{today.month}-{today.day}'):
                    prompt_parts.append(f'今天是{event}！')
            except:
                pass

        # 检查距离上次互动的时间
        if last_interaction:
            days_since = (today - last_interaction).days
            if days_since >= 2:
                prompt_parts.append(f'已经{days_since}天没有聊天了。')

        # 添加上下文
        if context:
            prompt_parts.append(context)

        # 构建完整提示
        prompt = '\n'.join(prompt_parts)
        prompt += '\n\n请生成一条简短、温暖的主动关怀消息（不超过50字），像老朋友打招呼一样自然。只输出消息内容。'

        try:
            response = Generation.call(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                result_format='message',
                temperature=0.8
            )

            if response.status_code == 200:
                return response.output.choices[0].message.content.strip()

        except Exception as e:
            print(f'生成主动关怀消息错误: {e}')

        return None

    def generate_food_therapy(self, symptom: str) -> Dict:
        """
        生成食疗建议

        Args:
            symptom: 症状描述

        Returns:
            食疗建议字典
        """
        prompt = f"""根据以下症状，给出一个简单易做的食疗方子。

症状：{symptom}

请用JSON格式回复，包含以下字段：
- name: 食疗名称
- ingredients: 材料列表
- steps: 做法步骤
- effect: 功效说明

只输出JSON，不要其他内容。"""

        try:
            response = Generation.call(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                result_format='message',
                temperature=0.5
            )

            if response.status_code == 200:
                content = response.output.choices[0].message.content

                # 提取JSON
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))

        except Exception as e:
            print(f'生成食疗建议错误: {e}')

        # 返回默认建议
        return {
            'name': '红枣枸杞茶',
            'ingredients': ['红枣5颗', '枸杞10粒'],
            'steps': '开水冲泡，焖5分钟即可饮用',
            'effect': '补气养血，增强体质'
        }

    def extract_user_info(self, conversation_history: List[Dict]) -> Dict:
        """
        从对话历史中提取用户信息用于更新画像

        Args:
            conversation_history: 对话历史

        Returns:
            提取的用户信息
        """
        if len(conversation_history) < 2:
            return {}

        # 只取最近10轮对话
        recent_history = conversation_history[-20:]
        conversation_text = '\n'.join([
            f"{'用户' if msg['role'] == 'user' else 'AI'}：{msg['content']}"
            for msg in recent_history
        ])

        prompt = f"""请从以下对话中提取老人的个人信息。

对话记录：
{conversation_text}

请用JSON格式输出提取到的信息，可能包含：
- interests: 兴趣爱好（数组）
- family_members: 家庭成员提及（数组）
- health_mentions: 健康相关提及（数组）
- preferences: 偏好习惯
- mood_patterns: 情绪模式
- important_info: 其他重要信息

如果某项没有提取到，就不要包含该字段。只输出JSON。"""

        try:
            response = Generation.call(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                result_format='message',
                temperature=0.3
            )

            if response.status_code == 200:
                content = response.output.choices[0].message.content
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))

        except Exception as e:
            print(f'提取用户信息错误: {e}')

        return {}

    # ==================== 异步包装方法 ====================
    # 以下方法通过 asyncio.to_thread() 将同步的 Generation.call()
    # 放到线程池执行，避免阻塞 FastAPI 的事件循环

    async def analyze_emotion_async(self, text: str) -> Dict:
        """情绪分析（异步版本）"""
        return await asyncio.to_thread(self.analyze_emotion, text)

    async def generate_food_therapy_async(self, symptom: str) -> Dict:
        """生成食疗建议（异步版本）"""
        return await asyncio.to_thread(self.generate_food_therapy, symptom)

    async def generate_proactive_care_async(
        self,
        user_profile: Dict,
        last_interaction: Optional[datetime] = None,
        context: str = ""
    ) -> Optional[str]:
        """生成主动关怀消息（异步版本）"""
        return await asyncio.to_thread(
            self.generate_proactive_care, user_profile, last_interaction, context
        )

    async def extract_user_info_async(self, conversation_history: List[Dict]) -> Dict:
        """从对话历史中提取用户信息（异步版本）"""
        return await asyncio.to_thread(self.extract_user_info, conversation_history)


# 全局实例
chat_service = QwenChatService()
