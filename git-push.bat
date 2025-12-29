@echo off
chcp 65001 >nul
echo ====================================
echo 推送代码到 GitHub
echo ====================================

echo.
echo [1/5] 配置安全目录...
git config --global --add safe.directory "H:/000-cursor学习/fishbowl_monitor"

echo.
echo [2/5] 添加远程仓库...
git remote add origin https://github.com/wuwenjia6498/fishbowl_monitor.git 2>nul
if errorlevel 1 (
    echo 远程仓库已存在，跳过
) else (
    echo 远程仓库添加成功
)

echo.
echo [3/5] 添加所有文件到暂存区...
git add .

echo.
echo [4/5] 提交更改...
git commit -m "feat: v7.0-v7.2 完整功能实现

- v7.0: 趋势图增量追加模式（稳定性升级）
- v7.0.1: 数据点不足自动修复
- v7.0.2: 移除黄金板块展示
- v7.1: 行业板块增加区间涨幅字段
- v7.2: 行业板块增加持续天数字段

Features:
- 增量追加模式大幅提升稳定性
- 自动检测并修复数据不足问题
- 行业板块与宽基指数功能对齐
- 完整的错误处理和异常保护
- 优化 API 调用频率和延迟

Technical:
- 修改 scripts/etl.py 实现增量追加逻辑
- 修改 components/market-header.tsx 移除黄金卡片
- 修改 components/business/fishbowl-table.tsx 添加新列
- 新增修复脚本 scripts/fix_sparkline_v7.py
- 新增文档 v7.0_troubleshooting.md, CHANGELOG_v7.0.md
"

echo.
echo [5/5] 推送到 GitHub...
git branch -M main
git push -u origin main

echo.
echo ====================================
echo ✅ 推送完成！
echo ====================================
pause

