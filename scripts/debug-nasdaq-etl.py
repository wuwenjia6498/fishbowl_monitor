#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试纳指100数据处理流程
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
print("调试纳指100数据处理流程")
print("=" * 80)

# 获取原始数据
print("\n1. 获取Tushare原始数据")
print("-" * 80)
df = pro.index_global(ts_code='IXIC')
print(f"获取到 {len(df)} 条记录")
print("\n最近5条原始数据：")
print(df.head(5)[['trade_date', 'close']])

# 数据清洗
print("\n2. 数据清洗和转换")
print("-" * 80)
df = df.rename(columns={'trade_date': 'date'})
df['date'] = pd.to_datetime(df['date'])
df['close'] = pd.to_numeric(df['close'])
df = df.sort_values('date').reset_index(drop=True)

print("转换后的最新5条数据：")
print(df.tail(5)[['date', 'close']])

# 计算MA20
print("\n3. 计算MA20")
print("-" * 80)
df['ma20_price'] = df['close'].rolling(window=20, min_periods=1).mean()

# 计算偏离度和状态
print("\n4. 计算状态")
print("-" * 80)

statuses = []
for i in range(len(df)):
    close = df.loc[i, 'close']
    ma20 = df.loc[i, 'ma20_price']
    deviation = (close - ma20) / ma20

    if i == 0:
        status = 'YES' if deviation > 0.01 else 'NO'
    else:
        prev_status = statuses[-1]
        if deviation > 0.01:
            status = 'YES'
        elif deviation < -0.01:
            status = 'NO'
        else:
            status = prev_status

    statuses.append(status)

df['status'] = statuses

# 显示最后一行（将入库的数据）
print("最后一行数据（将入库）：")
last_row = df.iloc[-1]
print(f"  日期: {last_row['date']}")
print(f"  类型: {type(last_row['date'])}")
print(f"  date(): {last_row['date'].date() if hasattr(last_row['date'], 'date') else last_row['date']}")
print(f"  收盘价: {last_row['close']}")
print(f"  MA20: {last_row['ma20_price']:.2f}")
print(f"  状态: {last_row['status']}")

print("\n" + "=" * 80)
print("结论: 检查日期处理是否正确")
print("=" * 80)
