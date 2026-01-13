@echo off
chcp 65001 >nul
echo ========================================
echo Twitter 爬虫 - 快速运行
echo ========================================
echo.

cd /d "%~dp0.."

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo [√] 虚拟环境已激活
) else (
    echo [!] 未找到虚拟环境，使用全局 Python
)

echo.
echo [*] 开始抓取 @elonmusk 的推文...
echo [*] 滚动20次，预计耗时约 60-90 秒
echo.

python src\twitter\scraper.py

echo.
echo ========================================
echo 运行完成！
echo ========================================
echo.
echo 查看数据：
echo   python -c "import sqlite3; conn=sqlite3.connect('data/twitter.db'); total=conn.execute('SELECT COUNT(*) FROM tweets').fetchone()[0]; print(f'总推文: {total}')"
echo.
pause
