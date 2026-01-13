#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库性能基准测试
对比优化前后的性能差异
"""

import sqlite3
import time
from pathlib import Path

DB_PATH = Path("data/twitter.db")
AI_DB_PATH = Path("data/twitter_ai.db")

def test_query_performance():
    """测试查询性能"""
    print("=" * 60)
    print("数据库性能测试")
    print("=" * 60)
    
    if not DB_PATH.exists():
        print("[ERROR] 数据库不存在，请先运行爬虫")
        return
    
    conn = sqlite3.connect(DB_PATH)
    
    # 获取数据量
    tweet_count = conn.execute("SELECT COUNT(*) FROM tweets").fetchone()[0]
    print(f"测试数据量: {tweet_count:,} 条推文\n")
    
    # 测试1：查询最近300条（使用索引）
    print("[测试1] 查询最近300条推文")
    start = time.time()
    rows = conn.execute(
        "SELECT id FROM tweets WHERE user_handle = ? ORDER BY fetched_at DESC LIMIT 300",
        ("elonmusk",)
    ).fetchall()
    duration = time.time() - start
    print(f"返回: {len(rows)} 条")
    print(f"耗时: {duration*1000:.2f}ms")
    print()
    
    # 测试2：查询所有推文（对比全表扫描）
    print("[测试2] 查询所有推文ID（全表）")
    start = time.time()
    rows = conn.execute("SELECT id FROM tweets").fetchall()
    duration = time.time() - start
    print(f"返回: {len(rows)} 条")
    print(f"耗时: {duration*1000:.2f}ms")
    print()
    
    # 测试3和4：对比循环查询 vs 批量查询
    test_ids = []
    if tweet_count > 0:
        test_ids = [r[0] for r in rows[:10]]  # 取10条测试
        
        print("[测试3] 单条查询性能（模拟N+1问题）")
        start = time.time()
        for tweet_id in test_ids:
            conn.execute("SELECT 1 FROM tweets WHERE id = ?", (tweet_id,)).fetchone()
        duration = time.time() - start
        
        print(f"查询次数: {len(test_ids)}")
        print(f"总耗时: {duration*1000:.2f}ms")
        print(f"平均: {duration*1000/len(test_ids):.2f}ms/次")
        print()
        
        # 测试4：批量查询（优化方案）
        print("[测试4] 批量查询性能（优化方案）")
        start = time.time()
        all_ids = {r[0] for r in conn.execute("SELECT id FROM tweets").fetchall()}
        duration_query = time.time() - start
        
        # 内存查找
        start = time.time()
        for tweet_id in test_ids:
            _ = tweet_id in all_ids  # O(1) 查找
        duration_lookup = time.time() - start
        
        print(f"批量查询耗时: {duration_query*1000:.2f}ms")
        print(f"内存查找耗时: {duration_lookup*1000:.2f}ms (10次)")
        print(f"总耗时: {(duration_query + duration_lookup)*1000:.2f}ms")
        
        # 对比
        improvement = (duration / (duration_query + duration_lookup))
        print(f"\n性能提升: {improvement:.1f}x ⚡")
        print()
    
    conn.close()
    
    # 测试AI数据库
    if AI_DB_PATH.exists():
        print("-" * 60)
        print("AI 结果数据库测试")
        print("-" * 60)
        
        ai_conn = sqlite3.connect(AI_DB_PATH)
        ai_count = ai_conn.execute("SELECT COUNT(*) FROM twitter_ai_results").fetchone()[0]
        print(f"AI分析数量: {ai_count:,} 条\n")
        
        # 测试索引性能
        if ai_count > 0:
            print("[测试5] tweet_id 索引查询")
            test_id = ai_conn.execute("SELECT tweet_id FROM twitter_ai_results LIMIT 1").fetchone()[0]
            
            start = time.time()
            for _ in range(100):
                ai_conn.execute("SELECT 1 FROM twitter_ai_results WHERE tweet_id = ? LIMIT 1", (test_id,)).fetchone()
            duration = time.time() - start
            
            print(f"查询次数: 100")
            print(f"总耗时: {duration*1000:.2f}ms")
            print(f"平均: {duration*1000/100:.2f}ms/次")
            print()
        
        ai_conn.close()
    
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)


def test_index_usage():
    """检查索引是否被使用"""
    print("\n" + "=" * 60)
    print("索引使用情况分析")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    
    # 检查查询计划
    queries = [
        ("查询最近推文", "SELECT id FROM tweets WHERE user_handle = 'elonmusk' ORDER BY fetched_at DESC LIMIT 300"),
        ("单条查询", "SELECT 1 FROM tweets WHERE id = '123'"),
        ("时间范围查询", "SELECT COUNT(*) FROM tweets WHERE fetched_at > '2026-01-01'"),
    ]
    
    for name, query in queries:
        print(f"\n[{name}]")
        print(f"SQL: {query}")
        print("查询计划:")
        
        plan = conn.execute(f"EXPLAIN QUERY PLAN {query}").fetchall()
        for row in plan:
            print(f"  {row}")
    
    conn.close()
    print()


def test_db_size():
    """分析数据库大小和统计信息"""
    print("=" * 60)
    print("数据库统计信息")
    print("=" * 60)
    
    dbs = [
        ("推文数据库", DB_PATH, "tweets"),
        ("AI结果数据库", AI_DB_PATH, "twitter_ai_results"),
    ]
    
    for name, path, table in dbs:
        if not path.exists():
            continue
        
        print(f"\n{name}: {path}")
        
        # 文件大小
        size_mb = path.stat().st_size / 1024 / 1024
        print(f"  文件大小: {size_mb:.2f} MB")
        
        # 记录数
        conn = sqlite3.connect(path)
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  记录数: {count:,}")
        
        if count > 0:
            avg_size = (size_mb * 1024) / count
            print(f"  平均大小: {avg_size:.2f} KB/条")
        
        # 索引信息
        print(f"  索引:")
        indexes = conn.execute(f"PRAGMA index_list({table})").fetchall()
        for idx in indexes:
            print(f"    - {idx[1]} ({'UNIQUE' if idx[2] else 'INDEX'})")
        
        conn.close()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_query_performance()
    test_index_usage()
    test_db_size()
