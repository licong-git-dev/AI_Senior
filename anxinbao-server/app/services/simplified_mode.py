"""
简化操作模式服务
为老人提供简洁、易用的操作界面和流程
"""
import logging
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class SimplifiedModeLevel(Enum):
    """简化模式级别"""
    STANDARD = 'standard'  # 标准模式（完整功能）
    SIMPLIFIED = 'simplified'  # 简化模式（精简功能）
    MINIMAL = 'minimal'  # 最小模式（核心功能）
    VOICE_ONLY = "voice_only"  # 纯语音模式


@dataclass
class QuickAction:
    """快捷操作"""
    action_id: str
    name: str
    icon: str
    description: str
    command: str
    params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # 显示优先级，数字越小越靠前
    voice_trigger: List[str] = field(default_factory=list)  # 语音触发词


@dataclass
class SimpleMenu:
    """简化菜单"""
    menu_id: str
    name: str
    icon: str
    actions: List[QuickAction]
    is_visible: bool = True


# ==================== 预设快捷操作 ====================

PRESET_QUICK_ACTIONS = {
    # 通话相关
    "call_family": QuickAction(
        action_id="call_family",
        name='呼叫家人',
        icon='📞',
        description='一键呼叫主要联系人',
        command='call',
        params={"target": "primary_contact"},
        priority=1,
        voice_trigger=['打电话给家人', '呼叫家人', '找家人', '给儿子打电话', '给女儿打电话']
    ),
    'video_call': QuickAction(
        action_id='video_call',
        name='视频通话',
        icon='📹',
        description='发起视频通话',
        command='video_call',
        params={"target": "primary_contact"},
        priority=2,
        voice_trigger=['视频通话', '看看家人', '视频聊天']
    ),

    # 聊天相关
    'start_chat': QuickAction(
        action_id='start_chat',
        name='聊聊天',
        icon='💬',
        description='和安心宝聊天',
        command='chat',
        params={},
        priority=3,
        voice_trigger=['聊天', '说话', '和我聊天', "陪我说话"]
    ),

    # 健康相关
    "health_check": QuickAction(
        action_id="health_check",
        name='测量血压',
        icon='❤️',
        description="记录今日血压",
        command="health_input",
        params={'type': "blood_pressure"},
        priority=4,
        voice_trigger=['测血压', '量血压', "记录血压"]
    ),
    "medication_reminder": QuickAction(
        action_id="medication_reminder",
        name='吃药提醒',
        icon='💊',
        description='查看今日用药',
        command='medication',
        params={},
        priority=5,
        voice_trigger=['该吃什么药', '今天吃什么药', '用药提醒']
    ),

    # 紧急相关
    'sos': QuickAction(
        action_id='sos',
        name='紧急求助',
        icon='🆘',
        description='紧急情况呼叫帮助',
        command='sos',
        params={},
        priority=0,
        voice_trigger=['救命', '帮帮我', '紧急求助', '我不舒服', '摔倒了']
    ),

    # 娱乐相关
    'play_music': QuickAction(
        action_id='play_music',
        name='听音乐',
        icon='🎵',
        description='播放音乐',
        command='play_music',
        params={'genre': 'classic'},
        priority=6,
        voice_trigger=['放音乐', '听歌', '播放音乐', '来首歌']
    ),
    'play_radio': QuickAction(
        action_id='play_radio',
        name='听广播',
        icon='📻',
        description='播放广播电台',
        command='play_radio',
        params={},
        priority=7,
        voice_trigger=['放广播', '听新闻', '播放广播']
    ),
    'play_opera': QuickAction(
        action_id='play_opera',
        name='听戏曲',
        icon='🎭',
        description='播放戏曲',
        command='play_opera',
        params={},
        priority=8,
        voice_trigger=['放戏曲', '听京剧', '听戏']
    ),

    # 生活相关
    'weather': QuickAction(
        action_id='weather',
        name='查天气',
        icon='🌤️',
        description='查看今日天气',
        command='weather',
        params={},
        priority=9,
        voice_trigger=['今天天气', '天气怎么样', '会下雨吗']
    ),
    'time': QuickAction(
        action_id='time',
        name='几点了',
        icon='🕐',
        description='查看当前时间',
        command='time',
        params={},
        priority=10,
        voice_trigger=['几点了', '现在几点', '什么时间']
    ),

    # 智能家居
    'lights_on': QuickAction(
        action_id='lights_on',
        name='开灯',
        icon='💡',
        description='打开房间灯光',
        command='iot',
        params={'device_type': 'light', 'action': 'turn_on'},
        priority=11,
        voice_trigger=['开灯', '打开灯', '太黑了']
    ),
    'lights_off': QuickAction(
        action_id='lights_off',
        name='关灯',
        icon='🌙',
        description='关闭房间灯光',
        command='iot',
        params={'device_type': 'light', 'action': 'turn_off'},
        priority=12,
        voice_trigger=['关灯', '关掉灯', '睡觉了']
    ),
    'ac_on': QuickAction(
        action_id='ac_on',
        name='开空调',
        icon='❄️',
        description='打开空调',
        command='iot',
        params={'device_type': 'ac', 'action': 'turn_on'},
        priority=13,
        voice_trigger=['开空调', '打开空调', '太热了', "太冷了"]
    )
}


# ==================== 简化菜单预设 ====================

PRESET_MENUS = {
    SimplifiedModeLevel.SIMPLIFIED: [
        SimpleMenu(
            menu_id="communication",
            name='联系',
            icon="📱",
            actions=[
                PRESET_QUICK_ACTIONS["call_family"],
                PRESET_QUICK_ACTIONS['video_call'],
                PRESET_QUICK_ACTIONS['start_chat']
            ]
        ),
        SimpleMenu(
            menu_id='health',
            name='健康',
            icon="❤️",
            actions=[
                PRESET_QUICK_ACTIONS["health_check"],
                PRESET_QUICK_ACTIONS["medication_reminder"]
            ]
        ),
        SimpleMenu(
            menu_id="entertainment",
            name='娱乐',
            icon='🎵',
            actions=[
                PRESET_QUICK_ACTIONS['play_music'],
                PRESET_QUICK_ACTIONS['play_radio'],
                PRESET_QUICK_ACTIONS['play_opera']
            ]
        ),
        SimpleMenu(
            menu_id='emergency',
            name='紧急',
            icon='🆘',
            actions=[
                PRESET_QUICK_ACTIONS['sos']
            ]
        )
    ],
    SimplifiedModeLevel.MINIMAL: [
        SimpleMenu(
            menu_id='main',
            name='主菜单',
            icon='🏠',
            actions=[
                PRESET_QUICK_ACTIONS["sos"],
                PRESET_QUICK_ACTIONS["call_family"],
                PRESET_QUICK_ACTIONS['start_chat']
            ]
        )
    ],
    SimplifiedModeLevel.VOICE_ONLY: []  # 纯语音模式无需菜单
}


# ==================== 语音命令解析 ====================

class VoiceCommandParser:
    """语音命令解析器"""

    def __init__(self):
        self.commands = PRESET_QUICK_ACTIONS

    def parse(self, text: str) -> Optional[QuickAction]:
        """
        解析语音文本，匹配快捷操作

        Args:
            text: 语音识别文本

        Returns:
            匹配到的快捷操作，未匹配返回None
        """
        text_lower = text.lower().strip()

        # 遍历所有快捷操作的触发词
        for action_id, action in self.commands.items():
            for trigger in action.voice_trigger:
                if trigger in text_lower:
                    logger.info(f"语音命令匹配: '{text}' -> {action_id}")
                    return action

        return None

    def get_suggestions(self, text: str) -> List[QuickAction]:
        """
        获取可能的命令建议

        基于部分匹配返回可能的操作
        """
        suggestions = []
        text_lower = text.lower().strip()

        for action_id, action in self.commands.items():
            # 检查名称匹配
            if any(char in action.name for char in text_lower):
                suggestions.append(action)
                continue

            # 检查触发词部分匹配
            for trigger in action.voice_trigger:
                if any(char in trigger for char in text_lower):
                    suggestions.append(action)
                    break

        return suggestions[:5]  # 最多返回5个建议


# ==================== 简化模式管理器 ====================

class SimplifiedModeManager:
    """简化模式管理器"""

    def __init__(self):
        self.user_modes: Dict[int, SimplifiedModeLevel] = {}
        self.user_quick_actions: Dict[int, List[str]] = {}  # 用户自定义快捷操作
        self.voice_parser = VoiceCommandParser()

    def get_user_mode(self, user_id: int) -> SimplifiedModeLevel:
        """获取用户当前模式"""
        return self.user_modes.get(user_id, SimplifiedModeLevel.SIMPLIFIED)

    def set_user_mode(self, user_id: int, mode: SimplifiedModeLevel):
        """设置用户模式"""
        self.user_modes[user_id] = mode
        logger.info(f"用户 {user_id} 模式设为: {mode.value}")

    def get_menus(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的简化菜单"""
        mode = self.get_user_mode(user_id)
        menus = PRESET_MENUS.get(mode, [])

        return [
            {
                'menu_id': menu.menu_id,
                'name': menu.name,
                'icon': menu.icon,
                'is_visible': menu.is_visible,
                'actions': [
                    {
                        'action_id': action.action_id,
                        'name': action.name,
                        'icon': action.icon,
                        "description": action.description,
                        'priority': action.priority
                    }
                    for action in menu.actions
                ]
            }
            for menu in menus
        ]

    def get_quick_actions(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的快捷操作列表"""
        mode = self.get_user_mode(user_id)

        # 根据模式返回不同数量的快捷操作
        if mode == SimplifiedModeLevel.MINIMAL:
            action_ids = ['sos', 'call_family', 'start_chat']
        elif mode == SimplifiedModeLevel.VOICE_ONLY:
            action_ids = ['sos']  # 语音模式仅保留SOS
        else:
            # 简化模式返回常用操作
            action_ids = [
                'sos', 'call_family', 'start_chat',
                'health_check', 'play_music', 'weather'
            ]

        # 用户自定义优先
        custom_actions = self.user_quick_actions.get(user_id, [])
        if custom_actions:
            action_ids = custom_actions

        actions = []
        for action_id in action_ids:
            action = PRESET_QUICK_ACTIONS.get(action_id)
            if action:
                actions.append({
                    'action_id': action.action_id,
                    'name': action.name,
                    "icon": action.icon,
                    "description": action.description,
                    'command': action.command,
                    'params': action.params,
                    'priority': action.priority
                })

        # 按优先级排序
        actions.sort(key=lambda x: x["priority"])
        return actions

    def set_user_quick_actions(self, user_id: int, action_ids: List[str]):
        """设置用户自定义快捷操作"""
        # 验证操作ID
        valid_ids = [
            aid for aid in action_ids
            if aid in PRESET_QUICK_ACTIONS
        ]
        self.user_quick_actions[user_id] = valid_ids
        logger.info(f"用户 {user_id} 快捷操作设为: {valid_ids}")

    def parse_voice_command(self, text: str) -> Optional[Dict[str, Any]]:
        """解析语音命令"""
        action = self.voice_parser.parse(text)
        if action:
            return {
                'matched': True,
                'action_id': action.action_id,
                'name': action.name,
                'command': action.command,
                'params': action.params
            }
        return {'matched': False, 'text': text}

    def get_voice_suggestions(self, text: str) -> List[Dict[str, str]]:
        """获取语音命令建议"""
        suggestions = self.voice_parser.get_suggestions(text)
        return [
            {
                'action_id': s.action_id,
                'name': s.name,
                'icon': s.icon
            }
            for s in suggestions
        ]

    def get_all_voice_triggers(self) -> Dict[str, List[str]]:
        """获取所有语音触发词"""
        return {
            action_id: action.voice_trigger
            for action_id, action in PRESET_QUICK_ACTIONS.items()
        }

    def execute_action(
        self,
        user_id: int,
        action_id: str
    ) -> Dict[str, Any]:
        """
        执行快捷操作

        实际执行逻辑需要根据command类型调用相应服务
        """
        action = PRESET_QUICK_ACTIONS.get(action_id)
        if not action:
            return {'success': False, 'error': "未知操作"}

        logger.info(f"用户 {user_id} 执行操作: {action_id}")

        return {
            'success': True,
            'action_id': action_id,
            'command': action.command,
            'params': action.params,
            "message": f"正在执行: {action.name}"
        }


# ==================== 操作引导服务 ====================

class OperationGuideService:
    """操作引导服务"""

    # 操作步骤指引
    OPERATION_GUIDES = {
        "call_family": [
            {'step': 1, 'text': '点击\'呼叫家人\'按钮', "voice": "请点击屏幕中央的呼叫家人按钮"},
            {'step': 2, 'text': '等待接通', 'voice': '正在呼叫，请稍等'},
            {'step': 3, 'text': '开始通话', 'voice': "已接通，请开始通话"}
        ],
        "health_check": [
            {'step': 1, 'text': '点击\"测量血压\"', 'voice': '请点击测量血压按钮'},
            {'step': 2, 'text': '佩戴血压计', "voice": "请将血压计袖带缠绕在左臂上"},
            {'step': 3, 'text': '保持安静', "voice": "请保持安静，不要说话和移动"},
            {'step': 4, 'text': '开始测量', 'voice': '正在测量，请稍等'},
            {'step': 5, 'text': '查看结果', "voice": "测量完成，您的血压是..."}
        ],
        'sos': [
            {'step': 1, 'text': '按住SOS按钮3秒', "voice": "请按住红色的紧急按钮3秒钟"},
            {'step': 2, 'text': '确认求助', 'voice': '确认要发送紧急求助吗'},
            {'step': 3, 'text': '等待帮助', "voice": "已发送求助，正在通知您的家人"}
        ]
    }

    @classmethod
    def get_guide(cls, action_id: str) -> List[Dict]:
        """获取操作指引"""
        return cls.OPERATION_GUIDES.get(action_id, [])

    @classmethod
    def get_step_voice(cls, action_id: str, step: int) -> Optional[str]:
        """获取步骤语音提示"""
        guide = cls.OPERATION_GUIDES.get(action_id, [])
        for item in guide:
            if item['step'] == step:
                return item.get("voice")
        return None


# 全局实例
simplified_mode_manager = SimplifiedModeManager()
operation_guide = OperationGuideService()
