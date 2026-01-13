#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新初始化 Git 仓库（清空历史）
适用于项目初期，还没有重要的历史记录
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

print("=" * 70)
print("重新初始化 Git 仓库")
print("=" * 70)
print()
print("⚠️  警告：此操作将删除所有 Git 历史记录！")
print("⚠️  如果已推送到远程仓库，远程仓库将无法合并")
print()

response = input("确认重新初始化？(yes/no): ")
if response.lower() != 'yes':
    print("已取消")
    sys.exit(0)

print()
print("步骤 1: 备份当前 .git 目录...")

# 备份 .git
git_dir = Path(".git")
backup_dir = Path(".git.backup")

if git_dir.exists():
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    shutil.copytree(git_dir, backup_dir)
    print(f"✅ 已备份到 {backup_dir}")
else:
    print("❌ 未找到 .git 目录")
    sys.exit(1)

print()
print("步骤 2: 删除 .git 目录...")
shutil.rmtree(git_dir)
print("✅ 已删除")

print()
print("步骤 3: 重新初始化 Git...")
subprocess.run(['git', 'init'], check=True)
print("✅ Git 仓库已初始化")

print()
print("步骤 4: 添加所有文件（敏感文件已被 .gitignore 忽略）...")
subprocess.run(['git', 'add', '.'], check=True)
print("✅ 文件已添加")

print()
print("步骤 5: 创建初始提交...")
subprocess.run(['git', 'commit', '-m', 'Initial commit (clean history)'], check=True)
print("✅ 初始提交完成")

print()
print("=" * 70)
print("✅ 重新初始化完成！")
print("=" * 70)
print()
print("后续步骤：")
print("  1. 检查提交内容：git log")
print("  2. 检查敏感文件是否被忽略：git status")
print("  3. 推送到远程（如果是新仓库）：")
print("     git remote add origin <your-repo-url>")
print("     git push -u origin main")
print()
print("  4. 如果远程仓库已存在，需要强制推送：")
print("     git push --force origin main")
print()
print(f"备份目录：{backup_dir}")
print("如果一切正常，可以删除备份：")
print(f"  Remove-Item -Recurse -Force {backup_dir}")
print()
