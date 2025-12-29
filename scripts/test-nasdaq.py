#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Tushare获取纳斯达克指数数据
"""

import os
import sys
import tushare as ts
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 设置标准输出编码为UTF-8
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

token = os.getenv('TUSHARE_TOKEN')
if not token:
    print("错误: 未设置TUSHARE_TOKEN")
    exit(1)

ts.set_token(token)
pro = ts.pro_api()

print("=" * 80)
print("测试获取纳斯达克指数数据")
print("=" * 80)

# 测试不同的代码
test_codes = ['IXIC', 'NDX', 'NASDAQ']

for code in test_codes:
    print(f"\n测试代码: {code}")
    print("-" * 80)

    try:
        # 获取最近10天的数据
        df = pro.index_global(ts_code=code)

        if df.empty:
            print(f"  没有数据")
        else:
            # 按日期降序排列
            df = df.sort_values('trade_date', ascending=False)
            print(f"  成功获取 {len(df)} 条记录")
            print(f"\n  最近5个交易日:")
            for idx, row in df.head(5).iterrows():
                print(f"    {row['trade_date']}: 收盘 {row['close']:.2f}, 涨跌幅 {row.get('pct_chg', 0):.2f}%")

    except Exception as e:
        print(f"  错误: {str(e)}")

print("\n" + "=" * 80)
print("结论: 检查哪个代码能获取到最新数据")
print("=" * 80)
