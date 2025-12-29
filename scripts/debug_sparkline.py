#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本：检查 sparkline_data 与当前数据的一致性
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 设置编码
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

def check_data_consistency():
    """检查数据一致性"""
    base_url = os.getenv('DATABASE_URL')
    if '?' in base_url:
        connection_url = f"{base_url}&options=-c%20timezone%3DAsia/Shanghai"
    else:
        connection_url = f"{base_url}?options=-c%20timezone%3DAsia/Shanghai"

    conn = psycopg2.connect(connection_url)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # 获取问题资产的数据
    query = """
        SELECT
            c.name,
            d.symbol,
            d.date,
            d.close_price,
            d.ma20_price,
            d.deviation_pct,
            d.sparkline_json
        FROM fishbowl_daily d
        JOIN monitor_config c ON d.symbol = c.symbol
        WHERE d.date = '2025-12-18'
        AND c.name IN ('半导体/芯片', '芯片设计', '家电')
        ORDER BY c.name
    """

    cursor.execute(query)
    results = cursor.fetchall()

    print("=" * 80)
    print("数据一致性检查报告")
    print("=" * 80)

    for row in results:
        print(f"\n【{row['name']} ({row['symbol']})】")
        print(f"  日期: {row['date']}")
        print(f"  当前收盘价: {row['close_price']}")
        print(f"  当前MA20: {row['ma20_price']}")
        print(f"  偏离度: {row['deviation_pct']:.4f} ({row['deviation_pct']*100:.2f}%)")

        # 计算预期颜色
        expected_color = "红色" if row['deviation_pct'] > 0 else "绿色"
        print(f"  预期颜色: {expected_color}")

        # 检查 sparkline_data
        if row['sparkline_json']:
            # sparkline_json 已经是 list 类型（PostgreSQL JSONB 自动解析）
            sparkline_data = row['sparkline_json'] if isinstance(row['sparkline_json'], list) else json.loads(row['sparkline_json'])

            if sparkline_data:
                last_point = sparkline_data[-1]
                print(f"\n  Sparkline 最后一个点:")
                print(f"    日期: {last_point['date']}")
                print(f"    价格: {last_point['price']}")
                print(f"    MA20: {last_point['ma20']}")

                # 计算 sparkline 的偏离度
                sparkline_deviation = (last_point['price'] - last_point['ma20']) / last_point['ma20']
                sparkline_color = "红色" if last_point['price'] > last_point['ma20'] else "绿色"

                print(f"    偏离度: {sparkline_deviation:.4f} ({sparkline_deviation*100:.2f}%)")
                print(f"    实际颜色: {sparkline_color}")

                # 检查是否一致
                is_consistent = (
                    last_point['date'] == str(row['date']) and
                    abs(float(last_point['price']) - float(row['close_price'])) < 0.01 and
                    abs(float(last_point['ma20']) - float(row['ma20_price'])) < 0.01
                )

                if is_consistent:
                    print(f"  ✓ 数据一致")
                else:
                    print(f"  ❌ 数据不一致！")
                    print(f"     日期匹配: {last_point['date'] == str(row['date'])}")
                    print(f"     价格差异: {abs(float(last_point['price']) - float(row['close_price'])):.4f}")
                    print(f"     MA20差异: {abs(float(last_point['ma20']) - float(row['ma20_price'])):.4f}")
            else:
                print(f"  ⚠️  sparkline_data 为空")
        else:
            print(f"  ⚠️  sparkline_json 为空")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_data_consistency()
