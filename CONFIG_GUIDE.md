# 配置指南

## 🔐 敏感信息配置

本项目使用两种方式管理敏感配置：

### 方式1: secrets.json（推荐用于本地开发）

1. 复制配置模板：
```bash
cp config/secrets.json.example config/secrets.json
```

2. 编辑 `config/secrets.json`，填入真实的配置：
```json
{
  "oss": {
    "access_key_id": "your_actual_key_id",
    "access_key_secret": "your_actual_secret",
    "bucket": "your_bucket_name",
    "region": "cn-hangzhou"
  },
  "qianwen": {
    "api_key": "your_actual_api_key",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen-vl-plus"
  },
  "feishu": {
    "webhook": "your_actual_webhook_url"
  },
  "twitter": {
    "target_user": "elonmusk"
  }
}
```

### 方式2: 环境变量（推荐用于 Docker/生产环境）

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入真实的配置：
```bash
# OSS 配置
OSS_ACCESS_KEY_ID=your_actual_key_id
OSS_ACCESS_KEY_SECRET=your_actual_secret
OSS_BUCKET=your_bucket_name
OSS_REGION=cn-hangzhou

# 千问 AI 配置
QIANWEN_API_KEY=your_actual_api_key
QIANWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QIANWEN_MODEL=qwen-vl-plus

# 飞书 Webhook
TWITTER_FEISHU_WEBHOOK=your_actual_webhook_url

# Twitter 配置
TWITTER_USER=elonmusk
TWITTER_HEADLESS=true
```

## 📋 配置优先级

系统按以下优先级读取配置：

1. **环境变量** （最高优先级）
2. **secrets.json** 
3. **代码默认值** （最低优先级）

这样设计的好处：
- 本地开发：使用 `secrets.json`
- Docker 部署：使用 `.env` 文件
- CI/CD：使用环境变量注入

## 🚀 快速开始

### 本地开发

```bash
# 1. 配置 secrets.json
cp config/secrets.json.example config/secrets.json
# 编辑 config/secrets.json

# 2. 运行程序
python src/twitter/twitter_pipeline.py
```

### Docker 部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env

# 2. 启动容器
docker-compose up -d
```

## ⚠️ 安全提示

**以下文件包含敏感信息，请勿提交到 Git：**

- ✅ `config/secrets.json` - 已在 .gitignore 中
- ✅ `.env` - 已在 .gitignore 中
- ✅ `config/twitter_cookies.json` - 已在 .gitignore 中
- ✅ `data/*.db` - 已在 .gitignore 中

**可以安全提交的文件：**

- ✅ `config/secrets.json.example` - 配置模板（不含真实值）
- ✅ `.env.example` - 环境变量模板（不含真实值）
- ✅ `docker-compose.yml` - 不含硬编码密钥

## 🔍 验证配置

运行以下命令验证配置是否正确加载：

```bash
python -c "
import sys
sys.path.insert(0, 'src/twitter')
from twitter_pipeline import OSS_ACCESS_KEY_ID, AI_API_KEY, FEISHU_WEBHOOK
print(f'OSS Key: {OSS_ACCESS_KEY_ID[:10]}...' if OSS_ACCESS_KEY_ID else 'OSS Key: 未配置')
print(f'AI Key: {AI_API_KEY[:10]}...' if AI_API_KEY else 'AI Key: 未配置')
print(f'Feishu: {FEISHU_WEBHOOK[:30]}...' if FEISHU_WEBHOOK else 'Feishu: 未配置')
"
```

## 📚 相关文档

- [Twitter 爬虫指南](./TWITTER_GUIDE.md)
- [飞书通知格式](./docs/FEISHU_FORMAT.md)
- [数据库备份](./docs/BACKUP.md)
- [性能优化](./docs/DB_PERFORMANCE.md)
