-- ================================================
-- 迁移脚本 v5.4: 添加 ETF 核心持仓字段
-- 功能：存储 ETF 前十大重仓股数据 (Markdown 格式)
-- ================================================

-- 添加 top_holdings 字段（存储 Markdown 格式的持仓列表）
ALTER TABLE monitor_config 
ADD COLUMN IF NOT EXISTS top_holdings TEXT;

-- 添加持仓数据更新时间
ALTER TABLE monitor_config 
ADD COLUMN IF NOT EXISTS holdings_updated_at TIMESTAMP;

-- 添加注释
COMMENT ON COLUMN monitor_config.top_holdings IS '核心持仓：Markdown 格式的前十大重仓股列表';
COMMENT ON COLUMN monitor_config.holdings_updated_at IS '持仓数据最后更新时间';






