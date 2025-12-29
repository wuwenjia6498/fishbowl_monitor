#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试日期插入PostgreSQL的行为
"""

import os
import sys
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, date

# 设置UTF-8编码
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# 获取数据库连接
DATABASE_URL = os.getenv('DATABASE_URL')

print("=" * 80)
print("测试日期插入PostgreSQL")
print("=" * 80)

# 创建测试日期
test_date_str = "20251212"
print(f"\n1. 原始日期字符串: {test_date_str}")

# 转换为pandas Timestamp
ts = pd.to_datetime(test_date_str)
print(f"2. pd.to_datetime结果: {ts}")
print(f"   类型: {type(ts)}")
print(f"   tzinfo: {ts.tzinfo}")

# 转换为Python date
py_date = ts.date()
print(f"3. .date()结果: {py_date}")
print(f"   类型: {type(py_date)}")

# 测试插入数据库
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

print("\n4. 测试插入数据库...")

# 先删除测试记录（使用特殊日期2099-12-12）
test_symbol = 'IXIC'
test_insert_date = date(2099, 12, 12)

cursor.execute("DELETE FROM fishbowl_daily WHERE symbol = %s AND date = %s", (test_symbol, test_insert_date))

# 插入测试记录
insert_query = """
    INSERT INTO fishbowl_daily
        (date, symbol, close_price, ma20_price, status, deviation_pct, duration_days, signal_tag, change_pct, trend_pct)
    VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

cursor.execute(insert_query, (
    test_insert_date,  # 使用测试日期
    test_symbol,
    23195.17,
    23111.37,
    'YES',
    0.36,
    10,
    'STRONG',
    -1.69,
    5.23
))

conn.commit()

# 读取回来检查
cursor.execute("SELECT date FROM fishbowl_daily WHERE symbol = %s AND date = %s", (test_symbol, test_insert_date))
result = cursor.fetchone()

print(f"5. 数据库中读取的日期: {result[0]}")
print(f"   类型: {type(result[0])}")
print(f"   期望的日期: {test_insert_date}")
print(f"   是否一致: {result[0] == test_insert_date}")

# 检查PostgreSQL的时区设置
cursor.execute("SHOW TIMEZONE")
tz = cursor.fetchone()
print(f"\n6. PostgreSQL时区设置: {tz[0]}")

# 清理测试数据
cursor.execute("DELETE FROM fishbowl_daily WHERE symbol = %s AND date = %s", (test_symbol, test_insert_date))
conn.commit()

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("结论: 检查日期是否被PostgreSQL时区影响")
print("=" * 80)
