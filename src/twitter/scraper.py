#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter/X 爬虫：抓取指定用户的推文
使用 Playwright 模拟浏览器 + 本地 Cookie 认证
新方案：进入每条推文详情页，提取文字并截图
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import os
import random
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Set

from playwright.async_api import async_playwright, Page, Browser

# ==================== 配置 ====================
TARGET_USER = os.getenv("TWITTER_USER", "elonmusk")
TARGET_URL = f"https://x.com/{TARGET_USER}"
COOKIE_FILE = Path(os.getenv("TWITTER_COOKIE_FILE", "config/twitter_cookies.json"))
DB_PATH = Path(os.getenv("TWITTER_DB_PATH", "data/twitter.db"))
SCREENSHOT_DIR = Path(os.getenv("TWITTER_SCREENSHOT_DIR", "screenshots"))

# 浏览器配置
HEADLESS = os.getenv("TWITTER_HEADLESS", "true").lower() == "true"
TIMEOUT = int(os.getenv("TWITTER_TIMEOUT", "60000"))  # 毫秒

# 滚动配置
MAX_SCROLLS = int(os.getenv("TWITTER_MAX_SCROLLS", "5"))  # 最多滚动次数（降低风控风险）
SCROLL_DELAY = int(os.getenv("TWITTER_SCROLL_DELAY", "3000"))  # 每次滚动后等待时间（毫秒）
MAX_DETAIL_PAGES = int(os.getenv("TWITTER_MAX_DETAIL_PAGES", "10"))  # 最多进入详情页数量（避免触发 Rate Limit）


# ==================== 数据库操作 ====================
def ensure_db() -> sqlite3.Connection:
    """初始化数据库和表结构"""
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
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tweets_user ON tweets(user_handle);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tweets_fetched ON tweets(fetched_at);")
    
    # 迁移：为旧表添加 screenshot_path 列（如果不存在）
    cursor = conn.execute("PRAGMA table_info(tweets);")
    columns = {row[1] for row in cursor.fetchall()}
    if "screenshot_path" not in columns:
        conn.execute("ALTER TABLE tweets ADD COLUMN screenshot_path TEXT;")
        print("[INFO] 已添加 screenshot_path 列到数据库")
    
    conn.commit()
    return conn


def known_tweet_ids(conn: sqlite3.Connection, user_handle: str) -> Set[str]:
    """获取已存储的推文 ID（只查最近300条，提升性能）"""
    rows = conn.execute(
        "SELECT id FROM tweets WHERE user_handle = ? ORDER BY fetched_at DESC LIMIT 300",
        (user_handle,)
    ).fetchall()
    return {r[0] for r in rows}


def save_tweet(conn: sqlite3.Connection, tweet: Dict[str, Any]) -> bool:
    """保存单条推文到数据库"""
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
        print(f"[WARN] Failed to save tweet {tweet.get('id')}: {exc}")
        return False


# ==================== Cookie 管理 ====================
def load_cookies() -> List[Dict[str, Any]]:
    """从 JSON 文件加载 Cookie"""
    if not COOKIE_FILE.exists():
        raise SystemExit(
            f"Cookie 文件不存在: {COOKIE_FILE}\n"
            f"请创建该文件并填入从浏览器导出的 Cookie（JSON 格式）。"
        )

    text = COOKIE_FILE.read_text(encoding="utf-8")
    try:
        cookies = json.loads(text)
        if not isinstance(cookies, list):
            raise ValueError("Cookie 文件必须是 JSON 数组格式")
        return cookies
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cookie 文件格式错误: {exc}") from exc


async def inject_cookies(page: Page, cookies: List[Dict[str, Any]]) -> None:
    """注入 Cookie 到浏览器上下文"""
    await page.context.add_cookies(cookies)  # type: ignore
    print(f"[INFO] 已注入 {len(cookies)} 个 Cookie")


# ==================== 页面操作 ====================
async def wait_for_timeline(page: Page, user: str, timeout: int = 30000) -> None:
    """等待 Timeline 区域加载完成"""
    timeline_selector = f'div[aria-label*="Timeline"][aria-label*="{user}"]'
    try:
        await page.wait_for_selector(timeline_selector, timeout=timeout, state="visible")
        print(f"[INFO] Timeline 加载成功")
    except Exception:
        print(f"[WARN] Timeline 加载超时，尝试使用备用选择器")
        await page.wait_for_selector('[data-testid="cellInnerDiv"]', timeout=10000, state="visible")


async def collect_tweet_links(page: Page, user_handle: str) -> List[Dict[str, Any]]:
    """从列表页收集推文链接和基本信息（不提取文本）"""
    tweets = []
    
    tweet_cells = await page.locator('[data-testid="cellInnerDiv"]').all()
    print(f"[INFO] 找到 {len(tweet_cells)} 个推文单元格")

    for idx, cell in enumerate(tweet_cells):
        try:
            # 提取推文 ID
            tweet_id = None
            user_name_locator = cell.locator('[data-testid="User-Name"]')
            if await user_name_locator.count() > 0:
                status_link = user_name_locator.locator('a[href*="/status/"]').first
                if await status_link.count() > 0:
                    href = await status_link.get_attribute("href")
                    if href:
                        match = re.search(r"/status/(\d+)", href)
                        if match:
                            tweet_id = match.group(1)
            
            if not tweet_id:
                continue

            # 检查是否是转发
            is_repost = 0
            social_context_locator = cell.locator('[data-testid="socialContext"]')
            if await social_context_locator.count() > 0:
                social_text = await social_context_locator.inner_text()
                if "reposted" in social_text.lower():
                    is_repost = 1
            
            # 构建链接
            link = f"https://x.com/{user_handle}/status/{tweet_id}"

            tweets.append({
                "id": tweet_id,
                "user_handle": user_handle,
                "is_repost": is_repost,
                "link": link,
            })

        except Exception as exc:
            print(f"[WARN] 收集推文 #{idx + 1} 链接时出错: {exc}")

    return tweets


async def smooth_scroll(page: Page) -> None:
    """平滑滚动，模拟真人操作"""
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
    
    # 向下滚动 2-3 屏
    scroll_distance = view_height * random.uniform(2, 3)
    target_y = min(current_y + scroll_distance, total_height - view_height)
    
    # 分步滚动
    steps = random.randint(8, 12)
    step_distance = (target_y - current_y) / steps
    
    print(f"[INFO] 平滑滚动中（{steps}步）...")
    for step in range(steps):
        next_y = current_y + step_distance * (step + 1)
        await page.evaluate(f"window.scrollTo({{ top: {next_y}, behavior: 'smooth' }})")
        pause = random.randint(150, 400)
        await page.wait_for_timeout(pause)
    
    await page.wait_for_timeout(SCROLL_DELAY)


async def fetch_tweet_detail(page: Page, tweet: Dict[str, Any], screenshot_dir: Path) -> Dict[str, Any]:
    """进入推文详情页，提取文字并截图"""
    tweet_id = tweet["id"]
    link = tweet["link"]
    
    print(f"[INFO] 进入详情页: {link}")
    
    try:
        # 导航到详情页
        await page.goto(link, timeout=TIMEOUT)
        
        # 等待推文本体加载（article 是推文的精准容器）
        await page.wait_for_selector('article[data-testid="tweet"]', timeout=15000, state="visible")
        await page.wait_for_timeout(1500)  # 额外等待渲染完成
        
        # 展开长推文（点击 "Show more" 按钮）
        try:
            show_more_btn = page.locator('article[data-testid="tweet"] button').filter(has_text="Show more").first
            if await show_more_btn.count() > 0:
                await show_more_btn.click()
                print(f"[INFO] 已点击 Show more 展开长推文")
                await page.wait_for_timeout(800)
        except Exception:
            pass  # 没有 Show more 按钮，忽略
        
        # 查看敏感内容（点击 "View" 按钮）
        try:
            view_btn = page.locator('article[data-testid="tweet"] button').filter(has_text="View").first
            if await view_btn.count() > 0:
                await view_btn.click()
                print(f"[INFO] 已点击 View 展示敏感内容")
                await page.wait_for_timeout(800)
        except Exception:
            pass  # 没有 View 按钮，忽略
        
        # 提取推文文本（只取第一个 tweetText）
        text = ""
        text_locator = page.locator('[data-testid="tweetText"]').first
        if await text_locator.count() > 0:
            text = await text_locator.inner_text()
        
        tweet["text"] = text.strip()
        
        # 截图：对推文本体 article 区域截图（避免 cellInnerDiv 的上下留白）
        article_locator = page.locator('article[data-testid="tweet"]').first
        if await article_locator.count() > 0:
            screenshot_path = screenshot_dir / f"{tweet_id}.jpg"
            await article_locator.screenshot(path=str(screenshot_path), type="jpeg", quality=90)
            tweet["screenshot_path"] = str(screenshot_path)
            print(f"[INFO] 已保存截图: {screenshot_path}")
        else:
            print(f"[WARN] 未找到推文区域，跳过截图")
            tweet["screenshot_path"] = None
        
        # 随机等待，模拟真人浏览
        await page.wait_for_timeout(random.randint(800, 1500))
        
    except Exception as exc:
        print(f"[WARN] 获取推文详情失败 {tweet_id}: {exc}")
        tweet["text"] = ""
        tweet["screenshot_path"] = None
    
    return tweet


# ==================== 主流程 ====================
async def scrape_user_tweets(user_handle: str) -> List[Dict[str, Any]]:
    """抓取指定用户的推文（新方案：进入详情页获取文字和截图）"""
    cookies = load_cookies()
    all_tweet_links: Dict[str, Dict[str, Any]] = {}  # 去重

    # 确保截图目录存在
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] 截图保存目录: {SCREENSHOT_DIR}")

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

        # 先注入 Cookie（必须在 goto 之前，避免以游客身份加载触发限制）
        await inject_cookies(page, cookies)

        # ========== 阶段1：收集推文链接 ==========
        print(f"\n[INFO] ========== 阶段1：收集推文链接 ==========")
        print(f"[INFO] 导航到用户页面: {TARGET_URL}")
        await page.goto(TARGET_URL, timeout=TIMEOUT)
        await wait_for_timeline(page, user_handle, timeout=30000)

        # 滚动收集链接
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

        # ========== 阶段2：逐个进入详情页获取文字和截图 ==========
        print(f"\n[INFO] ========== 阶段2：获取详情和截图 ==========")
        
        all_tweets = []
        tweet_list = list(all_tweet_links.values())
        
        # 限制最多进入的详情页数量（避免触发 Rate Limit）
        if len(tweet_list) > MAX_DETAIL_PAGES:
            print(f"[INFO] 收集到 {len(tweet_list)} 条，限制只处理前 {MAX_DETAIL_PAGES} 条")
            tweet_list = tweet_list[:MAX_DETAIL_PAGES]
        
        for idx, tweet in enumerate(tweet_list):
            print(f"\n[INFO] === 处理 {idx + 1}/{len(tweet_list)} ===")
            
            # 进入详情页获取文字和截图
            detailed_tweet = await fetch_tweet_detail(page, tweet, SCREENSHOT_DIR)
            all_tweets.append(detailed_tweet)
            
            # 每处理5条输出进度
            if (idx + 1) % 5 == 0:
                print(f"[INFO] 进度: {idx + 1}/{len(tweet_list)} ({(idx+1)*100//len(tweet_list)}%)")

        await browser.close()

    return all_tweets


async def main() -> None:
    """主入口"""
    print(f"[INFO] 开始抓取用户 @{TARGET_USER} 的推文")
    print(f"[INFO] Cookie 文件: {COOKIE_FILE}")
    print(f"[INFO] 数据库路径: {DB_PATH}")
    print(f"[INFO] 截图目录: {SCREENSHOT_DIR}")
    print(f"[INFO] 无头模式: {HEADLESS}")

    conn = ensure_db()
    known_ids = known_tweet_ids(conn, TARGET_USER)
    print(f"[INFO] 数据库中已有 {len(known_ids)} 条推文（最近300条）")

    tweets = await scrape_user_tweets(TARGET_USER)
    print(f"\n[INFO] 本次抓取到 {len(tweets)} 条推文")

    # 过滤出新推文
    new_tweets = [t for t in tweets if t["id"] not in known_ids]
    print(f"[INFO] 其中新推文 {len(new_tweets)} 条")

    # 保存到数据库
    saved_count = 0
    for tweet in tweets:
        if save_tweet(conn, tweet):
            saved_count += 1
    
    print(f"[INFO] 已保存 {saved_count} 条推文到数据库")

    conn.close()
    print(f"[INFO] 完成！数据库: {DB_PATH}，截图目录: {SCREENSHOT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
