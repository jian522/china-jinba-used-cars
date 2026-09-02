@echo off
REM ========================================
REM Jinba Auto Export - 搜索引擎自动提交工具包
REM ========================================

echo ========================================
echo 搜索引擎自动化提交工具包
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查Playwright是否安装
python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装 Playwright...
    pip install playwright
    python -m playwright install
)

echo.
echo ========================================
echo 选择要执行的操作:
echo ========================================
echo.
echo 1. Google Search Console 自动化
echo 2. Bing Webmaster Tools 自动化
echo 3. 两者都执行
echo 4. 仅打开浏览器（手动操作）
echo 5. 退出
echo.

set /p choice="请输入选项 (1-5): "

if "%choice%"=="1" (
    echo.
    echo [执行] Google Search Console 自动化...
    python "%~dp0google-sc-automation.py"
) else if "%choice%"=="2" (
    echo.
    echo [执行] Bing Webmaster Tools 自动化...
    python "%~dp0bing-webmaster-automation.py"
) else if "%choice%"=="3" (
    echo.
    echo [执行] Google Search Console 自动化...
    python "%~dp0google-sc-automation.py"
    echo.
    echo [执行] Bing Webmaster Tools 自动化...
    python "%~dp0bing-webmaster-automation.py"
) else if "%choice%"=="4" (
    echo.
    echo [打开] 正在打开搜索引擎工具...
    start https://search.google.com/search-console
    start https://www.bing.com/webmasters
    echo.
    echo 请在打开的浏览器中完成操作
    pause
) else (
    echo.
    echo 退出程序
)

echo.
echo ========================================
echo 完成！
echo ========================================
pause
