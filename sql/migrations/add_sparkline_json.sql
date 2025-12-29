-- Migration: 添加 sparkline_json 字段用于存储近30日趋势数据
-- Version: v5.9
-- Date: 2025-12-15

-- 添加 sparkline_json 字段到 fishbowl_daily 表
ALTER TABLE fishbowl_daily ADD COLUMN IF NOT EXISTS sparkline_json JSONB;

-- 添加字段注释
COMMENT ON COLUMN fishbowl_daily.sparkline_json IS '近30日价格和MA20趋势数据，用于前端迷你图展示';

-- 创建索引以提升 JSON 查询性能（可选）
CREATE INDEX IF NOT EXISTS idx_fishbowl_daily_sparkline ON fishbowl_daily USING GIN (sparkline_json);
