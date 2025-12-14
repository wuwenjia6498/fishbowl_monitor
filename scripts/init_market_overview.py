#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速初始化 market_overview 表
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# 设置标准输出编码为UTF-8
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# 加载环境变量
load_dotenv()

def create_market_overview_table():
    """创建 market_overview 表"""
    
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ 错误: 环境变量 DATABASE_URL 未设置")
        print("请在 .env 文件中配置 DATABASE_URL")
        return False
    
    try:
        print("=" * 60)
        print("📊 创建 market_overview 表...")
        print("=" * 60)
        
        # 连接数据库
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # 创建表的 SQL
        create_table_sql = """
        -- 如果表已存在则先删除
        DROP TABLE IF EXISTS market_overview CASCADE;
        
        -- 创建新表
        CREATE TABLE market_overview (
            date DATE PRIMARY KEY,
            data JSONB NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 创建索引
        CREATE INDEX idx_market_overview_date ON market_overview(date DESC);
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        
        print("✅ market_overview 表创建成功！")
        
        # 验证表是否存在
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'market_overview'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"✓ 验证通过: 表 '{result[0]}' 已存在")
        
        cursor.close()
        conn.close()
        
        print("=" * 60)
        print("🎉 初始化完成！")
        print("=" * 60)
        print("\n下一步: 运行 ETL 脚本生成数据")
        print("  python scripts/etl.py")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_market_overview_table()
    sys.exit(0 if success else 1)
