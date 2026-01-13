# Twitter Screenshot Processor

处理Twitter截图的自动化工具，支持：
- 上传截图到阿里云OSS
- 使用通义千问视觉模型进行AI分析
- 将结果存储到SQLite数据库
- 发送分析结果到飞书

## 功能特性

1. **OSS上传**：自动将截图上传到阿里云OSS，生成公网访问URL
2. **AI分析**：使用阿里云通义千问视觉模型(qwen-vl-plus)分析截图内容
3. **结构化输出**：
   - 一句话摘要
   - 信号类型（A/B/C/D）
   - 利好/利空映射
   - 置信度评分
4. **数据持久化**：将分析结果保存到SQLite数据库
5. **飞书通知**：自动发送分析结果到飞书群
6. **幂等性**：已处理的截图不会重复处理

## 环境准备

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

#### OSS访问密钥（必需）

使用PowerShell设置用户级环境变量（推荐）：

```powershell
[Environment]::SetEnvironmentVariable("OSS_ACCESS_KEY_ID", "YOUR_ACCESS_KEY_ID", [EnvironmentVariableTarget]::User)
[Environment]::SetEnvironmentVariable("OSS_ACCESS_KEY_SECRET", "YOUR_ACCESS_KEY_SECRET", [EnvironmentVariableTarget]::User)
```

或在代码中设置（不推荐，有安全风险）：

```python
import os
os.environ["OSS_ACCESS_KEY_ID"] = "YOUR_ACCESS_KEY_ID"
os.environ["OSS_ACCESS_KEY_SECRET"] = "YOUR_ACCESS_KEY_SECRET"
```

#### 其他可选配置

```python
# Twitter数据库路径
os.environ["TWITTER_AI_DB_PATH"] = "data/twitter_ai.db"

# 截图目录
os.environ["TWITTER_SCREENSHOT_DIR"] = "screenshots"

# OSS配置
os.environ["OSS_BUCKET"] = "shenyuan-x"
os.environ["OSS_REGION"] = "cn-hangzhou"

# 飞书Webhook
os.environ["TWITTER_FEISHU_WEBHOOK"] = "https://www.feishu.cn/flow/api/trigger-webhook/YOUR_WEBHOOK_ID"

# AI配置
os.environ["QIANWEN_API_KEY"] = "sk-xxx"
os.environ["QIANWEN_BASE_URL"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
os.environ["QIANWEN_MODEL"] = "qwen-vl-plus"
```

## 使用方法

### 方式一：直接运行Python脚本

```bash
python twitter_screenshot_processor.py
```

### 方式二：使用批处理文件（Windows）

```bash
run_twitter_processor.bat
```

### 方式三：命令行设置环境变量后运行

```powershell
$env:OSS_ACCESS_KEY_ID = "YOUR_KEY"
$env:OSS_ACCESS_KEY_SECRET = "YOUR_SECRET"
python twitter_screenshot_processor.py
```

## 工作流程

1. **扫描截图目录**：查找所有`.jpg`和`.png`文件
2. **检查处理状态**：跳过已处理的截图（幂等性）
3. **上传到OSS**：将截图上传到阿里云OSS
4. **AI分析**：调用通义千问视觉模型分析截图
5. **提取摘要**：从AI返回中提取一句话摘要
6. **保存结果**：将完整结果保存到数据库
7. **飞书通知**：发送分析结果到飞书

## 数据库结构

```sql
CREATE TABLE twitter_ai_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tweet_id TEXT NOT NULL UNIQUE,          -- 推文ID（从文件名提取）
    screenshot_path TEXT,                    -- 本地截图路径
    oss_url TEXT,                            -- OSS公网URL
    ai_result TEXT,                          -- AI完整响应（JSON）
    summary TEXT,                            -- 一句话摘要
    processed_at TEXT NOT NULL               -- 处理时间
);
```

## AI输出格式

AI分析输出严格遵循以下格式：

```
【一句话摘要】
马斯克宣布特斯拉Q4交付量超预期，可能提振市场对新能源汽车板块的信心。

【信号类型】
A. 行动/公司行为

【利好】
- 概念：新能源汽车、电动车
- 标的：特斯拉（TSLA）、宁德时代

【利空】
无明确利好/利空

【置信度】
85 / 100
```

## 飞书通知格式

发送到飞书的消息包含：
- `title`：一句话摘要
- `image_url`：OSS图片URL
- `text`：完整的AI分析结果

## 常见问题

### 1. OSS上传失败：FileImmutable

这表示OSS中已存在同名文件且设置了不可变属性。解决方法：
- 删除OSS中的同名文件后重新上传
- 或修改截图文件名

### 2. AI分析超时

通义千问视觉模型可能因网络或服务负载导致超时。可以：
- 检查网络连接
- 增加超时时间
- 稍后重试

### 3. 飞书通知失败

检查：
- Webhook URL是否正确
- 飞书机器人是否有权限
- 网络是否可达

## 与Twitter爬虫集成

本工具设计用于处理`twitter_scraper.py`生成的截图。典型工作流：

1. 运行`twitter_scraper.py`抓取推文并截图
2. 运行`twitter_screenshot_processor.py`分析截图
3. 查看飞书通知和数据库结果

## 文件说明

- `twitter_screenshot_processor.py`：主处理脚本
- `run_twitter_processor.bat`：Windows批处理启动脚本
- `data/twitter_ai.db`：SQLite数据库（自动创建）
- `screenshots/`：截图存储目录（由twitter_scraper.py生成）

## 注意事项

1. **环境变量安全**：不要将OSS密钥硬编码到代码中
2. **成本控制**：AI调用和OSS存储都会产生费用
3. **幂等性**：脚本支持多次运行，已处理的截图会自动跳过
4. **错误处理**：单个截图处理失败不会影响其他截图

## License

本项目仅供学习和研究使用。
