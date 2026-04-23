"""
Comprehensive quote escaping fix script.
Fixes all broken quote patterns in Python files.
"""
import ast
import re
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# Already fixed files - skip these
ALREADY_FIXED = {
    'app/models/database.py',
    'app/core/config.py',
    'app/core/cache.py',
    'app/core/security.py',
    'app/core/deps.py',
    'app/api/chat.py',
    'app/api/emergency.py',
    'app/api/family.py',
    'app/services/health_evaluator.py',
    'app/services/notification_service.py',
    'app/services/sms_service.py',
    'app/services/email_service.py',
    'app/services/emergency_service.py',
    'app/services/family_service.py',
}


def fix_file(filepath):
    """Fix quote escaping bugs in a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # We'll do line-by-line fixing for most patterns,
    # but some patterns span concepts we need to handle carefully

    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Pattern 1: Broken triple-quote docstrings ending with "\"' or ""' or ""\"
        # These are docstrings that should end with """ (three double quotes)

        # Pattern: """text"\"'  -> should be """text"""
        # The docstring opened with """ but closes with "\"'
        if '"\\"\'' in line:
            line = line.replace('"\\"\'' , '"""')

        # Pattern: """text""'  -> should be """text"""
        # But be careful not to match inside strings
        # This is a docstring that opened with """ but closes with ""'
        if '""\'') in line:
            # Only fix if this looks like a docstring ending
            stripped = line.strip()
            if stripped.endswith('""\''):
                line = line[:-3] + '"""' if line.endswith('""\'') else line.replace('""\'', '"""')
            elif '""\'') in line:
                line = line.replace('""\'', '"""')

        # Pattern: ""\"  at start of line (opening triple quote with escaping)
        if '""\\' in line:
            line = line.replace('""\\"', '"""')

        # Now handle mixed single/double quote issues on individual lines
        # We need to be smart about this - fix string literals that mix quotes

        fixed_lines.append(line)
        i += 1

    content = '\n'.join(fixed_lines)

    # Now do regex-based fixes for common patterns

    # Fix: '...\") -> '...')  (single-quoted string ending with \")
    # This is a string that starts with ' but has \" at the end before )
    # Pattern: ='value\"  should be ='value'
    # or: ('value\"  should be ('value'

    # Strategy: Find all string-like patterns and fix mismatched quotes

    # Fix pattern: 'text\"  ->  'text'  (started with single, ended with backslash-double)
    # This appears as:  'some text\"  in the source
    content = re.sub(r"'([^'\"\\]*(?:\\.[^'\"\\]*)*)\\\"\s*(?=[,\)\]\}\s:+])", r"'\1'", content)

    # Fix pattern: "text'  ->  "text"  (started with double, ended with single)
    content = re.sub(r'"([^"\'\\]*(?:\\.[^"\'\\]*)*)\'\s*(?=[,\)\]\}\s:+])', r'"\1"', content)

    # Fix pattern: \"text'  ->  'text'  (backslash-double start, single end)
    content = re.sub(r'\\"([^"\'\\]*(?:\\.[^"\'\\]*)*)\'', r"'\1'", content)

    # Fix pattern: ='text\"  or  ="text'  at end of line
    content = re.sub(r"'([^'\"\\]*)\\\"(\s*)$", r"'\1'\2", content, flags=re.MULTILINE)
    content = re.sub(r'"([^"\'\\]*)\'(\s*)$', r'"\1"\2', content, flags=re.MULTILINE)

    return content, content != original


def fix_file_iterative(filepath):
    """
    Fix a file iteratively until it parses correctly or we give up.
    Uses a line-by-line approach for maximum accuracy.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Apply all fixes
    content = apply_all_fixes(content)

    return content, content != original_content


def apply_all_fixes(content):
    """Apply all quote fixes to content."""

    # Phase 1: Fix broken triple-quote docstrings
    # Pattern: """text"\"'  should be """text"""
    content = content.replace('"\\"\'' , '"""')

    # Pattern: starts as """ but ends as ""'
    content = re.sub(r'""\'(?=\s*\n)', '"""', content)

    # Pattern: ""\" at start of a triple-quote
    content = re.sub(r'(?<!")""\\"(?=[^"])', '"""', content)

    # Phase 2: Fix mixed quote strings line by line
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        fixed_lines.append(fix_line_quotes(line))

    content = '\n'.join(fixed_lines)

    return content


def fix_line_quotes(line):
    """Fix quote issues in a single line."""

    # Skip comment-only lines
    stripped = line.strip()
    if stripped.startswith('#'):
        return line

    # We need to find string literals and fix mismatched quotes
    # Strategy: scan character by character, track string state

    result = []
    i = 0

    while i < len(line):
        # Check for triple-quote strings
        if i < len(line) - 2:
            three = line[i:i+3]
            if three == '"""' or three == "'''":
                # Triple quoted string on same line - find the end
                quote_char = three[0]
                end_pattern = quote_char * 3
                j = i + 3
                while j < len(line) - 2:
                    if line[j:j+3] == end_pattern:
                        result.append(line[i:j+3])
                        i = j + 3
                        break
                    j += 1
                else:
                    # No end found on this line, it continues
                    result.append(line[i:])
                    return ''.join(result)
                continue

        # Check for single/double quoted strings
        if line[i] in ('"', "'"):
            fixed_str, new_i = fix_string_literal(line, i)
            result.append(fixed_str)
            i = new_i
            continue

        # Check for backslash-quote which starts a mis-quoted string
        if line[i] == '\\' and i + 1 < len(line) and line[i+1] in ('"', "'"):
            # This is likely a mismatched string start like \"text'
            actual_quote = line[i+1]
            # The intended opening quote is the OTHER quote type
            if actual_quote == '"':
                intended_quote = "'"
            else:
                intended_quote = '"'

            # Find the end of this string
            j = i + 2
            end_char = None
            while j < len(line):
                if line[j] == '\\' and j + 1 < len(line):
                    j += 2
                    continue
                if line[j] in ('"', "'"):
                    end_char = line[j]
                    break
                j += 1

            if end_char is not None:
                # Extract string content
                string_content = line[i+2:j]
                # Use a consistent quote
                result.append(intended_quote + string_content + intended_quote)
                i = j + 1
                continue

        result.append(line[i])
        i += 1

    return ''.join(result)


def fix_string_literal(line, start):
    """
    Fix a string literal starting at position 'start'.
    Returns (fixed_string, next_position).
    """
    open_quote = line[start]

    # Check for triple quote
    if start + 2 < len(line) and line[start:start+3] in ('"""', "'''"):
        # Triple quoted - find the matching end
        triple = line[start:start+3]
        j = start + 3
        while j < len(line):
            if j + 2 < len(line) and line[j:j+3] == triple:
                return line[start:j+3], j + 3
            # Check for broken triple-quote endings
            if line[j:j+3] == '"\\"\'' or line[j:j+3] == "'\\'\"":
                return line[start:j] + triple, j + 3
            if line[j:j+2] == '""' and j+2 < len(line) and line[j+2] == "'":
                return line[start:j] + '"""', j + 3
            if line[j:j+2] == "''" and j+2 < len(line) and line[j+2] == '"':
                return line[start:j] + "'''", j + 3
            j += 1
        # Didn't find end on this line
        return line[start:], len(line)

    # Single quoted string
    j = start + 1
    while j < len(line):
        c = line[j]

        # Handle escape sequences
        if c == '\\':
            if j + 1 < len(line):
                next_c = line[j+1]
                if next_c == '"' and open_quote == "'":
                    # \\" inside a single-quoted string might be a mismatched end
                    # Check if this looks like end of string
                    after = j + 2
                    if after >= len(line) or line[after] in (',', ')', ']', '}', ':', ' ', '\t', '+', '.', '\n'):
                        # This is likely 'text\"  which should be 'text'
                        return open_quote + line[start+1:j] + open_quote, after
                elif next_c == "'" and open_quote == '"':
                    # Escaped single quote inside double-quoted string - ok
                    pass
                j += 2
                continue
            j += 1
            continue

        # Normal end of string
        if c == open_quote:
            return line[start:j+1], j + 1

        # Mismatched end quote
        if c in ('"', "'") and c != open_quote:
            # Check if this is the end of the string
            after = j + 1
            if after >= len(line) or line[after] in (',', ')', ']', '}', ':', ' ', '\t', '+', '.', '\n', '#'):
                # Mismatch: started with one quote, ended with another
                return open_quote + line[start+1:j] + open_quote, after

        j += 1

    # Reached end of line without closing - return as-is
    return line[start:], len(line)


def aggressive_fix(content):
    """
    More aggressive fixing approach - use regex patterns to fix
    the most common broken patterns found in the codebase.
    """

    # Fix 1: Broken docstrings  """text"\"'  -> """text"""
    content = content.replace('"\\"\''  , '"""')
    content = content.replace("'\\'\"", "'''")

    # Fix 2: ""' at end of docstring -> """
    # Match: some text""' followed by newline
    content = re.sub(r'""\'(\s*\n)', r'"""\1', content)
    content = re.sub(r"''\"\s*(\n)", r"'''\1", content)

    # Fix 3: ""\  at start of docstring/string -> """
    # e.g., ""\"text  should be """text
    content = re.sub(r'""\\"', '"""', content)

    # Fix 4: Mixed quotes in router definitions and function params
    # Pattern: prefix='/api/auth\", tags=['...\"])
    # Should be: prefix='/api/auth', tags=['...'])
    # or: prefix="/api/auth", tags=["..."])

    # General approach: find 'text\" and replace with 'text'
    # and find "text' and replace with "text"

    # This regex finds: single-quote, content without quotes, backslash-double-quote
    # followed by typical string terminators
    content = re.sub(
        r"'([^'\"\\]*?)\\\"(?=[,\)\]\}\s:+\.])",
        r"'\1'",
        content
    )

    # Find: double-quote, content, single-quote followed by terminators
    content = re.sub(
        r"\"([^'\"\\]*?)'(?=[,\)\]\}\s:+\.])",
        r'"\1"',
        content
    )

    # Fix 5: Backslash-quote at start: =\"text' -> ="text" or ='text'
    # Pattern: =\" or (\" at the start of a value
    content = re.sub(
        r'=\\"([^"\'\\]*?)\'',
        r"='\1'",
        content
    )
    content = re.sub(
        r'\(\\"([^"\'\\]*?)\'',
        r"('\1'",
        content
    )
    content = re.sub(
        r',\s*\\"([^"\'\\]*?)\'',
        lambda m: m.group(0).replace('\\"' + m.group(1) + "'", "'" + m.group(1) + "'"),
        content
    )

    # Fix 6: Pattern  \"text"  ->  "text"  (escaped start, normal end)
    # Usually appears as: action=\"text"
    content = re.sub(
        r'=\\"([^"\'\\]*?)"',
        r'="\1"',
        content
    )

    # Fix 7: Standalone backslash-quote starts in various contexts
    # resource=\"device_auth'  -> resource='device_auth'
    content = re.sub(
        r'(?<==)\\"([^"\'\\]*?)\'',
        r"'\1'",
        content
    )

    # Fix 8: f-string and concatenation fixes
    # f\"{var}text'  -> f'{var}text' or f"{var}text"
    content = re.sub(
        r'f\\"([^"\']*?)\'',
        r"f'\1'",
        content
    )
    content = re.sub(
        r"f'([^'\"]*?)\\\"",
        r"f'\1'",
        content
    )

    # Fix 9: In dict/list contexts
    # 'key\": value  -> 'key': value
    content = re.sub(
        r"'([^'\"\\]*?)\\\"(\s*:)",
        r"'\1'\2",
        content
    )
    # "key': value  -> "key": value  or 'key': value
    content = re.sub(
        r'"([^"\'\\]*?)\'(\s*:)',
        r"'\1'\2",
        content
    )

    # Fix 10: Inside f-strings: {msg['content\"]}  -> {msg['content']}
    content = re.sub(
        r"'([^'\"\\]*?)\\\"(\s*[\]\)])",
        r"'\1'\2",
        content
    )

    # Fix 11: Remaining \"  at end of string before common terminators
    content = re.sub(
        r"'([^'\"\\]*?)\\\"(\s*[,\)\]\}\n])",
        r"'\1'\2",
        content
    )
    content = re.sub(
        r'"([^"\'\\]*?)\'(\s*[,\)\]\}\n])',
        r"'\1'\2",
        content
    )

    return content


def fix_remaining_issues(content):
    """Fix any remaining issues after the main passes."""

    # Handle specific patterns that the regex might miss

    # Pattern: b"'.join(  should be b"".join( or b''.join(
    content = content.replace("b\"'.join(", "b''.join(")

    # Pattern: r'\{.*\}\" should be r'\{.*\}'
    # But this is tricky with raw strings - fix carefully
    content = re.sub(r"(r'[^']*?)\\\"", r"\1'", content)
    content = re.sub(r'(r"[^"]*?)\'', r'\1"', content)

    # Full-width comma fix (U+FF0C)
    content = content.replace('\uff0c', ',')

    # Fix remaining mismatched quotes we might have missed
    # These are very specific patterns

    # 'text\")   -> 'text')
    content = re.sub(r"'([^'\"\\]+)\\\"(\))", r"'\1'\2", content)

    # "text')   -> "text") or 'text')
    content = re.sub(r'"([^"\'\\]+)\'(\))', r"'\1'\2", content)

    return content


def verify_file(filepath):
    """Verify a file parses correctly."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, str(e)


def process_file(filepath):
    """Process a single file: fix and verify."""
    rel_path = os.path.relpath(filepath, ROOT).replace(os.sep, '/')

    if rel_path in ALREADY_FIXED:
        return 'skipped', None

    # First check if file already parses
    ok, err = verify_file(filepath)
    if ok:
        return 'clean', None

    # Read file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Apply fixes in multiple passes
    for pass_num in range(5):
        content = aggressive_fix(content)
        content = fix_remaining_issues(content)

        # Check if it parses now
        try:
            ast.parse(content)
            # It parses! Write it back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return 'fixed', None
        except SyntaxError as e:
            last_error = str(e)
            continue

    # If we still can't fix it, write what we have and report
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    return 'failed', last_error


def main():
    results = {'fixed': [], 'clean': [], 'skipped': [], 'failed': []}

    # Find all Python files
    files_to_check = []

    # app/ directory
    for root, dirs, files in os.walk(os.path.join(ROOT, 'app')):
        for f in files:
            if f.endswith('.py'):
                files_to_check.append(os.path.join(root, f))

    # main.py
    main_py = os.path.join(ROOT, 'main.py')
    if os.path.exists(main_py):
        files_to_check.append(main_py)

    for filepath in sorted(files_to_check):
        rel_path = os.path.relpath(filepath, ROOT).replace(os.sep, '/')
        status, error = process_file(filepath)
        results[status].append((rel_path, error))

    # Print results
    print("\n=== RESULTS ===\n")

    print(f"Fixed ({len(results['fixed'])}):")
    for path, _ in results['fixed']:
        print(f"  + {path}")

    print(f"\nClean ({len(results['clean'])}):")
    for path, _ in results['clean']:
        print(f"  . {path}")

    print(f"\nSkipped ({len(results['skipped'])}):")
    for path, _ in results['skipped']:
        print(f"  - {path}")

    print(f"\nFailed ({len(results['failed'])}):")
    for path, error in results['failed']:
        print(f"  ! {path}: {error}")

    # Final verification
    print("\n=== FINAL VERIFICATION ===\n")
    all_ok = True
    for filepath in sorted(files_to_check):
        rel_path = os.path.relpath(filepath, ROOT).replace(os.sep, '/')
        if rel_path in ALREADY_FIXED:
            continue
        ok, err = verify_file(filepath)
        if not ok:
            print(f"FAIL: {rel_path}: {err}")
            all_ok = False

    if all_ok:
        print("All files parse successfully!")

    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
