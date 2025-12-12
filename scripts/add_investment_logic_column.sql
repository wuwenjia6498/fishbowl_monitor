-- 为 monitor_config 表添加 investment_logic 字段
-- 迁移脚本 v4.6

ALTER TABLE monitor_config 
ADD COLUMN IF NOT EXISTS investment_logic TEXT;

-- 添加注释
COMMENT ON COLUMN monitor_config.investment_logic IS 'ETF投资逻辑说明（Markdown格式）';

