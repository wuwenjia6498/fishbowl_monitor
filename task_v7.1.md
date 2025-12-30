# 任务：趋势图浮层增加“当日涨幅”字段 (v7.1 Trend Tooltip)

用户希望在点击趋势图弹出的详情浮层 (Tooltip) 中，增加 **当日涨幅** 数据。
目前仅显示：日期、收盘价、MA20、偏离度。
新增目标：**当日涨幅 (例如: +1.52%)**，并根据正负显示红/绿颜色。

## 1. 后端 ETL 数据增强 (`scripts/etl.py`)

请修改生成趋势图数据 (`sparkline_json`) 的逻辑 (例如 `generate_sparkline` 函数)。

**修改要求:**
* 在构建 JSON 对象时，除了 `date`, `price`, `ma20`，请增加 **`change`** 字段。
* **数据源:** 对应 Tushare/Dataframe 中的 `pct_chg`。
* **格式:** 保留 2 位小数。

**代码示例:**
```python
# Old
# data.append({'date': d, 'price': p, 'ma20': m})

# New
data.append({
    'date': row['trade_date'], 
    'price': round(row['close'], 2), 
    'ma20': round(row['ma20'], 2),
    'change': round(row['pct_chg'], 2) # [Added] 涨跌幅
})

2. 前端组件渲染 (components/trend-lens.tsx)
请修改图表中的 CustomTooltip 组件。

修改点:

从 payload 中解构出新增的 change 字段。

在“偏离度”上方或下方，增加一行“当日涨幅”。

样式:

Value > 0: text-red-500，前缀 +。

Value < 0: text-green-500。

Value = 0: text-gray-500。

代码参考:

TypeScript

// Inside CustomTooltip
const change = payload[0].payload.change;
const changeColor = change > 0 ? 'text-red-500' : change < 0 ? 'text-green-500' : 'text-muted-foreground';
const changeText = change > 0 ? `+${change.toFixed(2)}%` : `${change.toFixed(2)}%`;

return (
  <div className="bg-popover border p-2 rounded shadow-lg ...">
    {/* ... 日期 ... */}
    <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
      <span className="text-muted-foreground">收盘价:</span>
      <span className="font-mono font-medium">{price}</span>
      
      <span className="text-muted-foreground">当日涨幅:</span>
      <span className={`font-mono font-medium ${changeColor}`}>{changeText}</span>
      
      {/* ... MA20 ... */}
      {/* ... 偏离度 ... */}
    </div>
  </div>
);
执行指令
Backend: 修改 etl.py，确保 sparkline_json 包含 change 字段。

Frontend: 更新 trend-lens.tsx 的 Tooltip 渲染逻辑。

Action: 提醒我重新运行 ETL，否则旧数据的 JSON 里没有这个字段，前端会显示 undefined 或空。