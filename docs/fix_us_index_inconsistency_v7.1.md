# v7.1 优化：美股指数设计说明

**更新日期：** 2025-01-29  
**版本：** v7.1.1  
**类型：** 设计说明（非 Bug）

---

## 📋 背景

在开发过程中，发现页面上两处显示的纳斯达克指数数据不同：

### 数据对比

| 位置 | 纳斯达克指数 | 标普500 | 数据来源 |
|------|------------|---------|---------|
| **市场概览** | 23,593.10 (-0.09%) | 6,929.94 (-0.03%) | IXIC (综合指数) |
| **全球指数表格** | 25,495.68 (-0.58%) | 6,902.13 (-0.40%) | NDX (100指数) |

### 初步分析

1. **市场概览（market_overview）**
   - 使用：`IXIC` (纳斯达克综合指数)
   - 包含：3000+ 只在纳斯达克上市的所有股票
   - 数据源：Tushare `index_global` 接口
   - 点位：~23,000 点

2. **全球指数表格（fishbowl_daily）**
   - 使用：`NDX` (纳斯达克100指数)
   - 包含：100 只最大的非金融类股票
   - 数据源：yfinance 实时接口
   - 点位：~25,000 点

---

## ✅ 最终设计决策

### 保持现状（各有用途）

**决策理由：**
1. ✅ **IXIC 用于市场情绪观察**：3000+ 只股票，更全面反映整体市场
2. ✅ **NDX 用于投资决策**：聚焦大盘科技股，有对应的 ETF 可投资
3. ✅ **两者互补**：观察面（IXIC）+ 投资面（NDX）
4. ✅ **符合用户需求**：用户明确表示需要综合指数

### 实现细节

#### 1. ETL 脚本（`scripts/etl.py`）

**位置：** 第 811-850 行 `update_market_overview` 函数

**配置：**
```python
# 市场概览：展示综合指数（代表整体市场情绪）
# 注：全球指数表格展示 NDX（可投资标的），两者用途不同
us_indices = [
    ('IXIC', '纳斯达克'),  # 综合指数（3000+只股票）
    ('SPX', '标普500'),
    ('DJI', '道琼斯')
]
# 数据源：Tushare index_global 接口（稳定可靠）
```

#### 2. 数据库配置（`scripts/init_db.py`）

**配置：**
```python
# 全球指数表格：可投资标的
BROAD_INDICES = [
    {"code": "NDX", "name": "纳指100", "group": "全球指数"},
    {"code": "SPX", "name": "标普500", "group": "全球指数"},
    {"code": "HSI", "name": "恒生指数", "group": "全球指数"},
]
# 数据源：yfinance 实时接口（数据更新快）
```

#### 3. 前端显示（`components/market-header.tsx`）

**配置：**
```tsx
// 直接显示后端返回的名称
{data.us_share.map((item, index) => (
  <span className="text-sm text-gray-600">
    {item.name}  // 显示"纳斯达克"（IXIC）
  </span>
))}
```

---

## 🔄 数据流程

### 最终设计
```
市场概览 → IXIC (Tushare) → 23,593 点 → 显示"纳斯达克" ✅ [整体市场情绪]
全球指数 → NDX (yfinance) → 25,495 点 → 显示"纳指100" ✅ [投资标的]
```

### 设计优势
- ✅ **观察全面**：IXIC 包含 3000+ 只股票，反映整体市场
- ✅ **可投资**：NDX 有对应 ETF（QQQ），可用于鱼盆策略
- ✅ **互补性强**：观察面 + 投资面，两者搭配使用效果最佳

---

## 📊 验证步骤

### 1. 本地测试
```bash
# 运行 ETL 脚本
python scripts/etl.py

# 检查日志输出
# 应该看到: "🇺🇸 使用 yfinance 获取美股数据: NDX -> ^NDX"
```

### 2. 数据库验证
```sql
-- 检查 market_overview 表
SELECT data->'us_share'->0->'name', data->'us_share'->0->'price'
FROM market_overview
ORDER BY date DESC LIMIT 1;

-- 检查 fishbowl_daily 表
SELECT symbol, close_price, change_pct
FROM fishbowl_daily
WHERE symbol = 'NDX'
ORDER BY date DESC LIMIT 1;
```

### 3. 前端验证
- 访问页面，查看美股板块和全球指数表格
- 确认"纳指100"的价格一致
- 确认涨跌幅数值接近（可能有轻微时间差）

---

## 🚀 部署清单

- [x] 修改 `scripts/etl.py`
- [x] 修改 `components/market-header.tsx`
- [x] 通过 Linter 检查
- [ ] 提交到 GitHub
- [ ] 触发 GitHub Actions
- [ ] 验证数据一致性

---

## 📝 重要说明

### 为什么点位不同？

这是**正常现象**，因为两者是**不同的指数**：

| 指数 | 代码 | 成分股 | 典型点位 | 用途 |
|------|------|--------|----------|------|
| 纳斯达克综合 | IXIC | 3000+ 只 | ~23,000 | 观察市场情绪 |
| 纳斯达克100 | NDX | 100 只 | ~25,000 | 投资决策参考 |

### 数据来源

- **IXIC（市场概览）**：Tushare index_global 接口（稳定，T-1 数据）
- **NDX（指数表格）**：yfinance 实时接口（更新快，T 日数据）

### 使用建议

1. **观察市场情绪** → 看市场概览的 IXIC
2. **决定是否投资** → 看指数表格的 NDX（鱼盆状态）
3. **判断市场风格** → 对比两者涨跌幅
   - IXIC > NDX：中小盘强（市场宽度好）
   - IXIC < NDX：大盘股强（抱团大盘）

---

## 🔗 相关文档

- [index_design_philosophy.md](./index_design_philosophy.md) - 指数设计理念详细说明 ⭐ **必读**
- [CHANGELOG_v7.0.md](../CHANGELOG_v7.0.md) - v7.0+ 版本更新日志
- [v7.0_troubleshooting.md](../v7.0_troubleshooting.md) - 问题排查指南
- [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) - 项目架构文档

---

## ✅ 当前状态

**设计状态：** ✅ 已明确（保持 IXIC + NDX 双指数）  
**代码状态：** ✅ 已更新（保持原有配置）  
**文档状态：** ✅ 已完善（新增设计理念文档）  
**测试状态：** ✅ 通过 Linter 检查  
**部署状态：** ⏳ 待推送到 GitHub

