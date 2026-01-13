#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter Screenshot Processor - 自测脚本
验证所有功能是否正常工作
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_environment():
    """检查环境配置"""
    print("=" * 50)
    print("1. 检查环境配置")
    print("=" * 50)
    
    checks = {
        "OSS_ACCESS_KEY_ID": os.getenv("OSS_ACCESS_KEY_ID"),
        "OSS_ACCESS_KEY_SECRET": os.getenv("OSS_ACCESS_KEY_SECRET"),
    }
    
    all_ok = True
    for key, value in checks.items():
        status = "✓" if value else "✗"
        print(f"{status} {key}: {'已设置' if value else '未设置'}")
        if not value:
            all_ok = False
    
    return all_ok

def check_dependencies():
    """检查依赖包"""
    print("\n" + "=" * 50)
    print("2. 检查依赖包")
    print("=" * 50)
    
    packages = [
        "requests",
        "alibabacloud_oss_v2",
        "openai",
        "sqlite3",
    ]
    
    all_ok = True
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"✓ {pkg}: 已安装")
        except ImportError:
            print(f"✗ {pkg}: 未安装")
            all_ok = False
    
    return all_ok

def check_directories():
    """检查目录和文件"""
    print("\n" + "=" * 50)
    print("3. 检查目录和文件")
    print("=" * 50)
    
    paths = {
        "screenshots": Path("screenshots"),
        "data": Path("data"),
        "src/twitter/processor.py": Path("src/twitter/processor.py"),
        "src/twitter/view_results.py": Path("src/twitter/view_results.py"),
        "tests/test_feishu.py": Path("tests/test_feishu.py"),
    }
    
    all_ok = True
    for name, path in paths.items():
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {name}: {'存在' if exists else '不存在'}")
        if not exists and name in ["screenshots", "src/twitter/processor.py"]:
            all_ok = False
    
    # 统计截图文件
    if paths["screenshots"].exists():
        screenshots = list(paths["screenshots"].glob("*.jpg")) + list(paths["screenshots"].glob("*.png"))
        print(f"   截图文件数: {len(screenshots)}")
    
    return all_ok

def check_database():
    """检查数据库"""
    print("\n" + "=" * 50)
    print("4. 检查数据库")
    print("=" * 50)
    
    db_path = Path("data/twitter_ai.db")
    
    if not db_path.exists():
        print("✗ 数据库不存在（首次运行时会自动创建）")
        return True
    
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        
        # 检查表是否存在
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='twitter_ai_results'"
        ).fetchall()
        
        if tables:
            print("✓ 数据库表存在")
            
            # 统计记录数
            count = conn.execute("SELECT COUNT(*) FROM twitter_ai_results").fetchone()[0]
            print(f"   已处理记录数: {count}")
            
            if count > 0:
                # 显示最近一条记录
                recent = conn.execute(
                    "SELECT tweet_id, summary, processed_at FROM twitter_ai_results ORDER BY processed_at DESC LIMIT 1"
                ).fetchone()
                print(f"   最近处理: {recent[0]} ({recent[2]})")
                print(f"   摘要: {recent[1][:50]}...")
        else:
            print("✗ 数据库表不存在（首次运行时会自动创建）")
        
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 数据库检查失败: {e}")
        return False

def test_imports():
    """测试核心模块导入"""
    print("\n" + "=" * 50)
    print("5. 测试核心模块导入")
    print("=" * 50)
    
    try:
        from src.twitter.processor import (
            ensure_db,
            upload_to_oss,
            analyze_screenshot,
            send_to_feishu,
        )
        print("✓ src.twitter.processor 模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def main():
    """主测试流程"""
    print("\n")
    print("*" * 50)
    print("Twitter Screenshot Processor - 自测")
    print("*" * 50)
    print("\n")
    
    results = []
    
    # 执行所有检查
    results.append(("环境配置", check_environment()))
    results.append(("依赖包", check_dependencies()))
    results.append(("目录和文件", check_directories()))
    results.append(("数据库", check_database()))
    results.append(("模块导入", test_imports()))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("自测结果汇总")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ 所有检查通过！系统可以正常运行。")
        print("\n运行命令:")
        print("  python twitter_screenshot_processor.py")
    else:
        print("✗ 部分检查失败，请根据上述错误信息进行修复。")
        print("\n环境变量设置命令（如果未设置）:")
        print('  [Environment]::SetEnvironmentVariable("OSS_ACCESS_KEY_ID", "YOUR_KEY", [EnvironmentVariableTarget]::User)')
        print('  [Environment]::SetEnvironmentVariable("OSS_ACCESS_KEY_SECRET", "YOUR_SECRET", [EnvironmentVariableTarget]::User)')
        print("\n依赖安装命令（如果缺失）:")
        print("  pip install -r requirements.txt")
    print("=" * 50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
