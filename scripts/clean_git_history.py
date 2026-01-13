#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 Git 历史中的敏感信息
使用 git filter-repo 工具
"""

import subprocess
import sys

print("=" * 70)
print("Git 历史清理工具")
print("=" * 70)
print()
print("⚠️  警告：此操作将重写 Git 历史！")
print("⚠️  如果已推送到远程仓库，需要强制推送（force push）")
print()

# 检查是否安装了 git-filter-repo
try:
    result = subprocess.run(['git', 'filter-repo', '--help'], 
                          capture_output=True, 
                          text=True)
    if result.returncode != 0:
        print("❌ 未安装 git-filter-repo")
        print()
        print("安装方法：")
        print("  pip install git-filter-repo")
        print()
        sys.exit(1)
except FileNotFoundError:
    print("❌ 未安装 git-filter-repo")
    print()
    print("安装方法：")
    print("  pip install git-filter-repo")
    print()
    sys.exit(1)

print("✅ git-filter-repo 已安装")
print()

# 要替换的敏感信息
REPLACEMENTS = [
    ("LTAI5tE6gbbeCaTKGvUFYyhk", "YOUR_OSS_ACCESS_KEY_ID"),
    ("4is2uzGFFPR0mk3hk8CZwDT909NiV5", "YOUR_OSS_ACCESS_KEY_SECRET"),
    ("sk-768d09acb469423f9888f93b31695fd0", "YOUR_QIANWEN_API_KEY"),
    ("https://www.feishu.cn/flow/api/trigger-webhook/6228b59ee92453808a92d08ff000cb4c", "YOUR_FEISHU_WEBHOOK"),
    ("https://open.feishu.cn/open-apis/bot/v2/hook/86321410-9779-4562-8f39-c5be8f55f6b3", "YOUR_FEISHU_WEBHOOK"),
]

print("将替换以下敏感信息：")
for old, new in REPLACEMENTS:
    print(f"  {old[:20]}... => {new}")
print()

response = input("确认执行？(yes/no): ")
if response.lower() != 'yes':
    print("已取消")
    sys.exit(0)

print()
print("开始清理历史...")
print()

# 创建替换表达式文件
expressions_file = "expressions.txt"
with open(expressions_file, 'w', encoding='utf-8') as f:
    for old, new in REPLACEMENTS:
        # 转义特殊字符
        old_escaped = old.replace('/', r'\/')
        new_escaped = new.replace('/', r'\/')
        f.write(f"s/{old_escaped}/{new_escaped}/g\n")

# 执行替换
try:
    cmd = [
        'git', 'filter-repo', 
        '--replace-text', expressions_file,
        '--force'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Git 历史清理完成！")
        print()
        print("后续步骤：")
        print("  1. 检查历史记录：git log")
        print("  2. 如果已推送到远程，需要强制推送：")
        print("     git push --force --all")
        print("     git push --force --tags")
        print()
        print("⚠️  强制推送会覆盖远程仓库的历史！")
    else:
        print("❌ 清理失败：")
        print(result.stderr)
        sys.exit(1)
        
finally:
    # 清理临时文件
    import os
    if os.path.exists(expressions_file):
        os.remove(expressions_file)

