#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询Twitter截图AI分析结果
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path("data/twitter_ai.db")

def main():
    if not DB_PATH.exists():
        print(f"数据库不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    
    # 统计
    count = conn.execute("SELECT COUNT(*) FROM twitter_ai_results").fetchone()[0]
    print(f"=== Twitter AI 分析结果统计 ===")
    print(f"总记录数: {count}\n")
    
    # 查询所有记录
    rows = conn.execute("""
        SELECT tweet_id, summary, oss_url, processed_at 
        FROM twitter_ai_results 
        ORDER BY processed_at DESC
    """).fetchall()
    
    print("=== 处理记录列表 ===")
    for idx, row in enumerate(rows, 1):
        tweet_id, summary, oss_url, processed_at = row
        print(f"\n{idx}. Tweet ID: {tweet_id}")
        print(f"   处理时间: {processed_at}")
        print(f"   摘要: {summary}")
        print(f"   OSS URL: {oss_url}")
    
    # 显示一条详细结果
    if rows:
        print(f"\n=== 详细示例（Tweet ID: {rows[0][0]}）===")
        detail = conn.execute(
            "SELECT ai_result FROM twitter_ai_results WHERE tweet_id = ?",
            (rows[0][0],)
        ).fetchone()
        
        if detail and detail[0]:
            try:
                result = json.loads(detail[0])
                # 提取AI文本内容
                if "choices" in result and len(result["choices"]) > 0:
                    ai_text = result["choices"][0].get("message", {}).get("content", "")
                    print(ai_text)
                else:
                    print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
            except json.JSONDecodeError:
                # 如果不是JSON格式，直接打印
                print(detail[0][:500])
            except Exception as e:
                print(f"解析错误: {e}")
                print(detail[0][:500])
    
    conn.close()

if __name__ == "__main__":
    main()
