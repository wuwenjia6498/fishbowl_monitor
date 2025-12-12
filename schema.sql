-- 鱼盆趋势雷达 (Fishbowl Monitor) 数据库 Schema
-- 适配 Vercel Postgres

-- 监控配置表
CREATE TABLE IF NOT EXISTS monitor_config (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    category VARCHAR(20) NOT NULL,
    industry_level VARCHAR(50),
    dominant_etf VARCHAR(50),
    sort_rank INT,
    investment_logic TEXT,
    is_active BOOLEAN DEFAULT false,
    is_system_bench BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 鱼盆日线数据表
CREATE TABLE IF NOT EXISTS fishbowl_daily (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    symbol VARCHAR(16) NOT NULL REFERENCES monitor_config(symbol),
    close_price NUMERIC(12,4) NOT NULL,
    ma20_price NUMERIC(12,4) NOT NULL,
    status VARCHAR(10) NOT NULL CHECK (status IN ('YES', 'NO')),
    deviation_pct NUMERIC(10,6) NOT NULL,
    duration_days INTEGER NOT NULL,
    trend_rank INTEGER,
    signal_tag VARCHAR(20) CHECK (signal_tag IN ('BREAKOUT', 'STRONG', 'OVERHEAT', 'SLUMP', 'EXTREME_BEAR')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_symbol_date UNIQUE(symbol, date)
);

-- 创建索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_fishbowl_daily_date ON fishbowl_daily(date);
CREATE INDEX IF NOT EXISTS idx_fishbowl_daily_symbol ON fishbowl_daily(symbol);
CREATE INDEX IF NOT EXISTS idx_fishbowl_daily_status ON fishbowl_daily(status);
CREATE INDEX IF NOT EXISTS idx_fishbowl_daily_signal_tag ON fishbowl_daily(signal_tag);
CREATE INDEX IF NOT EXISTS idx_fishbowl_daily_trend_rank ON fishbowl_daily(trend_rank);
CREATE INDEX IF NOT EXISTS idx_fishbowl_daily_composite ON fishbowl_daily(date, status, signal_tag);

-- 为 monitor_config 表创建索引
CREATE INDEX IF NOT EXISTS idx_monitor_config_sort_rank ON monitor_config(sort_rank);
CREATE INDEX IF NOT EXISTS idx_monitor_config_category ON monitor_config(category);
CREATE INDEX IF NOT EXISTS idx_monitor_config_industry_level ON monitor_config(industry_level);
CREATE INDEX IF NOT EXISTS idx_monitor_config_is_active ON monitor_config(is_active);
CREATE INDEX IF NOT EXISTS idx_monitor_config_is_system_bench ON monitor_config(is_system_bench);

-- 添加更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为 monitor_config 表创建更新时间触发器
DROP TRIGGER IF EXISTS update_monitor_config_updated_at ON monitor_config;
CREATE TRIGGER update_monitor_config_updated_at 
    BEFORE UPDATE ON monitor_config 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 为 fishbowl_daily 表创建更新时间触发器
DROP TRIGGER IF EXISTS update_fishbowl_daily_updated_at ON fishbowl_daily;
CREATE TRIGGER update_fishbowl_daily_updated_at 
    BEFORE UPDATE ON fishbowl_daily 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入初始监控配置 (使用 ON CONFLICT 避免重复插入)
-- 宽基指数 (系统基准)
INSERT INTO monitor_config (symbol, name, category, industry_level, dominant_etf, sort_rank, is_active, is_system_bench) VALUES
('000300.SH', '沪深300', '宽基', '宽基', '沪深300ETF', 1, true, true),
('399006.SZ', '创业板指', '宽基', '宽基', '创业板ETF', 2, true, true),
('000905.SH', '中证500', '宽基', '宽基', '中证500ETF', 3, true, true),
('000852.SH', '中证1000', '宽基', '宽基', '中证1000ETF', 4, true, true)
ON CONFLICT (symbol) DO NOTHING;