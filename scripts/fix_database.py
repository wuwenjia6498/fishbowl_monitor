#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库修复脚本：添加缺失的 updated_at 字段
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


def get_db_connection():
    """连接到 Supabase PostgreSQL"""
    connection_string = os.getenv('DATABASE_URL')
    if not connection_string:
        raise ValueError("环境变量 DATABASE_URL 未设置")
    
    return psycopg2.connect(connection_string)


def fix_database():
    """修复数据库 schema"""
    print("=" * 60)
    print("数据库修复：添加缺失的 updated_at 字段")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查 updated_at 字段是否存在
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'fishbowl_daily' AND column_name = 'updated_at'
        """)
        
        if cursor.fetchone():
            print("\n✓ fishbowl_daily 表已有 updated_at 字段，无需修复")
        else:
            print("\n正在添加 updated_at 字段...")
            
            cursor.execute("""
                ALTER TABLE fishbowl_daily 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            
            conn.commit()
            print("✓ 成功添加 updated_at 字段")
        
        # 验证表结构
        print("\n验证 fishbowl_daily 表结构：")
        print("-" * 60)
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'fishbowl_daily'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        for col_name, data_type, nullable, default in columns:
            nullable_str = "NULL" if nullable == 'YES' else "NOT NULL"
            default_str = f" DEFAULT {default}" if default else ""
            print(f"  {col_name:20} {data_type:20} {nullable_str:10}{default_str}")
        
        print("\n" + "=" * 60)
        print("修复完成！")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    fix_database()









