#!/usr/bin/env python
"""批量修复所有Python文件中的三引号语法错误"""
import os
import re
import glob

def fix_file(filepath):
    """修复单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # 修复单行三引号: ""'...'""  ->  """..."""
        # 匹配 ""'任意非单引号内容'""
        content = re.sub(r'""\'([^\']*?)\'""', r'"""\1"""', content)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

# 获取所有Python文件
base_dir = 'app'
fixed_count = 0

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            if fix_file(filepath):
                fixed_count += 1
                print(f"Fixed: {filepath}")

# 也修复tests目录
for root, dirs, files in os.walk('tests'):
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
