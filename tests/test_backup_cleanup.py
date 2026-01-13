#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试备份脚本的清理功能"""

import shutil
from pathlib import Path
from datetime import datetime, timedelta

# 创建测试备份（模拟不同日期）
backup_dir = Path("data/backups")
backup_dir.mkdir(parents=True, exist_ok=True)

# 模拟5天的备份（应该只保留最新3个）
dates = [
    datetime.now() - timedelta(days=4),
    datetime.now() - timedelta(days=3),
    datetime.now() - timedelta(days=2),
    datetime.now() - timedelta(days=1),
    datetime.now()
]

print("创建测试备份文件...")
for i, date in enumerate(dates):
    date_str = date.strftime("%Y%m%d")
    test_file = backup_dir / f"test_{date_str}.db"
    
    # 创建测试文件
    with open(test_file, 'w') as f:
        f.write(f"Test backup {i+1}")
    
    print(f"  创建: test_{date_str}.db")

print(f"\n总共创建了 {len(dates)} 个测试备份文件")
print("\n现在运行备份脚本，应该会清理掉最旧的2个...")
