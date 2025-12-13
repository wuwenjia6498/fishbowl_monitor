# 任务：优化宽基看板，引入趋势区间涨幅 (v4.7 Trend Performance)

用户要求对 **[宽基大势]** Tab 进行数据化改造：
1.  **移除** 主观的 "ETF 操作建议" 列。
2.  **新增** "当日涨幅" (Change) 列。
3.  **新增** "区间涨幅" (Trend Performance) 列 -> *核心计算点*。

## 1. 后端 ETL 逻辑升级 (`scripts/etl.py`)

请修改 `FishbowlCalculator` 类，增加 `trend_pct` (趋势区间涨幅) 的计算。

**计算逻辑：**
1.  找到当前状态 (`YES` 或 `NO`) 的**起始点**。
    * 利用 `duration_days`。如果 `duration_days = 5`，说明 5 天前状态发生了反转。
    * 获取 `T - duration` 那一天的 `close` 价格，记为 `start_price`。
2.  计算涨跌幅：
    * `trend_pct = (current_close - start_price) / start_price`
3.  **特殊处理：** 如果 `duration_days` 很大导致无法追溯（比如数据源长度不够），则暂时返回 0 或空。

**输出数据结构 (API Response):**
在 `fishbowl_daily` 表或 API 返回中，增加 `change_pct` (当日) 和 `trend_pct` (区间)。

## 2. 数据库变更 (`schema.sql`)

```sql
ALTER TABLE fishbowl_daily ADD COLUMN change_pct DECIMAL(10, 4); -- 当日涨幅
ALTER TABLE fishbowl_daily ADD COLUMN trend_pct DECIMAL(10, 4);  -- 趋势累计涨幅

3. 前端列定义调整 (columns.tsx - Broad Tab)
请重构 宽基大势 的表格列：
排序	列名	数据源	样式说明
1	指数名称	name	-
2	现价	close	-
3	当日涨幅	change_pct	[NEW] 红涨绿跌，带 %
4	状态	status	Badge (YES/NO)
5	持续天数	duration_days	数字
6	区间涨幅	trend_pct	
[NEW] 核心列
显示格式：+5.23%
逻辑：
若 Status=YES 且 >0，显示红色 (盈利)
若 Status=NO 且 <0，显示绿色 (避险/跌幅)

7	偏离度	deviation_pct	辅助参考

执行指令
SQL: 添加新字段。
Python: 修改 etl.py，实现回溯计算 trend_pct 的逻辑，并计算 change_pct。Frontend: 更新宽基表格的列定义。

