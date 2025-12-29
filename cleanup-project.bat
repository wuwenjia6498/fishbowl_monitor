@echo off
chcp 65001 >nul
echo ====================================
echo 项目文件清理脚本
echo ====================================

echo.
echo 即将删除以下类型的文件：
echo   - 调试和测试脚本
echo   - 日志和临时数据库
echo   - 临时任务文档
echo   - 过时的脚本和文档
echo   - 重复的批处理文件
echo.
echo 按任意键继续，或 Ctrl+C 取消...
pause >nul

echo.
echo [1/6] 删除根目录的调试和测试文件...
del /Q debug_*.py 2>nul
del /Q test_*.py 2>nul
del /Q check_*.py 2>nul
del /Q get_real_gold_price.py 2>nul
del /Q etl_test.py 2>nul
echo ✓ 完成

echo.
echo [2/6] 删除日志和数据库文件...
del /Q etl_log*.txt 2>nul
del /Q *.db 2>nul
del /Q nul 2>nul
del /Q =0.2.0 2>nul
echo ✓ 完成

echo.
echo [3/6] 删除临时任务文档...
del /Q task_v7.*.md 2>nul
del /Q audit_report*.md 2>nul
del /Q BUGFIX_*.md 2>nul
echo ✓ 完成

echo.
echo [4/6] 删除过时文档...
del /Q SETUP_GUIDE.md 2>nul
del /Q project_brief.md 2>nul
del /Q schema.sql 2>nul
del /Q push_to_github.bat 2>nul
echo ✓ 完成

echo.
echo [5/6] 删除 scripts/ 下的调试和测试文件...
cd scripts
del /Q check_*.py 2>nul
del /Q check-*.js 2>nul
del /Q test-*.py 2>nul
del /Q debug*.py 2>nul
del /Q debug-*.js 2>nul
del /Q verify*.py 2>nul
del /Q verify-*.js 2>nul
del /Q simulate-*.py 2>nul
del /Q manual-*.py 2>nul
del /Q compare-*.py 2>nul
del /Q fix_database.py 2>nul
del /Q fix_schema.sql 2>nul
del /Q fix-us-dates.js 2>nul
del /Q clean-us-data.js 2>nul
del /Q delete-us-latest.js 2>nul
del /Q run-migration.js 2>nul
del /Q quick-*.py 2>nul
del /Q quick-*.js 2>nul
del /Q recalculate_history.py 2>nul
del /Q set_broad_etf.py 2>nul
cd ..
echo ✓ 完成

echo.
echo [6/6] 删除 scripts/__pycache__...
rmdir /S /Q scripts\__pycache__ 2>nul
echo ✓ 完成

echo.
echo ====================================
echo ✅ 清理完成！
echo ====================================
echo.
echo 保留的核心文件：
echo   📁 app/ components/ lib/ sql/    (前端代码)
echo   📄 scripts/etl.py                (主 ETL 脚本)
echo   📄 scripts/init_db.py            (数据库初始化)
echo   📄 scripts/fix_sparkline_v7.py   (修复工具)
echo   📄 scripts/update_holdings.py    (持仓更新)
echo   📄 scripts/requirements.txt      (依赖列表)
echo   📄 README.md                     (项目说明)
echo   📄 CHANGELOG_v7.0.md             (更新日志)
echo   📄 v7.0_troubleshooting.md       (问题排查)
echo   📄 .gitignore                    (Git 配置)
echo   📄 git-push.bat                  (推送脚本)
echo   📄 run_etl.bat                   (ETL 快捷方式)
echo.
pause

