# 安全配置说明

## ⚠️ 重要：密码和敏感信息保护

本项目已配置 `.gitignore` 来防止敏感信息被提交到 Git 仓库。

## 🔒 被忽略的文件和目录

### 数据库文件
- `*.db` - 所有 SQLite 数据库
- `*.sqlite`, `*.sqlite3` - SQLite 数据库变体
- `data/` - 整个数据目录

### 截图和图片
- `screenshots/` - 截图目录
- `*.png`, `*.jpg`, `*.jpeg`, `*.gif`, `*.bmp` - 所有图片文件

### 敏感配置文件
- `twitter_cookies.json` - Twitter Cookie
- `ai_config.json` - AI 配置
- `config/secrets.json` - 密钥配置文件
- `config/*.json` - 所有 config 目录下的 JSON 文件（除了 .example）

### 日志文件
- `*.log` - 所有日志文件
- `logs/` - 日志目录

### 其他
- `.env`, `.env.*` - 环境变量文件
- `venv/`, `.venv/` - 虚拟环境

## 📝 配置文件设置

### 1. 创建密钥配置文件

```bash
# 复制示例文件
copy config\secrets.json.example config\secrets.json

# 编辑配置文件，填入真实密钥
notepad config\secrets.json
```

### 2. 配置 Twitter Cookie

```bash
copy twitter_cookies.json.example twitter_cookies.json
notepad twitter_cookies.json
```

### 3. 配置 AI

```bash
copy ai_config.json.example ai_config.json
notepad ai_config.json
```

## ✅ 已清理的敏感文件

以下文件已从 Git 追踪中移除：
- `data/mofcom.db`
- `data/Untitled-1.sqlite3-query`

## 🔍 验证配置

运行以下命令验证敏感文件不会被提交：

```powershell
# 检查特定文件是否被忽略
git check-ignore data/twitter.db screenshots/ config/secrets.json

# 查看当前 git 状态
git status

# 确保没有 .db, .jpg, .png 或 secrets.json 文件
```

## ⚠️ 代码中的密码

**警告：** 目前以下文件中包含硬编码的密码（用于本地开发）：
- `src/twitter/processor.py` - OSS 和千问 API Key
- `src/common/ai.py` - 千问 API Key
- `tools/qianwen.py` - 千问 API Key

**建议：**
1. 生产环境使用环境变量或 `config/secrets.json`
2. 不要将这些文件中的密码修改后提交到公开仓库
3. 如需分享代码，先移除硬编码密码，改用占位符

## 🚀 Docker 部署

Docker 部署时使用环境变量：

```yaml
# docker-compose.yml
environment:
  - OSS_ACCESS_KEY_ID=${OSS_ACCESS_KEY_ID}
  - OSS_ACCESS_KEY_SECRET=${OSS_ACCESS_KEY_SECRET}
  - QIANWEN_API_KEY=${QIANWEN_API_KEY}
  - FEISHU_WEBHOOK=${FEISHU_WEBHOOK}
```

创建 `.env` 文件（不会被提交）：
```bash
OSS_ACCESS_KEY_ID=your_key_id
OSS_ACCESS_KEY_SECRET=your_secret
QIANWEN_API_KEY=your_api_key
FEISHU_WEBHOOK=your_webhook_url
```

## 📚 更多信息

参考文档：
- `LOCAL_RUN.md` - 本地运行指南
- `docs/DOCKER_DEPLOYMENT.md` - Docker 部署指南
- `TWITTER_GUIDE.md` - Twitter Cookie 获取指南
