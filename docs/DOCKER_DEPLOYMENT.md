# Docker 部署指南

## 快速开始

### 1. 构建镜像

```bash
docker-compose build
```

### 2. 启动容器

```bash
docker-compose up -d
```

### 3. 查看日志

```bash
# 查看所有日志
docker-compose logs -f

# 查看特定日志
docker exec spider tail -f /app/logs/mofcom.log
docker exec spider tail -f /app/logs/twitter_scraper.log
docker exec spider tail -f /app/logs/twitter_processor.log
```

### 4. 停止容器

```bash
docker-compose down
```

## 配置说明

### 环境变量 (docker-compose.yml)

```yaml
environment:
  # OSS配置 - 已配置默认值
  - OSS_ACCESS_KEY_ID=LTAI5tE6gbbeCaTKGvUFYyhk
  - OSS_ACCESS_KEY_SECRET=4is2uzGFFPR0mk3hk8CZwDT909NiV5
  
  # AI配置 - 已配置默认值
  - QIANWEN_API_KEY=sk-768d09acb469423f9888f93b31695fd0
  
  # 飞书Webhook - 已配置默认值
  - TWITTER_FEISHU_WEBHOOK=https://www.feishu.cn/flow/api/trigger-webhook/6228b59ee92453808a92d08ff000cb4c
```

**注意**: 代码中已内置默认配置，docker-compose.yml中的环境变量可以覆盖默认值。

### 定时任务 (crontab.txt)

```bash
# 商务部爬虫 - 每10分钟
*/10 * * * * root cd /app && /usr/local/bin/python /app/src/mofcom/scraper.py >> /app/logs/mofcom.log 2>&1

# Twitter爬虫 - 每30分钟
*/30 * * * * root cd /app && /usr/local/bin/python /app/src/twitter/scraper.py >> /app/logs/twitter_scraper.log 2>&1

# Twitter截图处理 - 每小时
0 * * * * root cd /app && /usr/local/bin/python /app/src/twitter/processor.py >> /app/logs/twitter_processor.log 2>&1
```

可以根据需要调整执行频率。

### 数据持久化

容器挂载了以下目录到宿主机：

```yaml
volumes:
  - ./data:/app/data              # 数据库文件
  - ./screenshots:/app/screenshots # 截图文件
  - ./logs:/app/logs              # 日志文件
  - ./config:/app/config          # 配置文件
```

## 常用操作

### 进入容器

```bash
docker exec -it spider /bin/bash
```

### 手动运行脚本

```bash
# 商务部爬虫
docker exec spider python /app/src/mofcom/scraper.py

# Twitter爬虫
docker exec spider python /app/src/twitter/scraper.py

# Twitter处理
docker exec spider python /app/src/twitter/processor.py

# 查看结果
docker exec spider python /app/src/twitter/view_results.py
```

### 查看cron状态

```bash
# 查看cron是否运行
docker exec spider ps aux | grep cron

# 查看crontab配置
docker exec spider crontab -l
```

### 重启容器

```bash
docker-compose restart
```

### 更新代码

```bash
# 停止容器
docker-compose down

# 重新构建镜像
docker-compose build

# 启动容器
docker-compose up -d
```

## 故障排查

### 1. 查看容器状态

```bash
docker-compose ps
```

### 2. 查看完整日志

```bash
docker-compose logs
```

### 3. 检查cron日志

```bash
docker exec spider tail -100 /app/logs/mofcom.log
docker exec spider tail -100 /app/logs/twitter_scraper.log
docker exec spider tail -100 /app/logs/twitter_processor.log
```

### 4. 检查数据库

```bash
docker exec spider python -c "import sqlite3; conn=sqlite3.connect('/app/data/twitter.db'); print(f'推文数: {conn.execute(\"SELECT COUNT(*) FROM tweets\").fetchone()[0]}')"
```

### 5. 测试网络连接

```bash
docker exec spider ping -c 3 x.com
docker exec spider curl -I https://x.com
```

## 生产环境建议

### 1. 修改敏感信息

在生产环境部署前，请修改以下配置：

- `docker-compose.yml` 中的 OSS 密钥
- `docker-compose.yml` 中的 AI API Key
- `docker-compose.yml` 中的飞书 Webhook
- `config/twitter_cookies.json` 中的 Cookie

### 2. 日志轮转

添加日志轮转配置，避免日志文件过大：

```bash
# 在容器中安装logrotate
docker exec spider apt-get update && apt-get install -y logrotate

# 配置logrotate
docker exec spider bash -c 'cat > /etc/logrotate.d/spider << EOF
/app/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
EOF'
```

### 3. 监控告警

- 配置容器健康检查
- 监控日志文件大小
- 监控爬虫运行状态
- 设置飞书告警

### 4. 资源限制

在 docker-compose.yml 中添加资源限制：

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

## 配置调整

### 修改执行频率

编辑 `crontab.txt`，然后重新构建镜像：

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### 修改API密钥

方式1：修改 docker-compose.yml 中的环境变量，然后重启：

```bash
docker-compose down
docker-compose up -d
```

方式2：直接修改代码中的默认值（不推荐）

## 备份与恢复

### 备份数据

```bash
# 备份数据库
docker cp spider:/app/data ./backup/data_$(date +%Y%m%d)

# 备份配置
docker cp spider:/app/config ./backup/config_$(date +%Y%m%d)
```

### 恢复数据

```bash
# 恢复数据库
docker cp ./backup/data_20260112 spider:/app/data

# 恢复配置
docker cp ./backup/config_20260112 spider:/app/config
```

## 性能优化

### 1. 调整定时任务频率

根据实际需求调整 crontab.txt 中的执行频率，避免过于频繁。

### 2. 限制并发

如果多个任务同时运行导致资源不足，可以错开执行时间：

```bash
# 错开执行
*/10 * * * * root cd /app && /usr/local/bin/python /app/src/mofcom/scraper.py
5,35 * * * * root cd /app && /usr/local/bin/python /app/src/twitter/scraper.py
15 * * * * root cd /app && /usr/local/bin/python /app/src/twitter/processor.py
```

### 3. 数据库优化

定期清理旧数据，保持数据库性能。

---

**最后更新**: 2026-01-12
