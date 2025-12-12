#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 执行 SQL 迁移文件
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


def execute_migration(sql_file_path: str):
    """
    执行迁移 SQL 文件

    Args:
        sql_file_path: SQL 文件的路径
    """
    # 获取数据库连接
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ 错误：环境变量 DATABASE_URL 未设置")
        sys.exit(1)

    # 读取 SQL 文件
    if not os.path.exists(sql_file_path):
        print(f"❌ 错误：SQL 文件不存在: {sql_file_path}")
        sys.exit(1)

    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print("=" * 60)
    print("🔧 数据库迁移工具")
    print("=" * 60)
    print(f"📄 迁移文件: {sql_file_path}")
    print(f"🗄️  数据库: {database_url.split('@')[-1].split('?')[0]}")
    print("-" * 60)

    try:
        # 连接数据库
        print("\n🔌 正在连接数据库...")
        conn = psycopg2.connect(database_url)
        conn.autocommit = False  # 使用事务
        cursor = conn.cursor()

        # 执行 SQL
        print("⚙️  正在执行迁移脚本...")
        cursor.execute(sql_content)

        # 提交事务
        conn.commit()
        print("✅ 迁移执行成功！")

        # 验证结果（如果 SQL 中有 SELECT 语句）
        try:
            results = cursor.fetchall()
            if results:
                print("\n📊 验证结果：")
                for row in results:
                    print(f"   - 列名: {row[0]}, 类型: {row[1]}, 可为空: {row[2]}")
        except:
            pass

        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("✅ 迁移完成！")
        print("💡 下一步：运行 ETL 脚本更新数据")
        print("   python scripts/etl.py")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # 默认迁移文件路径
    migration_file = "sql/migrations/add_change_and_trend_pct.sql"

    # 如果命令行提供了参数，使用该参数
    if len(sys.argv) > 1:
        migration_file = sys.argv[1]

    execute_migration(migration_file)
