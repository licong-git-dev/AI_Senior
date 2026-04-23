"""
Fix remaining 22 broken files with complex quote issues.
These need specific per-line or per-pattern fixes.
"""
import ast
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "D:/app/PythonFiles/AI_Senior/anxinbao-server"
BS = chr(92)
DQ = chr(34)
SQ = chr(39)


def fix_file(filepath):
    """Read, fix, validate, and write a file. Return (success, error)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Apply all general fixes
    content = general_fixes(content)

    # Apply file-specific fixes
    rel = os.path.relpath(filepath, BASE).replace(os.sep, '/')
    content = specific_fixes(rel, content)

    if content == original:
        return False, "No changes made"

    try:
        ast.parse(content)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"


def general_fixes(content):
    """Apply general fixes that work across files."""

    # Fix remaining dict key mismatches: 'key\": -> "key":  and  "key': -> "key":
    # These have a backslash still present
    content = re.sub(SQ + r'(\w+)' + BS + DQ + ':', DQ + r'\1' + DQ + ':', content)

    # Fix string join pattern: "'.join(x) -> " ".join(x) -- but this is actually
    # likely '' (empty string) join -> "".join
    # Actually, looking at the context: number_str = "'.join(numbers) should be
    # number_str = " ".join(numbers) or "".join(numbers)
    # Let's check: it's a number string, so likely "".join(numbers)
    # But we can't know for sure. Let's handle the quote issue: "' should be ""
    # "'.join -> "".join
    content = content.replace(DQ + SQ + '.join(', DQ + DQ + '.join(')

    # Fix: ', \".join(formatted) -> ', '.join(formatted) -- qwen_service pattern
    content = content.replace("', " + BS + DQ + ".join(", "', '.join(")

    # Fix: '\"从字典创建\"\"' pattern -> """从字典创建"""
    # This is:  ' " ' text " " '  -> should be """ text """
    # Actually it's the remnant of a broken docstring. Let's handle it.
    # Pattern: '"' + text + '""' on a line = broken docstring
    lines = content.split(chr(10))
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Pattern: '"'text""' -> """text"""
        if stripped.startswith(SQ + DQ + SQ) and stripped.endswith(DQ + DQ + SQ):
            inner = stripped[3:-3]
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = indent + DQ*3 + inner + DQ*3
        elif stripped.startswith(SQ + DQ + SQ) and stripped.endswith(DQ + DQ + DQ):
            inner = stripped[3:-3]
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = indent + DQ*3 + inner + DQ*3

    content = chr(10).join(lines)

    return content


def specific_fixes(rel_path, content):
    """Apply file-specific fixes."""

    if rel_path == 'app/api/admin.py':
        # f\"维护模式已{'开启' if enabled else '关闭\"}" -> f"维护模式已{'开启' if enabled else '关闭'}"
        content = content.replace(
            "f" + BS + DQ + "维护模式已{'开启' if enabled else '关闭" + BS + DQ + "}" + DQ,
            "f" + DQ + "维护模式已{'开启' if enabled else '关闭'}" + DQ
        )

    if rel_path == 'app/api/cognitive_api.py':
        # 'type\": "find_target\", -> "type": "find_target",
        content = content.replace(
            SQ + "type" + BS + DQ + ": " + DQ + "find_target" + BS + DQ + ",",
            DQ + "type" + DQ + ": " + DQ + "find_target" + DQ + ","
        )
        # f'在下面的选项中找到 '{target}'' -> f"在下面的选项中找到 '{target}'"
        content = content.replace(
            "f'在下面的选项中找到 '{target}''",
            'f"在下面的选项中找到 ' + SQ + '{target}' + SQ + '"'
        )
        # 'time_limit\": 10 -> "time_limit": 10
        content = content.replace(
            SQ + "time_limit" + BS + DQ + ":",
            DQ + "time_limit" + DQ + ":"
        )

    if rel_path == 'app/api/onboarding.py':
        # '您好!...请点击'开始\"按钮,...设置。" -> "您好!...请点击'开始'按钮,...设置。"
        content = content.replace(
            "请点击'开始" + BS + DQ + "按钮,我来帮您完成设置。" + DQ,
            '请点击' + SQ + '开始' + SQ + '按钮,我来帮您完成设置。' + DQ
        )
        # Fix the line more comprehensively
        content = content.replace(
            SQ + "您好!欢迎使用安心宝。请点击" + SQ + "开始" + SQ + "按钮,我来帮您完成设置。" + DQ,
            DQ + "您好!欢迎使用安心宝。请点击'开始'按钮,我来帮您完成设置。" + DQ
        )
        # \"voice_guide': -> "voice_guide":
        content = content.replace(BS + DQ + "voice_guide':", DQ + "voice_guide" + DQ + ":")

    if rel_path == 'app/api/preferences.py':
        # f'已应用'{preset_name}'预设\" -> f"已应用'{preset_name}'预设"
        content = content.replace(
            "f'已应用'{preset_name}'预设" + BS + DQ,
            'f"已应用' + SQ + '{preset_name}' + SQ + '预设"'
        )
        # "preferences\": -> "preferences":
        content = content.replace(DQ + "preferences" + BS + DQ + ":", DQ + "preferences" + DQ + ":")

    if rel_path == 'app/api/report.py':
        # f'{config.title if config else '报表\"}_{...}_{...}" -> f"{config.title if config else '报表'}_{...}_{...}"
        content = content.replace(
            "f'{config.title if config else '报表" + BS + DQ + "}_{report_request.start_date}_{report_request.end_date}" + DQ,
            "f" + DQ + "{config.title if config else '报表'}_{report_request.start_date}_{report_request.end_date}" + DQ
        )

    if rel_path == 'app/api/subscription.py':
        # 'success\": True -> "success": True
        content = content.replace(SQ + "success" + BS + DQ + ": True", DQ + "success" + DQ + ": True")
        # f\"订阅已取消...无限期\"}" -> f"订阅已取消...无限期'}"
        content = content.replace(
            "f" + BS + DQ + "订阅已取消，服务将持续到 {subscription.end_date.strftime('%Y年%m月%d日') if subscription.end_date else '无限期" + BS + DQ + "}" + DQ,
            "f" + DQ + "订阅已取消，服务将持续到 {subscription.end_date.strftime('%Y年%m月%d日') if subscription.end_date else '无限期'}" + DQ
        )

    if rel_path == 'app/api/voice_feedback.py':
        # f'好的,以后我会叫您\\"{name}\"" -> f"好的,以后我会叫您'{name}'"
        content = content.replace(
            "f'好的,以后我会叫您" + BS + BS + DQ + "{name}" + BS + DQ + DQ,
            "f" + DQ + "好的,以后我会叫您'{name}'" + DQ
        )

    if rel_path == 'app/core/accessibility.py':
        # '"'从字典创建""' -> """从字典创建"""
        content = content.replace(
            SQ + DQ + SQ + "从字典创建" + DQ + DQ + SQ,
            DQ*3 + "从字典创建" + DQ*3
        )

    if rel_path == 'app/core/scheduler.py':
        # f'{name}，{reminder.content or '这是一条提醒\"}" -> f"{name}，{reminder.content or '这是一条提醒'}"
        content = content.replace(
            "f'{name}，{reminder.content or '这是一条提醒" + BS + DQ + "}" + DQ,
            "f" + DQ + "{name}，{reminder.content or '这是一条提醒'}" + DQ
        )

    if rel_path == 'app/schemas/drug.py':
        # description='剂量，如'1片\"") -> description="剂量，如'1片'")
        content = content.replace(
            "description='剂量，如'1片" + BS + DQ + DQ + ")",
            'description="剂量，如' + SQ + '1片' + SQ + '")'
        )
        # description=\"频次，如'twice_daily\"") -> description="频次，如'twice_daily'")
        content = content.replace(
            "description=" + BS + DQ + "频次，如'twice_daily" + BS + DQ + DQ + ")",
            'description="频次，如' + SQ + 'twice_daily' + SQ + '")'
        )
        # description=\"服药时间，如[\"08:00", '20:00']') -> description="服药时间，如['08:00', '20:00']")
        content = content.replace(
            "description=" + BS + DQ + "服药时间，如[" + BS + DQ + '08:00", ' + SQ + "20:00']')",
            'description="服药时间，如[' + SQ + '08:00' + SQ + ', ' + SQ + '20:00' + SQ + ']")'
        )

    if rel_path == 'app/schemas/medication.py':
        # description=\"服药时间，如[\"08:00\", '20:00']') -> description="服药时间，如['08:00', '20:00']")
        content = content.replace(
            "description=" + BS + DQ + "服药时间，如[" + BS + DQ + "08:00" + BS + DQ + ", '20:00']')",
            'description="服药时间，如[' + SQ + '08:00' + SQ + ', ' + SQ + '20:00' + SQ + ']")'
        )

    if rel_path == 'app/schemas/nutrition.py':
        # description='份量描述，如'100g\"\")" -> description="份量描述，如'100g'")
        content = content.replace(
            "description='份量描述，如'100g" + BS + DQ + BS + DQ + ")",
            'description="份量描述，如' + SQ + '100g' + SQ + '")'
        )

    if rel_path == 'app/services/cognitive_game_service.py':
        # Already handled by general fix: "'.join -> "".join
        pass

    if rel_path == 'app/services/message_center_service.py':
        # f'msg_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S")}_{self._message_counter}'
        # -> f"msg_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._message_counter}"
        content = content.replace(
            "f'msg_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S" + DQ + ")}_{self._message_counter}'",
            'f"msg_{user_id}_{datetime.now().strftime(' + SQ + '%Y%m%d%H%M%S' + SQ + ')}_{self._message_counter}"'
        )

    if rel_path == 'app/services/onboarding_service.py':
        # Complex multiline list with broken quotes
        # "安心宝是专为您设计的智能助手\", -> "安心宝是专为您设计的智能助手",
        content = content.replace(
            "安心宝是专为您设计的智能助手" + BS + DQ + ",",
            "安心宝是专为您设计的智能助手" + DQ + ","
        )
        # '您可以随时说'帮助'获取使用指导\", -> "您可以随时说'帮助'获取使用指导",
        content = content.replace(
            SQ + "您可以随时说'帮助'获取使用指导" + BS + DQ + ",",
            DQ + "您可以随时说'帮助'获取使用指导" + DQ + ","
        )
        # \"不要着急，我们会慢慢来' -> "不要着急，我们会慢慢来"
        content = content.replace(
            BS + DQ + "不要着急，我们会慢慢来'",
            DQ + "不要着急，我们会慢慢来" + DQ
        )

    if rel_path == 'app/services/qwen_service.py':
        # Already handled by general fix: ', \".join -> ', '.join
        pass

    if rel_path == 'app/services/simplified_mode.py':
        # f'语音命令匹配: '{text}\" -> {action_id}" -> f"语音命令匹配: '{text}' -> {action_id}"
        content = content.replace(
            "f'语音命令匹配: '{text}" + BS + DQ + " -> {action_id}" + DQ + ")",
            'f"语音命令匹配: ' + SQ + '{text}' + SQ + ' -> {action_id}")'
        )

    if rel_path == 'app/services/social_service.py':
        # f'post_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S\")}'
        # -> f"post_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        content = content.replace(
            "f'post_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S" + BS + DQ + ")}'" ,
            'f"post_{user_id}_{datetime.now().strftime(' + SQ + '%Y%m%d%H%M%S' + SQ + ')}"'
        )

    if rel_path == 'app/services/subscription_service.py':
        # f'sub_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S\")}'
        content = content.replace(
            "f'sub_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S" + BS + DQ + ")}'" ,
            'f"sub_{user_id}_{datetime.now().strftime(' + SQ + '%Y%m%d%H%M%S' + SQ + ')}"'
        )

    if rel_path == 'app/services/support_service.py':
        # f'TK{datetime.now().strftime('%Y%m%d\")}{self.ticket_counter:04d}'
        content = content.replace(
            "f'TK{datetime.now().strftime('%Y%m%d" + BS + DQ + ")}{self.ticket_counter:04d}'",
            'f"TK{datetime.now().strftime(' + SQ + '%Y%m%d' + SQ + ')}{self.ticket_counter:04d}"'
        )

    if rel_path == 'app/services/voice_feedback_service.py':
        # This file has many complex broken patterns in a template dict
        # Need to fix the whole template section
        # 'help\": [ -> "help": [
        content = content.replace(SQ + "help" + BS + DQ + ": [", DQ + "help" + DQ + ": [")
        # \"需要帮助吗?您可以说'{command}\"。", -> "需要帮助吗?您可以说'{command}'。",
        content = content.replace(
            BS + DQ + "需要帮助吗?您可以说'{command}" + BS + DQ + "。" + DQ + ",",
            DQ + "需要帮助吗?您可以说'{command}'。" + DQ + ","
        )
        # \"如果需要帮助,随时说'帮助'或'帮我\"。", -> "如果需要帮助,随时说'帮助'或'帮我'。",
        content = content.replace(
            BS + DQ + "如果需要帮助,随时说'帮助'或'帮我" + BS + DQ + "。" + DQ + ",",
            DQ + "如果需要帮助,随时说'帮助'或'帮我'。" + DQ + ","
        )
        # \"有什么不明白的,可以问我哦。' -> "有什么不明白的,可以问我哦。"
        content = content.replace(
            BS + DQ + "有什么不明白的,可以问我哦。'",
            DQ + "有什么不明白的,可以问我哦。" + DQ
        )
        # '小提示：{tip}', -> '小提示：{tip}', (likely ok)
        # '温馨提醒：{tip}\", -> "温馨提醒：{tip}",
        content = content.replace(
            SQ + "温馨提醒：{tip}" + BS + DQ + ",",
            DQ + "温馨提醒：{tip}" + DQ + ","
        )

    if rel_path == 'app/services/xfyun_service.py':
        # f\"algorithm="hmac-sha256", ' -> f'algorithm="hmac-sha256", '
        content = content.replace(
            "f" + BS + DQ + 'algorithm="hmac-sha256", ' + SQ,
            "f'algorithm=" + BS + DQ + "hmac-sha256" + BS + DQ + ", '"
        )
        # f'headers="host date request-line", ' -> f'headers="host date request-line", '
        # This one is already using ' delimiters and contains " inside, which is valid
        # f'signature="{signature_sha_base64}"" -> f'signature="{signature_sha_base64}"'
        content = content.replace(
            'f' + SQ + 'signature="{signature_sha_base64}"' + DQ,
            'f' + SQ + 'signature="{signature_sha_base64}"' + SQ
        )

    return content


def main():
    broken_files = [
        'app/api/admin.py',
        'app/api/cognitive_api.py',
        'app/api/onboarding.py',
        'app/api/preferences.py',
        'app/api/report.py',
        'app/api/subscription.py',
        'app/api/voice_feedback.py',
        'app/core/accessibility.py',
        'app/core/scheduler.py',
        'app/schemas/drug.py',
        'app/schemas/medication.py',
        'app/schemas/nutrition.py',
        'app/services/cognitive_game_service.py',
        'app/services/message_center_service.py',
        'app/services/onboarding_service.py',
        'app/services/qwen_service.py',
        'app/services/simplified_mode.py',
        'app/services/social_service.py',
        'app/services/subscription_service.py',
        'app/services/support_service.py',
        'app/services/voice_feedback_service.py',
        'app/services/xfyun_service.py',
    ]

    fixed = []
    still_broken = []

    for rel in broken_files:
        filepath = os.path.join(BASE, rel.replace('/', os.sep))
        ok, err = fix_file(filepath)
        if ok:
            fixed.append(rel)
        else:
            still_broken.append((rel, err))

    print("=== FIXED (Round 2) ===")
    for p in fixed:
        print(f"  {p}")
    print(f"Total fixed: {len(fixed)}")
    print()
    if still_broken:
        print("=== STILL BROKEN ===")
        for p, e in still_broken:
            print(f"  {p}: {e}")
        print(f"Total still broken: {len(still_broken)}")


if __name__ == '__main__':
    main()
