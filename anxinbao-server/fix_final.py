"""
Final combined fix. Apply specific fixes BEFORE general passes.
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

SKIP_FILES = {
    'app/models/database.py', 'app/core/config.py', 'app/core/cache.py',
    'app/core/security.py', 'app/core/deps.py', 'app/api/chat.py',
    'app/api/emergency.py', 'app/api/family.py',
    'app/services/health_evaluator.py', 'app/services/notification_service.py',
    'app/services/sms_service.py', 'app/services/email_service.py',
    'app/services/emergency_service.py', 'app/services/family_service.py',
}


def find_string_end(chars, start, expected_quote):
    i = start
    other_quote = DQ if expected_quote == SQ else SQ
    while i < len(chars):
        c = chars[i]
        if c == BS:
            i += 2
            continue
        if c == expected_quote:
            return (i, expected_quote)
        if c == other_quote:
            next_i = i + 1
            if next_i >= len(chars):
                return (i, other_quote)
            next_c = chars[next_i]
            if next_c in (',', ')', ']', '}', ':', ' ', chr(13), chr(10)):
                return (i, other_quote)
        if c == '{':
            depth = 1
            i += 1
            while i < len(chars) and depth > 0:
                if chars[i] == '{': depth += 1
                elif chars[i] == '}': depth -= 1
                i += 1
            continue
        i += 1
    return (None, None)


def fix_line_charwise(line):
    stripped = line.strip()
    if stripped.startswith(DQ*3) and stripped.endswith(DQ*3) and len(stripped) > 6:
        return line
    if stripped == DQ*3 or stripped.startswith('#') or stripped == '':
        return line

    chars = list(line)
    i = 0
    result = []

    while i < len(chars):
        c = chars[i]
        if c in (DQ, SQ) and i + 2 < len(chars) and chars[i+1] == c and chars[i+2] == c:
            result.extend([c, c, c])
            i += 3
            while i < len(chars):
                if chars[i] == c and i + 2 < len(chars) and chars[i+1] == c and chars[i+2] == c:
                    result.extend([c, c, c])
                    i += 3
                    break
                result.append(chars[i])
                i += 1
            continue
        if c == 'f' and i + 1 < len(chars) and chars[i+1] in (DQ, SQ):
            open_quote = chars[i+1]
            close_idx, close_char = find_string_end(chars, i + 2, open_quote)
            if close_idx is not None and close_char != open_quote:
                str_content = chars[i+2:close_idx]
                result.append('f')
                result.append(DQ)
                result.extend(str_content)
                result.append(DQ)
                i = close_idx + 1
                continue
            elif close_idx is not None:
                result.append('f')
                result.extend(chars[i+1:close_idx+1])
                i = close_idx + 1
                continue
        if c in (DQ, SQ):
            open_quote = c
            close_idx, close_char = find_string_end(chars, i + 1, open_quote)
            if close_idx is not None and close_char != open_quote:
                str_content = chars[i+1:close_idx]
                result.append(DQ)
                result.extend(str_content)
                result.append(DQ)
                i = close_idx + 1
                continue
            elif close_idx is not None:
                result.extend(chars[i:close_idx+1])
                i = close_idx + 1
                continue
        result.append(c)
        i += 1

    return ''.join(result)


def pre_fix(content, rel_path):
    """Apply targeted fixes on ORIGINAL content, before general passes."""

    # ================================================================
    # UNIVERSAL PRE-FIXES
    # ================================================================

    # Fix f-strings with nested single-quoted strings that create ambiguity
    # Pattern: f'text '{var}' text\"  (in original files, with BS before DQ)
    # These should become: f"text '{var}' text"

    # Fix: ', \".join(  -> ', '.join(
    content = content.replace("', " + BS + DQ + ".join(", "', '.join(")

    # Fix: \"'.join(  -> ''.join(  (but actually this is "'.join which is broken)
    # The correct fix: "'.join -> "".join or ' '.join
    # Since after BS+DQ removal it becomes "'.join, let's fix the original
    content = content.replace(DQ + SQ + '.join(', DQ + DQ + '.join(')

    # Fix: '，\".join( -> '，'.join(
    content = content.replace(SQ + "，" + BS + DQ + ".join(", SQ + "，" + SQ + ".join(")

    # ================================================================
    # FILE-SPECIFIC PRE-FIXES (on original content with BS+DQ still present)
    # ================================================================

    if rel_path == 'app/api/cognitive_api.py':
        # 'type\": "word_association\", -> "type": "word_association",
        content = content.replace(
            SQ + "type" + BS + DQ + ": " + DQ + "word_association" + BS + DQ + ",",
            DQ + "type" + DQ + ": " + DQ + "word_association" + DQ + ","
        )
        # f''{word}' text？' -> f"'{word}' text？"
        qm = chr(0xFF1F)  # fullwidth question mark
        content = content.replace(
            "f'" + SQ + "{word}" + SQ + " " + chr(0x6700) + chr(0x5E38) + chr(0x8BA9) + chr(0x4EBA) + chr(0x8054) + chr(0x60F3) + chr(0x5230) + chr(0x4EC0) + chr(0x4E48) + qm + "'",
            'f"' + SQ + '{word}' + SQ + ' ' + chr(0x6700) + chr(0x5E38) + chr(0x8BA9) + chr(0x4EBA) + chr(0x8054) + chr(0x60F3) + chr(0x5230) + chr(0x4EC0) + chr(0x4E48) + qm + '"'
        )
        # f'箭头指向'{start}'，...？' -> f"箭头指向'{start}'，...？"
        comma_fw = chr(0xFF0C)  # fullwidth comma
        arrow_text = chr(0x7BAD) + chr(0x5934) + chr(0x6307) + chr(0x5411)
        rotate_text = comma_fw + chr(0x987A) + chr(0x65F6) + chr(0x9488) + chr(0x65CB) + chr(0x8F6C)
        after_rotate = chr(0x5EA6) + chr(0x540E) + chr(0x6307) + chr(0x5411) + chr(0x54EA) + chr(0x91CC) + qm
        content = content.replace(
            "f'" + arrow_text + "'{start}'" + rotate_text + "{rotations * 90}" + after_rotate + "'",
            'f"' + arrow_text + SQ + '{start}' + SQ + rotate_text + '{rotations * 90}' + after_rotate + '"'
        )
        # f'在下面的选项中找到 '{target}'' -> f"在下面的选项中找到 '{target}'"
        find_text = chr(0x5728) + chr(0x4E0B) + chr(0x9762) + chr(0x7684) + chr(0x9009) + chr(0x9879) + chr(0x4E2D) + chr(0x627E) + chr(0x5230)
        content = content.replace(
            "f'" + find_text + " '{target}''",
            'f"' + find_text + ' ' + SQ + '{target}' + SQ + '"'
        )

    if rel_path == 'app/api/onboarding.py':
        # voice_guide = '您好!...请点击'开始\"按钮,...设置。"
        content = content.replace(
            "= '您好!欢迎使用安心宝。请点击'开始" + BS + DQ + "按钮,我来帮您完成设置。" + DQ,
            '= "您好!欢迎使用安心宝。请点击' + SQ + '开始' + SQ + '按钮,我来帮您完成设置。"'
        )

    if rel_path == 'app/api/preferences.py':
        # f'已应用'{preset_name}'预设\", -> f"已应用'{preset_name}'预设",
        content = content.replace(
            "f'已应用'{preset_name}'预设" + BS + DQ + ",",
            'f"已应用' + SQ + '{preset_name}' + SQ + '预设",'
        )
        # "preferences\": -> "preferences":
        content = content.replace(
            DQ + "preferences" + BS + DQ + ":",
            DQ + "preferences" + DQ + ":"
        )

    if rel_path == 'app/api/report.py':
        # f'{config.title if config else '报表\"}_{...}" -> f"{config.title if config else '报表'}_{...}"
        content = content.replace(
            "f'{config.title if config else '报表" + BS + DQ + "}_{report_request.start_date}_{report_request.end_date}" + DQ,
            'f"{config.title if config else ' + SQ + '报表' + SQ + '}_{report_request.start_date}_{report_request.end_date}"'
        )

    if rel_path == 'app/api/voice_feedback.py':
        # f'好的,以后我会叫您\\\\"{name}\"", -> f"好的,以后我会叫您'{name}'",
        content = content.replace(
            "f'好的,以后我会叫您" + BS + BS + DQ + "{name}" + BS + DQ + DQ + ",",
            'f"好的,以后我会叫您' + SQ + '{name}' + SQ + '",'
        )

    if rel_path == 'app/core/scheduler.py':
        # f'{name}，{reminder.content or '这是一条提醒\"}" -> f"{name}，{reminder.content or '这是一条提醒'}"
        content = content.replace(
            "f'{name}，{reminder.content or '这是一条提醒" + BS + DQ + "}" + DQ,
            'f"{name}，{reminder.content or ' + SQ + '这是一条提醒' + SQ + '}"'
        )

    if rel_path == 'app/schemas/drug.py':
        # description='剂量，如'1片\"")  -> description="剂量，如'1片'")
        content = content.replace(
            "description='剂量，如'1片" + BS + DQ + DQ + ")",
            'description="剂量，如' + SQ + '1片' + SQ + '")'
        )
        # description=\"频次，如'twice_daily\"")  -> description="频次，如'twice_daily'")
        content = content.replace(
            "description=" + BS + DQ + "频次，如'twice_daily" + BS + DQ + DQ + ")",
            'description="频次，如' + SQ + 'twice_daily' + SQ + '")'
        )
        # description=\"服药时间，如[\"08:00", '20:00']')
        content = content.replace(
            "description=" + BS + DQ + "服药时间，如[" + BS + DQ + "08:00" + DQ + ", '20:00']')",
            'description="服药时间，如[' + SQ + '08:00' + SQ + ', ' + SQ + '20:00' + SQ + ']")'
        )

    if rel_path == 'app/schemas/medication.py':
        # description=\"服药时间，如[\"08:00\", '20:00']')
        content = content.replace(
            "description=" + BS + DQ + "服药时间，如[" + BS + DQ + "08:00" + BS + DQ + ", '20:00']')",
            'description="服药时间，如[' + SQ + '08:00' + SQ + ', ' + SQ + '20:00' + SQ + ']")'
        )

    if rel_path == 'app/services/onboarding_service.py':
        # "安心宝是专为您设计的智能助手\", -> "安心宝是专为您设计的智能助手",
        content = content.replace(
            DQ + "安心宝是专为您设计的智能助手" + BS + DQ + ",",
            DQ + "安心宝是专为您设计的智能助手" + DQ + ","
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
        # \"不用担心做错，可以多试几次' -> "不用担心做错，可以多试几次"
        content = content.replace(
            BS + DQ + "不用担心做错，可以多试几次'",
            DQ + "不用担心做错，可以多试几次" + DQ
        )
        # '有问题随时说'帮助\"", -> "有问题随时说'帮助'",
        content = content.replace(
            SQ + "有问题随时说'帮助" + BS + DQ + DQ + ",",
            DQ + "有问题随时说'帮助'" + DQ + ","
        )
        # \"熟能生巧，很快就会习惯' -> "熟能生巧，很快就会习惯"
        content = content.replace(
            BS + DQ + "熟能生巧，很快就会习惯'",
            DQ + "熟能生巧，很快就会习惯" + DQ
        )

    if rel_path == 'app/services/qwen_service.py':
        # ', \".join(formatted) -> ', '.join(formatted)
        # Already handled by universal pre-fix
        # r'\{'risk_score'.*?\}' -> r"\{'risk_score'.*?\}"
        content = content.replace(
            "r'" + BS + "{'risk_score'.*?" + BS + "}'",
            'r"' + BS + "{" + SQ + "risk_score" + SQ + ".*?" + BS + '}"'
        )

    if rel_path == 'app/services/social_service.py':
        # f'post_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S\")}'
        content = content.replace(
            "f'post_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S" + BS + DQ + ")}'",
            'f"post_{user_id}_{datetime.now().strftime(' + SQ + '%Y%m%d%H%M%S' + SQ + ')}"'
        )
        # f'activity_{organizer_id}_{datetime.now().strftime('%Y%m%d%H%M%S\")}'
        content = content.replace(
            "f'activity_{organizer_id}_{datetime.now().strftime('%Y%m%d%H%M%S" + BS + DQ + ")}'",
            'f"activity_{organizer_id}_{datetime.now().strftime(' + SQ + '%Y%m%d%H%M%S' + SQ + ')}"'
        )

    if rel_path == 'app/services/subscription_service.py':
        # f'sub_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S\")}'
        content = content.replace(
            "f'sub_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S" + BS + DQ + ")}'",
            'f"sub_{user_id}_{datetime.now().strftime(' + SQ + '%Y%m%d%H%M%S' + SQ + ')}"'
        )
        # f'pay_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S")}'
        content = content.replace(
            "f'pay_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S" + DQ + ")}'",
            'f"pay_{user_id}_{datetime.now().strftime(' + SQ + '%Y%m%d%H%M%S' + SQ + ')}"'
        )

    if rel_path == 'app/services/voice_feedback_service.py':
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
        # '温馨提醒：{tip}\", -> "温馨提醒：{tip}",
        content = content.replace(
            SQ + "温馨提醒：{tip}" + BS + DQ + ",",
            DQ + "温馨提醒：{tip}" + DQ + ","
        )
        # 'health': \"您可以说'测血压'或'健康报告\"。", -> "health": "您可以说'测血压'或'健康报告'。",
        content = content.replace(
            BS + DQ + "您可以说'测血压'或'健康报告" + BS + DQ + "。" + DQ + ",",
            DQ + "您可以说'测血压'或'健康报告'。" + DQ + ","
        )
        # 'social': \"您可以说'打电话给XXX'或'看看朋友圈\"。\", -> "social": "您可以说'打电话给XXX'或'看看朋友圈'。",
        content = content.replace(
            BS + DQ + "您可以说'打电话给XXX'或'看看朋友圈" + BS + DQ + "。" + BS + DQ + ",",
            DQ + "您可以说'打电话给XXX'或'看看朋友圈'。" + DQ + ","
        )
        # 'entertainment': '您可以说'放首歌'或'听新闻\"。", -> "entertainment": "您可以说'放首歌'或'听新闻'。",
        content = content.replace(
            SQ + "您可以说'放首歌'或'听新闻" + BS + DQ + "。" + DQ + ",",
            DQ + "您可以说'放首歌'或'听新闻'。" + DQ + ","
        )
        # 'home': \"您可以说'帮助'了解我能做什么。' -> "home": "您可以说'帮助'了解我能做什么。"
        content = content.replace(
            BS + DQ + "您可以说'帮助'了解我能做什么。'",
            DQ + "您可以说'帮助'了解我能做什么。" + DQ
        )
        # suggestions['home\"] -> suggestions["home"]
        content = content.replace(
            "suggestions['home" + BS + DQ + "']",
            'suggestions["home"]'
        )

    if rel_path == 'app/services/xfyun_service.py':
        # f'api_key='{self.api_key}', ' -> f"api_key='{self.api_key}', "
        content = content.replace(
            "f'api_key='{self.api_key}', '",
            'f"api_key=' + SQ + '{self.api_key}' + SQ + ', "'
        )
        # f\"algorithm="hmac-sha256", ' -> f'algorithm=\"hmac-sha256\", '
        content = content.replace(
            "f" + BS + DQ + 'algorithm="hmac-sha256", ' + SQ,
            "f'algorithm=" + BS + DQ + "hmac-sha256" + BS + DQ + ", '"
        )
        # f'signature="{signature_sha_base64}"" -> f'signature="{signature_sha_base64}"'
        content = content.replace(
            "f'signature=" + DQ + "{signature_sha_base64}" + DQ + DQ,
            "f'signature=" + DQ + "{signature_sha_base64}" + DQ + SQ
        )

    return content


def general_passes(content):
    """Apply general transformation passes."""

    # PASS 1: Fix broken triple-quote endings
    content = content.replace(DQ + BS + DQ + SQ, DQ + DQ + DQ)
    content = content.replace(DQ + DQ + BS + DQ, DQ + DQ + DQ)

    lines = content.split(chr(10))
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if re.match(r'^\s*' + DQ + DQ + SQ + r'$', stripped):
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = indent + DQ*3
        elif DQ*3 in stripped and stripped.endswith(DQ + DQ + SQ):
            lines[i] = stripped[:-1] + DQ
    content = chr(10).join(lines)

    # PASS 2: Remove spurious backslash-before-doublequote
    content = content.replace(BS + DQ, DQ)

    # PASS 3: Character-wise mismatch fix
    lines = content.split(chr(10))
    for i, line in enumerate(lines):
        lines[i] = fix_line_charwise(line)
    content = chr(10).join(lines)

    # PASS 4: Additional pattern fixes
    content = re.sub(SQ + r'(\w+)' + BS + DQ + ':', DQ + r'\1' + DQ + ':', content)
    content = content.replace(DQ + SQ + '.join(', DQ + DQ + '.join(')

    # Broken docstring: '"'text""' -> """text"""
    lines = content.split(chr(10))
    for i, line in enumerate(lines):
        stripped = line.strip()
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


def fix_content(content, rel_path):
    """Apply all fixes."""
    content = pre_fix(content, rel_path)
    content = general_passes(content)
    return content


def main():
    fixed = []
    still_broken = []
    clean = []

    for root, dirs, files in os.walk(os.path.join(BASE, 'app')):
        for fname in sorted(files):
            if not fname.endswith('.py'):
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, BASE).replace(os.sep, '/')

            if rel_path in SKIP_FILES:
                continue

            with open(full_path, 'r', encoding='utf-8') as f:
                original = f.read()

            try:
                ast.parse(original)
                clean.append(rel_path)
                continue
            except SyntaxError:
                pass

            content = fix_content(original, rel_path)

            if content != original:
                try:
                    ast.parse(content)
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed.append(rel_path)
                except SyntaxError as e:
                    still_broken.append((rel_path, f"Line {e.lineno}: {e.msg}"))
            else:
                still_broken.append((rel_path, "No changes made"))

    print("=== FIXED ===")
    for p in fixed:
        print(f"  {p}")
    print(f"Total fixed: {len(fixed)}")
    print()
    if still_broken:
        print("=== STILL BROKEN ===")
        for p, e in still_broken:
            try:
                print(f"  {p}: {e}")
            except UnicodeEncodeError:
                print(f"  {p}: (unicode err)")
        print(f"Total still broken: {len(still_broken)}")
    print()
    print(f"Total already clean: {len(clean)}")


if __name__ == '__main__':
    main()
