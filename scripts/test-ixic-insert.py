#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际插入IXIC数据到数据库
"""

import os
import sys
import pandas as pd
import tushare as ts
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from datetime import datetime, date

# 设置UTF-8编码
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
token = os.getenv('TUSHARE_TOKEN')
ts.set_token(token)
pro = ts.pro_api()

print("=" * 80)
print("测试实际插入IXIC数据到数据库")
print("=" * 80)

# 获取IXIC数据
print("\n1. 从Tushare获取IXIC数据")
df = pro.index_global(ts_code='IXIC')

# 数据清洗
df = df.rename(columns={'trade_date': 'date'})
df['date'] = pd.to_datetime(df['date'])
df['close'] = pd.to_numeric(df['close'])
df = df.sort_values('date').reset_index(drop=True)

# 取最后一行
last_row = df.iloc[-1]
py_date = last_row['date'].date() if hasattr(last_row['date'], 'date') else last_row['date']

print(f"   最新数据:")
print(f"   - 日期: {py_date}")
print(f"   - 收盘价: {last_row['close']}")

# 连接数据库
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# 先删除测试符号的记录
test_symbol = 'IXIC_TEST'
cursor.execute("DELETE FROM fishbowl_daily WHERE symbol = %s", (test_symbol,))
conn.commit()

print(f"\n2. 插入测试数据 (symbol={test_symbol})")

# 使用execute_values插入（模拟ETL的batch_upsert_daily_data）
insert_query = """
    INSERT INTO fishbowl_daily
        (date, symbol, close_price, ma20_price, status, deviation_pct, duration_days, signal_tag, change_pct, trend_pct)
    VALUES %s
    ON CONFLICT (symbol, date)
    DO UPDATE SET
        close_price = EXCLUDED.close_price,
        ma20_price = EXCLUDED.ma20_price,
        status = EXCLUDED.status,
        deviation_pct = EXCLUDED.deviation_pct,
        duration_days = EXCLUDED.duration_days,
        signal_tag = EXCLUDED.signal_tag,
        change_pct = EXCLUDED.change_pct,
        trend_pct = EXCLUDED.trend_pct,
        created_at = CURRENT_TIMESTAMP
"""

# 先在配置表中添加测试符号
cursor.execute("""
    INSERT INTO monitor_config (symbol, name, category, is_active, sort_rank, source_type)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (symbol) DO NOTHING
""", (test_symbol, '测试纳指100', 'broad', True, 999, 'global'))
conn.commit()

values = [(
    py_date,
    test_symbol,
    float(last_row['close']),
    float(last_row['close']),
    'YES',
    0.0,
    1,
    'STRONG',
    -1.69,
    5.23
)]

print(f"   准备插入的数据:")
print(f"   - date: {values[0][0]} (type: {type(values[0][0])})")
print(f"   - symbol: {values[0][1]}")
print(f"   - close: {values[0][2]}")

execute_values(cursor, insert_query, values)
conn.commit()

print(f"\n3. 读取数据库中的记录")
cursor.execute("SELECT date, close_price, created_at FROM fishbowl_daily WHERE symbol = %s", (test_symbol,))
result = cursor.fetchone()

if result:
    print(f"   - 数据库日期: {result[0]} (type: {type(result[0])})")
    print(f"   - 收盘价: {result[1]}")
    print(f"   - 创建时间: {result[2]}")
    print(f"\n   比较:")
    print(f"   - 期望日期: {py_date}")
    print(f"   - 实际日期: {result[0]}")
    print(f"   - 是否一致: {result[0] == py_date}")

    if result[0] != py_date:
        diff = (py_date - result[0]).days
        print(f"   - 日期差异: {diff} 天")
else:
    print("   ❌ 没有找到记录")

# 清理
cursor.execute("DELETE FROM fishbowl_daily WHERE symbol = %s", (test_symbol,))
cursor.execute("DELETE FROM monitor_config WHERE symbol = %s", (test_symbol,))
conn.commit()

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("结论: 检查使用execute_values时日期是否正确")
print("=" * 80)
