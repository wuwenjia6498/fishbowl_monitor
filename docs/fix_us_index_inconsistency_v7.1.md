# v7.1 修复：美股指数数据不一致问题

**修复日期：** 2025-01-29  
**问题编号：** #001  
**严重等级：** 中等（数据展示不一致）

---

## 📋 问题描述

用户发现页面上两处显示的美股数据存在矛盾：

### 数据对比

| 位置 | 纳斯达克指数 | 标普500 | 数据来源 |
|------|------------|---------|---------|
| **美股板块** | 23,593.10 (-0.09%) | 6,929.94 (-0.03%) | ❌ IXIC (综合指数) |
| **全球指数表格** | 25,495.68 (-0.58%) | 6,902.13 (-0.40%) | ✅ NDX (100指数) |

### 根本原因

**不同的指数代码导致数据来源不一致：**

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

## ✅ 解决方案

### 统一使用 NDX（纳斯达克100指数）

**选择理由：**
- ✅ 更具代表性（聚焦大盘科技股）
- ✅ 更常用作市场基准
- ✅ yfinance 数据更实时
- ✅ 与数据库配置保持一致

### 代码修改

#### 1. 修改 ETL 脚本（`scripts/etl.py`）

**位置：** 第 811-850 行 `update_market_overview` 函数

**修改内容：**
```python
# 旧代码（v7.0）
us_indices = [
    ('IXIC', '纳斯达克'),  # ❌ 综合指数
    ('SPX', '标普500'),
    ('DJI', '道琼斯')
]

# 新代码（v7.1）
us_indices = [
    ('NDX', '纳指100'),   # ✅ 100指数
    ('SPX', '标普500'),
    ('DJI', '道琼斯')
]
```

**优化点：**
1. 统一使用 `NDX` 代码
2. 优先使用 `yfinance` 实时数据
3. 失败时自动回退到 Tushare
4. 兼容两种数据格式（yfinance / Tushare）
5. 自动计算涨跌幅（yfinance 不提供）

#### 2. 简化前端显示逻辑（`components/market-header.tsx`）

**位置：** 第 194-196 行

**修改内容：**
```tsx
// 旧代码（v6.7）
{item.name === '纳斯达克' || item.name.includes('纳斯达克') ? '纳指100' : item.name}

// 新代码（v7.1）
{item.name}  // 后端已统一返回"纳指100"
```

---

## 🔄 数据流程

### 修复前
```
市场概览 → IXIC (Tushare) → 23,593 点 → 前端强制显示"纳指100" ❌
全球指数 → NDX (yfinance) → 25,495 点 → 显示"纳指100" ✅
```

### 修复后
```
市场概览 → NDX (yfinance) → 25,495 点 → 显示"纳指100" ✅
全球指数 → NDX (yfinance) → 25,495 点 → 显示"纳指100" ✅
```

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

## 📝 注意事项

### 时间差异
- **市场概览**：可能是 T-1 数据（取决于 ETL 运行时间）
- **全球指数表格**：可能是 T 日数据（更实时）
- **轻微差异属于正常**：只要使用同一指数即可

### API 依赖
- **yfinance**：优先使用（实时数据）
- **Tushare**：备用方案（可能滞后1-2天）
- **NDX**：只能依赖 yfinance（Tushare 不支持）

### 未来优化
- 可考虑为市场概览增加"数据时间戳"显示
- 可考虑统一所有美股数据的更新时间

---

## 🔗 相关文档

- [CHANGELOG_v7.0.md](../CHANGELOG_v7.0.md) - v7.0 版本更新日志
- [v7.0_troubleshooting.md](../v7.0_troubleshooting.md) - v7.0 故障排查
- [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) - 项目架构文档

---

## ✅ 修复状态

**当前状态：** 已修复，待部署  
**测试状态：** 通过 Linter 检查  
**部署状态：** 待用户确认后推送到 GitHub

