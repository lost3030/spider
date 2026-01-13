@echo off
REM Twitter Screenshot Processor
REM 处理Twitter截图：上传OSS、AI分析、飞书通知

echo ========================================
echo Twitter Screenshot Processor
echo ========================================
echo.

cd /d "%~dp0.."
python src\twitter\processor.py

echo.
echo ========================================
echo Processing Complete!
echo ========================================
pause
