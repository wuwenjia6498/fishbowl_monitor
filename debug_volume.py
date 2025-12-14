#!/usr/bin/env python3
"""
调试成交额数据问题
"""

import os
import pandas as pd
import tushare as ts
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化Tushare
token = os.getenv('TUSHARE_TOKEN')
if not token:
    raise ValueError("环境变量 TUSHARE_TOKEN 未设置")

ts.set_token(token)
pro = ts.pro_api()

print("=" * 50)
print("调试成交额数据问题")
print("=" * 50)

# 获取最新交易日
today = datetime.now().strftime('%Y%m%d')
print(f"查询日期: {today}")

# 获取上证指数数据
print("\n上证指数 (000001.SH):")
try:
    sh_df = pro.index_daily(ts_code='000001.SH', start_date='20251210', end_date=today)
    if not sh_df.empty:
        sh_df = sh_df.sort_values('trade_date', ascending=False)
        print(f"  最新交易日: {sh_df.iloc[0]['trade_date']}")
        print(f"  收盘点位: {sh_df.iloc[0]['close']}")
        print(f"  成交量(手): {sh_df.iloc[0]['vol']}")
        print(f"  成交额(千元): {sh_df.iloc[0]['amount']}")
        print(f"  成交额(亿元): {sh_df.iloc[0]['amount'] / 100000:.2f}")
        print(f"  涨跌幅(%): {sh_df.iloc[0]['pct_chg']}")
        
        # 显示最近5天数据
        print("\n  最近5天成交额:")
        for i in range(min(5, len(sh_df))):
            row = sh_df.iloc[i]
            print(f"    {row['trade_date']}: {row['amount'] / 100000:.1f}亿元")
            
        # 计算5日均值
        if len(sh_df) >= 5:
            avg_5d = sh_df.head(5)['amount'].sum() / 5 / 100000
            print(f"\n  5日均量: {avg_5d:.1f}亿元")
    else:
        print("  X 未获取到数据")
        
except Exception as e:
    print(f"  X 获取失败: {e}")

# 获取深证成指数据
print("\n深证成指 (399001.SZ):")
try:
    sz_df = pro.index_daily(ts_code='399001.SZ', start_date='20251210', end_date=today)
    if not sz_df.empty:
        sz_df = sz_df.sort_values('trade_date', ascending=False)
        print(f"  最新交易日: {sz_df.iloc[0]['trade_date']}")
        print(f"  收盘点位: {sz_df.iloc[0]['close']}")
        print(f"  成交量(手): {sz_df.iloc[0]['vol']}")
        print(f"  成交额(千元): {sz_df.iloc[0]['amount']}")
        print(f"  成交额(亿元): {sz_df.iloc[0]['amount'] / 100000:.2f}")
        print(f"  涨跌幅(%): {sz_df.iloc[0]['pct_chg']}")
    else:
        print("  X 未获取到数据")
        
except Exception as e:
    print(f"  X 获取失败: {e}")

# 计算两市总成交额
print("\n两市总成交额:")
try:
    if not sh_df.empty and not sz_df.empty:
        sh_amount = sh_df.iloc[0]['amount']
        sz_amount = sz_df.iloc[0]['amount']
        total_amount = sh_amount + sz_amount
        total_yi = total_amount / 100000  # 千元转亿元
        
        print(f"  上证成交额: {sh_amount / 100000:.1f}亿元")
        print(f"  深证成交额: {sz_amount / 100000:.1f}亿元")
        print(f"  两市总成交: {total_yi:.1f}亿元")
        
        if total_yi < 100:
            print("  [WARNING] 成交额异常低！可能原因:")
            print("    1. 非交易日")
            print("    2. Tushare API权限问题")
            print("    3. 数据源问题")
        elif total_yi < 3000:
            print("  [WARNING] 成交额偏低")
        else:
            print("  [OK] 成交额正常")
    else:
        print("  X 数据不完整")
        
except Exception as e:
    print(f"  X 计算失败: {e}")

print("\n" + "=" * 50)