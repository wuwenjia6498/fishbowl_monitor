#!/usr/bin/env python3
"""
分析GLD与黄金价格的正确换算关系
"""

import os
import pandas as pd
import tushare as ts
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化Tushare
token = os.getenv('TUSHARE_TOKEN')
if not token:
    raise ValueError("环境变量 TUSHARE_TOKEN 未设置")

ts.set_token(token)
pro = ts.pro_api()

print("=" * 60)
print("分析GLD与黄金价格换算关系")
print("=" * 60)

# 获取GLD当前价格
print("获取GLD价格:")
try:
    df = pro.us_daily(ts_code='GLD')
    if not df.empty:
        df = df.sort_values('trade_date', ascending=False)
        latest = df.iloc[0]
        gld_price = float(latest['close'])
        print(f"  GLD收盘价: ${gld_price}")
    else:
        print("  无GLD数据")
        exit()
except Exception as e:
    print(f"  获取GLD失败: {e}")
    exit()

# 根据当前金价分析换算系数
current_market_price = 4300  # 当前市场黄金价格
conversion_factor = current_market_price / gld_price

print(f"\n换算分析:")
print(f"  假设当前金价: ${current_market_price}/盎司")
print(f"  GLD价格: ${gld_price}")
print(f"  计算换算系数: {current_market_price} / {gld_price} = {conversion_factor:.2f}")

# 验证不同换算系数的效果
print(f"\n不同换算系数的效果:")
factors = [10, 2.65, conversion_factor]
for factor in factors:
    calculated_price = gld_price * factor
    print(f"  换算系数 {factor:.2f}: ${calculated_price:.2f}/盎司")

print(f"\n建议使用换算系数: {conversion_factor:.2f}")

# 分析GLD的规格
print(f"\nGLD规格分析:")
print(f"  GLD每份代表黄金: 0.1盎司")
print(f"  理论换算系数: 10")
print(f"  实际换算系数: {conversion_factor:.2f}")
print(f"  差异原因: 管理费用、跟踪误差、市场溢价等因素")

print("=" * 60)