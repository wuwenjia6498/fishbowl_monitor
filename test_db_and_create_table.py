#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库连接并创建 market_overview 表
"""

import os
import sys
from dotenv import load_dotenv

# 设置标准输出编码为UTF-8
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# 加载环境变量
load_dotenv()

print("=" * 70)
print("🔧 数据库连接测试与表创建工具")
print("=" * 70)

# 1. 检查环境变量
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("\n❌ 错误: 找不到 DATABASE_URL 环境变量")
    print("\n请检查:")
    print("  1. .env 文件是否存在于项目根目录")
    print("  2. .env 文件中是否包含 DATABASE_URL=...")
    sys.exit(1)

print(f"\n✓ 找到 DATABASE_URL 配置")
# 隐藏密码部分
masked_url = database_url.split('@')[0].split(':')[0] + ':****@' + database_url.split('@')[1] if '@' in database_url else '****'
print(f"  连接字符串: {masked_url}")

# 2. 尝试导入 psycopg2
try:
    import psycopg2
    print("\n✓ psycopg2 模块已安装")
except ImportError:
    print("\n❌ 错误: 未安装 psycopg2 模块")
    print("\n请运行: pip install psycopg2-binary")
    sys.exit(1)

# 3. 测试数据库连接
print("\n📡 正在连接数据库...")
try:
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    # 测试查询
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"\n✅ 数据库连接成功！")
    print(f"  版本: {version.split(',')[0]}")
    
except Exception as e:
    print(f"\n❌ 数据库连接失败!")
    print(f"\n错误信息: {str(e)}")
    print("\n可能的原因:")
    print("  1. PostgreSQL 服务未启动")
    print("  2. 连接字符串配置错误")
    print("  3. 防火墙阻止连接")
    print("  4. 数据库用户名/密码错误")
    sys.exit(1)

# 4. 检查表是否已存在
print("\n📊 检查 market_overview 表...")
try:
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'market_overview'
        );
    """)
    exists = cursor.fetchone()[0]
    
    if exists:
        print("  ⚠️  表已存在，将重新创建...")
    else:
        print("  表不存在，准备创建...")
        
except Exception as e:
    print(f"  检查失败: {str(e)}")

# 5. 创建表
print("\n🔨 创建 market_overview 表...")
try:
    create_sql = """
    DROP TABLE IF EXISTS market_overview CASCADE;
    
    CREATE TABLE market_overview (
        date DATE PRIMARY KEY,
        data JSONB NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX idx_market_overview_date ON market_overview(date DESC);
    """
    
    cursor.execute(create_sql)
    conn.commit()
    
    print("\n✅ market_overview 表创建成功！")
    
    # 验证
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'market_overview'
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    print("\n表结构:")
    for col_name, col_type in columns:
        print(f"  • {col_name}: {col_type}")
    
except Exception as e:
    print(f"\n❌ 创建表失败: {str(e)}")
    conn.rollback()
    cursor.close()
    conn.close()
    sys.exit(1)

# 6. 清理并关闭
cursor.close()
conn.close()

print("\n" + "=" * 70)
print("✨ 全部完成！")
print("=" * 70)
print("\n下一步操作:")
print("  1️⃣  运行 ETL 脚本生成数据:")
print("      python scripts/etl.py")
print("\n  2️⃣  刷新浏览器查看全景战术驾驶舱:")
print("      http://localhost:3001")
print("\n" + "=" * 70)
