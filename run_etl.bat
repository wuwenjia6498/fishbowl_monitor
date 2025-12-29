@echo off
chcp 65001 >nul
echo ====================================
echo 运行 ETL 更新脚本
echo ====================================
python scripts\etl.py
pause

