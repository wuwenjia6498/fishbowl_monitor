#!/usr/bin/env python3
"""
获取真实的国际黄金价格
使用多种数据源进行对比
"""

import os
import requests
import json
from datetime import datetime

# 获取当前黄金价格
def get_current_gold_price():
    """尝试从多个免费API获取当前黄金价格"""
    
    prices = {}
    
    # 方法1: 使用freegoldprice API
    try:
        url = "https://api.freegoldprice.org/latest/USD"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            price = float(data.get('price', 0))
            prices['freegoldprice'] = price
            print(f"✓ FreeGoldPrice API: ${price:.2f}/盎司")
    except Exception as e:
        print(f"✗ FreeGoldPrice API 失败: {e}")
    
    # 方法2: 使用metals-api API
    try:
        url = "https://api.metals.live/v1/spot/gold"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            price = float(data.get('price', 0))
            prices['metals_api'] = price
            print(f"✓ Metals API: ${price:.2f}/盎司")
    except Exception as e:
        print(f"✗ Metals API 失败: {e}")
    
    # 方法3: 使用JSONVat API
    try:
        url = "https://api.jsonvat.com/"
        # 这个API可能不提供黄金价格，我们可以尝试其他方法
        pass
    except:
        pass
    
    # 方法4: 使用固定值作为参考（基于当前市场情况的合理估算）
    # 根据2025年1月的黄金市场情况，合理价格范围
    reasonable_price = 2650.0  # 2025年初的合理黄金价格估算
    prices['estimated'] = reasonable_price
    print(f"✓ 基于市场估算: ${reasonable_price:.2f}/盎司")
    
    return prices

if __name__ == "__main__":
    print("=" * 50)
    print("获取真实国际黄金价格")
    print("=" * 50)
    print(f"查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    prices = get_current_gold_price()
    
    if prices:
        print("\n" + "=" * 50)
        print("价格汇总:")
        for source, price in prices.items():
            print(f"  {source}: ${price:.2f}/盎司")
        
        # 计算平均价格（排除估算值）
        real_prices = [p for s, p in prices.items() if s != 'estimated']
        if real_prices:
            avg_price = sum(real_prices) / len(real_prices)
            print(f"\n平均价格: ${avg_price:.2f}/盎司")
        
        print("=" * 50)
    else:
        print("\n无法获取黄金价格，使用默认值: $2650.00/盎司")