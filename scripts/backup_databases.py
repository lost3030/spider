#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库备份脚本
- 备份所有数据库文件
- 使用日期作为后缀
- 只保留最新的3个备份
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

# 配置
BACKUP_DIR = Path("data/backups")
DB_FILES = [
    "data/twitter.db",
    "data/twitter_ai.db",
    "data/mofcom.db"
]
MAX_BACKUPS = 3  # 保留最新的3个备份

def ensure_backup_dir():
    """确保备份目录存在"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] 备份目录: {BACKUP_DIR}")

def backup_database(db_path: str) -> bool:
    """备份单个数据库文件"""
    db_file = Path(db_path)
    
    if not db_file.exists():
        print(f"[WARN] 数据库文件不存在，跳过: {db_path}")
        return False
    
    # 生成备份文件名（带日期后缀）
    timestamp = datetime.now().strftime("%Y%m%d")
    backup_name = f"{db_file.stem}_{timestamp}{db_file.suffix}"
    backup_path = BACKUP_DIR / backup_name
    
    try:
        # 复制数据库文件
        shutil.copy2(db_file, backup_path)
        file_size = backup_path.stat().st_size / 1024  # KB
        print(f"[INFO] 备份成功: {backup_name} ({file_size:.1f} KB)")
        return True
    except Exception as exc:
        print(f"[ERROR] 备份失败 {db_path}: {exc}")
        return False

def cleanup_old_backups(db_name: str):
    """清理旧备份，只保留最新的N个"""
    # 查找该数据库的所有备份文件
    pattern = f"{db_name}_*.db"
    backups = sorted(BACKUP_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if len(backups) <= MAX_BACKUPS:
        print(f"[INFO] {db_name}: 当前有 {len(backups)} 个备份，无需清理")
        return
    
    # 删除多余的旧备份
    for old_backup in backups[MAX_BACKUPS:]:
        try:
            old_backup.unlink()
            print(f"[INFO] 删除旧备份: {old_backup.name}")
        except Exception as exc:
            print(f"[WARN] 删除失败 {old_backup.name}: {exc}")

def main():
    """主函数"""
    print("=" * 60)
    print("数据库备份任务")
    print("=" * 60)
    print(f"[INFO] 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[INFO] 保留最新 {MAX_BACKUPS} 个备份")
    print()
    
    ensure_backup_dir()
    
    # 备份所有数据库
    success_count = 0
    for db_path in DB_FILES:
        if backup_database(db_path):
            success_count += 1
            # 清理该数据库的旧备份
            db_name = Path(db_path).stem
            cleanup_old_backups(db_name)
    
    print()
    print("=" * 60)
    print(f"[INFO] 备份完成！成功 {success_count}/{len(DB_FILES)} 个数据库")
    print(f"[INFO] 备份目录: {BACKUP_DIR.absolute()}")
    print("=" * 60)

if __name__ == "__main__":
    main()
