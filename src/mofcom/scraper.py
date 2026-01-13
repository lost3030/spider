#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor the MOFCOM policy page, persist new articles locally, send them to an AI
for analysis, and forward the AI conclusion to Feishu.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import html
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from playwright.async_api import async_playwright

LIST_URL = "https://www.mofcom.gov.cn/zwgk/zcfb/index.html"
DB_PATH = Path(os.getenv("MOFCOM_DB_PATH", "data/mofcom.db"))
AI_CONFIG_PATH = Path(os.getenv("MOFCOM_AI_CONFIG", "config/ai_config.json"))
DEFAULT_PROVIDER = os.getenv("MOFCOM_AI_PROVIDER")
FEISHU_WEBHOOK = os.getenv(
    "FEISHU_WEBHOOK", "https://www.feishu.cn/flow/api/trigger-webhook/bddf3cb6f0d84b025ae922df47e69804"
)

AI_PROMPT = """
# Role
你是一位拥有20年经验的全球宏观对冲基金策略师，擅长地缘政治博弈分析、中美贸易关系以及供应链安全研究。你的核心能力是透过中国商务部的官方公文，推演其对A股（CN）和美股（US）的深层影响。

Objective
分析用户提供的【中国商务部新闻】，输出结构化的投资情报。重点评估该新闻是否会触发“贸易战升级”或“对手国报复（如美国制裁/特朗普推特恐慌）”。

Analysis Framework (必须遵循的思考步骤)
Fact Extraction: 提取核心事实（管制物项、制裁实体、贸易数据、反倾销调查等）。
Direct Impact (一阶效应): 直接受影响的行业供需关系。例如：稀土限制 -> 供给减少 -> 价格上涨 -> 利好上游资源股。
Geopolitical Risk (二阶效应 - 关键): 该行动的政治含义。
这是一次常规的行政管理，还是一次蓄意的“反制/亮剑”？
Provocation Score (挑衅/摩擦评分 0-10): 评分越高，意味着美国（特别是特朗普政府）做出激烈反应（发推、加关税、制裁）的概率越大。
Market Transmission:
A股逻辑：通常利好国产替代、稀缺资源；利空出口依赖型企业。
美股逻辑：通常利空高通胀敏感、供应链依赖中国的科技/军工股；利好美国本土替代概念。
Output Constraints
逻辑必须严密，区分“短期情绪”和“长期基本面”。
"""

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )
}


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise SystemExit(f"Config not found: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def load_ai_config(config_path: Path) -> Dict[str, Any]:
    cfg = _load_json(config_path)
    if not isinstance(cfg, dict) or "providers" not in cfg:
        raise SystemExit("ai_config.json must contain a top-level 'providers' object.")
    if not cfg["providers"]:
        raise SystemExit("ai_config.providers must not be empty.")
    return cfg


def _resolve_api_key(pcfg: Dict[str, Any]) -> str:
    if pcfg.get("api_key"):
        return str(pcfg["api_key"])
    env_name = pcfg.get("api_key_env")
    if env_name and os.getenv(env_name):
        return os.getenv(env_name)  # type: ignore
    raise SystemExit(f"API key missing for provider. Set 'api_key' or env '{env_name}'.")


def _resolve_provider(cfg: Dict[str, Any], provider_name: Optional[str]) -> Dict[str, Any]:
    name = provider_name or cfg.get("default_provider")
    if not name:
        raise SystemExit("No provider specified and no default_provider in config.")

    providers: Dict[str, Any] = cfg["providers"]
    pcfg = providers.get(name)
    if not pcfg:
        available = ", ".join(sorted(providers)) or "none"
        raise SystemExit(f"Provider '{name}' not found. Available: {available}")

    api_key = _resolve_api_key(pcfg)
    model = pcfg.get("model") or pcfg.get("model_name")
    if not model:
        raise SystemExit(f"Provider '{name}' must define 'model'.")

    client_kwargs = {"api_key": api_key, "max_retries": 0}
    if pcfg.get("base_url"):
        client_kwargs["base_url"] = pcfg["base_url"]

    return {
        "name": name,
        "client": OpenAI(**client_kwargs),
        "model": model,
        "timeout": float(pcfg.get("timeout") or cfg.get("timeout") or 180),
        "temperature": pcfg.get("temperature", cfg.get("temperature", 0.3)),
    }


def ensure_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            link TEXT NOT NULL UNIQUE,
            content TEXT,
            fetched_at TEXT,
            ai_result TEXT
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(date);")
    return conn


def known_links(conn: sqlite3.Connection) -> Set[str]:
    rows = conn.execute("SELECT link FROM articles").fetchall()
    return {r[0] for r in rows}


def run_ai_query(payload: str, prompt: str, config: Dict[str, Any], provider: Optional[str] = None) -> str:
    p = _resolve_provider(config, provider)
    messages = [
        {"role": "system", "content": prompt.strip()},
        {"role": "user", "content": payload.strip()},
    ]
    response = p["client"].chat.completions.create(
        model=p["model"],
        messages=messages,
        timeout=p["timeout"],
        temperature=p["temperature"],
    )
    choice = response.choices[0].message if response.choices else None
    return (choice.content or "").strip() if choice else ""


async def fetch_listing_html() -> str:
    # The listing is rendered via an async request to /api-gateway/.../front/page/build/unit.
    # We mimic the front-end by pulling queryData + url from the column page, then calling the unit API.
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=20)
    resp.encoding = resp.apparent_encoding or "utf-8"
    html_text = resp.text

    m_qd = re.search(r'queryData="([^"]+)"', html_text)
    m_url = re.search(r'url="([^"]+)"', html_text)
    if not m_qd or not m_url:
        raise SystemExit("Failed to extract queryData/url from listing page.")

    query_data_raw = m_qd.group(1).replace("'", '"')
    query_data = json.loads(query_data_raw)
    params = dict(query_data)
    params.setdefault("pageNum", 1)
    params.setdefault("pageSize", 15)

    unit_url = urljoin(LIST_URL, m_url.group(1))
    unit_resp = requests.get(unit_url, params=params, headers=HEADERS, timeout=20)
    unit_resp.raise_for_status()
    data = unit_resp.json().get("data", {})
    return data.get("html", "")


def parse_listing(html_text: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html_text, "lxml")
    entries: List[Dict[str, str]] = []

    # Prefer the main listing block to avoid sidebar links
    li_nodes = soup.select("ul.txtList_01 li")
    if not li_nodes:
        li_nodes = soup.select("section.iListCon li")

    for li in li_nodes:
        a = li.find("a", href=True)
        if not a or not a.get("href"):
            continue
        if "/zwgk/zcfb/" not in a.get("href"):
            continue
        span = li.find("span")
        date_text = span.get_text(strip=True) if span else li.get_text(" ", strip=True)
        mdate = re.search(r"(\d{4}-\d{2}-\d{2})", date_text)
        if not mdate:
            continue
        date = mdate.group(1)
        href = a.get("href").strip()
        title_html = a.decode_contents().strip()
        title = re.sub("<[^>]+>", "", title_html).strip()
        title = html.unescape(title)
        if href.startswith("/"):
            link = "https://www.mofcom.gov.cn" + href
        elif href.startswith("http"):
            link = href
        else:
            base = LIST_URL.rsplit("/", 1)[0]
            link = base + "/" + href
        entries.append({"date": date, "title": title, "link": link})

    if entries:
        return entries

    fallback_html = html_text
    # Fallback: regex if structured parsing fails
    items = re.findall(r"<li[^>]*>([\s\S]*?)</li>", fallback_html, re.I)
    for item in items:
        mdate = re.search(r"(\d{4}-\d{2}-\d{2})", item)
        atag = re.search(r'<a[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', item, re.I)
        if not mdate or not atag:
            continue
        date = mdate.group(1).strip()
        href = atag.group(1).strip()
        title_html = atag.group(2).strip()
        title = re.sub("<[^>]+>", "", title_html).strip()
        title = html.unescape(title)
        if href.startswith("/"):
            link = "https://www.mofcom.gov.cn" + href
        elif href.startswith("http"):
            link = href
        else:
            base = LIST_URL.rsplit("/", 1)[0]
            link = base + "/" + href
        entries.append({"date": date, "title": title, "link": link})
    return entries


async def fetch_article_html(url: str) -> str:
    def _get() -> str:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text

    return await asyncio.to_thread(_get)


def extract_article_text(article_html: str, base_url: str = "") -> str:
    soup = BeautifulSoup(article_html, "lxml")
    # Remove style/script noise to avoid polluting extracted text
    for tag in soup(["style", "script"]):
        tag.decompose()

    selectors = [
        'div[ergodic="article"]',
        ".art-con-bottonmLine",
        ".art-con",
        "#zoom",
        ".article",
        ".articleCon",
        ".con",
        ".content",
        ".mleft",
        ".TRS_Editor",
    ]

    node = None
    for sel in selectors:
        node = soup.select_one(sel)
        if node and node.get_text(strip=True):
            break

    if not node:
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
        if paragraphs:
            return "\n".join(paragraphs)
        return soup.get_text("\n", strip=True)

    # Keep attachment links by inlining href next to text
    for a in node.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = urljoin(base_url, a.get("href", "")) if base_url else a.get("href", "")
        a.replace_with(f"{text} ({href})" if href else text)

    return node.get_text("\n", strip=True)


def persist_article(
    conn: sqlite3.Connection, entry: Dict[str, str], content: str, ai_result: str = ""
) -> Tuple[int, Path]:
    fetched_at = dt.datetime.now().isoformat(timespec="seconds")
    with conn:
        conn.execute(
            """
            INSERT INTO articles (title, date, link, content, fetched_at, ai_result)
            VALUES (:title, :date, :link, :content, :fetched_at, :ai_result)
            ON CONFLICT(link) DO UPDATE SET
                title=excluded.title,
                date=excluded.date,
                content=excluded.content,
                fetched_at=excluded.fetched_at,
                ai_result=excluded.ai_result;
            """,
            {
                "title": entry["title"],
                "date": entry["date"],
                "link": entry["link"],
                "content": content,
                "fetched_at": fetched_at,
                "ai_result": ai_result,
            },
        )
        rowid = conn.execute("SELECT id FROM articles WHERE link = ?", (entry["link"],)).fetchone()[0]
    return rowid, DB_PATH


def build_ai_payload(entry: Dict[str, str], content: str) -> str:
    return (
        f"【新闻标题】{entry['title']}\n"
        f"【发布日期】{entry['date']}\n"
        f"【原文链接】{entry['link']}\n"
        f"【新闻原文】\n{content}"
    )


def send_msg(text: str) -> None:
    if not FEISHU_WEBHOOK:
        print("[WARN] FEISHU_WEBHOOK not configured, skipping Feishu send. Message:", text)
        return
    msg = {"msg_type": "text", "content": {"text": text}}
    try:
        requests.post(FEISHU_WEBHOOK, json=msg, timeout=10)
    except Exception as exc:
        print("[WARN] Failed to send Feishu message:", exc)


def build_feishu_text(entry: Dict[str, str], stored_at: Path, ai_conclusion: str) -> str:
    conclusion = ai_conclusion or "AI 未返回结果"
    return (
        f"【商务部新闻】{entry['title']}\n"
        f"发布日期: {entry['date']}\n"
        f"链接: {entry['link']}\n"
        f"本地存储: {stored_at}\n"
        f"AI结论:\n{conclusion}"
    )


async def process_entry(
    entry: Dict[str, str], ai_config: Dict[str, Any], conn: sqlite3.Connection
) -> Optional[str]:
    article_html = await fetch_article_html(entry["link"])
    content = extract_article_text(article_html, base_url=entry["link"])
    if not content:
        print(f"[WARN] No content extracted for {entry['title']}")
        return None

    rowid, stored_at = persist_article(conn, entry, content)
    ai_payload = build_ai_payload(entry, content)
    ai_result = ""
    try:
        ai_result = run_ai_query(ai_payload, AI_PROMPT, ai_config, provider=DEFAULT_PROVIDER)
    except Exception as exc:
        ai_result = ""
        print(f"[WARN] AI call failed for {entry['title']}: {exc}")

    with conn:
        conn.execute("UPDATE articles SET ai_result = ? WHERE link = ?", (ai_result, entry["link"]))

    send_msg(build_feishu_text(entry, stored_at, ai_result))
    return entry["title"]


async def main() -> None:
    today = dt.date.today().isoformat()
    page_html = await fetch_listing_html()
    entries = parse_listing(page_html)

    conn = ensure_db()
    processed_links = known_links(conn)
    todays = [e for e in entries if e["date"] == today]
    new_entries = [e for e in todays if e["link"] not in processed_links]

    if not new_entries:
        print(f"{dt.datetime.now()}: 今日({today})无新政策或均已推送。")
        return

    ai_config = load_ai_config(AI_CONFIG_PATH)

    for entry in new_entries:
        await process_entry(entry, ai_config, conn)


if __name__ == "__main__":
    asyncio.run(main())
