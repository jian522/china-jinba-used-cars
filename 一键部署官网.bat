@echo off
chcp 65001 >nul
cd /d D:\二手车出口网站
echo === 金霸官网部署到 Cloudflare Pages ===
echo.
"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" scripts\deploy_pages.py
echo.
if errorlevel 1 (
  echo [FAIL] 部署失败，请把上面的输出发给豆豆
) else (
  echo [OK] 部署完成，等 1-2 分钟刷新 jinbacars.com
)
pause
