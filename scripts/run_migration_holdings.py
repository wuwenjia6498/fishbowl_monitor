#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行持仓字段迁移
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# 设置标准输出编码为UTF-8（解决Windows编码问题）
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# 加载环境变量
load_dotenv()

def run_migration():
    """执行数据库迁移"""
    connection_url = os.getenv('DATABASE_URL')
    if not connection_url:
        print("❌ 错误: 环境变量 DATABASE_URL 未设置")
        return False
    
    print("=" * 60)
    print("🐟 鱼盆趋势雷达 - 持仓字段迁移脚本")
    print("=" * 60)
    
    try:
        # 连接数据库
        print("📡 正在连接数据库...")
        conn = psycopg2.connect(connection_url)
        cursor = conn.cursor()
        
        # 执行迁移
        print("📝 正在添加 top_holdings 字段...")
        cursor.execute("""
            ALTER TABLE monitor_config 
            ADD COLUMN IF NOT EXISTS top_holdings TEXT;
        """)
        
        print("📝 正在添加 holdings_updated_at 字段...")
        cursor.execute("""
            ALTER TABLE monitor_config 
            ADD COLUMN IF NOT EXISTS holdings_updated_at TIMESTAMP;
        """)
        
        # 提交更改
        conn.commit()
        
        # 验证字段是否存在
        print("🔍 正在验证字段...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'monitor_config' 
            AND column_name IN ('top_holdings', 'holdings_updated_at')
            ORDER BY column_name;
        """)
        
        columns = cursor.fetchall()
        if len(columns) == 2:
            print("✅ 迁移成功！已添加以下字段：")
            for col in columns:
                print(f"   - {col[0]}")
        else:
            print(f"⚠️ 警告: 只找到 {len(columns)} 个字段")
        
        cursor.close()
        conn.close()
        
        print("=" * 60)
        print("✅ 数据库迁移完成！")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)






