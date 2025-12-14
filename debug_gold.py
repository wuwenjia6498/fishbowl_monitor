#!/usr/bin/env python3
"""
调试黄金数据获取问题
"""

import os
import pandas as pd
import tushare as ts
import time
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
print("调试黄金数据获取")
print("=" * 50)

# 尝试不同的黄金代码
gold_codes = [
    'XAU',          # 伦敦金
    'GC',           # COMEX黄金期货
    'AU',           # 上期所黄金期货
    'AUTD',         # 黄金T+D
    'SAU9999',      # 上海金9999
    'XAG',          # 伦敦银
    'HGCMX',        # COMEX黄金
]

for code in gold_codes:
    print(f"\n尝试代码: {code}")
    try:
        # 尝试全球指数接口
        df = pro.index_global(ts_code=code)
        if not df.empty:
            df = df.sort_values('trade_date', ascending=False)
            print(f"  [OK] 全球指数接口成功获取数据")
            print(f"     最新交易日: {df.iloc[0]['trade_date']}")
            print(f"     收盘价: {df.iloc[0]['close']}")
            print(f"     涨跌幅: {df.iloc[0].get('pct_chg', 'N/A')}%")
        else:
            print(f"  [X] 全球指数接口无数据")
            
    except Exception as e:
        print(f"  [X] 全球指数接口失败: {e}")
    
    try:
        # 尝试商品期货接口
        time.sleep(0.2)
        df = pro.fut_daily(ts_code=code)
        if not df.empty:
            df = df.sort_values('trade_date', ascending=False)
            print(f"  [OK] 期货接口成功获取数据")
            print(f"     最新交易日: {df.iloc[0]['trade_date']}")
            print(f"     收盘价: {df.iloc[0]['close']}")
            print(f"     涨跌幅: {df.iloc[0].get('pct_chg', 'N/A')}%")
        else:
            print(f"  [X] 期货接口无数据")
            
    except Exception as e:
        print(f"  [X] 期货接口失败: {e}")

# 尝试上海黄金交易所数据
print(f"\n尝试上海黄金交易所数据...")
try:
    sge_codes = ['Au99.99', 'Au100g', 'Au(T+D)']
    for code in sge_codes:
        time.sleep(0.2)
        df = pro.sge_daily(ts_code=code)
        if not df.empty:
            df = df.sort_values('trade_date', ascending=False)
            print(f"  [OK] SGE {code}: {df.iloc[0]['close']}元/克")
            break
        else:
            print(f"  [X] SGE {code}: 无数据")
except Exception as e:
    print(f"  [X] SGE接口失败: {e}")

# 检查Tushare API权限
print(f"\n检查API权限...")
try:
    # 检查积分
    df = pro.user()
    if not df.empty:
        points = df.iloc[0]['points']
        print(f"  当前积分: {points}")
        
        # 根据积分判断可能的权限
        if points >= 2000:
            print("  [OK] 积分充足，应该有权限获取国际数据")
        else:
            print("  [WARNING] 积分可能不足，可能需要升级账户获取国际数据")
    else:
        print("  [X] 无法获取积分信息")
        
except Exception as e:
    print(f"  [X] 检查积分失败: {e}")

print("\n" + "=" * 50)
print("建议解决方案:")
print("1. 如果XAU无效，可以尝试使用美股黄金ETF代码，如GLD")
print("2. 或者使用国内黄金ETF代码，如518880.SH")  
print("3. 也可以使用上海黄金交易所的现货价格")
print("=" * 50)