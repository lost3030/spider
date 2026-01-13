#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter Screenshot Processor
处理Twitter截图：上传到OSS、AI分析、存储结果、发送飞书通知
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

import alibabacloud_oss_v2 as oss
import requests
from alibabacloud_oss_v2.models import PutObjectRequest
from openai import OpenAI

# ==================== 配置加载 ====================
def load_secrets():
    """加载 secrets.json 配置文件"""
    secrets_path = Path("config/secrets.json")
    if secrets_path.exists():
        with open(secrets_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

SECRETS = load_secrets()

# ==================== 配置 ====================
DB_PATH = Path(os.getenv("TWITTER_AI_DB_PATH", "data/twitter_ai.db"))
SCREENSHOT_DIR = Path(os.getenv("TWITTER_SCREENSHOT_DIR", "screenshots"))

# OSS配置（优先从环境变量，其次从 secrets.json）
OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID") or SECRETS.get("oss", {}).get("access_key_id", "")
OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET") or SECRETS.get("oss", {}).get("access_key_secret", "")
OSS_BUCKET = os.getenv("OSS_BUCKET") or SECRETS.get("oss", {}).get("bucket", "shenyuan-x")
OSS_REGION = os.getenv("OSS_REGION") or SECRETS.get("oss", {}).get("region", "cn-hangzhou")
OSS_BASE_URL = f"https://{OSS_BUCKET}.oss-{OSS_REGION}.aliyuncs.com/"

# 飞书配置（优先从环境变量，其次从 secrets.json）
FEISHU_WEBHOOK = os.getenv("TWITTER_FEISHU_WEBHOOK") or SECRETS.get("feishu", {}).get("webhook", "")

# AI配置（优先从环境变量，其次从 secrets.json）
AI_API_KEY = os.getenv("QIANWEN_API_KEY") or SECRETS.get("qianwen", {}).get("api_key", "")
AI_BASE_URL = os.getenv("QIANWEN_BASE_URL") or SECRETS.get("qianwen", {}).get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
AI_MODEL = os.getenv("QIANWEN_MODEL") or SECRETS.get("qianwen", {}).get("model", "qwen-vl-plus")
AI_TIMEOUT = int(os.getenv("QIANWEN_TIMEOUT", "120"))  # AI调用超时时间（秒）

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
- 若不存在，写"无明确利好/利空"

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


# ==================== 数据库操作 ====================
def ensure_db() -> sqlite3.Connection:
    """初始化数据库和表结构"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS twitter_ai_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tweet_id TEXT NOT NULL UNIQUE,
            screenshot_path TEXT,
            oss_url TEXT,
            ai_result TEXT,
            summary TEXT,
            processed_at TEXT NOT NULL
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tweet_id ON twitter_ai_results(tweet_id);")
    conn.commit()
    return conn


def is_processed(conn: sqlite3.Connection, tweet_id: str) -> bool:
    """检查推文是否已处理"""
    row = conn.execute(
        "SELECT id FROM twitter_ai_results WHERE tweet_id = ?", (tweet_id,)
    ).fetchone()
    return row is not None


def save_result(
    conn: sqlite3.Connection,
    tweet_id: str,
    screenshot_path: str,
    oss_url: str,
    ai_result: str,
    summary: str,
    processed_at: str
) -> bool:
    """保存处理结果到数据库"""
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO twitter_ai_results (
                    tweet_id, screenshot_path, oss_url, ai_result, summary, processed_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(tweet_id) DO UPDATE SET
                    screenshot_path=excluded.screenshot_path,
                    oss_url=excluded.oss_url,
                    ai_result=excluded.ai_result,
                    summary=excluded.summary,
                    processed_at=excluded.processed_at;
                """,
                (tweet_id, screenshot_path, oss_url, ai_result, summary, processed_at),
            )
        return True
    except Exception as exc:
        print(f"[WARN] Failed to save result for {tweet_id}: {exc}")
        return False


# ==================== OSS上传 ====================
def upload_to_oss(file_path: str) -> Optional[str]:
    """上传文件到OSS，返回URL"""
    # 获取文件名
    object_name = os.path.basename(file_path)
    oss_url = f"{OSS_BASE_URL}{object_name}"
    
    try:
        # 使用配置的凭证信息
        credentials_provider = oss.credentials.StaticCredentialsProvider(
            access_key_id=OSS_ACCESS_KEY_ID,
            access_key_secret=OSS_ACCESS_KEY_SECRET
        )
        cfg = oss.config.load_default()
        cfg.credentials_provider = credentials_provider
        cfg.region = OSS_REGION

        client = oss.Client(cfg)

        # 上传文件
        with open(file_path, 'rb') as file_obj:
            request = PutObjectRequest(
                bucket=OSS_BUCKET,
                key=object_name,
                body=file_obj
            )
            response = client.put_object(request)
            print(f"[INFO] 上传成功: {object_name}, ETag: {response.etag}")

        return oss_url

    except Exception as exc:
        # 检查是否是文件已存在错误（FileImmutable）
        error_msg = str(exc)
        if "FileImmutable" in error_msg or "ObjectAlreadyExists" in error_msg:
            print(f"[WARN] 文件已存在于OSS: {object_name}，使用现有URL")
            return oss_url
        else:
            print(f"[ERROR] OSS上传失败 {file_path}: {exc}")
            return None


# ==================== AI分析 ====================
def analyze_screenshot(oss_url: str, retry_count: int = 3) -> Dict[str, Any]:
    """使用通义千问视觉模型分析截图"""
    last_error = None
    
    for attempt in range(retry_count):
        try:
            if attempt > 0:
                print(f"[INFO] AI调用重试 {attempt}/{retry_count-1}...")
            
            client = OpenAI(
                api_key=AI_API_KEY,
                base_url=AI_BASE_URL,
                timeout=AI_TIMEOUT,
            )

            completion = client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": AI_PROMPT.strip()},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": oss_url}
                            },
                        ]
                    }
                ]
            )

            # 获取完整响应
            result = completion.model_dump()
            
            # 提取AI返回的文本内容
            ai_text = ""
            if result.get("choices") and len(result["choices"]) > 0:
                message = result["choices"][0].get("message", {})
                ai_text = message.get("content", "")

            return {
                "success": True,
                "ai_text": ai_text,
                "full_response": json.dumps(result, ensure_ascii=False)
            }

        except Exception as exc:
            last_error = exc
            print(f"[WARN] AI分析失败（尝试 {attempt + 1}/{retry_count}）: {exc}")
            if attempt < retry_count - 1:
                import time
                time.sleep(2)  # 等待2秒后重试
    
    # 所有重试都失败
    print(f"[ERROR] AI分析最终失败: {last_error}")
    return {
        "success": False,
        "ai_text": "",
        "full_response": str(last_error)
    }


def extract_summary(ai_text: str) -> str:
    """从AI返回文本中提取一句话摘要"""
    # 匹配【一句话摘要】后面的内容
    match = re.search(r'【一句话摘要】\s*\n\s*(.+?)(?:\n\n|【|$)', ai_text, re.DOTALL)
    if match:
        summary = match.group(1).strip()
        # 清理多余的换行
        summary = re.sub(r'\s+', ' ', summary)
        return summary
    return ai_text[:100] if ai_text else "无摘要"


# ==================== 飞书通知 ====================
def send_to_feishu(title: str, image_url: str, text: str) -> bool:
    """发送消息到飞书"""
    if not FEISHU_WEBHOOK:
        print("[WARN] FEISHU_WEBHOOK not configured, skipping Feishu send.")
        return False

    payload = {
        "msg_type": "text",
        "content": {
            "text": text,
            "image_url": image_url,
            "title": title
        }
    }

    try:
        response = requests.post(
            FEISHU_WEBHOOK,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        print(f"[INFO] 飞书通知发送成功")
        return True
    except Exception as exc:
        print(f"[ERROR] 飞书通知发送失败: {exc}")
        return False


# ==================== 主处理流程 ====================
def process_screenshot(screenshot_path: Path, conn: sqlite3.Connection) -> bool:
    """处理单个截图：上传、分析、存储、通知"""
    import datetime as dt

    # 从文件名提取tweet_id（假设文件名是 {tweet_id}.jpg）
    tweet_id = screenshot_path.stem
    
    print(f"\n[INFO] ========== 处理截图: {tweet_id} ==========")

    # 检查是否已处理
    if is_processed(conn, tweet_id):
        print(f"[INFO] 推文 {tweet_id} 已处理，跳过")
        return False

    # 1. 上传到OSS
    print(f"[INFO] 上传截图到OSS...")
    oss_url = upload_to_oss(str(screenshot_path))
    if not oss_url:
        print(f"[ERROR] OSS上传失败，跳过该推文")
        return False

    print(f"[INFO] OSS URL: {oss_url}")

    # 2. AI分析
    print(f"[INFO] 调用AI分析...")
    ai_result = analyze_screenshot(oss_url)
    
    if not ai_result["success"]:
        print(f"[ERROR] AI分析失败，跳过该推文")
        return False

    ai_text = ai_result["ai_text"]
    full_response = ai_result["full_response"]
    
    print(f"[INFO] AI分析完成")
    print(f"[INFO] AI返回内容:\n{ai_text[:200]}...")

    # 3. 提取摘要
    summary = extract_summary(ai_text)
    print(f"[INFO] 摘要: {summary}")

    # 4. 保存到数据库
    processed_at = dt.datetime.now().isoformat(timespec="seconds")
    if save_result(conn, tweet_id, str(screenshot_path), oss_url, full_response, summary, processed_at):
        print(f"[INFO] 结果已保存到数据库")
    else:
        print(f"[WARN] 数据库保存失败")

    # 5. 发送飞书通知
    print(f"[INFO] 发送飞书通知...")
    send_to_feishu(
        title=summary,
        image_url=oss_url,
        text=ai_text
    )

    return True


def validate_config() -> bool:
    """验证配置是否完整"""
    # 检查OSS配置
    if not OSS_ACCESS_KEY_ID or not OSS_ACCESS_KEY_SECRET:
        print("[ERROR] OSS密钥配置缺失")
        return False
    
    # 检查AI配置
    if not AI_API_KEY:
        print("[ERROR] AI API KEY未配置")
        return False
    
    return True


def main():
    """主入口"""
    print(f"[INFO] Twitter截图处理器启动")
    print(f"[INFO] 截图目录: {SCREENSHOT_DIR}")
    print(f"[INFO] 数据库路径: {DB_PATH}")
    print(f"[INFO] OSS Bucket: {OSS_BUCKET}")
    print(f"[INFO] 飞书 Webhook: {FEISHU_WEBHOOK}")

    # 验证配置
    if not validate_config():
        print("\n[ERROR] 配置验证失败，请检查代码中的密钥配置")
        return

    # 确保目录和数据库存在
    if not SCREENSHOT_DIR.exists():
        print(f"[ERROR] 截图目录不存在: {SCREENSHOT_DIR}")
        return

    conn = None
    try:
        conn = ensure_db()

        # 获取所有截图文件
        screenshots = list(SCREENSHOT_DIR.glob("*.jpg")) + list(SCREENSHOT_DIR.glob("*.png"))
        print(f"[INFO] 找到 {len(screenshots)} 个截图文件")

        # 处理每个截图
        processed_count = 0
        for screenshot in screenshots:
            if process_screenshot(screenshot, conn):
                processed_count += 1

        print(f"\n[INFO] 处理完成！共处理 {processed_count} 个新截图")
    
    except KeyboardInterrupt:
        print(f"\n[INFO] 用户中断，正在退出...")
    except Exception as exc:
        print(f"\n[ERROR] 程序异常: {exc}")
    finally:
        if conn:
            conn.close()
            print(f"[INFO] 数据库连接已关闭")


if __name__ == "__main__":
    main()
