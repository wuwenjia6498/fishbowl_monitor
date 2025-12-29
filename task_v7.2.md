# 任务：行业板块增加“持续天数”字段 (v7.2 Duration Field)

用户希望 **[行业轮动]** 表格也能展示 **"持续天数"** (Duration)，即当前状态 (YES/NO) 连续维持了多少个交易日。
请复用宽基指数的计算逻辑，将其应用到行业板块中。

## 1. 后端 ETL 逻辑同步 (`scripts/etl.py`)

请检查行业数据的计算流程，确保计算并返回了 `duration` (或 `days_count`) 字段。

**核心算法 (参考宽基逻辑):**
1.  **输入:** 今日状态 (`current_status`)，昨日状态 (`prev_status`)，昨日持续天数 (`prev_duration`)。
2.  **逻辑:**
    * **IF** `current_status == prev_status`:
        `duration = prev_duration + 1`
    * **ELSE** (状态发生反转):
        `duration = 1` (新趋势的第一天)
3.  **初始化:** 如果是新上市或无历史记录，`duration = 1`。
4.  **存储:** 确保将计算结果写入数据库。

## 2. 前端列定义添加 (`components/columns.tsx`)

请在 **行业表格 (Industry Columns)** 的定义中增加一列。

**位置建议:**
放在 **"状态" (Status)** 之后，**"区间涨幅"** 之前。

**代码逻辑要求:**
1.  **字段名:** `duration` (需与后端对齐)。
2.  **表头:** "持续天数" (必须支持排序，方便用户筛选“老妖股”或“新启动”板块)。
3.  **样式:**
    * 居中显示。
    * 纯数字即可，或者为了强调，可以加粗 (`font-medium`)。
    * *可选:* 如果天数 > 20 (趋势非常稳固)，可以加一个淡背景色或高亮标记，否则保持默认。

**代码片段参考:**
```tsx
{
  accessorKey: "duration",
  header: ({ column }) => (
    <DataTableColumnHeader column={column} title="持续天数" />
  ),
  cell: ({ row }) => {
    const value = parseInt(row.getValue("duration") || "1");
    return <div className="text-center font-medium">{value}</div>;
  },
},

执行指令
Backend: 确认 etl.py 中行业数据已包含 duration 的递归计算逻辑。

Frontend: 修改 components/columns.tsx，在行业表中添加“持续天数”列。