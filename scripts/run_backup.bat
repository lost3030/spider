@echo off
REM 数据库备份脚本 - Windows 版本
REM 每天运行一次，备份所有数据库

echo ========================================
echo 数据库备份任务
echo ========================================
echo.

cd /d "%~dp0.."
python scripts\backup_databases.py

echo.
echo ========================================
echo 备份完成！
echo ========================================
pause
