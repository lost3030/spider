#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter 完整流水线：爬取 → 上传OSS → AI分析 → 飞书通知
合并版本：先完成爬取，然后批量处理
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import os
import random
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import alibabacloud_oss_v2 as oss
import requests
from alibabacloud_oss_v2.models import PutObjectRequest
from openai import OpenAI
from playwright.async_api import async_playwright, Page, Browser

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
# Twitter 配置
TARGET_USER = os.getenv("TWITTER_USER") or SECRETS.get("twitter", {}).get("target_user", "elonmusk")
TARGET_URL = f"https://x.com/{TARGET_USER}"
COOKIE_FILE = Path(os.getenv("TWITTER_COOKIE_FILE", "config/twitter_cookies.json"))
DB_PATH = Path(os.getenv("TWITTER_DB_PATH", "data/twitter.db"))
SCREENSHOT_DIR = Path(os.getenv("TWITTER_SCREENSHOT_DIR", "screenshots"))

# 浏览器配置
HEADLESS = os.getenv("TWITTER_HEADLESS", "true").lower() == "true"
TIMEOUT = int(os.getenv("TWITTER_TIMEOUT", "60000"))

# 滚动配置
MAX_SCROLLS = int(os.getenv("TWITTER_MAX_SCROLLS", "5"))
SCROLL_DELAY = int(os.getenv("TWITTER_SCROLL_DELAY", "3000"))
MAX_DETAIL_PAGES = int(os.getenv("TWITTER_MAX_DETAIL_PAGES", "10"))

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
AI_TIMEOUT = int(os.getenv("QIANWEN_TIMEOUT", "120"))

# AI 分析数据库
AI_DB_PATH = Path(os.getenv("TWITTER_AI_DB_PATH", "data/twitter_ai.db"))

AI_PROMPT = """
你是一名事件驱动型投资信号分析器。

输入：
- 一张 Elon Musk 的 X 截图（可能包含文字、图片、视频或转发）

任务：
将该截图压缩为【交易级信号】，而不是内容解读。

请严格按以下步骤执行：

1. 一句话摘要summary
- 用一句话概括马斯克本次发言的核心信息及其潜在市场含义  
- 禁止背景解释与复述原文

2. 信号类型（只能选一个） signal_type 
A. 行动/公司行为（回购、产能、订单、并购等）  
B. 政策立场（对关税、监管、贸易的态度）  
C. 技术突破/产品发布  
D. 情绪/口水战（与竞争对手/政府的冲突）  
E. 纯个人生活/娱乐（对市场无影响）

3. 影响方向 direction
- Long（做多）/ Short（做空）/ Neutral（中性）  
- 必须有明确方向，除非是纯娱乐

4. 资产映射（必填）assets
列出受影响的具体资产，按影响强度排序：  
美股：
A股：  
- 如果影响宽泛（如"美国科技股"），只列核心3个

5. 置信度（0-10） confidence
- 0-3：噪音/个人观点，不可操作  
- 4-6：有价值但需观察  
- 7-10：可直接采取行动

6. 失效时间（必填）expiry
- 该信号的时效性（即刻/1天/3天/1周/1个月）  
- 示例："2小时内"（如盘前发推影响开盘）

输出格式（JSON）：
{
  "summary": "",
  "signal_type": "A",
  "direction": "Long",
  "assets": {
    "US": [""],
    "CN": [""]
  },
  "confidence": 7,
  "expiry": "3天"
}

注意：
- 禁止输出任何解释性文字，只输出 JSON
- 如果截图是纯娱乐/生活内容，confidence 设为 0-2
"""



# ==================== 数据库操作（爬虫部分）====================
def ensure_twitter_db() -> sqlite3.Connection:
    """初始化推文数据库"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tweets (
            id TEXT PRIMARY KEY,
            user_handle TEXT NOT NULL,
            text TEXT NOT NULL,
            is_repost INTEGER DEFAULT 0,
            link TEXT,
            screenshot_path TEXT,
            fetched_at TEXT NOT NULL,
            raw_json TEXT
        );
        """
    )
    # 删除旧的单列索引，使用复合索引替代
    conn.execute("DROP INDEX IF EXISTS idx_tweets_user;")
    
    # 时间索引：用于时间范围查询
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tweets_fetched ON tweets(fetched_at);")
    
    # 复合索引：优化 WHERE user_handle = ? ORDER BY fetched_at 查询
    # 这是一个覆盖索引(covering index)，避免了临时排序
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tweets_user_fetched ON tweets(user_handle, fetched_at DESC);")
    
    # 检查并添加 screenshot_path 列
    cursor = conn.execute("PRAGMA table_info(tweets);")
    columns = {row[1] for row in cursor.fetchall()}
    if "screenshot_path" not in columns:
        conn.execute("ALTER TABLE tweets ADD COLUMN screenshot_path TEXT;")
        print("[INFO] 已添加 screenshot_path 列到数据库")
    
    conn.commit()
    return conn


def known_tweet_ids(conn: sqlite3.Connection, user_handle: str) -> Set[str]:
    """获取已存储的推文 ID"""
    rows = conn.execute(
        "SELECT id FROM tweets WHERE user_handle = ? ORDER BY fetched_at DESC LIMIT 300",
        (user_handle,)
    ).fetchall()
    return {r[0] for r in rows}


def save_tweet(conn: sqlite3.Connection, tweet: Dict[str, Any]) -> bool:
    """保存推文到数据库"""
    fetched_at = dt.datetime.now().isoformat(timespec="seconds")
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO tweets (
                    id, user_handle, text, is_repost, link, screenshot_path, fetched_at, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    text=excluded.text,
                    is_repost=excluded.is_repost,
                    screenshot_path=excluded.screenshot_path,
                    fetched_at=excluded.fetched_at,
                    raw_json=excluded.raw_json;
                """,
                (
                    tweet["id"],
                    tweet.get("user_handle", ""),
                    tweet.get("text", ""),
                    tweet.get("is_repost", 0),
                    tweet.get("link"),
                    tweet.get("screenshot_path"),
                    fetched_at,
                    json.dumps(tweet, ensure_ascii=False),
                ),
            )
        return True
    except Exception as exc:
        print(f"[WARN] 保存推文失败 {tweet.get('id')}: {exc}")
        return False


# ==================== 数据库操作（AI处理部分）====================
def ensure_ai_db() -> sqlite3.Connection:
    """初始化AI分析结果数据库"""
    AI_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(AI_DB_PATH)
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
    # 索引：优化按时间查询已处理的推文
    conn.execute("CREATE INDEX IF NOT EXISTS idx_processed_at ON twitter_ai_results(processed_at);")
    conn.commit()
    return conn


def is_ai_processed(conn: sqlite3.Connection, tweet_id: str) -> bool:
    """检查推文是否已经AI分析过"""
    # 使用 UNIQUE 索引，查询速度 O(1)
    row = conn.execute(
        "SELECT 1 FROM twitter_ai_results WHERE tweet_id = ? LIMIT 1", (tweet_id,)
    ).fetchone()
    return row is not None


def get_processed_tweet_ids(conn: sqlite3.Connection) -> Set[str]:
    """批量获取已处理的推文ID（优化性能，避免循环查询）"""
    rows = conn.execute(
        "SELECT tweet_id FROM twitter_ai_results"
    ).fetchall()
    return {r[0] for r in rows}


def save_ai_result(
    conn: sqlite3.Connection,
    tweet_id: str,
    screenshot_path: str,
    oss_url: str,
    ai_result: str,
    summary: str,
    processed_at: str
) -> bool:
    """保存AI分析结果"""
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO twitter_ai_results (
                    tweet_id, screenshot_path, oss_url, ai_result, summary, processed_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(tweet_id) DO UPDATE SET
                    oss_url=excluded.oss_url,
                    ai_result=excluded.ai_result,
                    summary=excluded.summary,
                    processed_at=excluded.processed_at;
                """,
                (tweet_id, screenshot_path, oss_url, ai_result, summary, processed_at),
            )
        return True
    except Exception as exc:
        print(f"[WARN] 保存AI结果失败 {tweet_id}: {exc}")
        return False


# ==================== Cookie 管理 ====================
def load_cookies() -> List[Dict[str, Any]]:
    """从 JSON 文件加载 Cookie"""
    if not COOKIE_FILE.exists():
        raise SystemExit(
            f"❌ Cookie 文件不存在: {COOKIE_FILE}\n"
            f"请参考 twitter_cookies.json.example 创建配置文件"
        )
    
    with open(COOKIE_FILE, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    
    if not cookies:
        raise SystemExit("❌ Cookie 文件为空")
    
    return cookies


async def inject_cookies(page: Page, cookies: List[Dict[str, Any]]) -> None:
    """注入 Cookie 到浏览器"""
    await page.context.add_cookies(cookies)
    print(f"[INFO] 已注入 {len(cookies)} 个 Cookie")


# ==================== Twitter 爬虫逻辑 ====================
async def wait_for_timeline(page: Page, user_handle: str, timeout: int = 30000) -> None:
    """等待时间线加载"""
    try:
        await page.wait_for_selector(
            'article[data-testid="tweet"]',
            timeout=timeout,
            state="visible"
        )
        print(f"[INFO] 时间线加载成功")
    except Exception as exc:
        raise SystemExit(f"❌ 时间线加载失败（可能需要重新获取 Cookie）: {exc}")


async def collect_tweet_links(page: Page, user_handle: str) -> List[Dict[str, Any]]:
    """收集当前页面的推文链接"""
    articles = await page.query_selector_all('article[data-testid="tweet"]')
    tweets = []
    
    for article in articles:
        try:
            link_elem = await article.query_selector(f'a[href*="/{user_handle}/status/"]')
            if not link_elem:
                continue
            
            href = await link_elem.get_attribute("href")
            if not href:
                continue
            
            full_link = f"https://x.com{href}" if href.startswith("/") else href
            tweet_id = href.split("/status/")[-1].split("?")[0]
            
            tweets.append({
                "id": tweet_id,
                "user_handle": user_handle,
                "link": full_link,
                "is_repost": 0,
            })
        except Exception:
            continue
    
    return tweets


async def smooth_scroll(page: Page) -> None:
    """平滑滚动"""
    scroll_info = await page.evaluate("""
        () => ({
            currentY: window.scrollY,
            totalHeight: document.body.scrollHeight,
            viewHeight: window.innerHeight
        })
    """)
    
    current_y = scroll_info["currentY"]
    total_height = scroll_info["totalHeight"]
    view_height = scroll_info["viewHeight"]
    
    scroll_distance = view_height * random.uniform(2, 3)
    target_y = min(current_y + scroll_distance, total_height - view_height)
    
    steps = random.randint(8, 12)
    step_distance = (target_y - current_y) / steps
    
    for step in range(steps):
        next_y = current_y + step_distance * (step + 1)
        await page.evaluate(f"window.scrollTo({{ top: {next_y}, behavior: 'smooth' }})")
        await page.wait_for_timeout(random.randint(150, 400))
    
    await page.wait_for_timeout(SCROLL_DELAY)


async def fetch_tweet_detail(page: Page, tweet: Dict[str, Any], screenshot_dir: Path) -> Dict[str, Any]:
    """进入推文详情页，提取文字并截图"""
    tweet_id = tweet["id"]
    link = tweet["link"]
    
    print(f"[INFO] 进入详情页: {link}")
    
    try:
        await page.goto(link, timeout=TIMEOUT)
        await page.wait_for_selector('article[data-testid="tweet"]', timeout=15000, state="visible")
        await page.wait_for_timeout(1500)
        
        # 展开长推文
        try:
            show_more_btn = page.locator('article[data-testid="tweet"] button').filter(has_text="Show more").first
            if await show_more_btn.is_visible():
                await show_more_btn.click()
                await page.wait_for_timeout(1000)
        except Exception:
            pass
        
        # 提取文字
        try:
            text_locator = page.locator('article[data-testid="tweet"] [data-testid="tweetText"]').first
            text = await text_locator.inner_text() if await text_locator.count() > 0 else ""
            tweet["text"] = text.strip()
        except Exception:
            tweet["text"] = ""
        
        # 截图
        try:
            article_locator = page.locator('article[data-testid="tweet"]').first
            screenshot_path = screenshot_dir / f"{tweet_id}.jpg"
            await article_locator.screenshot(path=str(screenshot_path), type="jpeg", quality=90)
            tweet["screenshot_path"] = str(screenshot_path)
            print(f"[INFO] 已保存截图: {screenshot_path}")
        except Exception as exc:
            print(f"[WARN] 截图失败: {exc}")
            tweet["screenshot_path"] = None
        
        await page.wait_for_timeout(random.randint(2000, 4000))
        
    except Exception as exc:
        print(f"[WARN] 获取推文详情失败 {tweet_id}: {exc}")
        tweet["text"] = ""
        tweet["screenshot_path"] = None
    
    return tweet


async def scrape_new_tweets(user_handle: str, known_ids: Set[str]) -> List[Dict[str, Any]]:
    """爬取新推文（只处理不在 known_ids 中的推文）"""
    cookies = load_cookies()
    all_tweet_links: Dict[str, Dict[str, Any]] = {}
    
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        
        page = await context.new_page()
        await inject_cookies(page, cookies)
        
        # 阶段1：收集推文链接
        print(f"\n[INFO] ========== 阶段1：收集推文链接 ==========")
        await page.goto(TARGET_URL, timeout=TIMEOUT)
        await wait_for_timeline(page, user_handle, timeout=30000)
        
        for scroll_num in range(MAX_SCROLLS):
            print(f"\n[INFO] === 第 {scroll_num + 1}/{MAX_SCROLLS} 次滚动 ===")
            
            current_links = await collect_tweet_links(page, user_handle)
            
            new_count = 0
            for t in current_links:
                if t["id"] not in all_tweet_links:
                    all_tweet_links[t["id"]] = t
                    new_count += 1
            
            print(f"[INFO] 本次收集 {len(current_links)} 条，新增 {new_count} 条，总计 {len(all_tweet_links)} 条")
            
            if scroll_num < MAX_SCROLLS - 1:
                await smooth_scroll(page)
        
        print(f"\n[INFO] 链接收集完成，共 {len(all_tweet_links)} 条推文")
        
        # 过滤出新推文
        new_tweet_links = {tid: t for tid, t in all_tweet_links.items() if tid not in known_ids}
        print(f"[INFO] 其中新推文 {len(new_tweet_links)} 条（已排除数据库中已有的）")
        
        if not new_tweet_links:
            print(f"[INFO] 没有新推文，跳过详情页抓取")
            await browser.close()
            return []
        
        # 阶段2：只对新推文进入详情页
        print(f"\n[INFO] ========== 阶段2：获取新推文详情和截图 ==========")
        
        new_tweets = []
        tweet_list = list(new_tweet_links.values())
        
        # 限制数量
        if len(tweet_list) > MAX_DETAIL_PAGES:
            print(f"[INFO] 新推文 {len(tweet_list)} 条，限制只处理前 {MAX_DETAIL_PAGES} 条")
            tweet_list = tweet_list[:MAX_DETAIL_PAGES]
        
        for idx, tweet in enumerate(tweet_list):
            print(f"\n[INFO] === 处理 {idx + 1}/{len(tweet_list)} ===")
            detailed_tweet = await fetch_tweet_detail(page, tweet, SCREENSHOT_DIR)
            new_tweets.append(detailed_tweet)
            
            if (idx + 1) % 5 == 0:
                print(f"[INFO] 进度: {idx + 1}/{len(tweet_list)} ({(idx+1)*100//len(tweet_list)}%)")
        
        await browser.close()
    
    return new_tweets


# ==================== OSS 上传 ====================
def upload_to_oss(file_path: str) -> Optional[str]:
    """上传文件到OSS"""
    object_name = os.path.basename(file_path)
    oss_url = f"{OSS_BASE_URL}{object_name}"
    
    try:
        credentials_provider = oss.credentials.StaticCredentialsProvider(
            access_key_id=OSS_ACCESS_KEY_ID,
            access_key_secret=OSS_ACCESS_KEY_SECRET
        )
        cfg = oss.config.load_default()
        cfg.credentials_provider = credentials_provider
        cfg.region = OSS_REGION
        
        client = oss.Client(cfg)
        
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
        error_msg = str(exc)
        if "FileImmutable" in error_msg or "ObjectAlreadyExists" in error_msg:
            print(f"[WARN] 文件已存在于OSS: {object_name}，使用现有URL")
            return oss_url
        else:
            print(f"[ERROR] OSS上传失败 {file_path}: {exc}")
            return None


# ==================== AI 分析 ====================
def analyze_screenshot(image_url: str) -> Dict[str, Any]:
    """调用AI分析截图"""
    client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL, timeout=AI_TIMEOUT)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": AI_PROMPT},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
            )
            
            ai_text = response.choices[0].message.content
            full_response = response.model_dump_json(indent=2)
            
            return {
                "success": True,
                "ai_text": ai_text,
                "full_response": full_response
            }
        
        except Exception as exc:
            print(f"[WARN] AI分析失败 (尝试 {attempt + 1}/{max_retries}): {exc}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return {"success": False, "error": str(exc)}


def extract_summary(ai_text: str) -> str:
    """从AI响应中提取摘要"""
    try:
        json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("summary", "")[:100]
    except Exception:
        pass
    
    if "summary" in ai_text.lower():
        lines = ai_text.split("\n")
        for line in lines:
            if "summary" in line.lower() and ":" in line:
                summary = line.split(":", 1)[1].strip().strip('"')
                summary = re.sub(r'\s+', ' ', summary)
                return summary
    
    return ai_text[:100] if ai_text else "无摘要"


# ==================== 飞书通知 ====================
def format_ai_result(ai_text: str, image_url: str) -> str:
    """将AI分析结果格式化为友好的文本"""
    try:
        # 尝试解析 JSON
        json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            
            # 信号类型映射
            signal_types = {
                "A": "📊 行动/公司行为",
                "B": "🏛️ 政策立场",
                "C": "🚀 技术突破/产品发布",
                "D": "💬 情绪/口水战",
                "E": "🎮 纯娱乐"
            }
            
            # 方向映射
            direction_icons = {
                "Long": "📈 做多",
                "Short": "📉 做空",
                "Neutral": "➖ 中性"
            }
            
            # 置信度评级
            confidence = data.get("confidence", 0)
            if confidence >= 7:
                confidence_text = f"⭐⭐⭐ 高置信度 ({confidence}/10)"
            elif confidence >= 4:
                confidence_text = f"⭐⭐ 中等置信度 ({confidence}/10)"
            else:
                confidence_text = f"⭐ 低置信度 ({confidence}/10) - 噪音"
            
            # 构建友好的文本
            formatted = f"""📝 摘要
{data.get('summary', '无')}

🏷️ 信号类型
{signal_types.get(data.get('signal_type', 'E'), '未知')}

📊 影响方向
{direction_icons.get(data.get('direction', 'Neutral'), '中性')}

💼 受影响资产
"""
            
            # 添加美股资产
            assets = data.get('assets', {})
            us_assets = assets.get('US', [])
            if us_assets:
                formatted += f"🇺🇸 美股：{', '.join(us_assets)}\n"
            else:
                formatted += "🇺🇸 美股：无直接影响\n"
            
            # 添加A股资产
            cn_assets = assets.get('CN', [])
            if cn_assets:
                formatted += f"🇨🇳 A股：{', '.join(cn_assets)}\n"
            else:
                formatted += "🇨🇳 A股：无直接影响\n"
            
            # 添加置信度
            formatted += f"\n{confidence_text}\n"
            
            # 添加失效时间
            expiry = data.get('expiry', '未知')
            formatted += f"\n⏰ 信号时效：{expiry}\n"
            
            # 添加风险提示
            risk = data.get('risk', '无')
            if risk and risk != '无':
                formatted += f"\n⚠️ 关键风险\n{risk}\n"
            
            # 添加截图链接
            formatted += f"\n🖼️ 截图：{image_url}"
            
            return formatted
    
    except Exception as e:
        print(f"[WARN] 格式化AI结果失败: {e}")
    
    # 如果解析失败，返回原始文本
    return f"🔔 马斯克推文分析\n\n{ai_text}\n\n🖼️ 截图：{image_url}"


def send_to_feishu(title: str, image_url: str, text: str) -> bool:
    """发送消息到飞书（格式化后的富文本）"""
    if not FEISHU_WEBHOOK:
        print("[WARN] FEISHU_WEBHOOK 未配置，跳过飞书通知")
        return False
    
    # 格式化 AI 结果
    formatted_text = format_ai_result(text, image_url)
    
    payload = {
        "msg_type": "text",
        "content": {
            "text": formatted_text
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


# ==================== 处理流程 ====================
def process_new_tweets(new_tweets: List[Dict[str, Any]], ai_conn: sqlite3.Connection) -> int:
    """处理新推文：上传OSS、AI分析、发送飞书"""
    if not new_tweets:
        print(f"[INFO] 没有新推文需要处理")
        return 0
    
    # 过滤出有截图的推文
    tweets_with_screenshots = [t for t in new_tweets if t.get("screenshot_path")]
    
    if not tweets_with_screenshots:
        print(f"[INFO] 没有截图需要处理")
        return 0
    
    print(f"\n[INFO] ========== 开始处理 {len(tweets_with_screenshots)} 个新截图 ==========")
    
    # 【性能优化】批量查询已处理的推文ID，避免循环中频繁查询数据库
    processed_ids = get_processed_tweet_ids(ai_conn)
    print(f"[INFO] 数据库中已有 {len(processed_ids)} 条AI分析记录")
    
    processed_count = 0
    
    for idx, tweet in enumerate(tweets_with_screenshots):
        tweet_id = tweet["id"]
        screenshot_path = tweet["screenshot_path"]
        
        print(f"\n[INFO] === 处理 {idx + 1}/{len(tweets_with_screenshots)}: {tweet_id} ===")
        
        # 【性能优化】使用内存中的 Set 检查，O(1) 复杂度
        if tweet_id in processed_ids:
            print(f"[INFO] 推文 {tweet_id} 已处理过，跳过")
            continue
        
        # 1. 上传OSS
        print(f"[INFO] 上传到OSS...")
        oss_url = upload_to_oss(screenshot_path)
        if not oss_url:
            print(f"[ERROR] OSS上传失败，跳过")
            continue
        
        print(f"[INFO] OSS URL: {oss_url}")
        
        # 2. AI分析
        print(f"[INFO] AI分析中...")
        ai_result = analyze_screenshot(oss_url)
        
        if not ai_result["success"]:
            print(f"[ERROR] AI分析失败，跳过")
            continue
        
        ai_text = ai_result["ai_text"]
        full_response = ai_result["full_response"]
        
        print(f"[INFO] AI分析完成")
        print(f"[INFO] AI返回: {ai_text[:150]}...")
        
        # 3. 提取摘要
        summary = extract_summary(ai_text)
        print(f"[INFO] 摘要: {summary}")
        
        # 4. 保存结果
        processed_at = dt.datetime.now().isoformat(timespec="seconds")
        if save_ai_result(ai_conn, tweet_id, screenshot_path, oss_url, full_response, summary, processed_at):
            print(f"[INFO] 已保存到AI数据库")
        
        # 5. 发送飞书
        print(f"[INFO] 发送飞书通知...")
        send_to_feishu(title=summary, image_url=oss_url, text=ai_text)
        
        processed_count += 1
    
    return processed_count


# ==================== 主流程 ====================
async def main():
    """主流程：爬取 → 处理 → 通知"""
    print(f"=" * 60)
    print(f"Twitter 完整流水线启动")
    print(f"=" * 60)
    print(f"[INFO] 目标用户: @{TARGET_USER}")
    print(f"[INFO] 推文数据库: {DB_PATH}")
    print(f"[INFO] AI数据库: {AI_DB_PATH}")
    print(f"[INFO] 截图目录: {SCREENSHOT_DIR}")
    print(f"[INFO] OSS Bucket: {OSS_BUCKET}")
    print(f"[INFO] 飞书 Webhook: {FEISHU_WEBHOOK}")
    
    # 验证配置
    if not OSS_ACCESS_KEY_ID or not OSS_ACCESS_KEY_SECRET:
        print("[ERROR] OSS配置缺失")
        return
    
    if not AI_API_KEY:
        print("[ERROR] AI API KEY 未配置")
        return
    
    try:
        # ========== 步骤1：爬取新推文 ==========
        print(f"\n{'='*60}")
        print(f"步骤1：爬取新推文")
        print(f"{'='*60}")
        
        twitter_conn = ensure_twitter_db()
        known_ids = known_tweet_ids(twitter_conn, TARGET_USER)
        print(f"[INFO] 数据库中已有 {len(known_ids)} 条推文")
        
        new_tweets = await scrape_new_tweets(TARGET_USER, known_ids)
        print(f"[INFO] 本次爬取到 {len(new_tweets)} 条新推文")
        
        # 保存到数据库
        saved_count = 0
        for tweet in new_tweets:
            if save_tweet(twitter_conn, tweet):
                saved_count += 1
        
        print(f"[INFO] 已保存 {saved_count} 条推文到数据库")
        twitter_conn.close()
        
        if not new_tweets:
            print(f"\n[INFO] 没有新推文，流程结束")
            return
        
        # ========== 步骤2：AI处理新推文 ==========
        print(f"\n{'='*60}")
        print(f"步骤2：AI处理新推文")
        print(f"{'='*60}")
        
        ai_conn = ensure_ai_db()
        processed_count = process_new_tweets(new_tweets, ai_conn)
        ai_conn.close()
        
        # ========== 完成 ==========
        print(f"\n{'='*60}")
        print(f"流程完成！")
        print(f"{'='*60}")
        print(f"[INFO] 新推文: {len(new_tweets)} 条")
        print(f"[INFO] 已处理: {processed_count} 条")
        print(f"[INFO] 推文数据库: {DB_PATH}")
        print(f"[INFO] AI数据库: {AI_DB_PATH}")
    
    except KeyboardInterrupt:
        print(f"\n[INFO] 用户中断")
    except Exception as exc:
        print(f"\n[ERROR] 程序异常: {exc}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
