# UI 细节优化与数据清洗 - 修改日志

**日期:** 2025-12-09  
**版本:** v3.1.1

---

## 📋 修改概览

本次更新解决了用户反馈的两个关键问题：

1. ✅ **UI 优化**：修复表格列宽问题，防止"指数名称"列过宽
2. ✅ **数据清洗**：确保宽基指数（如上证指数）无 ETF 映射

---

## 🔧 具体修改

### 1. 表格列宽优化 (`components/fishbowl-table.tsx`)

#### 问题描述
- "指数名称"列使用 `min-w-[140px]`，但没有最大宽度限制
- 导致该列在某些情况下过宽，挤占其他数据列空间

#### 解决方案
为两个表格的"指数名称"/"板块名称"列添加固定宽度：

**宽基大势表格：**
```tsx
// 修改前
<TableHead className="min-w-[140px]">指数名称</TableHead>

// 修改后
<TableHead className="w-[140px] min-w-[140px]">指数名称</TableHead>
```

**行业轮动表格：**
```tsx
// 修改前
<TableHead className="min-w-[140px]">板块名称</TableHead>

// 修改后
<TableHead className="w-[140px] min-w-[140px]">板块名称</TableHead>
```

#### 效果
- ✅ 列宽固定为 140px，不会无限拉伸
- ✅ 保持最小宽度约束，防止内容被过度压缩
- ✅ 其他数据列获得更合理的空间分配

---

### 2. 数据清洗：宽基指数无 ETF (`scripts/clean_broad_etf.py`)

#### 问题描述
- 用户指出上证指数 (`000001.SH`) 等综合指数没有对应的 ETF 产品
- 需要确保 `dominant_etf` 字段为空

#### 解决方案

**2.1 创建数据清洗脚本**

新增 `scripts/clean_broad_etf.py`，功能：
- 自动检测所有 `category='broad'` 的指数
- 将其 `dominant_etf` 字段设置为 `NULL`
- 输出清洗前后的对比报告

**2.2 验证数据准确性**

运行清洗脚本后的验证结果：

```
✓ 所有宽基指数的 ETF 映射均为空，数据正常

当前宽基指数列表：
  上证指数     (000001.SH) | ETF: -
  上证50      (000016.SH) | ETF: -
  沪深300     (000300.SH) | ETF: -
  科创50      (000688.SH) | ETF: -
  中证1000    (000852.SH) | ETF: -
  中证500     (000905.SH) | ETF: -
  深证成指     (399001.SZ) | ETF: -
  中小100     (399005.SZ) | ETF: -
  创业板指     (399006.SZ) | ETF: -
```

**2.3 前端空值处理**

前端代码已正确处理空值显示（`components/fishbowl-table.tsx:292`）：

```tsx
{item.dominant_etf ? (
  <button onClick={() => copyToClipboard(item.dominant_etf!, item.name)}>
    {item.dominant_etf}
  </button>
) : (
  <span className="text-muted-foreground text-sm">-</span>
)}
```

#### 效果
- ✅ 所有 9 个宽基指数的 `dominant_etf` 均为 `NULL`
- ✅ 前端显示为 `-`，不会显示 `null` 或报错
- ✅ 行业指数的 ETF 映射不受影响（115 个行业有 ETF）

---

## 📊 验证结果

### 数据统计

| 指标 | 数值 | 状态 |
|------|------|------|
| 宽基指数总数 | 9 | ✓ |
| 宽基指数有ETF | 0 | ✓ 正确 |
| 行业指数总数 | 796 | ✓ |
| 行业指数有ETF | 115 | ✓ |
| 激活监控总数 | 284 | ✓ |

### 最新交易日数据示例 (2025-12-09)

**宽基指数：**
```
上证指数  | 价格: 3909.52 | MA20: 3914.07 | 状态: NO  | 偏离: -0.12% | ETF: -
沪深300  | 价格: 4598.22 | MA20: 4563.02 | 状态: YES | 偏离:  0.77% | ETF: -
创业板指  | 价格: 1347.11 | MA20: 1333.89 | 状态: YES | 偏离:  0.99% | ETF: -
```

所有宽基指数的 ETF 列均显示为 `-`，符合预期。

---

## 🛠️ 新增工具脚本

### 1. `scripts/clean_broad_etf.py`
**功能：** 清理宽基指数的 ETF 映射  
**使用：** `python scripts/clean_broad_etf.py`

### 2. `scripts/verify_changes.py`
**功能：** 验证修改效果，输出详细报告  
**使用：** `python scripts/verify_changes.py`

---

## 📝 配置文件确认

### `sql/schema.sql`
宽基指数初始化数据中，`dominant_etf` 字段均未设置（默认 NULL）：

```sql
INSERT INTO monitor_config (symbol, name, category, industry_level, is_active, is_system_bench) VALUES
('000300.SH', '沪深300', 'broad', 'N/A', true, true),
('000001.SH', '上证指数', 'broad', 'N/A', true, true),
('399001.SZ', '深证成指', 'broad', 'N/A', true, true)
-- ... 其他宽基指数
```

### `scripts/init_db.py`
`ETF_MAPPING` 字典只包含行业关键词，不包含宽基指数名称：

```python
ETF_MAPPING = {
    # 科技板块
    '半导体': '512480',
    '消费电子': '159732',
    # ... 其他行业
    
    # ❌ 不包含 '上证指数', '沪深300' 等宽基指数
}
```

---

## ✅ 测试清单

- [x] 表格列宽固定为 140px
- [x] 宽基指数 ETF 字段为空
- [x] 前端空值显示为 `-`
- [x] 行业指数 ETF 映射正常
- [x] 数据库数据一致性
- [x] 无 TypeScript 编译错误
- [x] 无 Linter 错误

---

## 🚀 部署建议

1. **前端更新：** 重新构建前端应用
   ```bash
   npm run build
   ```

2. **数据库清洗：** 如果生产环境有脏数据，运行清洗脚本
   ```bash
   python scripts/clean_broad_etf.py
   ```

3. **验证：** 运行验证脚本确认数据正确
   ```bash
   python scripts/verify_changes.py
   ```

---

## 📞 技术支持

如有问题，请检查：
1. 数据库连接是否正常（`DATABASE_URL` 环境变量）
2. 前端是否重新构建
3. 浏览器缓存是否清除

---

**修改完成！** 🎉



