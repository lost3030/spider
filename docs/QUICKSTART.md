# Twitter Screenshot Processor - 快速开始指南

## 🚀 5分钟快速开始

### 第一步：配置环境变量（只需一次）

打开PowerShell，执行：

```powershell
[Environment]::SetEnvironmentVariable("OSS_ACCESS_KEY_ID", "LTAI5tE6gbbeCaTKGvUFYyhk", [EnvironmentVariableTarget]::User)
[Environment]::SetEnvironmentVariable("OSS_ACCESS_KEY_SECRET", "4is2uzGFFPR0mk3hk8CZwDT909NiV5", [EnvironmentVariableTarget]::User)
```

**注意**：设置后需要重启终端或IDE才能生效。

### 第二步：运行自测

```bash
python self_test.py
```

看到所有 ✓ PASS 就说明环境正常。

### 第三步：处理截图

```bash
python twitter_screenshot_processor.py
```

或双击运行：
```bash
run_twitter_processor.bat
```

### 第四步：查看结果

```bash
python view_twitter_results.py
```

---

## 📋 典型使用场景

### 场景1：定期处理Twitter截图

1. 运行 `twitter_scraper.py` 抓取推文并截图
2. 运行 `twitter_screenshot_processor.py` 处理截图
3. 自动收到飞书通知
4. 在数据库中查询历史结果

### 场景2：测试单个功能

**测试飞书通知：**
```bash
python test_feishu.py
```

**查看数据库结果：**
```bash
python view_twitter_results.py
```

**上传单个文件到OSS：**
```bash
python tools/oss.py screenshots/your_image.jpg
```

---

## 🔧 临时运行（不设置环境变量）

如果不想设置永久环境变量，可以每次运行时临时设置：

```powershell
$env:OSS_ACCESS_KEY_ID = "LTAI5tE6gbbeCaTKGvUFYyhk"
$env:OSS_ACCESS_KEY_SECRET = "4is2uzGFFPR0mk3hk8CZwDT909NiV5"
python twitter_screenshot_processor.py
```

---

## 📊 输出说明

### 控制台输出示例

```
[INFO] Twitter截图处理器启动
[INFO] 找到 6 个截图文件
[INFO] ========== 处理截图: 2009543812801241315 ==========
[INFO] 上传截图到OSS...
[INFO] 上传成功: 2009543812801241315.jpg
[INFO] OSS URL: https://shenyuan-x.oss-cn-hangzhou.aliyuncs.com/2009543812801241315.jpg
[INFO] 调用AI分析...
[INFO] AI分析完成
[INFO] 摘要: 马斯克旗下 Grok 应用在芬兰登顶...
[INFO] 结果已保存到数据库
[INFO] 飞书通知发送成功
[INFO] 处理完成！共处理 1 个新截图
```

### 飞书消息示例

- **标题**：马斯克旗下 Grok 应用在芬兰登顶，可能强化其 AI 业务的市场叙事。
- **图片**：显示截图
- **内容**：完整的AI分析（信号类型、利好利空、置信度）

---

## ❓ 常见问题

### Q1: 环境变量设置后不生效？
**A**: 需要重启终端或IDE。或者使用临时环境变量的方式运行。

### Q2: OSS上传失败：FileImmutable？
**A**: OSS中已存在同名文件且设置了不可变属性。解决方法：
- 删除OSS中的同名文件
- 或重命名本地文件

### Q3: AI分析失败？
**A**: 可能原因：
- 网络问题：检查网络连接
- API配额：检查通义千问账号余额
- 图片问题：确保图片可以正常访问

### Q4: 飞书通知收不到？
**A**: 检查：
- Webhook URL是否正确
- 飞书群机器人是否正常
- 运行 `python test_feishu.py` 测试

### Q5: 如何只处理新增的截图？
**A**: 脚本已支持幂等性，已处理的截图会自动跳过。

---

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `twitter_screenshot_processor.py` | 主处理脚本 |
| `view_twitter_results.py` | 查询处理结果 |
| `test_feishu.py` | 测试飞书通知 |
| `self_test.py` | 自动化测试 |
| `run_twitter_processor.bat` | Windows批处理启动 |
| `data/twitter_ai.db` | SQLite数据库（自动创建） |
| `screenshots/` | 截图存储目录 |

---

## 💡 进阶使用

### 自定义配置

通过环境变量自定义配置：

```python
# 数据库路径
os.environ["TWITTER_AI_DB_PATH"] = "custom/path/twitter_ai.db"

# 截图目录
os.environ["TWITTER_SCREENSHOT_DIR"] = "custom/screenshots"

# 飞书Webhook
os.environ["TWITTER_FEISHU_WEBHOOK"] = "https://your-webhook-url"

# AI模型
os.environ["QIANWEN_MODEL"] = "qwen-vl-max"  # 使用更强大的模型
```

### 查询数据库

使用SQLite客户端或Python：

```python
import sqlite3
conn = sqlite3.connect('data/twitter_ai.db')

# 查询所有高置信度的信号
cursor = conn.execute("""
    SELECT tweet_id, summary, oss_url 
    FROM twitter_ai_results 
    WHERE ai_result LIKE '%置信度】%[7-9][0-9]%'
    ORDER BY processed_at DESC
""")

for row in cursor:
    print(row)
```

---

## 📞 支持

如有问题，请查看：
- `README_twitter_processor.md` - 完整文档
- `PROJECT_DELIVERY.md` - 交付文档

---

**🎉 现在就开始使用吧！**

```bash
python twitter_screenshot_processor.py
```
