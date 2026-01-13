#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试飞书通知功能"""

import sqlite3
import sys
import asyncio
sys.path.insert(0, 'src/twitter')

from twitter_pipeline import process_new_tweets, upload_to_oss

# 查询一条有截图的推文
conn = sqlite3.connect('data/twitter.db')
tweet = conn.execute("""
    SELECT id, text, screenshot_path, user_handle, fetched_at
    FROM tweets 
    WHERE screenshot_path IS NOT NULL 
    LIMIT 1
""").fetchone()

if not tweet:
    print("❌ 没有找到有截图的推文")
    sys.exit(1)

tweet_id, text, screenshot_path, user_handle, fetched_at = tweet
print(f"📝 找到推文: {tweet_id}")
print(f"👤 用户: @{user_handle}")
print(f"📄 内容: {text[:100]}...")
print(f"📸 截图: {screenshot_path}")
print(f"⏰ 时间: {fetched_at}")
print()

# 先删除这条推文的 AI 分析结果（如果存在）
ai_conn = sqlite3.connect('data/twitter_ai.db')
deleted = ai_conn.execute("DELETE FROM twitter_ai_results WHERE tweet_id = ?", (tweet_id,)).rowcount
ai_conn.commit()
if deleted > 0:
    print(f"✅ 已清除旧的 AI 分析结果")
else:
    print(f"ℹ️  这条推文之前没有 AI 分析结果")
print()

# 构造推文数据
test_tweet = {
    'id': tweet_id,
    'text': text,
    'user_handle': user_handle,
    'screenshot_path': screenshot_path,
    'fetched_at': fetched_at
}

# 运行处理流程
print("🚀 开始测试 AI 分析和飞书通知...")
print("=" * 60)
# process_new_tweets 不是异步函数，直接调用
process_new_tweets([test_tweet], ai_conn)

# 关闭连接
conn.close()
ai_conn.close()

print("\n" + "=" * 60)
print("✅ 测试完成！")
