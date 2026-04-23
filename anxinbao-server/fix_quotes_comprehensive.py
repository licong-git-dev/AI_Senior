#!/usr/bin/env python
"""批量修复所有Python文件中的引号错误 - 全面修复"""
import os
import re

def fix_file(filepath):
    """修复单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # 修复 f''" -> f"""
        content = content.replace('f\'\'\"', 'f"""')

        # 修复 ''" -> """
        content = content.replace('\'\'\"', '"""')

        # 修复 '"" -> """
        content = content.replace('\'\"\"', '"""')

        # 修复错误的引号组合在字符串中间
        # "family_members', [] -> 'family_members', []
        content = re.sub(r'"(\w+)\',', r"'\1',", content)

        # 修复 '无记录" -> '无记录'
        content = re.sub(r"'([^']*?)\"([,\)])", r"'\1'\2", content)

        # 修复 "...'  结尾 -> "..."
        content = re.sub(r'"([^"]*?)\'([,\)\n])', r'"\1"\2', content)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

# 获取所有Python文件
base_dirs = ['app', 'tests']
fixed_count = 0

for base_dir in base_dirs:
    if os.path.exists(base_dir):
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    if fix_file(filepath):
                        fixed_count += 1
                        print(f"Fixed: {filepath}")

# 修复main.py
if os.path.exists('main.py'):
    if fix_file('main.py'):
        fixed_count += 1
        print("Fixed: main.py")

print(f"\nTotal files fixed: {fixed_count}")
