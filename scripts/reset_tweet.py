#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新处理指定的推文截图（清除数据库记录）
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("data/twitter_ai.db")

def reset_tweet(tweet_id: str):
    """清除指定推文的处理记录"""
    if not DB_PATH.exists():
        print(f"[ERROR] 数据库不存在: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM twitter_ai_results WHERE tweet_id = ?", (tweet_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"[INFO] 已删除推文 {tweet_id} 的记录，可以重新处理")
        else:
            print(f"[WARN] 未找到推文 {tweet_id} 的记录")
    finally:
        conn.close()

def reset_all():
    """清空所有记录"""
    if not DB_PATH.exists():
        print(f"[ERROR] 数据库不存在: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM twitter_ai_results")
        conn.commit()
        print(f"[INFO] 已删除所有记录 ({cursor.rowcount} 条)")
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scripts/reset_tweet.py <tweet_id>  # 重置指定推文")
        print("  python scripts/reset_tweet.py --all       # 重置所有推文")
        sys.exit(1)
    
    if sys.argv[1] == "--all":
        confirm = input("确认要删除所有记录？(yes/no): ")
        if confirm.lower() == "yes":
            reset_all()
        else:
            print("已取消")
    else:
        tweet_id = sys.argv[1]
        reset_tweet(tweet_id)
