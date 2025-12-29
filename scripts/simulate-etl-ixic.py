#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟ETL处理IXIC的完整流程
"""

import os
import sys
import pandas as pd
import tushare as ts
from dotenv import load_dotenv

# 设置UTF-8编码
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

token = os.getenv('TUSHARE_TOKEN')
ts.set_token(token)
pro = ts.pro_api()

print("=" * 80)
print("模拟ETL处理IXIC的完整流程")
print("=" * 80)

symbol = 'IXIC'

# 步骤1: 获取原始数据
print(f"\n1. 获取{symbol}原始数据")
df = pro.index_global(ts_code=symbol)
print(f"   获取到 {len(df)} 条记录")
print(f"   原始最新3条:")
for i in range(min(3, len(df))):
    print(f"     {df.iloc[i]['trade_date']}: {df.iloc[i]['close']}")

# 步骤2: 数据清洗（模拟fetch_history）
print(f"\n2. 数据清洗（fetch_history逻辑）")
df = df.rename(columns={'trade_date': 'date'})
df['date'] = pd.to_datetime(df['date'])
df['close'] = pd.to_numeric(df['close'])
df = df.sort_values('date').reset_index(drop=True)
df = df[['date', 'close']]

print(f"   清洗后最新3条:")
for i in range(min(3, len(df))):
    idx = -(i+1)
    print(f"     [{len(df)+idx}] {df.iloc[idx]['date'].date()}: {df.iloc[idx]['close']}")

# 步骤3: 计算MA20（简化版）
print(f"\n3. 计算指标（calculate_all_metrics简化）")
df['ma20_price'] = df['close'].rolling(window=20, min_periods=1).mean()
df['symbol'] = symbol

# 计算状态（简化，只看最后几行）
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

print(f"   计算完成，最新3条:")
for i in range(min(3, len(df))):
    idx = -(i+1)
    row = df.iloc[idx]
    print(f"     [{len(df)+idx}] {row['date'].date()}: close={row['close']:.2f}, ma20={row['ma20_price']:.2f}, status={row['status']}")

# 步骤4: 取最后一行（模拟ETL line 778）
print(f"\n4. 取最后一行（df.iloc[-1]）")
last_row = df.iloc[-1]
print(f"   索引: {df.index[-1]}")
print(f"   日期: {last_row['date']}")
print(f"   date(): {last_row['date'].date()}")
print(f"   收盘价: {last_row['close']:.2f}")
print(f"   MA20: {last_row['ma20_price']:.2f}")
print(f"   状态: {last_row['status']}")

# 检查DataFrame的长度和索引
print(f"\n5. DataFrame信息")
print(f"   len(df): {len(df)}")
print(f"   df.index[-1]: {df.index[-1]}")
print(f"   df.index[-2]: {df.index[-2]}")
print(f"   最后一行的日期: {df.iloc[-1]['date'].date()}")
print(f"   倒数第二行的日期: {df.iloc[-2]['date'].date()}")

print("\n" + "=" * 80)
print("结论: 检查iloc[-1]是否真的取到了最新的数据")
print("=" * 80)
