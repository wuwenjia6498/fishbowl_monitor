#!/usr/bin/env python3
"""
测试国际黄金数据获取
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

print("=" * 50)
print("测试国际黄金数据获取")
print("=" * 50)

# 测试不同的国际黄金代码
gold_codes = [
    ('XAUUSD', '伦敦金/美元'),
    ('GOLD', 'COMEX黄金'),
    ('GC', 'COMEX黄金期货'),
    ('XAU', '伦敦金'),
    ('GLD', 'SPDR黄金ETF'),  # 美股ETF
]

for code, desc in gold_codes:
    print(f"\n测试 {code} ({desc}):")
    
    # 尝试全球指数接口
    try:
        df = pro.index_global(ts_code=code)
        if not df.empty:
            df = df.sort_values('trade_date', ascending=False)
            latest = df.iloc[0]
            print(f"  [OK] 全球指数接口:")
            print(f"      日期: {latest['trade_date']}")
            print(f"      收盘: {latest['close']}")
            print(f"      涨跌: {latest.get('pct_chg', 'N/A')}%")
        else:
            print(f"  [X] 全球指数接口无数据")
    except Exception as e:
        print(f"  [X] 全球指数接口失败: {str(e)[:50]}")
    
    time.sleep(0.2)

# 测试美股ETF接口
print(f"\n测试美股ETF (GLD):")
try:
    df = pro.us_daily(ts_code='GLD')
    if not df.empty:
        df = df.sort_values('trade_date', ascending=False)
        latest = df.iloc[0]
        print(f"  [OK] 美股ETF接口:")
        print(f"      日期: {latest['trade_date']}")
        print(f"      收盘: ${latest['close']}")
        print(f"      涨跌: {latest.get('pct_chg', 'N/A')}%")
    else:
        print(f"  [X] 美股ETF接口无数据")
except Exception as e:
    print(f"  [X] 美股ETF接口失败: {str(e)[:50]}")

# 如果以上都不行，尝试硬编码一个示例
print(f"\n如果API都失败，使用示例数据:")
print(f"  [INFO] 使用示例数据:")
print(f"      国际金价: $2,650.50 (+0.85%)")
print(f"      数据来源: 可考虑使用其他金融API")

print("\n" + "=" * 50)