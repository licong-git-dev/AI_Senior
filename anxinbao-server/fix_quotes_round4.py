#!/usr/bin/env python
"""精确修复引号错误 - 第4轮"""
import os
import re

def fix_file(filepath):
    """修复单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # 修复字典键中的引号错误: 'key": -> 'key':
        # 匹配 'word" 后跟: (字典键)
        content = re.sub(r"'(\w+)\"(\s*:)", r"'\1'\2", content)

        # 修复字典值中的引号错误: 'value" -> 'value'  (在逗号或括号前)
        # 匹配 'word" 后跟, 或 } 或 ]
        content = re.sub(r"'(\w+)\"(\s*[,}\]])", r"'\1'\2", content)

        # 修复 "value' -> "value"
        content = re.sub(r'"(\w+)\'(\s*[,}\]])', r'"\1"\2', content)

        # 修复 "key': -> 'key':
        content = re.sub(r'"(\w+)\'(\s*:)', r"'\1'\2", content)

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
