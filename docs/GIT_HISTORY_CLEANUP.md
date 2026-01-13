# 清理 Git 历史中的敏感信息

## ⚠️ 问题

即使现在的代码中没有硬编码的敏感信息，Git 历史记录中仍然保存着之前的提交，任何人都可以通过以下命令查看：

```bash
# 查看历史文件内容
git show <commit-hash>:src/twitter/twitter_pipeline.py

# 搜索历史中的敏感信息
git log -p | grep "LTAI5tE6"
```

## 🔐 解决方案

### 方案1: 重新初始化 Git（最简单，推荐）

**适用场景：** 项目刚开始，没有重要的提交历史

```bash
# 运行重新初始化脚本
python scripts/reinit_git.py
```

或手动操作：

```bash
# 1. 备份 .git
cp -r .git .git.backup

# 2. 删除 .git 目录
Remove-Item -Recurse -Force .git

# 3. 重新初始化
git init
git add .
git commit -m "Initial commit (clean history)"

# 4. 强制推送到远程（如果需要）
git remote add origin <your-repo-url>
git push --force origin main
```

**优点：**
- ✅ 操作简单
- ✅ 100% 清除敏感信息
- ✅ 不需要额外工具

**缺点：**
- ❌ 丢失所有提交历史
- ❌ 如果团队协作，会影响其他人

---

### 方案2: 使用 git-filter-repo（保留历史结构）

**适用场景：** 需要保留提交历史，但替换敏感信息

```bash
# 1. 安装工具
pip install git-filter-repo

# 2. 运行清理脚本
python scripts/clean_git_history.py

# 3. 强制推送到远程
git push --force --all
git push --force --tags
```

**优点：**
- ✅ 保留提交历史结构
- ✅ 只替换敏感信息
- ✅ 官方推荐工具

**缺点：**
- ❌ 需要安装额外工具
- ❌ 操作复杂
- ❌ 需要强制推送

---

### 方案3: 使用 BFG Repo-Cleaner（最快）

**适用场景：** 大型仓库，需要快速清理

```bash
# 1. 下载 BFG
# https://rtyley.github.io/bfg-repo-cleaner/

# 2. 创建敏感信息列表
echo "LTAI5tE6gbbeCaTKGvUFYyhk" > passwords.txt
echo "4is2uzGFFPR0mk3hk8CZwDT909NiV5" >> passwords.txt
echo "sk-768d09acb469423f9888f93b31695fd0" >> passwords.txt

# 3. 运行 BFG
java -jar bfg.jar --replace-text passwords.txt

# 4. 清理和推送
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force --all
```

**优点：**
- ✅ 速度最快
- ✅ 专业工具
- ✅ 支持大型仓库

**缺点：**
- ❌ 需要 Java 环境
- ❌ 需要下载额外工具

---

### 方案4: 如果已经推送到公共仓库（GitHub）

**如果敏感信息已经泄露到公共仓库：**

1. **立即撤销密钥！** 🚨
   ```bash
   # 登录阿里云/飞书等平台
   # 1. 撤销泄露的 Access Key
   # 2. 生成新的密钥
   # 3. 更新本地配置
   ```

2. **清理 Git 历史**（选择上述方案之一）

3. **通知 GitHub 删除缓存**
   - GitHub 会缓存旧的提交
   - 清理后需要联系 GitHub Support
   - 或等待缓存自动过期（90天）

4. **检查是否被爬取**
   ```bash
   # 在 GitHub 搜索你的密钥
   # 使用 Google 搜索：
   site:github.com "LTAI5tE6gbbeCaTKGvUFYyhk"
   ```

---

## 🎯 推荐流程（根据你的情况）

### 情况1: 还没推送到远程 ✅

```bash
# 直接重新初始化（最简单）
python scripts/reinit_git.py

# 检查
git log
git status

# 推送（如果有远程）
git push --force origin main
```

### 情况2: 已推送到私有仓库

```bash
# 方案1：重新初始化（推荐）
python scripts/reinit_git.py
git push --force origin main

# 或方案2：使用 git-filter-repo
pip install git-filter-repo
python scripts/clean_git_history.py
git push --force --all
```

### 情况3: 已推送到公共仓库 🚨

```bash
# 1. 立即撤销所有密钥！
#    - 阿里云 OSS Access Key
#    - 千问 API Key
#    - 飞书 Webhook

# 2. 清理历史
python scripts/reinit_git.py

# 3. 强制推送
git push --force origin main

# 4. 联系 GitHub Support 清理缓存
#    https://support.github.com/

# 5. 生成新密钥，更新配置
```

---

## ✅ 验证清理结果

```bash
# 1. 检查当前文件
git status
python scripts/pre_commit_check.py

# 2. 检查历史记录
git log --all --full-history --source -S "LTAI5tE6gbbeCaTKGvUFYyhk"
# 应该返回空

# 3. 搜索所有历史
git log --all --full-history -p | grep -i "sk-768d09"
# 应该返回空
```

---

## 📋 提交前检查清单

- [ ] 运行清理脚本（选择方案1或2）
- [ ] 验证历史中无敏感信息
- [ ] 更新所有泄露的密钥
- [ ] 检查 `.env` 和 `secrets.json` 在 .gitignore 中
- [ ] 运行 `python scripts/pre_commit_check.py`
- [ ] 如果推送到公共仓库，联系平台删除缓存

---

## 🔒 防止未来泄露

1. **使用 pre-commit hook**
   ```bash
   # 创建 .git/hooks/pre-commit
   #!/bin/sh
   python scripts/pre_commit_check.py
   if [ $? -ne 0 ]; then
       exit 1
   fi
   ```

2. **启用 Git secrets**
   ```bash
   pip install detect-secrets
   detect-secrets scan > .secrets.baseline
   ```

3. **定期审计**
   ```bash
   # 每月运行一次
   python scripts/pre_commit_check.py
   git log --all --full-history -p | grep -E "sk-|LTAI"
   ```

---

**立即行动！🚨**
