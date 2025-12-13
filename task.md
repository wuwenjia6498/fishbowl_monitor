# 任务：扩展全球指数与贵金属现货 (v5.3 Real Indices)

用户要求在 **[宽基大势]** Tab 中增加 **美股指数、港股指数** 和 **贵金属现货**。
**关键要求：**
1.  **直接展示指数/现货**，而不是 ETF。
2.  **接受时间滞后：** 美股使用前一日收盘数据。
3.  **数据源：** 使用 Tushare 的 `index_global` (全球) 和 `sge_daily` (黄金/白银) 接口。

## 1. 初始化配置更新 (`scripts/init_db.py`)

请修改 `BROAD_INDICES` 列表，加入以下 6 个全球/商品标的。
**注意：** 我们需要增加一个 `api_type` 字段（或者通过代码特征判断），以便 ETL 知道调用哪个接口。这里建议直接在配置里硬编码 `symbol`，ETL 负责识别。

```python
# 更新后的宽基指数池
BROAD_INDICES = [
    # --- A股原生指数 (接口: pro.index_daily) ---
    {"sort_id": 1, "code": "000016.SH", "name": "上证50", "group": "A股指数", "etf_label": "上证50"},
    {"sort_id": 2, "code": "000300.SH", "name": "沪深300", "group": "A股指数", "etf_label": "沪深300"},
    {"sort_id": 3, "code": "399006.SZ", "name": "创业板指", "group": "A股指数", "etf_label": "创业板"},
    {"sort_id": 4, "code": "000688.SH", "name": "科创50", "group": "A股指数", "etf_label": "科创50"},
    {"sort_id": 5, "code": "000905.SH", "name": "中证500", "group": "A股指数", "etf_label": "中证500"},
    {"sort_id": 6, "code": "000852.SH", "name": "中证1000", "group": "A股指数", "etf_label": "中证1000"},
    {"sort_id": 7, "code": "932000.CSI", "name": "中证2000", "group": "A股指数", "etf_label": "中证2000"},
    
    # --- 全球指数 (接口: pro.index_global) ---
    {"sort_id": 20, "code": "NDX", "name": "纳指100", "group": "全球/商品", "etf_label": "纳指"},
    {"sort_id": 21, "code": "SPX", "name": "标普500", "group": "全球/商品", "etf_label": "标普"},
    {"sort_id": 22, "code": "HSI", "name": "恒生指数", "group": "全球/商品", "etf_label": "恒指"},
    {"sort_id": 23, "code": "HSTECH", "name": "恒生科技", "group": "全球/商品", "etf_label": "恒生科技"},

    # --- 贵金属现货 (接口: pro.sge_daily) ---
    {"sort_id": 24, "code": "Au99.99", "name": "黄金现价", "group": "全球/商品", "etf_label": "黄金"},
    {"sort_id": 25, "code": "Ag(T+D)", "name": "白银现价", "group": "全球/商品", "etf_label": "白银"},
]

2. ETL 逻辑升级 (scripts/etl.py)
请修改 DataFetcher 类的 fetch_history 方法，实现多接口路由。

路由逻辑：

Python

    def fetch_history(self, symbol: str, category: str) -> pd.DataFrame:
        try:
            # 1. 行业轮动 -> 基金接口 (ETF)
            if category == 'industry':
                return self.pro.fund_daily(ts_code=symbol, adj='qfq')
            
            # 2. 宽基大势 -> 混合接口路由
            # A. 贵金属 (代码特征: Au, Ag 开头) -> 上海金交所接口
            if symbol.startswith('Au') or symbol.startswith('Ag'):
                # sge_daily 返回字段可能不同，需统一 rename 为 close, trade_date
                df = self.pro.sge_daily(ts_code=symbol)
                
            # B. 全球指数 (代码特征: 纯字母不带点，或特定列表) -> 全球指数接口
            elif symbol in ['NDX', 'SPX', 'HSI', 'HSTECH', 'DJI', 'IXIC']:
                df = self.pro.index_global(ts_code=symbol)
                
            # C. A股指数 (代码特征: 数字开头) -> A股指数接口
            else:
                df = self.pro.index_daily(ts_code=symbol)

            # --- 数据清洗标准化 (Normalization) ---
            # 必须确保返回的 DataFrame 包含且仅包含: ['date', 'close'] 且按日期升序
            if df.empty: return pd.DataFrame()
            
            # 统一列名 (Tushare 不同接口返回的日期列名可能不同)
            # index_global/sge_daily 通常也是 trade_date, close
            df = df.rename(columns={'trade_date': 'date'}) 
            
            # 格式转换
            df['date'] = pd.to_datetime(df['date']).dt.date
            df['close'] = pd.to_numeric(df['close'])
            df = df.sort_values('date').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return pd.DataFrame()
3. 前端展示调整 (app/page.tsx)
分组: 请确保宽基 Tab 能够正确渲染 "A股指数" 和 "全球/商品" 两个分组。

日期提示: (可选) 可以在"全球/商品"分组的标题旁加一个小的提示文本 (T-1 数据)，以告知用户美股存在滞后。

执行指令
Python: 修改 init_db.py，更新 BROAD_INDICES。

Python: 修改 etl.py，实现多接口 (index_daily, index_global, sge_daily) 的自动切换和数据标准化。

Action: 提醒我运行 init_db.py 重置宽基数据。
