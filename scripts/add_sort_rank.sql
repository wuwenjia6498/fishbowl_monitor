-- 添加 sort_rank 字段用于固定排序
ALTER TABLE monitor_config ADD COLUMN IF NOT EXISTS sort_rank INTEGER DEFAULT 0;

-- 为现有数据添加索引以提升查询性能
CREATE INDEX IF NOT EXISTS idx_monitor_config_sort_rank ON monitor_config(sort_rank);
CREATE INDEX IF NOT EXISTS idx_monitor_config_industry_level ON monitor_config(industry_level);
