# 1. 继续用你能拉到的基础镜像（trixie）
FROM python:3.11-slim

# 2. 删掉 debian.sources，避免系统再自己拉 deb.debian.org（和你手写源混用）
RUN rm -f /etc/apt/sources.list.d/debian.sources || true

# 3. 全量改成阿里云的 Debian trixie 源（和基础镜像版本一致）
RUN echo "deb http://mirrors.aliyun.com/debian/ trixie main non-free contrib" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security trixie-security main" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian/ trixie-updates main non-free contrib" >> /etc/apt/sources.list

# 4. 安装 Playwright 运行 Chromium 所需系统库 + cron
#    注意：这里用的是 trixie 的 t64 包名，避免和旧 ABI 冲突
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        cron \
        libnspr4 \
        libnss3 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libxcb1 \
        libxkbcommon0 \
        libatspi2.0-0 \
        libx11-6 \
        libxcomposite1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libcairo2 \
        libpango-1.0-0 \
        libglib2.0-0t64 \
        libasound2t64 \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 5. 安装 Python 依赖 + Playwright Chromium
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m playwright install chromium

# 6. 拷贝项目代码
COPY . .

# 7. 配置 crontab（定时跑爬虫）
COPY crontab.txt /etc/cron.d/spider_cron
RUN chmod 0644 /etc/cron.d/spider_cron && \
    crontab /etc/cron.d/spider_cron

# 8. 创建日志目录
RUN mkdir -p /app/logs

# 9. 用前台模式启动 cron（唯一 CMD）
CMD ["cron", "-f"]
