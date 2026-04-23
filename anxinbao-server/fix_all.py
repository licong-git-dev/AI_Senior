"""
Combined fix for all remaining broken Python files.
Applies: triple-quote fix, backslash removal, charwise quote matching, and targeted fixes.
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
    """Find where a string literal ends, allowing for mismatched close quotes."""
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
                if chars[i] == '{':
                    depth += 1
                elif chars[i] == '}':
                    depth -= 1
                i += 1
            continue
        i += 1
    return (None, None)


def fix_line_charwise(line):
    """Fix mismatched quotes in a single line using character-level analysis."""
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

        # Triple-quote
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

        # f-string
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

        # Regular string
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


def fix_content(content, rel_path):
    """Apply all fixes to file content."""

    # ================================================================
    # PASS 1: Fix broken triple-quote endings
    # ================================================================
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

    # ================================================================
    # PASS 2: Remove ALL spurious backslash-before-doublequote
    # ================================================================
    content = content.replace(BS + DQ, DQ)

    # ================================================================
    # PASS 3: Fix mismatched quotes character-by-character
    # ================================================================
    lines = content.split(chr(10))
    for i, line in enumerate(lines):
        lines[i] = fix_line_charwise(line)
    content = chr(10).join(lines)

    # ================================================================
    # PASS 4: General pattern fixes
    # ================================================================
    # Dict key mismatches with remaining backslash: 'key\": -> "key":
    content = re.sub(SQ + r'(\w+)' + BS + DQ + ':', DQ + r'\1' + DQ + ':', content)

    # String join: "'.join -> "".join
    content = content.replace(DQ + SQ + '.join(', DQ + DQ + '.join(')
    content = content.replace("', " + BS + DQ + ".join(", "', '.join(")

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

    # ================================================================
    # PASS 5: File-specific targeted fixes
    # ================================================================
    content = specific_fixes(rel_path, content)

    return content


def specific_fixes(rel_path, content):
    """Apply file-specific fixes for complex patterns."""

    if rel_path == 'app/api/admin.py':
        # f"维护模式已{'开启' if enabled else '关闭"}" -> f"维护模式已{'开启' if enabled else '关闭'}"
        content = content.replace(
            "f" + DQ + "维护模式已{'开启' if enabled else '关闭" + DQ + "}" + DQ,
            "f" + DQ + "维护模式已{'开启' if enabled else '关闭'}" + DQ
        )

    if rel_path == 'app/api/cognitive_api.py':
        # After passes 1-3, check what remains
        # f'在下面的选项中找到 '{target}'' -> f"在下面的选项中找到 '{target}'"
        content = content.replace(
            "f'在下面的选项中找到 '{target}''",
            'f"在下面的选项中找到 ' + SQ + '{target}' + SQ + '"'
        )

    if rel_path == 'app/api/onboarding.py':
        # '您好!...请点击'开始'按钮,...设置。" -> "您好!...请点击'开始'按钮,...设置。"
        content = content.replace(
            SQ + "您好!欢迎使用安心宝。请点击" + SQ + "开始" + SQ + "按钮,我来帮您完成设置。" + DQ,
            DQ + "您好!欢迎使用安心宝。请点击'开始'按钮,我来帮您完成设置。" + DQ
        )

    if rel_path == 'app/api/preferences.py':
        # f'已应用'{preset_name}'预设" -> f"已应用'{preset_name}'预设"
        content = content.replace(
            "f'已应用'{preset_name}'预设" + DQ,
            'f"已应用' + SQ + '{preset_name}' + SQ + '预设"'
        )

    if rel_path == 'app/api/report.py':
        # f'{config.title if config else '报表"}_{...}' -> f"{config.title if config else '报表'}_{...}"
        content = content.replace(
            "f'{config.title if config else '报表" + DQ + "}_{report_request.start_date}_{report_request.end_date}" + DQ,
            "f" + DQ + "{config.title if config else '报表'}_{report_request.start_date}_{report_request.end_date}" + DQ
        )

    if rel_path == 'app/api/subscription.py':
        # f"订阅已取消...无限期"}" -> f"订阅已取消...无限期'}"
        content = content.replace(
            "f" + DQ + "订阅已取消，服务将持续到 {subscription.end_date.strftime('%Y年%m月%d日') if subscription.end_date else '无限期" + DQ + "}" + DQ,
            "f" + DQ + "订阅已取消，服务将持续到 {subscription.end_date.strftime('%Y年%m月%d日') if subscription.end_date else '无限期'}" + DQ
        )

    if rel_path == 'app/api/voice_feedback.py':
        # f'好的,以后我会叫您\\"{name}\"" -> f"好的,以后我会叫您'{name}'"
        # After pass 2 (BS+DQ removed): f'好的,以后我会叫您\"{name}\"" -> f'好的,...\"... hmm
        # After BS+DQ removal: the \\ becomes \ and " is already DQ
        # Let me check: original has \\\\ (two backslashes in repr) + DQ + {name} + \\ + DQ + DQ
        # After pass 2: \\ + {name} + DQ + DQ ... this is complex
        # Let me just handle the post-pass-3 pattern
        content = content.replace(
            "f'好的,以后我会叫您" + BS + DQ + "{name}" + DQ + DQ,
            "f" + DQ + "好的,以后我会叫您'{name}'" + DQ
        )
        # Also try without backslash
        content = content.replace(
            "f'好的,以后我会叫您" + DQ + "{name}" + DQ + DQ,
            "f" + DQ + "好的,以后我会叫您'{name}'" + DQ
        )

    if rel_path == 'app/core/scheduler.py':
        # f'{name}，{reminder.content or '这是一条提醒"}" -> f"{name}，{reminder.content or '这是一条提醒'}"
        content = content.replace(
            "f'{name}，{reminder.content or '这是一条提醒" + DQ + "}" + DQ,
            "f" + DQ + "{name}，{reminder.content or '这是一条提醒'}" + DQ
        )

    if rel_path == 'app/schemas/drug.py':
        # description='剂量，如'1片"") -> description="剂量，如'1片'")
        content = content.replace(
            "description='剂量，如'1片" + DQ + DQ + ")",
            'description="剂量，如' + SQ + '1片' + SQ + '")'
        )
        # description="频次，如'twice_daily"") -> description="频次，如'twice_daily'")
        content = content.replace(
            "description=" + DQ + "频次，如'twice_daily" + DQ + DQ + ")",
            'description="频次，如' + SQ + 'twice_daily' + SQ + '")'
        )
        # description="服药时间，如["08:00", '20:00']') -> description="服药时间，如['08:00', '20:00']")
        content = content.replace(
            "description=" + DQ + "服药时间，如[" + DQ + '08:00", ' + SQ + "20:00']')",
            'description="服药时间，如[' + SQ + '08:00' + SQ + ', ' + SQ + '20:00' + SQ + ']")'
        )

    if rel_path == 'app/schemas/medication.py':
        # description="服药时间，如["08:00", '20:00']') -> description="服药时间，如['08:00', '20:00']")
        content = content.replace(
            "description=" + DQ + "服药时间，如[" + DQ + "08:00" + DQ + ", '20:00']')",
            'description="服药时间，如[' + SQ + '08:00' + SQ + ', ' + SQ + '20:00' + SQ + ']")'
        )

    if rel_path == 'app/schemas/nutrition.py':
        # description='份量描述，如'100g"") -> description="份量描述，如'100g'")
        content = content.replace(
            "description='份量描述，如'100g" + DQ + DQ + ")",
            'description="份量描述，如' + SQ + '100g' + SQ + '")'
        )

    if rel_path == 'app/services/message_center_service.py':
        # f'msg_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S")}_{self._message_counter}'
        content = content.replace(
            "f'msg_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S" + DQ + ")}_{self._message_counter}'",
            'f"msg_{user_id}_{datetime.now().strftime(' + SQ + '%Y%m%d%H%M%S' + SQ + ')}_{self._message_counter}"'
        )

    if rel_path == 'app/services/onboarding_service.py':
        content = content.replace(
            SQ + "您可以随时说'帮助'获取使用指导" + DQ + ",",
            DQ + "您可以随时说'帮助'获取使用指导" + DQ + ","
        )
        content = content.replace(
            DQ + "不要着急，我们会慢慢来'",
            DQ + "不要着急，我们会慢慢来" + DQ
        )

    if rel_path == 'app/services/simplified_mode.py':
        # f'语音命令匹配: '{text}" -> {action_id}" -> f"语音命令匹配: '{text}' -> {action_id}"
        content = content.replace(
            "f'语音命令匹配: '{text}" + DQ + " -> {action_id}" + DQ + ")",
            'f"语音命令匹配: ' + SQ + '{text}' + SQ + ' -> {action_id}")'
        )

    if rel_path == 'app/services/social_service.py':
        # f'post_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S")}' -> f"..."
        content = content.replace(
            "f'post_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S" + DQ + ")}'",
            'f"post_{user_id}_{datetime.now().strftime(' + SQ + '%Y%m%d%H%M%S' + SQ + ')}"'
        )

    if rel_path == 'app/services/subscription_service.py':
        content = content.replace(
            "f'sub_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S" + DQ + ")}'",
            'f"sub_{user_id}_{datetime.now().strftime(' + SQ + '%Y%m%d%H%M%S' + SQ + ')}"'
        )

    if rel_path == 'app/services/support_service.py':
        content = content.replace(
            "f'TK{datetime.now().strftime('%Y%m%d" + DQ + ")}{self.ticket_counter:04d}'",
            'f"TK{datetime.now().strftime(' + SQ + '%Y%m%d' + SQ + ')}{self.ticket_counter:04d}"'
        )

    if rel_path == 'app/services/voice_feedback_service.py':
        content = content.replace(
            DQ + "需要帮助吗?您可以说'{command}" + DQ + "。" + DQ + ",",
            DQ + "需要帮助吗?您可以说'{command}'。" + DQ + ","
        )
        content = content.replace(
            DQ + "如果需要帮助,随时说'帮助'或'帮我" + DQ + "。" + DQ + ",",
            DQ + "如果需要帮助,随时说'帮助'或'帮我'。" + DQ + ","
        )
        content = content.replace(
            DQ + "有什么不明白的,可以问我哦。'",
            DQ + "有什么不明白的,可以问我哦。" + DQ
        )
        content = content.replace(
            SQ + "温馨提醒：{tip}" + DQ + ",",
            DQ + "温馨提醒：{tip}" + DQ + ","
        )

    if rel_path == 'app/services/xfyun_service.py':
        # After passes: f"algorithm="hmac-sha256", ' -> need f'algorithm="hmac-sha256", '
        content = content.replace(
            'f"algorithm="hmac-sha256", ' + SQ,
            "f'algorithm=" + BS + DQ + "hmac-sha256" + BS + DQ + ", '"
        )
        # f'signature="{signature_sha_base64}"" -> f'signature="{signature_sha_base64}"'
        content = content.replace(
            "f'signature=" + DQ + "{signature_sha_base64}" + DQ + DQ,
            "f'signature=" + DQ + "{signature_sha_base64}" + DQ + SQ
        )
        # f'api_key='{self.api_key}', ' -> f"api_key='{self.api_key}', "
        content = content.replace(
            "f'api_key='{self.api_key}', '",
            'f"api_key=' + SQ + '{self.api_key}' + SQ + ', "'
        )

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
                print(f"  {p}: (encoding error in message)")
        print(f"Total still broken: {len(still_broken)}")
    print()
    print(f"Total already clean: {len(clean)}")


if __name__ == '__main__':
    main()
