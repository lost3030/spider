# 数据库备份说明

## 📦 自动备份

项目已配置每天自动备份所有数据库文件。

### 备份配置

**备份的数据库：**
- `data/twitter.db` - Twitter 推文数据
- `data/twitter_ai.db` - AI 分析结果
- `data/mofcom.db` - 商务部数据

**备份策略：**
- ⏰ 每天凌晨 2:00 自动运行
- 📁 备份到 `data/backups/` 目录
- 📅 文件名格式：`数据库名_YYYYMMDD.db`（例如：`twitter_20260112.db`）
- 🔄 只保留最新的 **3 个备份**，自动清理旧备份

---

## 🚀 使用方法

### Docker 环境（自动运行）

备份任务已配置在 crontab 中，无需手动操作：

```cron
# 每天凌晨2点自动备份
0 2 * * * root cd /app && /usr/local/bin/python /app/scripts/backup_databases.py >> /app/logs/backup.log 2>&1
```

查看备份日志：
```bash
docker-compose logs -f | grep backup
# 或
docker exec spider cat /app/logs/backup.log
```

---

### 本地环境

#### 手动备份

```powershell
# 运行备份脚本
python scripts\backup_databases.py

# 或使用批处理
.\scripts\run_backup.bat
```

#### 定时备份（Windows 任务计划程序）

1. 打开任务计划程序：`taskschd.msc`
2. 创建基本任务
3. 触发器：每天 02:00
4. 操作：运行脚本
   - 程序：`D:\project\spider\scripts\run_backup.bat`
   - 起始于：`D:\project\spider`

---

## 📂 备份文件结构

```
data/
├── twitter.db          # 当前数据库
├── twitter_ai.db
├── mofcom.db
└── backups/            # 备份目录
    ├── twitter_20260112.db     # 最新
    ├── twitter_20260111.db
    ├── twitter_20260110.db     # 最旧（第4个会被删除）
    ├── twitter_ai_20260112.db
    ├── twitter_ai_20260111.db
    ├── twitter_ai_20260110.db
    ├── mofcom_20260112.db
    ├── mofcom_20260111.db
    └── mofcom_20260110.db
```

---

## 🔧 配置选项

编辑 `scripts/backup_databases.py` 修改配置：

```python
# 备份保留数量（默认3个）
MAX_BACKUPS = 3

# 备份的数据库文件
DB_FILES = [
    "data/twitter.db",
    "data/twitter_ai.db",
    "data/mofcom.db"
]

# 备份目录
BACKUP_DIR = Path("data/backups")
```

---

## 📊 查看备份

### 列出所有备份

```powershell
# Windows
Get-ChildItem data\backups\*.db | Format-Table Name, Length, LastWriteTime -AutoSize

# Linux/Docker
ls -lh /app/data/backups/
```

### 查看备份数量

```powershell
# Windows
(Get-ChildItem data\backups\*.db).Count

# Linux
ls /app/data/backups/*.db | wc -l
```

---

## 🔄 恢复数据库

### 从备份恢复

```powershell
# 1. 停止正在运行的程序
# Docker: docker-compose down
# 本地: 关闭所有爬虫

# 2. 备份当前数据库（可选）
copy data\twitter.db data\twitter_current.db.bak

# 3. 从备份恢复
copy data\backups\twitter_20260112.db data\twitter.db

# 4. 重启程序
# Docker: docker-compose up -d
# 本地: 重新运行爬虫
```

### 查看备份内容

```powershell
# 查看备份的推文数量
python -c "import sqlite3; conn = sqlite3.connect('data/backups/twitter_20260112.db'); print(f'推文数: {conn.execute(\"SELECT COUNT(*) FROM tweets\").fetchone()[0]}'); conn.close()"

# 或使用 SQLite 工具
sqlite3 data\backups\twitter_20260112.db "SELECT COUNT(*) FROM tweets"
```

---

## ⚠️ 注意事项

### 1. 备份文件大小

根据数据量，备份文件可能会占用较多磁盘空间：

| 数据库 | 典型大小 | 说明 |
|--------|---------|------|
| twitter.db | 50-200 MB | 取决于推文数量 |
| twitter_ai.db | 20-100 MB | 取决于AI分析数量 |
| mofcom.db | 5-50 MB | 取决于文章数量 |

**磁盘空间估算：**
```
每个数据库 × 3 个备份 = 总空间
例如：150MB × 3 = 450MB（仅 twitter.db）
```

### 2. 备份文件不会被 Git 追踪

`data/backups/` 已添加到 `.gitignore`，不会提交到代码仓库。

### 3. Docker Volume 持久化

Docker 的 `data/` 目录通过 Volume 挂载，备份文件会保存在宿主机：

```yaml
# docker-compose.yml
volumes:
  - ./data:/app/data  # 包括 data/backups/
```

### 4. 并发访问

备份时会短暂锁定数据库，建议在凌晨低峰期运行（已默认配置为 2:00）。

---

## 🧪 测试备份功能

```powershell
# 1. 手动运行备份
python scripts\backup_databases.py

# 2. 查看备份结果
Get-ChildItem data\backups\*.db | Sort-Object LastWriteTime -Descending

# 3. 测试恢复（使用测试数据库）
copy data\twitter.db data\twitter_test.db
copy data\backups\twitter_20260112.db data\twitter.db
# 验证数据正确性...
copy data\twitter_test.db data\twitter.db  # 恢复原状
```

---

## 📈 监控备份状态

### 查看备份日志

```powershell
# Docker
docker exec spider tail -f /app/logs/backup.log

# 本地
Get-Content logs\backup.log -Tail 50 -Wait
```

### 检查备份完整性

```powershell
# 验证备份文件可以打开
sqlite3 data\backups\twitter_20260112.db "PRAGMA integrity_check"
# 输出: ok
```

---

## 🔐 备份到远程

如需更安全的备份，可以添加云存储同步：

```python
# scripts/backup_databases.py 扩展（待实现）
# - 上传到 OSS
# - 上传到 Google Drive
# - 上传到 AWS S3
```

---

## 📞 故障排除

### 问题：备份文件没有生成

**检查：**
1. 数据库文件是否存在？
2. 备份目录权限是否正确？
3. 磁盘空间是否充足？

**解决：**
```powershell
# 手动运行查看错误
python scripts\backup_databases.py

# 检查磁盘空间
Get-PSDrive
```

### 问题：旧备份没有被清理

**检查：**
```powershell
# 查看所有备份及修改时间
Get-ChildItem data\backups\*.db | Format-Table Name, LastWriteTime
```

**解决：**
```python
# 手动清理
from scripts.backup_databases import cleanup_old_backups
cleanup_old_backups('twitter')
cleanup_old_backups('twitter_ai')
cleanup_old_backups('mofcom')
```

### 问题：备份文件损坏

**检查完整性：**
```powershell
sqlite3 data\backups\twitter_20260112.db "PRAGMA integrity_check"
```

**如果损坏：**
- 使用更早的备份
- 从主数据库重新备份

---

## 📚 相关文档

- `LOCAL_RUN.md` - 本地运行指南
- `docs/DOCKER_DEPLOYMENT.md` - Docker 部署指南
- `SECURITY.md` - 安全配置说明

---

**定期检查备份，确保数据安全！** 🔒✨
