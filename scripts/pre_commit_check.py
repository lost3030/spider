#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git 提交前安全检查
扫描即将提交的文件，检查是否包含敏感信息
"""

import re
import subprocess
import sys
from pathlib import Path

# 敏感信息模式
SENSITIVE_PATTERNS = [
    (r'LTAI[\w]{16,}', 'OSS Access Key ID'),
    (r'sk-[\w]{32,}', 'API Key'),
    (r'https://[^\s]*webhook[^\s]*', 'Webhook URL'),
    (r'access_key_secret.*["\'][\w+/=]{20,}["\']', 'Access Key Secret'),
]

def check_git_staged_files():
    """检查 git 暂存区的文件"""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        print("❌ 无法获取 git 暂存文件")
        return []

def scan_file_for_secrets(file_path: Path):
    """扫描文件中的敏感信息"""
    if not file_path.exists():
        return []
    
    # 跳过二进制文件和示例文件
    if file_path.suffix in ['.db', '.sqlite', '.jpg', '.png', '.gif']:
        return []
    if file_path.name.endswith('.example'):
        return []
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except:
        return []
    
    findings = []
    for pattern, description in SENSITIVE_PATTERNS:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            findings.append({
                'file': str(file_path),
                'line': line_num,
                'type': description,
                'match': match.group()[:50] + '...' if len(match.group()) > 50 else match.group()
            })
    
    return findings

def main():
    print("=" * 70)
    print("Git 提交前安全检查")
    print("=" * 70)
    
    # 获取即将提交的文件
    staged_files = check_git_staged_files()
    
    if not staged_files or staged_files == ['']:
        print("\n✅ 没有暂存的文件")
        return 0
    
    print(f"\n检查 {len(staged_files)} 个暂存文件...\n")
    
    all_findings = []
    for file_path_str in staged_files:
        if not file_path_str:
            continue
        file_path = Path(file_path_str)
        findings = scan_file_for_secrets(file_path)
        all_findings.extend(findings)
    
    if all_findings:
        print("⚠️  发现可能的敏感信息：\n")
        for finding in all_findings:
            print(f"  文件: {finding['file']}")
            print(f"  行号: {finding['line']}")
            print(f"  类型: {finding['type']}")
            print(f"  内容: {finding['match']}")
            print()
        
        print("=" * 70)
        print("❌ 检查失败！请移除敏感信息后再提交")
        print("=" * 70)
        print("\n建议：")
        print("  1. 将敏感信息移到 .env 或 config/secrets.json")
        print("  2. 使用环境变量替代硬编码")
        print("  3. 确保敏感文件在 .gitignore 中")
        return 1
    else:
        print("=" * 70)
        print("✅ 安全检查通过！未发现敏感信息")
        print("=" * 70)
        print("\n可以安全提交代码了！")
        return 0

if __name__ == "__main__":
    sys.exit(main())
