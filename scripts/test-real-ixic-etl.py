#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际IXIC数据的ETL流程
"""

import os
import sys
import pandas as pd
import tushare as ts
from dotenv import load_dotenv
from datetime import datetime

# 设置UTF-8编码
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

token = os.getenv('TUSHARE_TOKEN')
ts.set_token(token)
pro = ts.pro_api()

print("=" * 80)
print("测试实际IXIC数据的ETL流程")
print("=" * 80)

# 获取IXIC数据
print("\n1. 从Tushare获取IXIC数据")
df = pro.index_global(ts_code='IXIC')

print(f"   获取到 {len(df)} 条记录")
print("\n   最近3条原始数据:")
print(df.head(3)[['trade_date', 'close']])

# 数据清洗（模拟ETL）
print("\n2. 数据清洗和转换")
df = df.rename(columns={'trade_date': 'date'})
print(f"   date列转换前的类型: {type(df['date'].iloc[0])}")
print(f"   date列转换前的值: {df['date'].iloc[0]}")

df['date'] = pd.to_datetime(df['date'])
print(f"   date列转换后的类型: {type(df['date'].iloc[0])}")
print(f"   date列转换后的值: {df['date'].iloc[0]}")
print(f"   date列转换后的tzinfo: {df['date'].iloc[0].tzinfo}")

df['close'] = pd.to_numeric(df['close'])
df = df.sort_values('date').reset_index(drop=True)

print("\n   转换后最新3条数据:")
print(df.tail(3)[['date', 'close']])

# 取最后一行
last_row = df.iloc[-1]
print("\n3. 最后一行数据（将入库）")
print(f"   date: {last_row['date']}")
print(f"   类型: {type(last_row['date'])}")
print(f"   tzinfo: {last_row['date'].tzinfo}")
print(f"   收盘价: {last_row['close']}")

# 转换为Python date
py_date = last_row['date'].date() if hasattr(last_row['date'], 'date') else last_row['date']
print(f"\n4. 转换为Python date")
print(f"   py_date: {py_date}")
print(f"   类型: {type(py_date)}")

# 检查ISO格式
print(f"\n5. ISO格式")
print(f"   isoformat(): {py_date.isoformat()}")
print(f"   str(): {str(py_date)}")
print(f"   repr(): {repr(py_date)}")

print("\n" + "=" * 80)
print("结论: 检查date对象的所有属性")
print("=" * 80)
