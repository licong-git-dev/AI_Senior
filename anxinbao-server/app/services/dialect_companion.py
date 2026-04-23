"""
方言情感陪伴模板库
核心卖点"用乡音守护爸妈"的内容支撑

支持方言：武汉话(wuhan)、鄂州话(ezhou)、普通话(mandarin)
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import random
from datetime import datetime


# ==================== 方言问候语库 ====================

DIALECT_GREETINGS = {
    "wuhan": {
        "morning": [
            "{name}，早啊！今天起得蛮早嘞，精神不错！",
            "早上好{name}！外头天气{weather}，出门记得带伞啊。",
            "{name}早啊！早饭恰了冇？莫空着肚子。",
            "哎呀{name}，又是新的一天！今天想搞么事？",
            "{name}早上好！昨晚睡得好不好？有冇做好梦？",
        ],
        "afternoon": [
            "{name}，中午好！午觉困不困，歇一哈。",
            "下午好{name}！今天中饭恰了么事好的？",
            "{name}，下午了，莫一直坐着，起来走动走动。",
            "哎{name}，下午好！要不要我给你讲个笑话听听？",
        ],
        "evening": [
            "{name}，晚上好！今天过得开不开心？",
            "晚上好{name}！外头黑了，莫出门了啊。",
            "{name}，恰了晚饭冇？莫太晚恰，对胃不好。",
            "哎{name}，晚上好！今天有冇跟隔壁王阿姨聊天？",
            "{name}晚上好！天冷了，记得加件衣裳。",
        ],
        "night": [
            "{name}，夜深了，该困觉了。明天又是好天气！",
            "太晚了{name}，莫看手机了，对眼睛不好。晚安！",
            "{name}，该睡了，我在这守着您，晚安！",
        ],
    },
    "ezhou": {
        "morning": [
            "{name}，早啊！起来了啵？今天天气蛮好。",
            "早上好{name}！早饭吃了冇？记得吃个鸡蛋。",
            "{name}早啊！昨夜睡得好不好？精神好冇？",
            "哎{name}，大清早的，出去走走，活动活动。",
        ],
        "afternoon": [
            "{name}，下午好！歇了午觉冇？",
            "下午好{name}！莫坐久了，起来动一动。",
            "{name}，中饭吃了么事？要不要我教你搞个菜？",
        ],
        "evening": [
            "{name}，晚上好！今天过得好不好啊？",
            "晚上好{name}！晚饭吃了冇？莫饿着。",
            "{name}，天黑了，出门注意看路。",
            "哎{name}，晚上好！要不要我陪你聊聊天？",
        ],
        "night": [
            "{name}，夜深了，早点睡。明天再聊！",
            "太晚了{name}，该休息了。晚安！",
        ],
    },
    "mandarin": {
        "morning": [
            "{name}，早上好！今天天气{weather}，心情怎么样？",
            "早安{name}！新的一天开始了，吃早餐了吗？",
            "{name}早上好！昨晚休息得好吗？",
            "早上好{name}！今天有什么计划？",
        ],
        "afternoon": [
            "{name}，下午好！午饭吃了吗？",
            "下午好{name}！记得站起来活动活动。",
            "{name}，下午好！今天过得顺利吗？",
        ],
        "evening": [
            "{name}，晚上好！今天过得开心吗？",
            "晚上好{name}！晚饭别太晚吃哦。",
            "{name}，晚上好！天冷了注意保暖。",
        ],
        "night": [
            "{name}，夜深了，该休息了。晚安！",
            "太晚了{name}，早点睡，对身体好。晚安！",
        ],
    },
}


# ==================== 方言情感回应库 ====================

DIALECT_EMOTION_RESPONSES = {
    "wuhan": {
        "lonely": [
            "{name}，我晓得一个人在屋里闷得慌。要不我陪你聊聊？",
            "莫一个人闷着，{name}。{child_name}虽然不在身边，但心里一直想着您嘞。",
            "{name}，想伢了是不是？要不要我帮你跟{child_name}打个电话？",
            "一个人在屋里也莫急，{name}。我一直在这陪着您。",
        ],
        "sad": [
            "{name}，莫难过。有么事心里话跟我说说？",
            "哎{name}，看你不开心，是身体不舒服还是想家里人了？",
            "{name}莫伤心，日子总会越来越好的。来，我给你讲个开心的事。",
        ],
        "anxious": [
            "{name}莫急莫急，慢慢来，么事都有办法的。",
            "别着急{name}，深呼吸，慢慢跟我说是么事。",
            "{name}，莫担心。我在这里帮您想办法。",
        ],
        "happy": [
            "哎呀{name}，看你笑得这么开心，发生了么好事？",
            "{name}今天心情蛮好嘞！开心就对了！",
            "哈哈{name}，您一笑我都觉得开心！",
        ],
        "tired": [
            "{name}，累了就歇一哈，身体最重要。",
            "莫太累了{name}，来坐下歇歇，我给你放首歌听。",
            "{name}，累了就莫忙了，休息一下。",
        ],
        "pain": [
            "{name}，哪里不舒服？跟我说说，莫硬撑着。",
            "身体不舒服莫忍着{name}，要不要我帮您通知{child_name}？",
            "{name}，莫怕，我帮您记下来。严重的话我们去看看医生。",
        ],
    },
    "ezhou": {
        "lonely": [
            "{name}，一个人在屋里？莫闷着，跟我聊几句。",
            "想伢了啵{name}？{child_name}挂念着您嘞。",
            "{name}，我陪您说说话，比一个人坐着强。",
        ],
        "sad": [
            "{name}，不开心了？跟我讲讲是么事。",
            "莫难过{name}，有我在。想说么事都可以。",
        ],
        "anxious": [
            "{name}莫急，慢慢来，我帮您想办法。",
            "别慌{name}，深吸口气，一件一件来。",
        ],
        "happy": [
            "哎{name}，今天蛮开心嘞！好事要分享！",
            "{name}笑起来真好看！继续保持！",
        ],
        "tired": [
            "{name}累了就歇一下，身体要紧。",
            "莫太拼了{name}，歇歇再做。",
        ],
        "pain": [
            "{name}，哪里不得劲？跟我说说。",
            "身体不舒服莫扛着{name}，要不要通知家里人？",
        ],
    },
    "mandarin": {
        "lonely": [
            "{name}，一个人在家吗？我来陪您聊聊天。",
            "{name}，{child_name}虽然不在身边，但一直惦记着您呢。",
            "想家人了吧{name}？要不要给{child_name}打个电话？",
        ],
        "sad": [
            "{name}，看起来不太开心，有什么心事吗？",
            "别难过{name}，有什么想说的都可以跟我聊。",
        ],
        "anxious": [
            "{name}别着急，慢慢来，有什么我可以帮忙的？",
            "别担心{name}，深呼吸，一切都会好起来的。",
        ],
        "happy": [
            "{name}今天心情真好！发生什么开心的事了？",
            "看到您开心我也高兴，{name}！",
        ],
        "tired": [
            "{name}累了就休息一下，身体最重要。",
            "别太累了{name}，坐下来歇一会儿。",
        ],
        "pain": [
            "{name}，哪里不舒服？跟我说说。",
            "身体不舒服别硬撑{name}，需要通知家人吗？",
        ],
    },
}


# ==================== 方言食疗建议语库 ====================

DIALECT_FOOD_THERAPY = {
    "wuhan": {
        "hypertension": [
            "血压高了{name}，搞碗芹菜粥喝，武汉菜场芹菜新鲜得很。清淡点恰，莫吃太咸。",
            "{name}，血压偏高。来个荷叶莲子汤，我们武汉莲子好嘞。",
        ],
        "insomnia": [
            "{name}困觉不好？来碗酸枣仁汤，小火慢慢熬，助眠效果蛮好。",
            "睡不着{name}？晚上泡杯菊花茶，放点枸杞，安神。",
        ],
        "cold": [
            "{name}感冒了啊？搞碗姜汤，加红糖，趁热喝了捂被子发发汗。",
            "着凉了{name}？来个萝卜排骨汤，暖身子又补营养。",
        ],
        "digestion": [
            "{name}胃不舒服？搞点小米粥，养胃。武汉热干面先莫恰了。",
            "消化不好{name}？山楂泡水喝，开胃消食。",
        ],
        "general": [
            "{name}，今天搞个排骨藕汤怎么样？我们湖北的藕是全国最好的！",
            "换个口味{name}，来个莲藕炖猪蹄，补胶原蛋白，皮肤好。",
            "{name}，天冷了搞个鸡汤，加几颗红枣枸杞，暖和又滋补。",
        ],
    },
    "ezhou": {
        "hypertension": [
            "血压高了{name}，搞碗芹菜粥，清淡点吃。莫吃太咸的。",
            "{name}，来个木耳拌黄瓜，降压效果好。",
        ],
        "insomnia": [
            "{name}睡不好觉？煮点百合莲子汤，安神助眠。",
            "失眠了{name}？牛奶加蜂蜜，睡前喝一杯。",
        ],
        "cold": [
            "{name}感冒了？姜汤加红糖，趁热喝。",
            "着凉了{name}？搞碗鸡蛋面，加点葱花姜丝。",
        ],
        "general": [
            "{name}，来个鱼汤怎么样？鄂州的鱼最好吃。",
            "今天给自己搞个好的{name}，莲藕排骨汤，滋补。",
        ],
    },
    "mandarin": {
        "hypertension": [
            "{name}，血压偏高。建议喝点芹菜粥，清淡饮食。",
            "血压高了{name}，试试木耳拌黄瓜，对血管好。",
        ],
        "insomnia": [
            "{name}睡不好？试试酸枣仁汤，安神助眠效果好。",
            "失眠了{name}？睡前喝杯温牛奶，泡泡脚。",
        ],
        "cold": [
            "{name}感冒了？来碗姜汤加红糖，趁热喝。",
            "着凉了{name}？鸡汤加点生姜，暖身又补气。",
        ],
        "general": [
            "{name}，今天试试排骨莲藕汤，营养丰富又美味。",
            "换个口味{name}，百合银耳羹，润肺养颜。",
        ],
    },
}


# ==================== 方言关怀提醒语库 ====================

DIALECT_CARE_REMINDERS = {
    "wuhan": {
        "medication": [
            "{name}，该恰药了！{medicine_name}莫忘了哈。",
            "恰药时间到了{name}！{medicine_name}，一天不能少。",
            "{name}，药恰了冇？{medicine_name}要按时恰，身体才好。",
        ],
        "water": [
            "{name}，喝杯水吧！今天喝水少了点。",
            "该喝水了{name}！莫等到口渴才喝。",
        ],
        "exercise": [
            "{name}，坐久了，起来走动走动。去楼下散个步？",
            "该活动活动了{name}！走几步，舒展一下。",
        ],
        "meal": [
            "{name}，该恰饭了！莫饿着肚子。",
            "饭点到了{name}！今天想恰么事？",
        ],
        "weather": [
            "{name}，明天{weather}，出门记得{advice}。",
            "天气预报说明天{weather}，{name}注意{advice}。",
        ],
    },
    "ezhou": {
        "medication": [
            "{name}，该吃药了！{medicine_name}莫忘了。",
            "吃药时间到了{name}！{medicine_name}记得吃。",
        ],
        "water": [
            "{name}，喝杯水吧，今天喝得少了。",
            "该喝水了{name}！多喝水身体好。",
        ],
        "exercise": [
            "{name}，起来动一动，别老坐着。",
            "该活动了{name}！去外头走走。",
        ],
        "meal": [
            "{name}，该吃饭了！莫饿着。",
            "饭点了{name}！今天想吃么事？",
        ],
    },
    "mandarin": {
        "medication": [
            "{name}，该吃药了！{medicine_name}别忘了。",
            "吃药时间到了{name}！{medicine_name}要按时服用。",
        ],
        "water": [
            "{name}，该喝水了！今天喝水不太够哦。",
            "记得多喝水{name}！保持身体水分充足。",
        ],
        "exercise": [
            "{name}，坐久了起来活动活动吧。",
            "该运动了{name}！散个步对身体好。",
        ],
        "meal": [
            "{name}，到饭点了！记得按时吃饭。",
            "该吃饭了{name}！今天想吃什么？",
        ],
    },
}


# ==================== 方言陪伴服务 ====================

class DialectCompanionService:
    """方言情感陪伴服务 — 核心卖点实现"""

    def get_greeting(
        self,
        dialect: str = "mandarin",
        name: str = "您",
        weather: str = "晴天",
        activity: str = "出门散步",
        hour: Optional[int] = None
    ) -> str:
        """获取方言问候语"""
        if hour is None:
            hour = datetime.now().hour

        if 5 <= hour < 11:
            period = "morning"
        elif 11 <= hour < 18:
            period = "afternoon"
        elif 18 <= hour < 22:
            period = "evening"
        else:
            period = "night"

        templates = DIALECT_GREETINGS.get(dialect, DIALECT_GREETINGS["mandarin"])
        greetings = templates.get(period, templates.get("morning", []))

        if not greetings:
            return f"{name}，您好！"

        template = random.choice(greetings)
        return template.format(
            name=name,
            weather=weather,
            activity=activity
        )

    def get_emotion_response(
        self,
        emotion: str,
        dialect: str = "mandarin",
        name: str = "您",
        child_name: str = "孩子"
    ) -> str:
        """根据情绪获取方言安慰/回应"""
        templates = DIALECT_EMOTION_RESPONSES.get(
            dialect, DIALECT_EMOTION_RESPONSES["mandarin"]
        )
        responses = templates.get(emotion, templates.get("lonely", []))

        if not responses:
            return f"{name}，我在这里陪着您。"

        template = random.choice(responses)
        return template.format(name=name, child_name=child_name)

    def get_food_therapy(
        self,
        condition: str,
        dialect: str = "mandarin",
        name: str = "您"
    ) -> str:
        """获取方言食疗建议"""
        templates = DIALECT_FOOD_THERAPY.get(
            dialect, DIALECT_FOOD_THERAPY["mandarin"]
        )
        suggestions = templates.get(condition, templates.get("general", []))

        if not suggestions:
            return f"{name}，注意饮食健康。"

        template = random.choice(suggestions)
        return template.format(name=name)

    def get_care_reminder(
        self,
        reminder_type: str,
        dialect: str = "mandarin",
        name: str = "您",
        **kwargs
    ) -> str:
        """获取方言关怀提醒"""
        templates = DIALECT_CARE_REMINDERS.get(
            dialect, DIALECT_CARE_REMINDERS["mandarin"]
        )
        reminders = templates.get(reminder_type, [])

        if not reminders:
            return f"{name}，请注意身体健康。"

        template = random.choice(reminders)
        return template.format(name=name, **kwargs)


# 全局服务实例
dialect_companion = DialectCompanionService()
