@echo off
chcp 65001 >nul
echo ========================================
echo   连点器
echo ========================================
echo.

where py >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=py -3.11
) else (
    set PYTHON=python
)

cd /d "%~dp0"

echo 检查依赖...
%PYTHON% -m pip show pynput >nul 2>&1
if %errorlevel% neq 0 (
    echo 安装 pynput...
    %PYTHON% -m pip install pynput
)

echo 启动...
echo.
%PYTHON% -B main.py %*

pause
