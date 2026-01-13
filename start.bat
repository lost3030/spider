@echo off
chcp 65001 >nul
echo ========================================
echo Spider Project - 快速启动
echo ========================================
echo.

cd /d "%~dp0"

echo 请选择要运行的模块：
echo.
echo 1. Twitter爬虫 (抓取推文)
echo 2. Twitter截图处理 (AI分析)
echo 3. 商务部爬虫
echo 4. 查看Twitter AI结果
echo 5. 运行测试
echo 6. 退出
echo.

choice /c 123456 /n /m "请输入选项 (1-6): "

if errorlevel 6 goto :end
if errorlevel 5 goto :test
if errorlevel 4 goto :view
if errorlevel 3 goto :mofcom
if errorlevel 2 goto :processor
if errorlevel 1 goto :twitter

:twitter
echo.
echo [*] 启动Twitter爬虫...
call scripts\run_twitter.bat
goto :end

:processor
echo.
echo [*] 启动Twitter截图处理器...
call scripts\run_twitter_processor.bat
goto :end

:mofcom
echo.
echo [*] 启动商务部爬虫...
call scripts\run_mofcom.bat
goto :end

:view
echo.
echo [*] 查看Twitter AI分析结果...
python src\twitter\view_results.py
pause
goto :end

:test
echo.
echo [*] 运行自动化测试...
python tests\self_test.py
pause
goto :end

:end
echo.
echo 再见！
