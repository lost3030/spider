import os
from openai import OpenAI

AI_PROMPT = """
你是一名事件驱动型投资信号分析器。

输入：
- 一张 Elon Musk 的 X 截图（可能包含文字、图片、视频或转发）

任务：
将该截图压缩为【交易级信号】，而不是内容解读。

请严格按以下步骤执行：

1. 一句话摘要  
- 用一句话概括马斯克本次发言的核心信息及其潜在市场含义  
- 禁止背景解释与复述原文

2. 信号类型（只能选一个）  
A. 行动/公司行为（回购、产能、订单、并购等）  
B. 技术路线/时间表（量产、成本曲线、里程碑）  
C. 叙事转向（立场/态度改变，影响资金偏好）  
D. 噪音（无清晰对象或传导路径）

3. 利好 / 利空映射  
- 利好：给出明确【概念/产业】及【具体标的】  
- 利空：给出明确【概念/产业】及【具体标的】  
- 若不存在，写“无明确利好/利空”

4. 置信度（0–100）  
- 表示类似类型的马斯克发言在历史上引发真实市场反应的可信度  
- 若为噪音，置信度不得超过 40

输出格式（必须严格一致）：

【一句话摘要】
……

【信号类型】
A / B / C / D

【利好】
- 概念：
- 标的：

【利空】
- 概念：
- 标的：

【置信度】
XX / 100
"""

import os
import json
from pathlib import Path

# 加载配置
def load_secrets():
    """加载 secrets.json 配置文件"""
    secrets_path = Path("config/secrets.json")
    if secrets_path.exists():
        with open(secrets_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

SECRETS = load_secrets()

# 获取 API Key（优先从环境变量，其次从 secrets.json）
API_KEY = os.getenv("QIANWEN_API_KEY") or SECRETS.get("qianwen", {}).get("api_key", "")
BASE_URL = os.getenv("QIANWEN_BASE_URL") or SECRETS.get("qianwen", {}).get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")

if not API_KEY:
    raise ValueError("请配置 QIANWEN_API_KEY 环境变量或在 config/secrets.json 中设置 api_key")

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)
completion = client.chat.completions.create(
    model="qwen-vl-plus",  # 此处以qwen-vl-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    messages=[
        {"role": "system", "content": AI_PROMPT.strip()},
        {"role": "user","content": [
            {"type": "image_url",
             "image_url": {"url": "https://shenyuan-x.oss-cn-hangzhou.aliyuncs.com/2009211541800001587.jpg"}},
            ]}]
    )
print(completion.model_dump_json())