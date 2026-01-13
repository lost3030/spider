#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞书通知功能
"""

import os
import requests

FEISHU_WEBHOOK = os.getenv(
    "TWITTER_FEISHU_WEBHOOK",
    "https://www.feishu.cn/flow/api/trigger-webhook/6228b59ee92453808a92d08ff000cb4c"
)

def test_feishu_notification():
    """测试飞书通知"""
    
    # 测试数据
    title = "马斯克旗下 Grok 应用在芬兰登顶，可能强化其 AI 业务的市场叙事。"
    image_url = "https://shenyuan-x.oss-cn-hangzhou.aliyuncs.com/2009543812801241315.jpg"
    text = """【一句话摘要】
马斯克旗下 Grok 应用在芬兰登顶，可能强化其 AI 业务的市场叙事。

【信号类型】
C. 叙事转向（立场/态度改变，影响资金偏好）

【利好】
- 概念：人工智能应用、社交媒体平台
- 标的：X（原 Twitter）、Grok

【利空】
无明确利好/利空

【置信度】
75 / 100"""
    
    payload = {
        "msg_type": "text",
        "content": {
            "text": text,
            "image_url": image_url,
            "title": title
        }
    }
    
    print("=== 测试飞书通知 ===")
    print(f"Webhook: {FEISHU_WEBHOOK}")
    print(f"Title: {title}")
    print(f"Image URL: {image_url}")
    print(f"\n发送中...")
    
    try:
        response = requests.post(
            FEISHU_WEBHOOK,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        print(f"✓ 发送成功！")
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        return True
    except Exception as exc:
        print(f"✗ 发送失败: {exc}")
        return False

if __name__ == "__main__":
    test_feishu_notification()
