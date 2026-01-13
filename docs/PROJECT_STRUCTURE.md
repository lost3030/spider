# Spider Project Structure

```
spider/
│
├── 📁 config/                          # 配置文件
│   ├── ai_config.json                  # AI API配置
│   ├── twitter_cookies.json            # Twitter Cookie（需手动配置）
│   └── twitter_cookies.json.example    # Cookie示例
│
├── 📁 src/                             # 源代码
│   ├── __init__.py
│   │
│   ├── 📁 mofcom/                      # 商务部爬虫模块
│   │   ├── __init__.py
│   │   └── scraper.py                  # 商务部政策爬虫
│   │
│   ├── 📁 twitter/                     # Twitter爬虫模块
│   │   ├── __init__.py
│   │   ├── scraper.py                  # Twitter推文爬虫
│   │   ├── processor.py                # 截图AI处理
│   │   └── view_results.py             # 查看AI结果
│   │
│   └── 📁 common/                      # 共用工具
│       ├── __init__.py
│       ├── oss.py                      # OSS上传工具
│       └── ai.py                       # AI调用示例
│
├── 📁 scripts/                         # 运行脚本
│   ├── run_mofcom.bat                  # 运行商务部爬虫
│   ├── run_twitter.bat                 # 运行Twitter爬虫
│   └── run_twitter_processor.bat       # 运行截图处理
│
├── 📁 tests/                           # 测试文件
│   ├── test_feishu.py                  # 飞书通知测试
│   └── self_test.py                    # 自动化测试
│
├── 📁 docs/                            # 文档
│   ├── README_twitter.md               # Twitter爬虫文档
│   ├── README_twitter_processor.md     # 截图处理器文档
│   ├── TWITTER_GUIDE.md                # Twitter完整教程
│   ├── PROJECT_DELIVERY.md             # 项目交付文档
│   ├── QUICKSTART.md                   # 快速开始
│   ├── BUG_FIX_REPORT.md              # Bug修复报告
│   └── REFACTORING.md                  # 重构说明（本文档）
│
├── 📁 data/                            # 数据存储
│   ├── twitter.db                      # Twitter数据
│   ├── twitter_ai.db                   # AI分析结果
│   └── mofcom.db                       # 商务部数据
│
├── 📁 screenshots/                     # 截图文件
│
├── 🚀 start.bat                        # 快速启动入口
├── 📖 README.md                        # 项目主文档
├── 📄 requirements.txt                 # Python依赖
├── 🐳 Dockerfile                       # Docker配置
├── 🐳 docker-compose.yml               # Docker Compose配置
└── 🔒 .gitignore                       # Git忽略规则
```

## 快速导航

### 🏃 运行程序
```bash
# 快速启动菜单（推荐）
start.bat

# 或直接运行
scripts\run_twitter.bat              # Twitter爬虫
scripts\run_twitter_processor.bat    # 截图处理
scripts\run_mofcom.bat              # 商务部爬虫
```

### 📝 查看文档
- 主文档: [README.md](../README.md)
- Twitter教程: [docs/TWITTER_GUIDE.md](TWITTER_GUIDE.md)
- 快速开始: [docs/QUICKSTART.md](QUICKSTART.md)
- 重构说明: [docs/REFACTORING.md](REFACTORING.md)

### 🧪 运行测试
```bash
python tests\self_test.py          # 自动化测试
python tests\test_feishu.py        # 飞书通知测试
```

### 📊 查看数据
```bash
python src\twitter\view_results.py  # 查看AI分析结果
```

## 模块说明

### Twitter模块 (src/twitter/)
- **scraper.py**: 抓取Twitter推文和截图
- **processor.py**: 上传截图到OSS、AI分析、飞书通知
- **view_results.py**: 查询数据库中的AI分析结果

### 商务部模块 (src/mofcom/)
- **scraper.py**: 监控商务部政策发布，AI分析影响

### 共用工具 (src/common/)
- **oss.py**: 阿里云OSS文件上传工具
- **ai.py**: 通义千问AI调用示例

## 设计原则

1. **职责分离**: 配置、代码、脚本、测试、文档各自独立
2. **模块化**: 功能模块清晰划分，易于扩展
3. **标准化**: 符合Python项目最佳实践
4. **文档化**: 完整的文档支持
5. **可测试**: 独立的测试目录和脚本

## 版本历史

- **v1.0** (2026-01-12): 初始版本，扁平结构
- **v2.0** (2026-01-12): 重构为模块化结构 ✨

---

**最后更新**: 2026-01-12
