#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本执行器
用于执行 SQL 迁移文件
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
    """连接到数据库"""
    connection_url = os.getenv('DATABASE_URL')
    if not connection_url:
        raise ValueError("环境变量 DATABASE_URL 未设置")
    
    return psycopg2.connect(connection_url)


def run_migration(migration_file):
    """执行迁移文件"""
    print("=" * 60)
    print(f"数据库迁移：{migration_file}")
    print("=" * 60)
    
    try:
        # 读取 SQL 文件
        if not os.path.exists(migration_file):
            print(f"❌ 错误: 找不到迁移文件 {migration_file}")
            return False
            
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # 连接数据库
        conn = get_db_connection()
        print("✓ 数据库连接成功")
        
        # 执行 SQL
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        
        print("✓ 迁移执行成功")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    # 迁移文件路径
    migration_file = 'scripts/add_investment_logic_column.sql'
    
    if run_migration(migration_file):
        print("\n" + "=" * 60)
        print("迁移完成！")
        print("=" * 60)
    else:
        exit(1)


if __name__ == '__main__':
    main()
