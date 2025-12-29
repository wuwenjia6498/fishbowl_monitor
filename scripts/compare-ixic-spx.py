#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细对比IXIC和SPX的Tushare数据
"""

import os
import sys
import tushare as ts
import pandas as pd
from dotenv import load_dotenv

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

token = os.getenv('TUSHARE_TOKEN')
ts.set_token(token)
pro = ts.pro_api()

print("=" * 80)
print("详细对比 IXIC 和 SPX 的 Tushare 数据")
print("=" * 80)

symbols = ['IXIC', 'SPX']

for symbol in symbols:
    print(f"\n{'=' * 40}")
    print(f"  {symbol}")
    print('=' * 40)

    try:
        # 获取原始数据
        df = pro.index_global(ts_code=symbol)

        if df.empty:
            print("  ❌ 没有数据")
            continue

        print(f"  总记录数: {len(df)}")

        # 按日期降序
        df = df.sort_values('trade_date', ascending=False)

        print(f"\n  最新10条数据:")
        for idx, row in df.head(10).iterrows():
            print(f"    {row['trade_date']}: 收盘={row['close']:.2f}, 成交量={row.get('vol', 'N/A')}, 成交额={row.get('amount', 'N/A')}")

        # 检查最新日期
        latest_date = df.iloc[0]['trade_date']
        print(f"\n  >>> 最新交易日: {latest_date}")

        # 检查是否有12月13-15日的数据
        df['date'] = pd.to_datetime(df['trade_date'])
        has_1213 = not df[df['date'] == '2025-12-13'].empty
        has_1214 = not df[df['date'] == '2025-12-14'].empty
        has_1215 = not df[df['date'] == '2025-12-15'].empty

        print(f"  12月13日(周六): {'有数据' if has_1213 else '无数据'}")
        print(f"  12月14日(周日): {'有数据' if has_1214 else '无数据'}")
        print(f"  12月15日(周一): {'有数据' if has_1215 else '无数据'}")

    except Exception as e:
        print(f"  ❌ 错误: {str(e)}")

print("\n" + "=" * 80)
print("结论分析")
print("=" * 80)
print("如果SPX有12月15日数据而IXIC没有，这是Tushare数据源的问题")
print("建议：")
print("1. 检查Tushare是否有其他纳斯达克代码可用")
print("2. 联系Tushare技术支持反馈IXIC数据更新延迟问题")
print("3. 临时使用yfinance作为IXIC的备用数据源")
print("=" * 80)
