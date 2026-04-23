#!/usr/bin/env python
"""批量修复所有Python文件中的三引号语法错误 - 第二轮"""
import os
import re

def fix_file(filepath):
    """修复单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # 修复 ''"  开头 (应该是 """)
        content = re.sub(r"''\"\n", '"""\n', content)

        # 修复 '''...'""  格式 (应该是 """...""")
        content = re.sub(r"'''([^']*?)'\"\"", r'"""\1"""', content)

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
