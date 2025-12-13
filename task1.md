# 任务：实现 ETF 核心持仓展示与自动更新 (v5.4+v5.5 Combined)

用户希望在 [行业轮动] 表格中增加 **"核心持仓"** 字段。
**核心目标：**
1.  **数据库:** 新增字段存储持仓数据。
2.  **后端:** 编写脚本从 Tushare 自动拉取最新的 ETF 前十大重仓股。
3.  **前端:** 在表格中点击图标，侧边栏弹出展示持仓详情。

## 1. 数据库变更 (`sql/schema.sql`)

请修改 `monitor_config` 表，增加一个用于存储长文本的字段。

```sql
ALTER TABLE monitor_config ADD COLUMN top_holdings TEXT; -- 存储 Markdown 格式的持仓列表

没问题。将 v5.4 (前端展示与数据库字段) 和 v5.5 (后端自动获取数据) 合并执行是最优解。

这样您就不需要先手动硬编码一堆假数据，而是直接写好脚本去 Tushare 拉取真数据，一步到位实现动态更新。

这是为您整合好的 v5.4 & v5.5 联合任务指令包。请全选复制下方代码块。

Markdown

# 任务：实现 ETF 核心持仓展示与自动更新 (v5.4+v5.5 Combined)

用户希望在 [行业轮动] 表格中增加 **"核心持仓"** 字段。
**核心目标：**
1.  **数据库:** 新增字段存储持仓数据。
2.  **后端:** 编写脚本从 Tushare 自动拉取最新的 ETF 前十大重仓股。
3.  **前端:** 在表格中点击图标，侧边栏弹出展示持仓详情。

## 1. 数据库变更 (`sql/schema.sql`)

请修改 `monitor_config` 表，增加一个用于存储长文本的字段。

```sql
ALTER TABLE monitor_config ADD COLUMN top_holdings TEXT; -- 存储 Markdown 格式的持仓列表
2. 后端：持仓更新脚本 (scripts/update_holdings.py)
请创建一个独立的 Python 脚本，用于从 Tushare 获取数据并更新数据库。

逻辑要求：

连接数据库和 Tushare Pro。

查询所有 category='industry' 且 is_active=true 的 ETF 代码。

遍历代码，调用 pro.fund_portfolio(ts_code=symbol)。

取最新 ann_date (公告日) 的数据。

按 stk_mkv_ratio (持仓占比) 降序取前 10 名。

Markdown 生成: 将数据拼接为 Markdown 表格字符串。

格式: | 股票名称 | 代码 | 占比 |

底部追加: *(数据更新于: YYYY-MM-DD)*

执行 SQL 更新 top_holdings 字段。

代码参考:
Python

# ... imports (pandas, tushare, psycopg2/sqlalchemy) ...

def update_holdings():
    # ... db connection & tushare init ...
    
    # 获取目标 ETF 列表
    etfs = get_active_industry_etfs() 
    
    for etf in etfs:
        try:
            # Tushare 接口获取持仓
            df = pro.fund_portfolio(ts_code=etf['symbol'])
            if df.empty: continue
            
            # 数据清洗：取最新一期，按占比排序，取前10
            latest_date = df['ann_date'].max()
            df = df[df['ann_date'] == latest_date].sort_values('stk_mkv_ratio', ascending=False).head(10)
            
            # 生成 Markdown
            md = "| 股票名称 | 代码 | 占比 |\n| :--- | :--- | :--- |\n"
            for _, row in df.iterrows():
                name = row['symbol'] # 注意 Tushare 返回的 symbol 是股票代码，name 可能是股票名称需确认字段
                # 实际上 Tushare fund_portfolio 返回字段: symbol(股票代码), name(股票名称), stk_mkv_ratio(占比)
                # 需检查 Tushare 字段名是否包含 name, 若不包含需额外获取或只显示代码
                # *注：通常 fund_portfolio 包含 'symbol' 和 'stk_mkv_ratio'，可能不包含股票中文名。
                # 如果没有中文名，脚本需尝试调用 pro.stock_basic 获取，或者暂只显示代码。
                # 建议：简单起见，如果 df 中有 name 则用，没有则用 symbol。
                stock_name = row.get('name', row['symbol']) 
                md += f"| {stock_name} | {row['symbol']} | {row['stk_mkv_ratio']:.2f}% |\n"
            
            md += f"\n*(更新于 {datetime.now().strftime('%Y-%m-%d')})*"
            
            # 更新数据库
            update_db(etf['symbol'], md)
            print(f"Updated {etf['name']}")
            
        except Exception as e:
            print(f"Failed to update {etf['symbol']}: {e}")

if __name__ == "__main__":
    update_holdings()
    
3. 前端展示开发 (components/fishbowl-table.tsx & columns.tsx)
3.1 引入 UI 组件
请确保引入了 Shadcn UI 的 Sheet (侧边栏) 组件。

3.2 列定义更新 (columns.tsx)
在 "行业轮动" 的列定义中增加 "核心持仓" 列。

位置: 在 "ETF 标的" 之后。

内容: 一个 List 图标 (如 List 或 Database icon)。

交互: 点击图标打开 Sheet。

3.3 Sheet 内容渲染
在 Sheet 中展示 row.original.top_holdings。

使用 react-markdown 渲染 Markdown 文本。

样式优化: 为 Markdown 的 table 添加样式类 (如 w-full border-collapse text-sm), th (text-left border-b p-2), td (border-b p-2)，使其看起来像一个标准的 Shadcn 表格。

执行指令
SQL: 修改表结构添加字段。

Backend: 创建 scripts/update_holdings.py 脚本（需处理 Tushare 数据逻辑）。

Frontend: 修改前端表格组件，实现点击图标弹出持仓列表的功能。