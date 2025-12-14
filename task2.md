# 任务：重构顶部为“全景战术驾驶舱” (v5.8 Combined)

用户要求彻底重构页面的 Header 区域。
**核心目标：** 废弃旧的进度条，改为 **4 个独立的战术卡片**，分别展示 **A股基准、美股外盘、美元黄金、领涨板块**。

## 1. 数据库变更 (`sql/schema.sql`)

我们需要一张表来存储每日聚合的市场概览数据。

```sql
CREATE TABLE IF NOT EXISTS market_overview (
    date DATE PRIMARY KEY,
    data JSONB,  -- 存储所有面板数据的 JSON
    updated_at TIMESTAMP DEFAULT NOW()
);

2. 后端 ETL 聚合逻辑 (scripts/etl.py)
请修改 etl.py，增加一个聚合函数 update_market_overview()，在每日数据更新完成后调用。

2.1 数据获取需求 (多接口混合)
你需要调用不同的 Tushare 接口获取以下 4 类数据：

A股基准 (Internal):

接口: pro.index_daily

标的: 上证指数 (000001.SH)、深证成指 (399001.SZ)。

指标: 收盘价、涨跌幅、鱼盆状态 (YES/NO) (需基于 MA20 计算)。

量能: 获取两大指数的成交额 (amount)。

计算: 对比 5日均量 (vol_ratio = today_vol / ma5_vol)。

判定: > 1.0 为 "放量", < 1.0 为 "缩量"。

美股风向 (External T-1):

接口: pro.index_global

标的: 纳斯达克 (IXIC 或 NDX)、标普500 (SPX)、道琼斯 (DJI)。

注意: 取最近一个交易日的数据。

避险资产 (Gold USD):

接口: pro.fx_daily (外汇) 或 pro.index_global

标的: 伦敦金/美元黄金 (XAUUSD 或 XAU)。

注意: 必须展示美元价格。若无权限，请做好异常处理（可暂存空值）。

领涨先锋 (Leader):

逻辑: 基于当日数据库中所有 category='industry' 的 ETF 数据。

排序: 按 change_pct 降序排列，取 Top 3。

字段: 板块名称 (name)、涨幅 (change_pct)、ETF代码 (symbol)。

2.2 数据存储 (market_overview)
将上述数据打包为 JSON，存入数据库：

JSON

{
  "a_share": {
    "sh": {"price": 3000, "change": 0.5, "status": "YES"},
    "sz": {"price": 9500, "change": -0.2, "status": "NO"},
    "volume": {"amount": 98000000, "tag": "放量", "ratio": 1.2}
  },
  "us_share": [
    {"name": "纳指", "price": 16000, "change": -0.5},
    {"name": "标普", "price": 5100, "change": 0.2},
    {"name": "道指", "price": 39000, "change": 0.1}
  ],
  "gold": {
    "name": "伦敦金(USD)", "price": 2350.5, "change": 1.2, "unit": "$"
  },
  "leaders": [
    {"name": "半导体", "change": 4.5, "code": "512480"},
    {"name": "AI", "change": 3.2, "code": "159819"},
    {"name": "证券", "change": 2.1, "code": "512880"}
  ]
}
3. 前端 UI 重构 (components/market-header.tsx)
请完全重写 MarketHeader 组件，使用 Grid 布局 (grid-cols-2 lg:grid-cols-4) 展示 4 个卡片。

卡片 1: A股基准
布局: 左右或上下结构。

内容:

上证 & 深证：显示点位、涨跌幅颜色、YES/NO Badge (这是核心)。

底部：显示 "两市成交: [金额]" 及 "🔥 放量" 或 "🧊 缩量" 标签。

卡片 2: 美股风向 (T-1)
布局: 列表式。

内容: 依次显示 纳指、标普、道指 的名称和涨跌幅。

卡片 3: 黄金 (USD)
布局: 居中强调。

内容:

标题: "伦敦金 (USD)"

数值: $ 2,350.xx (注意美元符号)。

涨跌: 显示百分比。

卡片 4: 领涨先锋
布局: 列表式 (Top 3)。

内容:

板块名称 + 涨跌幅。

交互: 必须包含一个 "复制" 图标，点击复制对应的 ETF 代码。

执行指令
SQL: 创建 market_overview 表。

Python: 在 etl.py 中实现多源数据聚合与写入逻辑。

Frontend: 重写 market-header.tsx 实现新的 UI 设计。