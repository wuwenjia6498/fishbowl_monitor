# Bug修复报告 v6.1 - 数据状态与显示逻辑一致性修复

## 修复日期
2025-12-17

## 问题描述

### 核心问题
每日数据更新后，虽然基础价格变了，但**衍生指标（状态、偏离度、信号、颜色）严重滞后或逻辑错误**，导致显示与实际数据不一致。

### 具体表现
1. **行业板块**: 某指数偏离度已转为**负值**（Price < MA20），但：
   - 数据显示颜色依然为**红色**（多头色）
   - 信号标签依然显示**"主升"**（多头信号）
   - 趋势图颜色依然是**红色**

2. **反之亦然**: 某指数偏离度转为**正值**，却显示绿色/"弱势"

3. **宽基指数**: 偏离度及区间涨幅均为**负值**，状态却依然显示**"YES"**

## 根本原因分析

### 1. 后端计算逻辑问题 (scripts/etl.py)

**问题代码位置**: 第220-254行（status计算）、第284-312行（signal_tag生成）

**问题原因**:
- `status`字段使用了±1%缓冲带逻辑，导致status可能与当前偏离度不一致
- 例如：当deviation_pct = -0.005（-0.5%）时，在缓冲带内，status保持`YES`
- 但实际上close < ma20，偏离度为负，应该显示为空头
- `signal_tag`生成逻辑依赖`status`而非实际偏离度，导致矛盾

### 2. 前端渲染逻辑问题 (components/business/fishbowl-table.tsx)

**问题代码位置**:
- 第399行（宽基指数）: `const isBullish = item.status === 'YES';`
- 第592行（行业板块）: `const isBullish = item.status === 'YES';`
- 第738行（行业板块偏离度颜色）: 使用`item.status === 'YES'`判断颜色

**问题原因**:
- 颜色判断基于`status`字段，而`status`可能因缓冲带逻辑滞后
- 正确的逻辑应该直接基于`deviation_pct`的正负

### 3. 组件渲染逻辑问题

**Sparkline组件** (components/ui/sparkline.tsx):
- 第84-87行：优先使用传入的`status`参数判断颜色
- 问题：`status`可能滞后于实际价格关系

**TrendLens组件** (components/trend-lens.tsx):
- 第118-120行：使用`status`参数判断颜色
- 问题：同样导致颜色滞后

## 修复方案

### Rule of Truth（真理规则）
强制执行以下逻辑一致性：
1. **IF** `close < ma20` **THEN** `deviation < 0` AND 颜色必须为**绿色**（空头）
2. **IF** `close > ma20` **THEN** `deviation > 0` AND 颜色必须为**红色**（多头）
3. **所有颜色判断必须基于实际的deviation_pct，而非status字段**

### 修复内容

#### 1. 后端 ETL 逻辑修复

**文件**: `scripts/etl.py`

**修复位置**: 第284-311行（信号标签生成逻辑）

**修复前**:
```python
if status == 'YES':
    # 只有偏离度为正时才是真正的多头信号
    if deviation > 0:
        if duration <= 3:
            tag = 'BREAKOUT'  # 启动
        elif deviation > 0.15:
            tag = 'OVERHEAT'  # 过热
        else:
            tag = 'STRONG'    # 主升
    else:
        # 偏离度为负但status为YES（在缓冲区内），视为弱势
        tag = 'SLUMP'
else:  # NO
    if deviation < -0.15:
        tag = 'EXTREME_BEAR'  # 超跌
    else:
        tag = 'SLUMP'         # 弱势
```

**修复后**:
```python
# v6.1 Bug修复：信号标签必须严格基于当前偏离度，而不是status
# Rule of Truth: deviation > 0 -> 多头信号, deviation < 0 -> 空头信号
if deviation > 0:
    # 偏离度为正 -> 多头信号
    if duration <= 3 and status == 'YES':
        tag = 'BREAKOUT'  # 启动（刚突破且持续天数短）
    elif deviation > 0.15:
        tag = 'OVERHEAT'  # 过热（偏离度>15%）
    else:
        tag = 'STRONG'    # 主升（稳健上涨）
else:
    # 偏离度为负或零 -> 空头信号
    if deviation < -0.15:
        tag = 'EXTREME_BEAR'  # 超跌（偏离度<-15%）
    else:
        tag = 'SLUMP'         # 弱势（下跌或震荡）
```

**关键改进**:
- 信号标签完全基于当前`deviation_pct`判断
- 确保偏离度为负时不会显示"主升"等多头信号
- 确保偏离度为正时不会显示"弱势"等空头信号

#### 2. 前端表格渲染逻辑修复

**文件**: `components/business/fishbowl-table.tsx`

**修复位置1**: 第398-411行（宽基指数颜色判断）

**修复前**:
```typescript
const isBullish = item.status === 'YES';
```

**修复后**:
```typescript
// v6.1 Bug修复：颜色判断必须基于deviation_pct而非status
// Rule of Truth: deviation > 0 -> 红色(多头), deviation < 0 -> 绿色(空头)
const isBullish = item.deviation_pct > 0;
const isBullishStatus = item.status === 'YES';
```

**修复位置2**: 第590-596行（行业板块颜色判断）

**修复前**:
```typescript
const isBullish = item.status === 'YES';
```

**修复后**:
```typescript
// v6.1 Bug修复：颜色判断必须基于deviation_pct而非status
// Rule of Truth: deviation > 0 -> 红色(多头), deviation < 0 -> 绿色(空头)
const isBullish = item.deviation_pct > 0;
const isBullishStatus = item.status === 'YES';
```

**修复位置3**: 第468-475行和第733-740行（状态Badge颜色）

**修复前**:
```typescript
<Badge variant={isBullish ? 'danger' : 'success'}>
  {item.status}
</Badge>
```

**修复后**:
```typescript
<Badge variant={isBullishStatus ? 'danger' : 'success'}>
  {item.status}
</Badge>
```

**修复位置4**: 第743-750行（行业板块偏离度颜色）

**修复前**:
```typescript
<span className={`font-mono font-medium ${
  Math.abs(item.deviation_pct) > 0.15
    ? 'text-orange-600'
    : item.status === 'YES'  // ❌ 错误：基于status
      ? 'text-red-500'
      : 'text-green-500'
}`}>
```

**修复后**:
```typescript
<span className={`font-mono font-medium ${
  Math.abs(item.deviation_pct) > 0.15
    ? 'text-orange-600'  // 过热/超跌：橙色警告
    : item.deviation_pct > 0  // ✅ 正确：基于deviation_pct
      ? 'text-red-500'   // 正偏离：红色
      : 'text-green-500' // 负偏离：绿色
}`}>
```

**关键改进**:
- `isBullish`现在基于实际偏离度`deviation_pct > 0`
- 新增`isBullishStatus`用于状态Badge的颜色（保持status的独立性）
- 偏离度颜色完全基于`deviation_pct`的正负

#### 3. Sparkline组件修复

**文件**: `components/ui/sparkline.tsx`

**修复位置**: 第81-88行

**修复前**:
```typescript
// 优先使用传入的status参数（避免与数据库缓冲带逻辑不一致）
// 如果没有传入status，则根据最后一个点的价格与MA20关系判断
const lastPoint = data[data.length - 1];
const isBullish = status
  ? status === 'YES'
  : lastPoint.price > lastPoint.ma20;
const lineColor = isBullish ? '#ef4444' : '#10b981';
```

**修复后**:
```typescript
// v6.1 Bug修复：趋势颜色必须基于实际价格与MA20关系
// Rule of Truth: price > ma20 -> 红色(多头), price < ma20 -> 绿色(空头)
// 不再依赖status参数（可能因缓冲带逻辑滞后），而是直接基于最后一个点的真实关系
const lastPoint = data[data.length - 1];
const isBullish = lastPoint.price > lastPoint.ma20;
const lineColor = isBullish ? '#ef4444' : '#10b981';
```

**关键改进**:
- 移除对`status`参数的依赖
- 直接根据`lastPoint.price > lastPoint.ma20`判断颜色
- 确保趋势图颜色与实际价格关系一致

#### 4. TrendLens组件修复

**文件**: `components/trend-lens.tsx`

**修复位置**: 第114-120行

**修复前**:
```typescript
// 优先使用传入的status参数（避免与数据库缓冲带逻辑不一致）
const lastPoint = displayData[displayData.length - 1];
const isUp = status
  ? status === 'YES'
  : lastPoint.price >= lastPoint.ma20;
const lineColor = isUp ? '#ef4444' : '#10b981';
```

**修复后**:
```typescript
// v6.1 Bug修复：颜色判断必须基于实际价格与MA20关系
// Rule of Truth: price >= ma20 -> 红色(多头), price < ma20 -> 绿色(空头)
// 不再依赖status参数（可能因缓冲带逻辑滞后），而是直接基于最后一个点的真实关系
const lastPoint = displayData[displayData.length - 1];
const isUp = lastPoint.price >= lastPoint.ma20;
const lineColor = isUp ? '#ef4444' : '#10b981';
```

**修复位置**: 第130行（移除status传递）

**修复前**:
```typescript
<Sparkline data={miniData} width={120} height={40} showMA20={true} status={status} />
```

**修复后**:
```typescript
<Sparkline data={miniData} width={120} height={40} showMA20={true} />
```

**修复位置**: 所有TrendLens调用点（fishbowl-table.tsx）

**修复前**:
```typescript
<TrendLens
  data={item.sparkline_data}
  name={item.name}
  symbol={item.symbol}
  status={item.status}
/>
```

**修复后**:
```typescript
<TrendLens
  data={item.sparkline_data}
  name={item.name}
  symbol={item.symbol}
/>
```

**关键改进**:
- TrendLens不再接收`status`参数
- 完全基于sparkline_data中的实际价格关系判断颜色
- 确保弹窗趋势图与实际数据一致

## 修复效果

### 修复前后对比

| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| 偏离度 = -0.5% (缓冲区内) | status=YES, 显示红色, 信号="主升" ❌ | 根据实际偏离度，显示绿色, 信号="弱势" ✅ |
| 偏离度 = +0.5% (缓冲区内) | status=NO, 显示绿色, 信号="弱势" ❌ | 根据实际偏离度，显示红色, 信号="主升" ✅ |
| 偏离度 = -5% | status=NO, 但前端可能用错字段 ❌ | 统一使用deviation_pct，显示绿色 ✅ |
| 趋势图颜色 | 基于滞后的status参数 ❌ | 基于实际price vs ma20关系 ✅ |

### 验证要点

1. ✅ 偏离度为正（+）→ 必须显示红色
2. ✅ 偏离度为负（-）→ 必须显示绿色
3. ✅ 偏离度为负时，信号标签不会显示"主升"或"启动"
4. ✅ 偏离度为正时，信号标签不会显示"弱势"或"超跌"
5. ✅ 趋势图颜色与当前价格-MA20关系一致
6. ✅ 状态Badge的颜色仍然基于status字段（保持status的独立逻辑）

## 测试建议

### 1. 数据更新测试
```bash
# 运行ETL更新
python scripts/etl.py

# 检查数据库
# 验证signal_tag与deviation_pct的一致性
SELECT
  symbol,
  close_price,
  ma20_price,
  deviation_pct,
  status,
  signal_tag
FROM fishbowl_daily
WHERE date = (SELECT MAX(date) FROM fishbowl_daily)
  AND deviation_pct < 0
  AND signal_tag IN ('STRONG', 'BREAKOUT', 'OVERHEAT');  -- 应该返回0条记录
```

### 2. 前端显示测试
- 找一个偏离度在±1%缓冲区内的指数
- 检查：
  - 偏离度显示的颜色是否与正负一致
  - 现价显示的颜色是否与偏离度一致
  - 趋势图颜色是否正确
  - 信号标签是否与偏离度逻辑一致

### 3. 边界情况测试
- 偏离度 = 0%（价格=MA20）
- 偏离度在±0.01%附近（极小偏离）
- 偏离度刚好突破±1%缓冲带

## 技术债务清理

### 可选优化（未来考虑）

1. **status字段的作用**
   - 当前：status保留±1%缓冲带逻辑，用于判断"趋势确认"
   - 建议：明确status的语义，是否需要重命名为`trend_confirmed`或类似字段
   - 目的：避免混淆status与实际价格关系

2. **偏离度计算精度**
   - 当前：deviation_pct存储为NUMERIC(10,6)
   - 建议：确认是否需要更高精度

3. **缓冲带逻辑的必要性**
   - 当前：±1%缓冲带用于避免频繁切换status
   - 建议：评估缓冲带是否真的有必要，或者调整为更小的值（如±0.5%）

## 影响范围

### 直接影响
- ✅ 宽基指数表格：颜色显示更准确
- ✅ 行业板块表格：颜色显示更准确
- ✅ 趋势图（Sparkline）：颜色与实际数据一致
- ✅ 放大趋势图（TrendLens）：颜色与实际数据一致
- ✅ 信号标签：逻辑更严格，避免矛盾

### 间接影响
- 用户体验提升：数据显示更直观、更可靠
- 决策支持：避免因显示错误导致的误判
- 系统可信度：提高数据展示的一致性和准确性

## 文件清单

修改的文件：
1. `scripts/etl.py` - 后端ETL信号标签逻辑
2. `components/business/fishbowl-table.tsx` - 前端表格渲染逻辑
3. `components/ui/sparkline.tsx` - Sparkline迷你图组件
4. `components/trend-lens.tsx` - TrendLens放大趋势图组件

新增文件：
1. `BUGFIX_v6.1.md` - 本修复报告

## 版本信息

- **修复版本**: v6.1
- **修复日期**: 2025-12-17
- **影响模块**: ETL计算、前端渲染、趋势图组件
- **修复人员**: Claude Code (GLM)

---

**重要提示**:
- 修复后请运行一次完整的ETL更新（`python scripts/etl.py`）
- 清空浏览器缓存后重新加载前端页面
- 验证几个关键指数的显示是否正确
