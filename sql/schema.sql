-- ================================================
-- 鱼盆趋势雷达 v3.1 数据库架构
-- 支持：二级行业下沉 + ETF 交易辅助
-- ================================================

-- 1. 监控配置表（资产库）
DROP TABLE IF EXISTS monitor_config CASCADE;

CREATE TABLE monitor_config (
    symbol VARCHAR(20) PRIMARY KEY,        -- 指数代码（如 '000300.SH', '399006.SZ'）
    name VARCHAR(50) NOT NULL,             -- 指数名称（如 '沪深300', '创业板指'）
    category VARCHAR(20) NOT NULL,         -- 类别：'broad'(宽基) 或 'industry'(行业)
    industry_level VARCHAR(10),            -- 行业层级：'L1'(一级), 'L2'(二级), 'N/A'(非行业指数)

    -- [NEW v3.1] 关联 ETF 字段
    dominant_etf VARCHAR(20),              -- 龙头ETF代码（如 '512480'），若无则为NULL
    
    -- [NEW v5.4] ETF 持仓相关字段
    top_holdings TEXT,                     -- 核心持仓 (Markdown 格式的前十大重仓股列表)
    holdings_updated_at TIMESTAMP,         -- 持仓数据更新时间

    is_active BOOLEAN DEFAULT false,       -- 是否激活监控（用户关注）
    is_system_bench BOOLEAN DEFAULT false, -- 是否为系统标尺（用于计算气候看板）

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以优化查询
CREATE INDEX idx_category ON monitor_config(category);
CREATE INDEX idx_is_active ON monitor_config(is_active);
CREATE INDEX idx_industry_level ON monitor_config(industry_level);


-- 2. 每日数据表
DROP TABLE IF EXISTS fishbowl_daily CASCADE;

CREATE TABLE fishbowl_daily (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,                    -- 交易日期
    symbol VARCHAR(20) NOT NULL,           -- 指数代码（外键关联 monitor_config）
    close_price DECIMAL(10, 2) NOT NULL,   -- 收盘价

    -- 鱼盆核心指标
    ma20_price DECIMAL(10, 4) NOT NULL,    -- 20日均线
    status VARCHAR(10) NOT NULL,           -- 状态：'YES'(多头) 或 'NO'(空头)
    deviation_pct DECIMAL(10, 4) NOT NULL, -- 偏离度（百分比）
    duration_days INT NOT NULL,            -- 持续天数
    trend_rank INT,                        -- 趋势排名（按偏离度绝对值降序）
    signal_tag VARCHAR(20),                -- 信号标签：BREAKOUT, STRONG, OVERHEAT, SLUMP, EXTREME_BEAR

    -- v4.7 新增：涨幅指标
    change_pct DECIMAL(10, 4),             -- 当日涨幅
    trend_pct DECIMAL(10, 4),              -- 区间涨幅（从当前状态起始点到现在）

    -- v5.9 新增：迷你趋势图数据
    sparkline_json JSONB,                  -- 近30日价格和MA20趋势数据

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(symbol, date),                  -- 确保每个指数每天只有一条记录
    FOREIGN KEY (symbol) REFERENCES monitor_config(symbol) ON DELETE CASCADE
);

-- 创建索引以优化查询
CREATE INDEX idx_date ON fishbowl_daily(date);
CREATE INDEX idx_symbol_date ON fishbowl_daily(symbol, date);
CREATE INDEX idx_trend_rank ON fishbowl_daily(trend_rank);


-- ================================================
-- 初始数据：宽基指数（系统标尺）
-- ================================================
-- 这些宽基指数用于计算"大势风向"指标
INSERT INTO monitor_config (symbol, name, category, industry_level, is_active, is_system_bench) VALUES
('000300.SH', '沪深300', 'broad', 'N/A', true, true),
('000905.SH', '中证500', 'broad', 'N/A', true, true),
('000852.SH', '中证1000', 'broad', 'N/A', true, true),
('399006.SZ', '创业板指', 'broad', 'N/A', true, true),
('399001.SZ', '深证成指', 'broad', 'N/A', true, true),
('000001.SH', '上证指数', 'broad', 'N/A', true, true),
('000016.SH', '上证50', 'broad', 'N/A', true, false),
('399005.SZ', '中小100', 'broad', 'N/A', true, false),
('000688.SH', '科创50', 'broad', 'N/A', true, false)
ON CONFLICT (symbol) DO NOTHING;


-- ================================================
-- 3. 市场概览表（全景战术驾驶舱）
-- ================================================
DROP TABLE IF EXISTS market_overview CASCADE;

CREATE TABLE market_overview (
    date DATE PRIMARY KEY,                     -- 交易日期
    data JSONB NOT NULL,                       -- 存储所有面板数据的 JSON
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引优化查询
CREATE INDEX idx_market_overview_date ON market_overview(date DESC);


-- ================================================
-- 说明：
-- 行业指数数据将通过 Python 脚本 init_db.py 自动初始化
-- ================================================
