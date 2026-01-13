# Twitter 爬虫使用说明

## ✅ 自测结果

已完成自测，功能正常：
- ✅ Cookie 注入成功（15个Cookie）
- ✅ Timeline 定位正常（使用备用选择器）
- ✅ 推文提取正常（基于 `cellInnerDiv` 和 `tweetText`）
- ✅ 推文 ID 提取正常（从 `User-Name` 下的 `/status/` 链接）
- ✅ 转发标记正常（`socialContext` 包含 "reposted"）
- ✅ 滚动20次去重正常（61条推文，35条转发，26条原创）
- ✅ 数据库存储正常

## 🚀 快速使用

### 1. 直接运行（使用已配置的 Cookie）
```bash
python twitter_scraper.py
```

默认配置：
- 目标用户：elonmusk
- 滚动次数：20次
- 无头模式：开启
- 滚动延迟：3秒

### 2. 自定义用户
```powershell
$env:TWITTER_USER="BillGates"
python twitter_scraper.py
```

### 3. 查看浏览器运行（调试）
```powershell
$env:TWITTER_HEADLESS="false"
python twitter_scraper.py
```

### 4. 调整滚动次数
```powershell
$env:TWITTER_MAX_SCROLLS="10"
python twitter_scraper.py
```

## 📊 查看数据

### 统计数据
```bash
python -c "import sqlite3; conn=sqlite3.connect('data/twitter.db'); total=conn.execute('SELECT COUNT(*) FROM tweets').fetchone()[0]; reposts=conn.execute('SELECT COUNT(*) FROM tweets WHERE is_repost=1').fetchone()[0]; print(f'总推文: {total}\\n转发: {reposts}\\n原创: {total-reposts}')"
```

### 查看最新推文
```bash
python -c "import sqlite3; conn=sqlite3.connect('data/twitter.db'); rows=conn.execute('SELECT id, text, is_repost FROM tweets ORDER BY rowid DESC LIMIT 10').fetchall(); [print(f'{r[0]} | {r[1][:50]}... | 转发:{r[2]}\\n') for r in rows]"
```

### 导出为 CSV
```python
import sqlite3
import csv

conn = sqlite3.connect("data/twitter.db")
cursor = conn.execute("SELECT id, text, is_repost, link, fetched_at FROM tweets")
with open("tweets.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["ID", "Text", "Is_Repost", "Link", "Fetched_At"])
    writer.writerows(cursor.fetchall())
print("✅ 已导出到 tweets.csv")
```

## 🗄️ 数据库结构

```sql
CREATE TABLE tweets (
    id TEXT PRIMARY KEY,        -- 推文ID（从URL提取）
    user_handle TEXT NOT NULL,  -- 用户名
    text TEXT NOT NULL,         -- 推文内容
    is_repost INTEGER DEFAULT 0,-- 是否转发（0=原创，1=转发）
    link TEXT,                  -- 推文链接
    fetched_at TEXT NOT NULL,   -- 抓取时间
    raw_json TEXT               -- 原始JSON
);
```

## 🔧 技术实现细节

### 1. Timeline 定位
```python
# 优先使用精确的 aria-label
div[aria-label*="Timeline"][aria-label*="Elon Musk"]

# 备用：等待任意推文单元格
[data-testid="cellInnerDiv"]
```

### 2. 推文提取
```python
# 每条推文容器
[data-testid="cellInnerDiv"]

# 推文文本（只取第一个）
[data-testid="tweetText"]

# 推文ID（从 User-Name 区域的链接提取）
[data-testid="User-Name"] a[href*="/status/"]
```

### 3. 转发检测
```python
# 查找 socialContext 并检查是否包含 "reposted"
[data-testid="socialContext"]
```

### 4. 去重机制
- 每次滚动后读取所有可见推文
- 使用字典（key=tweet_id）自动去重
- 实时显示新增数量

### 5. 滚动策略
- 滚动到页面底部：`window.scrollTo(0, document.body.scrollHeight)`
- 每次滚动后等待 3 秒让新内容加载
- 默认滚动 20 次

## 🎯 自测数据

```
总推文数: 61
原创推文: 26
转发推文: 35

滚动过程：
第1次: 4条（新增4）
第2次: 11条（新增11）
第3次: 11条（新增11）
第4次: 10条（新增10）
第5次: 9条（新增9）
第6次: 10条（新增10）
第7次: 6条（新增6）
第8次: 5条（新增0）← 开始重复
...
第20次: 5条（新增0）

最终: 61条不重复推文
```

## ⚠️ 注意事项

1. **Cookie 有效期**：Cookie 会过期，需要定期更新
2. **频率控制**：避免过于频繁抓取
3. **网络环境**：确保能访问 x.com
4. **浏览器驱动**：首次运行需安装 Chromium：
   ```bash
   playwright install chromium
   ```

## 🔄 定时运行

### Windows 任务计划
创建 `run_twitter.bat`：
```bat
@echo off
cd /d D:\project\spider
call venv\Scripts\activate
python twitter_scraper.py >> logs\twitter_%date:~0,10%.log 2>&1
```

### Linux Cron
```bash
0 */6 * * * cd /path/to/spider && python twitter_scraper.py >> logs/twitter.log 2>&1
```

## 📝 更新日志

- **2026-01-09**: 
  - 根据实际 DOM 结构重写
  - 添加转发标记检测
  - 实现滚动去重机制
  - Cookie 配置完成
  - 通过自测验证

## 🎉 验收标准

✅ **所有需求已实现**：
1. ✅ 定位 Timeline 区域（aria-label 或备用选择器）
2. ✅ 提取 cellInnerDiv 推文容器
3. ✅ 只取第一个 tweetText
4. ✅ 从 User-Name 链接提取推文ID
5. ✅ 检测 socialContext "reposted" 标记转发
6. ✅ 滚动20次，每次读取并去重
7. ✅ 使用提供的真实 Cookie

**自测结果：功能正常，可交付使用！** 🚀
