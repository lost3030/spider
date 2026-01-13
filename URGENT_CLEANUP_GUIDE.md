# 🚨 紧急：清理 GitHub 历史中的敏感信息

## 当前状况

✅ 已完成：
- 代码中移除了硬编码的敏感信息
- 创建了配置文件系统
- 配置了 .gitignore

❌ **但是：Git 历史中仍然包含敏感信息！**

你的仓库：`https://github.com/lost3030/spider.git`
历史提交：3个（Initial commit, add ai, elon）
**所有人都可以查看这些历史提交中的敏感信息！**

---

## 🚨 立即行动（按顺序执行）

### 步骤1: 撤销所有密钥（最重要！⚠️）

**1.1 阿里云 OSS Access Key**
```
1. 访问：https://ram.console.aliyun.com/users
2. 找到并删除 Access Key: LTAI5tE6gbbeCaTKGvUFYyhk
3. 创建新的 Access Key
4. 更新到 config/secrets.json 和 .env
```

**1.2 千问 API Key**
```
1. 访问：https://bailian.console.aliyun.com/
2. 删除 API Key: sk-768d09acb469423f9888f93b31695fd0
3. 创建新的 API Key
4. 更新到 config/secrets.json 和 .env
```

**1.3 飞书 Webhook**
```
1. 访问飞书机器人管理
2. 删除旧的 Webhook
3. 创建新的 Webhook
4. 更新到 config/secrets.json 和 .env
```

---

### 步骤2: 清理本地 Git 历史

**手动操作（Windows）：**

```powershell
# 1. 关闭所有 Git 相关程序（VSCode、Git GUI等）

# 2. 删除 .git 目录（如果上面的脚本失败）
Remove-Item -Path .git -Recurse -Force

# 3. 重新初始化 Git
git init

# 4. 添加远程仓库
git remote add origin https://github.com/lost3030/spider.git

# 5. 添加所有文件（敏感文件会被 .gitignore 忽略）
git add .

# 6. 检查即将提交的文件
git status
# 确认 .env 和 config/secrets.json 不在列表中

# 7. 创建新的初始提交
git commit -m "Initial commit (clean history, no secrets)"

# 8. 强制推送到 GitHub（覆盖远程历史）
git push --force origin main
```

---

### 步骤3: 验证清理结果

```powershell
# 检查本地历史
git log --all --full-history -S "LTAI5tE6"
# 应该返回空

# 等待1-2分钟后，检查 GitHub
# 访问 https://github.com/lost3030/spider/commits/main
# 应该只看到一个 "Initial commit (clean history, no secrets)"

# 搜索是否还能找到敏感信息
# https://github.com/lost3030/spider/search?q=LTAI5tE6
# 应该找不到
```

---

### 步骤4: 通知 GitHub 删除缓存（可选但推荐）

GitHub 会缓存旧的提交约90天，即使你删除了历史。

**联系 GitHub Support：**
1. 访问：https://support.github.com/contact
2. 选择 "Security" 类别
3. 说明：
   ```
   Subject: Request to purge cached commits containing sensitive data
   
   Repository: https://github.com/lost3030/spider
   
   I accidentally committed sensitive credentials (API keys and access tokens) 
   to my repository. I have:
   1. Revoked all the exposed credentials
   2. Rewritten the Git history to remove them
   3. Force-pushed the clean history
   
   However, the old commits are still cached by GitHub. Could you please 
   purge the following commits from your cache:
   - bab4067b44eddd10d2cabdcf32574963fc2cacf4
   - abd2620723aa130b8ac396fb68a16779f905d196
   
   Thank you!
   ```

---

## ✅ 完成后的检查清单

- [ ] 已撤销所有泄露的密钥
- [ ] 已生成新的密钥
- [ ] 已更新 config/secrets.json（包含新密钥）
- [ ] 已更新 .env（包含新密钥）
- [ ] 已删除本地 .git 目录
- [ ] 已重新初始化 Git
- [ ] 已强制推送到 GitHub
- [ ] GitHub 历史只有1个干净的提交
- [ ] 搜索 GitHub 找不到旧的敏感信息
- [ ] （可选）已联系 GitHub Support 清除缓存

---

## 🔒 防止未来泄露

**安装 pre-commit hook：**

```powershell
# 创建 hook 文件
@"
#!/bin/sh
python scripts/pre_commit_check.py
if [ `$? -ne 0 ]; then
    exit 1
fi
"@ | Out-File -FilePath .git/hooks/pre-commit -Encoding ASCII

# Windows 上可能需要手动创建
# 位置：.git/hooks/pre-commit
# 内容：见上面
```

**每次提交前自动检查：**
```bash
git config --local core.hooksPath .git/hooks
```

---

## 📞 如果遇到问题

**问题1: 删除 .git 目录失败**
```powershell
# 关闭所有占用的程序
# 以管理员身份运行 PowerShell
Remove-Item -Path .git -Recurse -Force
```

**问题2: 强制推送失败**
```bash
# 确认远程仓库地址
git remote -v

# 尝试强制推送所有分支和标签
git push --force --all origin
git push --force --tags origin
```

**问题3: GitHub 仍能搜索到敏感信息**
```
等待几分钟让 GitHub 更新索引
如果超过24小时仍然可见，联系 GitHub Support
```

---

## ⏱️ 时间线

- **立即（0-30分钟）**：撤销所有密钥
- **30分钟内**：清理 Git 历史并强制推送
- **1-2小时内**：验证 GitHub 上已更新
- **24小时内**：联系 GitHub Support 清除缓存
- **7天后**：再次检查，确认无法搜索到敏感信息

---

**⚠️ 记住：先撤销密钥，再清理历史！**
