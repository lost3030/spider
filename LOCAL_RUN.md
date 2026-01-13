# 本地运行指南

## 📋 前置要求

1. **Python 环境**
   - Python 3.11 或更高版本
   - 已安装虚拟环境 venv（当前在 `D:\project\spider\venv`）

2. **依赖安装**
   ```powershell
   # 激活虚拟环境
   .\venv\Scripts\Activate.ps1
   
   # 安装依赖
   pip install -r requirements.txt
   
   # 安装 Playwright 浏览器（仅 Twitter 爬虫需要）
   playwright install chromium
   ```

3. **配置文件**
   - `twitter_cookies.json` - Twitter 登录 Cookie（参考 `twitter_cookies.json.example`）
   - `ai_config.json` - AI 配置（商务部爬虫需要）

---

## 🚀 快速运行

### 方式一：使用 BAT 脚本（推荐）

#### 1. Twitter 爬虫 + 截图处理器（一键运行）

**错误的路径（已过时）：**
```powershell
# ❌ 不要使用这些旧的脚本
.\run_twitter.bat  # 旧的，路径错误
.\run_twitter_processor.bat  # 旧的，路径错误
```

**正确的运行方式：**
```powershell
# ✅ 使用 scripts 目录下的脚本
.\scripts\run_twitter.bat           # 运行 Twitter 爬虫
.\scripts\run_twitter_processor.bat # 运行截图处理器
```

**或者直接运行 Python：**
```powershell
# 1. Twitter 爬虫（抓取推文 + 截图）
python src\twitter\scraper.py

# 2. 截图处理器（上传OSS + AI分析 + 飞书通知）
python src\twitter\processor.py
```

#### 2. 商务部爬虫

```powershell
# 使用脚本
.\scripts\run_mofcom.bat

# 或直接运行
python src\mofcom\scraper.py
```

---

## 📂 项目结构说明

```
D:\project\spider\
├── src\
│   ├── twitter\
│   │   ├── scraper.py         # Twitter爬虫（主程序）
│   │   ├── processor.py       # 截图处理器
│   │   └── view_results.py    # 查看结果
│   ├── mofcom\
│   │   └── scraper.py         # 商务部爬虫（主程序）
│   └── common\
│       └── oss.py             # OSS 工具类
├── scripts\
│   ├── run_twitter.bat        # Twitter爬虫启动脚本
│   ├── run_twitter_processor.bat  # 截图处理器启动脚本
│   └── run_mofcom.bat         # 商务部爬虫启动脚本
├── data\
│   ├── twitter.db             # Twitter数据库
│   ├── twitter_ai.db          # AI分析结果数据库
│   └── mofcom.db              # 商务部数据库
└── screenshots\               # Twitter截图存储目录
```

---

## 🔧 详细配置

### 1. Twitter 爬虫配置

**环境变量（可选）：**
```powershell
# 设置目标用户（默认：elonmusk）
$env:TWITTER_USER = "elonmusk"

# 设置Cookie文件路径（默认：twitter_cookies.json）
$env:TWITTER_COOKIE_FILE = "twitter_cookies.json"

# 设置数据库路径（默认：data/twitter.db）
$env:TWITTER_DB_PATH = "data/twitter.db"

# 设置截图目录（默认：screenshots）
$env:TWITTER_SCREENSHOT_DIR = "screenshots"
```

**Cookie 配置：**
1. 复制示例文件：`copy twitter_cookies.json.example twitter_cookies.json`
2. 编辑 `twitter_cookies.json`，填入你的 Twitter Cookie
3. 参考 `TWITTER_GUIDE.md` 获取 Cookie 的方法

### 2. 截图处理器配置

**OSS 凭证已硬编码**，无需配置环境变量！

代码中默认值：
- `OSS_ACCESS_KEY_ID`: LTAI5tE6gbbeCaTKGvUFYyhk
- `OSS_ACCESS_KEY_SECRET`: 4is2uzGFFPR0mk3hk8CZwDT909NiV5
- `QIANWEN_API_KEY`: sk-768d09acb469423f9888f93b31695fd0
- `FEISHU_WEBHOOK`: https://www.feishu.cn/flow/api/trigger-webhook/6228b59ee92453808a92d08ff000cb4c

**如需覆盖（可选）：**
```powershell
$env:OSS_ACCESS_KEY_ID = "your_key_id"
$env:OSS_ACCESS_KEY_SECRET = "your_key_secret"
$env:QIANWEN_API_KEY = "your_api_key"
$env:FEISHU_WEBHOOK = "your_webhook_url"
```

### 3. 商务部爬虫配置

**环境变量（可选）：**
```powershell
# AI 配置文件（默认：ai_config.json）
$env:MOFCOM_AI_CONFIG = "ai_config.json"

# AI Provider（可选）
$env:MOFCOM_AI_PROVIDER = "your_provider"

# 飞书 Webhook
$env:FEISHU_WEBHOOK = "https://www.feishu.cn/flow/api/trigger-webhook/bddf3cb6f0d84b025ae922df47e69804"

# 数据库路径（默认：data/mofcom.db）
$env:MOFCOM_DB_PATH = "data/mofcom.db"
```

---

## 🎯 运行流程

### Twitter 完整流程

```powershell
# 步骤1：激活虚拟环境
.\venv\Scripts\Activate.ps1

# 步骤2：运行Twitter爬虫（抓取推文 + 截图）
python src\twitter\scraper.py
# 输出：
# - 数据存储到 data/twitter.db
# - 截图保存到 screenshots/*.png

# 步骤3：运行截图处理器（AI分析）
python src\twitter\processor.py
# 执行：
# - 上传截图到 OSS
# - AI 分析推文内容
# - 保存到 data/twitter_ai.db
# - 发送飞书通知

# 步骤4：查看结果
python src\twitter\view_results.py
```

### 商务部完整流程

```powershell
# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 运行商务部爬虫
python src\mofcom\scraper.py
# 执行：
# - 抓取商务部政策新闻
# - AI 分析影响
# - 保存到 data/mofcom.db
# - 发送飞书通知
```

---

## 📊 查看数据

### Twitter 数据

```powershell
# 方式1：使用查看脚本
python src\twitter\view_results.py

# 方式2：直接查询数据库
python -c "import sqlite3; conn=sqlite3.connect('data/twitter.db'); print(f'总推文数: {conn.execute(\"SELECT COUNT(*) FROM tweets\").fetchone()[0]}'); conn.close()"

# 方式3：查看AI分析结果
python -c "import sqlite3; conn=sqlite3.connect('data/twitter_ai.db'); print(f'已分析: {conn.execute(\"SELECT COUNT(*) FROM tweet_analysis\").fetchone()[0]}'); conn.close()"
```

### 商务部数据

```powershell
python -c "import sqlite3; conn=sqlite3.connect('data/mofcom.db'); print(f'总文章数: {conn.execute(\"SELECT COUNT(*) FROM articles\").fetchone()[0]}'); conn.close()"
```

---

## 🧪 测试

### 运行自动化测试

```powershell
# 完整自测
python tests\self_test.py

# 测试飞书通知
python tests\test_feishu.py
```

---

## ⚠️ 常见问题

### 1. 虚拟环境未激活

**现象：** 提示找不到模块
```
ModuleNotFoundError: No module named 'playwright'
```

**解决：**
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Twitter Cookie 失效

**现象：** 爬虫无法登录
```
[ERROR] 未找到推文列表
```

**解决：** 重新获取 Cookie，参考 `TWITTER_GUIDE.md`

### 3. Playwright 浏览器未安装

**现象：** 
```
playwright._impl._api_types.Error: Executable doesn't exist
```

**解决：**
```powershell
playwright install chromium
```

### 4. OSS 上传失败

**现象：** 
```
[ERROR] OSS上传失败
```

**解决：** 检查网络连接，或检查 OSS 凭证是否正确（已硬编码在代码中）

### 5. AI API 调用失败

**现象：** 
```
[ERROR] AI分析失败
```

**解决：** 
- 检查 API Key 是否正确（默认：sk-768d09acb469423f9888f93b31695fd0）
- 检查网络连接
- 等待重试（已自动重试3次）

---

## 📝 日志位置

运行日志会输出到终端，包括：
- `[INFO]` 信息日志
- `[WARNING]` 警告日志
- `[ERROR]` 错误日志

如需保存日志：
```powershell
# Twitter爬虫
python src\twitter\scraper.py > logs\twitter_$(Get-Date -Format 'yyyyMMdd_HHmmss').log 2>&1

# 截图处理器
python src\twitter\processor.py > logs\processor_$(Get-Date -Format 'yyyyMMdd_HHmmss').log 2>&1

# 商务部爬虫
python src\mofcom\scraper.py > logs\mofcom_$(Get-Date -Format 'yyyyMMdd_HHmmss').log 2>&1
```

---

## 🔄 定时运行（可选）

### 使用 Windows 任务计划程序

1. 打开任务计划程序：`taskschd.msc`
2. 创建基本任务
3. 设置触发器（例如：每小时运行一次）
4. 操作：运行 BAT 脚本
   - Twitter: `D:\project\spider\scripts\run_twitter.bat`
   - 处理器: `D:\project\spider\scripts\run_twitter_processor.bat`
   - 商务部: `D:\project\spider\scripts\run_mofcom.bat`

### 推荐定时策略

- **Twitter 爬虫**: 每 30 分钟运行一次
- **截图处理器**: 每 1 小时运行一次（在爬虫运行后）
- **商务部爬虫**: 每 10 分钟运行一次

---

## 🐳 Docker 部署

如需 Docker 部署，参考 `docs/DOCKER_DEPLOYMENT.md`

```powershell
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

---

## 📚 更多文档

- `TWITTER_GUIDE.md` - Twitter Cookie 获取指南
- `README_twitter.md` - Twitter 爬虫详细说明
- `docs/DOCKER_DEPLOYMENT.md` - Docker 部署指南
- `docs/` - 其他技术文档

---

## 💡 技术栈

- **爬虫**: Playwright (Twitter), BeautifulSoup (商务部)
- **数据库**: SQLite
- **AI**: 阿里云千问 VL-Plus (qwen-vl-plus)
- **存储**: 阿里云 OSS
- **通知**: 飞书 Webhook
- **部署**: Docker + Cron
