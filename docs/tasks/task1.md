# 任务：实现“指数+ETF”混合双轨监控 (v4.4 Hybrid)

用户调整了需求：
1.  **宽基大势 (Category='broad'):** 必须监控**原生指数 (Indices)**，以获取最准确的市场风向。
2.  **行业轮动 (Category='industry'):** 继续监控**交易型 ETF**。

请对后端 ETL 和初始化逻辑进行重大升级。

## 1. 初始化脚本升级 (`scripts/init_db.py`)

请重写 `CUSTOM_ETF_POOL` 的结构，明确区分 **Index** 和 **ETF**。

```python
# 1. 宽基指数池 (使用原生指数代码)
BROAD_INDICES = [
    {"sort_id": 1, "code": "000016.SH", "name": "上证50", "group": "宽基指数", "etf_label": "上证50"},
    {"sort_id": 2, "code": "000300.SH", "name": "沪深300", "group": "宽基指数", "etf_label": "沪深300"},
    {"sort_id": 3, "code": "399006.SZ", "name": "创业板指", "group": "宽基指数", "etf_label": "创业板"},
    {"sort_id": 4, "code": "000688.SH", "name": "科创50", "group": "宽基指数", "etf_label": "科创50"},
    {"sort_id": 5, "code": "000905.SH", "name": "中证500", "group": "宽基指数", "etf_label": "中证500"},
    {"sort_id": 6, "code": "000852.SH", "name": "中证1000", "group": "宽基指数", "etf_label": "中证1000"},
    {"sort_id": 7, "code": "932000.CSI", "name": "中证2000", "group": "宽基指数", "etf_label": "中证2000"}, # 微盘代表
    {"sort_id": 8, "code": "899050.BJ", "name": "北证50", "group": "宽基指数", "etf_label": "北证50"},
]

# 2. 行业 ETF 池 (保持之前的 ETF 代码)
INDUSTRY_ETFS = [
    # ... (保持之前的科技、制造、消费、金融等 ETF 配置不变) ...
    # 示例: {"sort_id": 101, "code": "159819.SZ", "name": "人工智能(AI)", ...},
]

# 合并入库逻辑
# 遍历 BROAD_INDICES -> category='broad'
# 遍历 INDUSTRY_ETFS -> category='industry'

2. ETL 逻辑升级 (scripts/etl.py)
核心变更： DataFetcher 需要根据 category 智能选择不同的 Tushare 接口。

Python

    def fetch_history(self, symbol: str, category: str) -> pd.DataFrame:
        """
        混合数据获取策略:
        - category='broad'    -> 调用 pro.index_daily (获取指数数据)
        - category='industry' -> 调用 pro.fund_daily (获取ETF数据, 必须前复权 adj='qfq')
        """
        try:
            if category == 'broad':
                # 注意：Tushare index_daily 不需要 adj 参数
                df = self.pro.index_daily(ts_code=symbol)
            else:
                # 行业 ETF 必须复权，否则分红会导致假跌破
                df = self.pro.fund_daily(ts_code=symbol, adj='qfq')
            
            # ... 后续通用的数据清洗 (rename columns, sort date) ...
            return df
        except Exception as e:
            print(f"Error fetching {symbol} ({category}): {e}")
            return pd.DataFrame()
3. 前端展示微调 (app/page.tsx & columns.tsx)
宽基 Tab:

展示的是指数本身的行情。

不需要 “点击复制 ETF 代码”的功能（因为展示的是指数）。

依然保留“ETF 操作建议”列 (逻辑基于指数走势，但建议用户去操作对应标的)。

行业 Tab:

保持原样，展示 ETF 代码并支持复制。

执行指令
Python: 重写 init_db.py (注入新的指数列表)。

Python: 修改 etl.py (实现双接口混合抓取)。

Frontend: 确保宽基列表正确渲染 (无需 ETF 复制按钮)。

请开始工作。