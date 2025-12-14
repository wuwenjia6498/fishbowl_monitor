# 任务：配置 GitHub Actions 实现每日双时段自动化更新 (v6.0 Automation)

用户希望利用 GitHub Actions 实现 `etl.py` 的每日定时运行。
**核心调度策略：**
1.  **美股更新：** 北京时间 08:00 (UTC 00:00) -> 覆盖美股收盘。
2.  **A股/港股更新：** 北京时间 19:00 (UTC 11:00) -> 覆盖盘后数据清洗时间。

## 1. 创建 Workflow 文件 (`.github/workflows/daily_update.yml`)

请在项目根目录下创建 `.github/workflows` 文件夹（如果不存在），并新建 `daily_update.yml` 文件。

**文件内容配置要求：**

```yaml
name: Daily Market Data ETL

on:
  schedule:
    # 1. 美股/黄金更新
    # 北京时间 08:00 = UTC 00:00
    # 运行范围: 周二到周六 (因为美股周一的收盘是周二早上)
    - cron: '0 0 * * 2-6'
    
    # 2. A股/港股更新
    # 北京时间 19:00 = UTC 11:00 (避开高峰，确保 Tushare 数据已到位)
    # 运行范围: 周一到周五
    - cron: '0 11 * * 1-5'
    
  # 允许手动在 GitHub 界面触发 (方便测试)
  workflow_dispatch:

jobs:
  run-etl:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout Code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        cache: 'pip' # 开启缓存加速安装

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f scripts/requirements.txt ]; then pip install -r scripts/requirements.txt; fi

    - name: Run ETL Script
      env:
        # 这些 Secrets 需要用户在 GitHub 仓库设置中配置
        DATABASE_URL: ${{ secrets.DATABASE_URL }}
        TUSHARE_TOKEN: ${{ secrets.TUSHARE_TOKEN }}
      run: |
        python scripts/etl.py

2. 完善依赖管理 (scripts/requirements.txt)
为了确保 GitHub Actions 能成功安装所有库，请检查并更新 scripts/requirements.txt。 请扫描 scripts/ 目录下的所有 .py 文件，确保以下核心库都已列入：

Plaintext

pandas
tushare
psycopg2-binary  # 或 sqlalchemy，取决于 etl.py 用了什么
requests
python-dotenv
# 以及其他 etl.py 中 import 到的第三方库
3. 增强脚本鲁棒性 (scripts/etl.py)
虽然 GitHub Actions 会定时触发，但遇到非交易日（如春节、国庆）时，Tushare 可能会返回空数据。 请简单检查 etl.py 的 main 函数，确保增加了异常捕获 (Try-Except)：

如果某一部分数据（如美股）获取失败，不要中断整个脚本，应记录错误日志并继续执行下一部分（如A股）。

确保脚本在无数据更新时也能以此状态 exit(0) 正常退出，避免 GitHub Actions 报红（False Alarm）。

执行指令
Config: 创建 .github/workflows/daily_update.yml。

Dependency: 更新 scripts/requirements.txt。

Refactor: 微调 scripts/etl.py 的异常处理逻辑。