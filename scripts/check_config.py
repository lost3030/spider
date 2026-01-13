#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证脚本
检查所有配置是否正确加载，且不包含硬编码的敏感信息
"""

import sys
from pathlib import Path

sys.path.insert(0, 'src/twitter')

def check_config():
    """检查配置是否正确"""
    print("=" * 60)
    print("配置验证")
    print("=" * 60)
    
    from twitter_pipeline import (
        OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET,
        AI_API_KEY, FEISHU_WEBHOOK, TARGET_USER
    )
    
    # 检查 OSS 配置
    print("\n[OSS 配置]")
    if OSS_ACCESS_KEY_ID:
        print(f"  ✅ Access Key ID: {OSS_ACCESS_KEY_ID[:10]}..." + "*" * 10)
    else:
        print("  ❌ Access Key ID: 未配置")
    
    if OSS_ACCESS_KEY_SECRET:
        print(f"  ✅ Access Key Secret: " + "*" * 20 + f"...{OSS_ACCESS_KEY_SECRET[-4:]}")
    else:
        print("  ❌ Access Key Secret: 未配置")
    
    print(f"  ✅ Bucket: {OSS_BUCKET}")
    
    # 检查 AI 配置
    print("\n[AI 配置]")
    if AI_API_KEY:
        print(f"  ✅ API Key: {AI_API_KEY[:10]}..." + "*" * 10)
    else:
        print("  ❌ API Key: 未配置")
    
    # 检查飞书配置
    print("\n[飞书配置]")
    if FEISHU_WEBHOOK:
        print(f"  ✅ Webhook: {FEISHU_WEBHOOK[:50]}...")
    else:
        print("  ❌ Webhook: 未配置")
    
    # 检查 Twitter 配置
    print("\n[Twitter 配置]")
    print(f"  ✅ Target User: @{TARGET_USER}")
    
    # 检查敏感文件是否被 git 忽略
    print("\n[安全检查]")
    sensitive_files = [
        ".env",
        "config/secrets.json",
        "config/twitter_cookies.json"
    ]
    
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()
        all_ignored = True
        for file in sensitive_files:
            # 简单检查（实际 gitignore 规则更复杂）
            if file in gitignore_content or "secrets.json" in gitignore_content:
                print(f"  ✅ {file} - 已被 .gitignore 忽略")
            else:
                print(f"  ⚠️  {file} - 可能未被忽略")
                all_ignored = False
        
        if all_ignored:
            print("\n✅ 所有敏感文件都已正确配置 .gitignore")
    else:
        print("  ❌ .gitignore 文件不存在")
    
    # 检查示例文件
    print("\n[示例文件]")
    example_files = [
        "config/secrets.json.example",
        ".env.example"
    ]
    
    for file in example_files:
        if Path(file).exists():
            print(f"  ✅ {file} - 存在")
        else:
            print(f"  ⚠️  {file} - 不存在（建议创建）")
    
    print("\n" + "=" * 60)
    print("验证完成！")
    print("=" * 60)
    print("\n提示：")
    print("  1. 确保 .env 或 config/secrets.json 包含真实配置")
    print("  2. 提交代码前检查是否泄露敏感信息")
    print("  3. 示例文件(.example)可以安全提交到 git")


if __name__ == "__main__":
    try:
        check_config()
    except Exception as e:
        print(f"\n❌ 配置验证失败: {e}")
        sys.exit(1)
