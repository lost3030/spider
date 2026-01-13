# Spider Project

一个多功能的网页爬虫和数据处理项目，包含Twitter爬虫、商务部政策监控等模块。

## 📁 项目结构

```
spider/
├── config/                      # 配置文件
│   ├── ai_config.json          # AI API配置
│   ├── twitter_cookies.json    # Twitter登录Cookie
│   └── twitter_cookies.json.example
│
├── src/                         # 源代码
│   ├── mofcom/                 # 商务部爬虫模块
│   │   ├── __init__.py
│   │   └── scraper.py          # 商务部政策爬虫
│   │
│   ├── twitter/                # Twitter爬虫模块
│   │   ├── __init__.py
│   │   ├── scraper.py          # Twitter推文爬虫
│   │   ├── processor.py        # 截图处理和AI分析
│   │   └── view_results.py     # 查询处理结果
│   │
│   └── common/                 # 共用工具
│       ├── __init__.py
│       ├── oss.py              # 阿里云OSS上传
│       └── ai.py               # AI调用工具
│
├── scripts/                     # 运行脚本
│   ├── run_mofcom.bat          # 运行商务部爬虫
│   ├── run_twitter.bat         # 运行Twitter爬虫
│   └── run_twitter_processor.bat # 运行截图处理器
│
├── tests/                       # 测试文件
│   ├── test_feishu.py          # 飞书通知测试
│   └── self_test.py            # 自动化测试
│
├── docs/                        # 文档
│   ├── README_twitter.md
│   ├── README_twitter_processor.md
│   ├── TWITTER_GUIDE.md
│   ├── PROJECT_DELIVERY.md
│   ├── QUICKSTART.md
│   └── BUG_FIX_REPORT.md
│
├── data/                        # 数据存储
│   ├── twitter.db              # Twitter数据库
│   ├── twitter_ai.db           # AI分析结果
│   └── mofcom.db               # 商务部数据库
│
├── screenshots/                 # 截图存储
│
├── requirements.txt             # Python依赖
├── Dockerfile                   # Docker配置
├── docker-compose.yml
└── README.md                    # 本文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

#### Twitter截图处理（需要OSS）

```powershell
[Environment]::SetEnvironmentVariable("OSS_ACCESS_KEY_ID", "YOUR_KEY", [EnvironmentVariableTarget]::User)
[Environment]::SetEnvironmentVariable("OSS_ACCESS_KEY_SECRET", "YOUR_SECRET", [EnvironmentVariableTarget]::User)
```

### 3. 运行

#### 快速启动（推荐）
```bash
start.bat
```
提供交互式菜单，选择要运行的功能。

#### Twitter爬虫
```bash
# Windows
scripts\run_twitter.bat

# 或直接使用Python
python src/twitter/scraper.py
```

#### Twitter截图处理
```bash
# Windows
scripts\run_twitter_processor.bat

# 或直接使用Python
python src/twitter/processor.py
```

#### 商务部爬虫
```bash
# Windows
scripts\run_mofcom.bat

# 或直接使用Python
python src/mofcom/scraper.py
```

#### 查看结果
```bash
python src/twitter/view_results.py
```

#### 运行测试
```bash
python tests/self_test.py
```

## 📖 模块说明

### Twitter模块

- **scraper.py**: 抓取指定用户的推文，保存文字和截图
- **processor.py**: 处理截图 - 上传OSS、AI分析、飞书通知
- **view_results.py**: 查询AI分析结果

详细文档：
- [Twitter爬虫使用指南](docs/README_twitter.md)
- [截图处理器文档](docs/README_twitter_processor.md)
- [完整教程](docs/TWITTER_GUIDE.md)

### 商务部模块

监控商务部政策发布，自动抓取新政策并通过AI分析影响。

### 共用工具

- **oss.py**: 阿里云OSS文件上传
- **ai.py**: 通义千问AI调用示例

## 🧪 测试

```bash
# 运行自动化测试
python tests/self_test.py

# 测试飞书通知
python tests/test_feishu.py
```

## 📊 数据查看

### Twitter数据

```python
import sqlite3
conn = sqlite3.connect('data/twitter.db')

# 查看推文总数
total = conn.execute('SELECT COUNT(*) FROM tweets').fetchone()[0]
print(f'总推文: {total}')

# 查看最新推文
recent = conn.execute('SELECT * FROM tweets ORDER BY fetched_at DESC LIMIT 5').fetchall()
```

### AI分析结果

```bash
python src/twitter/view_results.py
```

## 🔧 配置文件

### config/ai_config.json

AI API配置，支持多provider：

```json
{
  "default_provider": "qwen",
  "providers": {
    "qwen": {
      "api_key": "sk-xxx",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "model": "qwen-plus"
    }
  }
}
```

### config/twitter_cookies.json

Twitter登录Cookie，用于绕过登录限制。

参考 `config/twitter_cookies.json.example` 创建。

## 🐳 Docker部署

```bash
# 构建镜像
docker-compose build

# 运行商务部爬虫
docker-compose up mofcom
```

## 📝 开发指南

### 添加新模块

1. 在 `src/` 下创建新目录
2. 添加 `__init__.py`
3. 在 `scripts/` 中创建运行脚本
4. 在 `docs/` 中添加文档

### 目录规范

- `src/`: 所有Python源代码
- `config/`: 配置文件（不提交敏感信息）
- `scripts/`: 运行脚本
- `tests/`: 测试代码
- `docs/`: 文档
- `data/`: 数据库和本地数据
- `screenshots/`: 临时文件

## 🔐 安全注意事项

1. **不要提交敏感信息**
   - Cookie文件
   - API密钥
   - 数据库文件

2. **使用环境变量**
   - OSS密钥
   - API密钥
   - Webhook地址

3. **配置.gitignore**
   ```
   config/*.json
   data/
   screenshots/
   *.db
   ```

## 📚 更多文档

- [Twitter快速开始](docs/QUICKSTART.md)
- [项目交付文档](docs/PROJECT_DELIVERY.md)
- [Bug修复报告](docs/BUG_FIX_REPORT.md)

## ⚖️ License

本项目仅供学习和研究使用。

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

**最后更新**: 2026-01-12
