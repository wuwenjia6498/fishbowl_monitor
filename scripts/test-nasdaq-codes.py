#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同的纳斯达克代码
"""

import os
import sys
import tushare as ts
from dotenv import load_dotenv

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

token = os.getenv('TUSHARE_TOKEN')
ts.set_token(token)
pro = ts.pro_api()

print("=" * 80)
print("测试不同的纳斯达克代码")
print("=" * 80)

# 测试不同的纳斯达克相关代码
test_codes = [
    'IXIC',      # 纳斯达克综合指数
    'NDX',       # 纳斯达克100指数
    'COMP',      # Nasdaq Composite
]

for code in test_codes:
    print(f"\n{'=' * 40}")
    print(f"  代码: {code}")
    print('=' * 40)

    try:
        df = pro.index_global(ts_code=code)

        if df.empty:
            print("  ❌ 没有数据")
        else:
            # 按日期降序
            df = df.sort_values('trade_date', ascending=False)
            print(f"  ✓ 总记录数: {len(df)}")
            print(f"\n  最新5条数据:")
            for idx, row in df.head(5).iterrows():
                print(f"    {row['trade_date']}: 收盘 {row['close']:.2f}")

    except Exception as e:
        print(f"  ❌ 错误: {str(e)}")

print("\n" + "=" * 80)
