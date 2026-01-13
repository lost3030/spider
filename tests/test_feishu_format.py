#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试飞书通知格式化"""

import sys
sys.path.insert(0, 'src/twitter')

from twitter_pipeline import format_ai_result, send_to_feishu

# 测试 JSON 数据
test_json = """```json
{
  "summary": "特斯拉Q4交付量超预期，马斯克暗示柏林工厂扩产，短期利好股价",
  "signal_type": "A",
  "direction": "Long",
  "assets": {
    "US": ["TSLA"],
    "CN": ["比亚迪 (002594.SZ)", "宁德时代 (300750.SZ)"]
  },
  "confidence": 7,
  "expiry": "3天",
  "risk": "若交付量被证伪或Q1指引低于预期，信号失效"
}
```"""

print("=" * 60)
print("原始 JSON:")
print("=" * 60)
print(test_json)
print()

print("=" * 60)
print("格式化后:")
print("=" * 60)
formatted = format_ai_result(test_json, "https://shenyuan-x.oss-cn-hangzhou.aliyuncs.com/test.jpg")
print(formatted)
print()

# 发送测试通知
print("=" * 60)
print("发送飞书测试通知...")
print("=" * 60)
result = send_to_feishu(
    title="测试标题",
    image_url="https://shenyuan-x.oss-cn-hangzhou.aliyuncs.com/2009543812801241315.jpg",
    text=test_json
)

if result:
    print("✅ 发送成功！请检查飞书")
else:
    print("❌ 发送失败")
