-- ================================================
-- 迁移脚本：添加当日涨幅和区间涨幅字段 (v4.7)
-- 创建时间：2025-12-12
-- 说明：为 fishbowl_daily 表添加 change_pct 和 trend_pct 字段
-- ================================================

-- 1. 添加当日涨幅字段
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'fishbowl_daily' AND column_name = 'change_pct'
    ) THEN
        ALTER TABLE fishbowl_daily ADD COLUMN change_pct DECIMAL(10, 4);
    END IF;
END $$;

-- 2. 添加区间涨幅字段
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'fishbowl_daily' AND column_name = 'trend_pct'
    ) THEN
        ALTER TABLE fishbowl_daily ADD COLUMN trend_pct DECIMAL(10, 4);
    END IF;
END $$;

-- 3. 添加字段注释
COMMENT ON COLUMN fishbowl_daily.change_pct IS '当日涨幅';
COMMENT ON COLUMN fishbowl_daily.trend_pct IS '区间涨幅（从当前状态起始点到现在）';

-- 4. 验证字段是否添加成功
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'fishbowl_daily'
  AND column_name IN ('change_pct', 'trend_pct');

-- 5. 说明
-- 执行完此脚本后，请运行 ETL 脚本重新计算所有数据
-- python scripts/etl.py
