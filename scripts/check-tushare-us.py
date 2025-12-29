#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Tushare当前返回的US指数最新数据
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
print(f"检查Tushare当前返回的US指数最新数据 (当前时间: {datetime.now()})")
print("=" * 80)

symbols = ['IXIC', 'SPX', 'DJI']

for symbol in symbols:
    print(f"\n{'=' * 40}")
    print(f"  {symbol}")
    print('=' * 40)

    try:
        # 获取数据
        df = pro.index_global(ts_code=symbol)

        if df.empty:
            print("  ❌ 没有数据")
            continue

        # 数据清洗
        df = df.rename(columns={'trade_date': 'date'})
        df['date'] = pd.to_datetime(df['date'])
        df['close'] = pd.to_numeric(df['close'])
        df = df.sort_values('date').reset_index(drop=True)

        print(f"  总记录数: {len(df)}")
        print(f"\n  最新5条数据:")
        for idx in range(min(5, len(df))):
            row = df.iloc[-(idx+1)]
            print(f"    {row['date'].date()}: {row['close']:.2f}")

        # 取最后一行
        last_row = df.iloc[-1]
        print(f"\n  >>> 最新记录 <<<")
        print(f"  日期: {last_row['date']}")
        print(f"  date(): {last_row['date'].date()}")
        print(f"  收盘价: {last_row['close']:.2f}")
        print(f"  tzinfo: {last_row['date'].tzinfo}")

    except Exception as e:
        print(f"  ❌ 错误: {str(e)}")

print("\n" + "=" * 80)
