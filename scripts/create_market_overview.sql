-- ================================================
-- 创建市场概览表（全景战术驾驶舱）
-- ================================================

-- 如果表已存在则先删除（可选，谨慎使用）
DROP TABLE IF EXISTS market_overview CASCADE;

-- 创建新表
CREATE TABLE market_overview (
    date DATE PRIMARY KEY,                     -- 交易日期
    data JSONB NOT NULL,                       -- 存储所有面板数据的 JSON
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引优化查询
CREATE INDEX idx_market_overview_date ON market_overview(date DESC);

-- 显示创建结果
SELECT 'market_overview 表创建成功！' AS result;







