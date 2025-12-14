#!/usr/bin/env python3
"""
获取真实的国际黄金价格数据
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

print("=" * 60)
print("获取真实国际黄金价格")
print("=" * 60)

# 方法1: 获取GLD ETF数据
print("\n方法1: SPDR黄金ETF (GLD)")
try:
    df = pro.us_daily(ts_code='GLD')
    if not df.empty:
        df = df.sort_values('trade_date', ascending=False)
        latest = df.iloc[0]
        print(f"  日期: {latest['trade_date']}")
        print(f"  GLD收盘价: ${latest['close']}")
        print(f"  GLD成交量: {latest['vol']}")
        
        # GLD与黄金的比例关系约为1:10（GLD约等于1/10盎司黄金）
        estimated_gold_price = float(latest['close']) * 10
        print(f"  估算金价: ${estimated_gold_price:.2f}/盎司")
        
        # 更准确的比例：GLD代表0.1盎司黄金
        more_accurate_price = float(latest['close']) / 0.1
        print(f"  准确估算: ${more_accurate_price:.2f}/盎司")
    else:
        print("  无数据")
except Exception as e:
    print(f"  失败: {e}")

time.sleep(0.5)

# 方法2: 尝试国际黄金现货数据
print("\n方法2: 国际黄金现货数据")
try:
    # 尝试不同的黄金代码
    codes = ['XAU', 'GOLD', 'XAUUSD', 'GC', 'HGCMX']
    
    for code in codes:
        try:
            df = pro.index_global(ts_code=code)
            if not df.empty:
                df = df.sort_values('trade_date', ascending=False)
                latest = df.iloc[0]
                print(f"  {code}: ${latest['close']} (日期: {latest['trade_date']})")
                print(f"        涨跌幅: {latest.get('pct_chg', 'N/A')}%")
                break
            else:
                print(f"  {code}: 无数据")
        except:
            print(f"  {code}: 失败")
        time.sleep(0.2)
            
except Exception as e:
    print(f"  失败: {e}")

# 方法3: 尝试商品期货数据
print("\n方法3: COMEX黄金期货")
try:
    # COMEX黄金期货代码
    futures_codes = ['GC', 'GCMX', 'HGCMX']
    
    for code in futures_codes:
        try:
            df = pro.fut_daily(ts_code=code)
            if not df.empty:
                df = df.sort_values('trade_date', ascending=False)
                latest = df.iloc[0]
                print(f"  {code}: ${latest['close']} (日期: {latest['trade_date']})")
                print(f"        涨跌幅: {latest.get('pct_chg', 'N/A')}%")
                break
            else:
                print(f"  {code}: 无数据")
        except:
            print(f"  {code}: 失败")
        time.sleep(0.2)
            
except Exception as e:
    print(f"  失败: {e}")

# 方法4: 尝试上海黄金交易所（作为参考）
print("\n方法4: 上海黄金交易所（参考）")
try:
    sge_codes = ['Au99.99', 'Au(T+D)']
    
    for code in sge_codes:
        try:
            df = pro.sge_daily(ts_code=code)
            if not df.empty:
                df = df.sort_values('trade_date', ascending=False)
                latest = df.iloc[0]
                print(f"  {code}: {latest['close']}元/克")
                
                # 转换为美元/盎司（汇率按7.2，1盎司=31.1克）
                usd_per_ounce = float(latest['close']) * 7.2 * 31.1 / 1000
                print(f"        转换后: ${usd_per_ounce:.2f}/盎司")
                break
            else:
                print(f"  {code}: 无数据")
        except:
            print(f"  {code}: 失败")
        time.sleep(0.2)
            
except Exception as e:
    print(f"  失败: {e}")

print("\n" + "=" * 60)
print("建议:")
print("1. 如果GLD数据可用，使用 accurate_price = close / 0.1")
print("2. 或者使用多个数据源交叉验证")
print("3. 考虑添加实时汇率转换")
print("=" * 60)