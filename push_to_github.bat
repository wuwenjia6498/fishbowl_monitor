@echo off
chcp 65001 >nul
echo ====================================
echo 推送代码到 GitHub
echo ====================================
echo.

echo 当前有两个选项：
echo [1] 创建新仓库 fishbowl_monitor（推荐）
echo [2] 覆盖 Dividend_Dashboard 仓库（会删除原有代码）
echo.

set /p choice="请选择 [1/2]: "

if "%choice%"=="1" (
    echo.
    echo ⚠️  请先在 GitHub 上创建新仓库：fishbowl_monitor
    echo    网址：https://github.com/new
    echo.
    pause
    
    echo.
    echo 开始推送...
    git init
    git add .
    git commit -m "v7.2: 鱼盆趋势雷达 - 完整功能版本"
    git branch -M main
    git remote add origin https://github.com/wuwenjia6498/fishbowl_monitor.git
    git push -u origin main
    
) else if "%choice%"=="2" (
    echo.
    echo ⚠️  警告：这将覆盖 Dividend_Dashboard 仓库的所有内容！
    echo.
    set /p confirm="确认继续？(yes/no): "
    
    if /i "%confirm%"=="yes" (
        echo.
        echo 开始推送...
        git init
        git add .
        git commit -m "v7.2: 鱼盆趋势雷达 - 完整功能版本"
        git branch -M main
        git remote add origin https://github.com/wuwenjia6498/Dividend_Dashboard.git
        git push -f origin main
    ) else (
        echo 已取消操作
    )
) else (
    echo 无效的选择
)

echo.
echo ====================================
echo 操作完成
echo ====================================
pause

