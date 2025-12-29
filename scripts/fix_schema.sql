-- 修复 fishbowl_daily 表，添加 updated_at 字段
-- 如果字段已存在则忽略

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'fishbowl_daily' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE fishbowl_daily 
        ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        
        RAISE NOTICE 'Added updated_at column to fishbowl_daily table';
    ELSE
        RAISE NOTICE 'updated_at column already exists in fishbowl_daily table';
    END IF;
END $$;









