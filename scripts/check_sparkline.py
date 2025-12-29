#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临时脚本：检查数据库中的 sparkline_json 数据
"""
import os
import psycopg2
from dotenv import load_dotenv
import json

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

# 检查上证50的数据
print("=" * 60)
print("检查上证50 (000001.SH) 的 sparkline_json 数据")
print("=" * 60)

cursor.execute("""
    SELECT date, symbol, 
           CASE 
               WHEN sparkline_json IS NULL THEN 'NULL'
               ELSE LENGTH(sparkline_json::text)::text || ' 字符'
           END as json_length,
           LEFT(sparkline_json::text, 200) as json_preview
    FROM fishbowl_daily 
    WHERE symbol = '000001.SH'
    ORDER BY date DESC 
    LIMIT 5
""")

rows = cursor.fetchall()
print(f"\n找到 {len(rows)} 条记录:\n")

for row in rows:
    date, symbol, json_length, json_preview = row
    print(f"日期: {date}")
    print(f"  JSON长度: {json_length}")
    print(f"  JSON预览: {json_preview}")
    print()

# 检查所有资产的 sparkline_json 状态
print("\n" + "=" * 60)
print("所有资产的 sparkline_json 状态")
print("=" * 60)

cursor.execute("""
    SELECT 
        c.name,
        d.symbol,
        d.date,
        CASE 
            WHEN d.sparkline_json IS NULL THEN '❌ NULL'
            WHEN d.sparkline_json::text = '[]' THEN '⚠️ 空数组'
            ELSE '✅ 有数据 (' || (LENGTH(d.sparkline_json::text) / 50)::text || ' 条记录)'
        END as status
    FROM fishbowl_daily d
    JOIN monitor_config c ON d.symbol = c.symbol
    WHERE d.date = (SELECT MAX(date) FROM fishbowl_daily)
    ORDER BY c.sort_rank
    LIMIT 15
""")

rows = cursor.fetchall()
print(f"\n最新日期的资产状态:\n")

for row in rows:
    name, symbol, date, status = row
    print(f"{name:12} ({symbol:12}): {status}")

cursor.close()
conn.close()

