# Twitter/X 推文爬虫使用说明

本爬虫使用 Playwright 浏览器自动化 + Cookie 认证方式抓取 Twitter/X 用户的推文。

## 功能特性

- ✅ 使用本地 Cookie 绕过登录
- ✅ Playwright 模拟真实浏览器，支持 JS 渲染
- ✅ 自动滚动加载更多推文
- ✅ 提取推文文本、时间、点赞数、转发数、回复数、浏览量
- ✅ SQLite 本地存储，自动去重
- ✅ 支持环境变量配置

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 获取 Twitter Cookie

#### 方法一：使用浏览器开发者工具（推荐）

1. 在浏览器中登录 https://x.com
2. 按 `F12` 打开开发者工具
3. 切换到 **Application** (Chrome/Edge) 或 **Storage** (Firefox) 标签
4. 左侧选择 **Cookies** → **https://x.com**
5. 找到以下关键 Cookie（必需）：
   - `auth_token` - 认证令牌（最重要）
   - `ct0` - CSRF 令牌

6. 复制 `twitter_cookies.json.example` 为 `twitter_cookies.json`：
   ```bash
   copy twitter_cookies.json.example twitter_cookies.json
   ```

7. 编辑 `twitter_cookies.json`，填入真实的 Cookie 值：
   ```json
   [
     {
       "name": "auth_token",
       "value": "你的_auth_token_值",
       "domain": ".x.com",
       "path": "/",
       "secure": true,
       "httpOnly": true,
       "sameSite": "None"
     },
     {
       "name": "ct0",
       "value": "你的_ct0_值",
       "domain": ".x.com",
       "path": "/",
       "secure": true,
       "httpOnly": false,
       "sameSite": "Lax"
     }
   ]
   ```

#### 方法二：使用浏览器扩展导出完整 Cookie（更简单）

1. 安装 Cookie 导出扩展：
   - Chrome: [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)
   - Firefox: [Cookie Quick Manager](https://addons.mozilla.org/zh-CN/firefox/addon/cookie-quick-manager/)

2. 登录 https://x.com 后，点击扩展图标
3. 选择 **Export** 导出为 JSON 格式
4. 将导出的 JSON 保存为 `twitter_cookies.json`

**⚠️ 安全提示**：Cookie 相当于你的账号密码，请勿泄露或上传到公开仓库！

### 3. 运行爬虫

```bash
python twitter_scraper.py
```

爬虫将：
- 加载 Cookie 并访问 https://x.com/elonmusk
- 自动滚动页面加载更多推文（默认 5 次）
- 提取推文内容并保存到 `data/twitter.db`

## 配置选项

可以通过环境变量自定义配置：

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `TWITTER_USER` | 目标用户名（不含 @） | `elonmusk` |
| `TWITTER_COOKIE_FILE` | Cookie 文件路径 | `twitter_cookies.json` |
| `TWITTER_DB_PATH` | 数据库路径 | `data/twitter.db` |
| `TWITTER_HEADLESS` | 是否无头模式 | `true` |
| `TWITTER_TIMEOUT` | 页面超时时间（毫秒） | `30000` |
| `TWITTER_MAX_SCROLLS` | 最大滚动次数 | `5` |
| `TWITTER_SCROLL_DELAY` | 滚动间隔（毫秒） | `2000` |

### 示例：爬取其他用户

```bash
# Windows PowerShell
$env:TWITTER_USER="BillGates"; python twitter_scraper.py

# Linux/macOS
TWITTER_USER=BillGates python twitter_scraper.py
```

### 示例：非无头模式（看到浏览器窗口）

```bash
# Windows PowerShell
$env:TWITTER_HEADLESS="false"; python twitter_scraper.py

# Linux/macOS
TWITTER_HEADLESS=false python twitter_scraper.py
```

## 数据库结构

SQLite 数据库保存在 `data/twitter.db`，表结构如下：

```sql
CREATE TABLE tweets (
    id TEXT PRIMARY KEY,           -- 推文 ID
    user_name TEXT NOT NULL,       -- 用户显示名
    user_handle TEXT NOT NULL,     -- 用户名（@xxx）
    text TEXT NOT NULL,            -- 推文内容
    created_at TEXT,               -- 发布时间
    likes INTEGER DEFAULT 0,       -- 点赞数
    retweets INTEGER DEFAULT 0,    -- 转发数
    replies INTEGER DEFAULT 0,     -- 回复数
    views INTEGER DEFAULT 0,       -- 浏览量
    link TEXT,                     -- 推文链接
    fetched_at TEXT NOT NULL,      -- 抓取时间
    raw_json TEXT                  -- 原始 JSON
);
```

## 查询数据

```bash
# 查看最新 10 条推文
python -c "import sqlite3; conn=sqlite3.connect('data/twitter.db'); rows=conn.execute('SELECT created_at, text, likes FROM tweets ORDER BY created_at DESC LIMIT 10').fetchall(); [print(r) for r in rows]"

# 或使用 SQLite 工具
sqlite3 data/twitter.db "SELECT created_at, text, likes FROM tweets ORDER BY created_at DESC LIMIT 10;"
```

## 常见问题

### 1. 抓取不到推文 / 显示登录失败

**原因**：Cookie 无效或过期

**解决**：
- 确保 Cookie 是从已登录的浏览器导出的
- 尝试重新获取 Cookie
- 检查 `twitter_cookies.json` 格式是否正确
- 查看 `debug_twitter.png` 截图诊断问题

### 2. 推文数量少于预期

**原因**：Twitter 动态加载，需要更多滚动

**解决**：增加滚动次数
```bash
$env:TWITTER_MAX_SCROLLS="10"; python twitter_scraper.py
```

### 3. Playwright 浏览器未安装

**错误**：`Executable doesn't exist at ...`

**解决**：
```bash
playwright install chromium
```

### 4. Cookie 被检测 / 账号风险提示

**原因**：频繁请求或异常行为被检测

**解决**：
- 增加 `TWITTER_SCROLL_DELAY` 延迟
- 使用非无头模式（`TWITTER_HEADLESS=false`）
- 减少滚动次数
- 等待一段时间后再运行

## 定时运行

### Windows 计划任务

创建批处理文件 `run_twitter.bat`：
```bat
@echo off
cd /d D:\project\spider
python twitter_scraper.py >> logs\twitter.log 2>&1
```

使用任务计划程序设置定时运行。

### Linux Cron

```bash
# 每小时运行一次
0 * * * * cd /path/to/spider && python twitter_scraper.py >> logs/twitter.log 2>&1
```

## 注意事项

1. **遵守 Twitter 服务条款**：本爬虫仅供学习研究，请勿用于商业用途或滥用
2. **Cookie 安全**：
   - 将 `twitter_cookies.json` 加入 `.gitignore`
   - 不要分享或上传 Cookie 文件
3. **频率控制**：避免过于频繁请求导致账号风险
4. **数据隐私**：抓取的数据请妥善保管，不要泄露他人隐私

## 进阶配置

### 1. 抓取多个用户

创建用户列表并循环抓取：

```python
import os
import asyncio
from twitter_scraper import scrape_user_tweets, ensure_db, save_tweets

users = ["elonmusk", "BillGates", "BarackObama"]

async def scrape_all():
    conn = ensure_db()
    for user in users:
        os.environ["TWITTER_USER"] = user
        print(f"抓取 @{user}...")
        tweets = await scrape_user_tweets(user)
        save_tweets(conn, tweets)
        await asyncio.sleep(10)  # 延迟 10 秒
    conn.close()

asyncio.run(scrape_all())
```

### 2. 导出为 CSV

```python
import sqlite3
import csv

conn = sqlite3.connect("data/twitter.db")
cursor = conn.execute("SELECT id, text, created_at, likes, retweets FROM tweets")
with open("tweets.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["ID", "Text", "Created At", "Likes", "Retweets"])
    writer.writerows(cursor.fetchall())
print("已导出到 tweets.csv")
```

## 技术栈

- **Playwright**: 浏览器自动化，模拟真实用户行为
- **SQLite**: 轻量级本地数据库
- **BeautifulSoup**: （备用）HTML 解析
- **asyncio**: 异步 IO 提升性能

## 更新日志

- **2026-01-08**: 初始版本，支持基础推文抓取

## 许可证

仅供学习研究使用，请遵守相关法律法规和平台服务条款。
