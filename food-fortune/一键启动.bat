@echo off
cd /d "%~dp0"
chcp 65001 >nul 2>&1

echo 正在为你准备今日食运...

if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat" >nul 2>&1

netstat -ano 2>nul | findstr ":8888 " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 goto :StartServer

for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8888 " ^| findstr "LISTENING"') do (
    tasklist /FI "PID eq %%a" /FO CSV /NH 2>nul | findstr /I "python.exe" >nul 2>&1
    if not errorlevel 1 (
        taskkill /F /PID %%a >nul 2>&1
        timeout /T 2 /NOBREAK >nul
        goto :StartServer
    )
    echo 抱歉，8888 端口被其他程序占用了，请关闭占用程序后再试。
    pause >nul
    exit /b 1
)

:StartServer
start /B "" cmd /c "python src\web\web.py >nul 2>&1"

for /L %%i in (1,1,15) do (
    timeout /T 1 /NOBREAK >nul
    netstat -ano 2>nul | findstr ":8888 " | findstr "LISTENING" >nul 2>&1
    if not errorlevel 1 goto :ready
)

echo 抱歉，服务启动失败，请稍后再试。
pause >nul
exit /b 1

:ready
start "" http://127.0.0.1:8888
echo 页面已打开，关闭本窗口即可停止服务。
pause >nul
