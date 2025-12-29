#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面验证脚本：检查所有资产的颜色逻辑一致性
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

def check_all_assets():
    """检查所有资产的数据一致性"""
    base_url = os.getenv('DATABASE_URL')
    if '?' in base_url:
        connection_url = f"{base_url}&options=-c%20timezone%3DAsia/Shanghai"
    else:
        connection_url = f"{base_url}?options=-c%20timezone%3DAsia/Shanghai"

    conn = psycopg2.connect(connection_url)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # 获取所有资产的最新数据
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
        WHERE d.date = (SELECT MAX(date) FROM fishbowl_daily)
        ORDER BY c.sort_rank, c.name
    """

    cursor.execute(query)
    results = cursor.fetchall()

    print("=" * 100)
    print("全资产颜色逻辑一致性检查")
    print("=" * 100)

    inconsistent_count = 0
    precision_loss_count = 0

    for row in results:
        # 当前数据的偏离度和预期颜色
        current_deviation = float(row['deviation_pct'])
        expected_color = "红" if current_deviation > 0 else "绿" if current_deviation < 0 else "灰"

        # 检查 sparkline_data
        if row['sparkline_json']:
            sparkline_data = row['sparkline_json'] if isinstance(row['sparkline_json'], list) else json.loads(row['sparkline_json'])

            if sparkline_data:
                last_point = sparkline_data[-1]

                # Sparkline 的偏离度和实际颜色
                sparkline_price = float(last_point['price'])
                sparkline_ma20 = float(last_point['ma20'])
                sparkline_deviation = (sparkline_price - sparkline_ma20) / sparkline_ma20 if sparkline_ma20 != 0 else 0
                actual_color = "红" if sparkline_price > sparkline_ma20 else "绿" if sparkline_price < sparkline_ma20 else "灰"

                # 检查是否一致
                is_color_match = (expected_color == actual_color)

                # 检查精度损失
                deviation_diff = abs(current_deviation - sparkline_deviation)
                has_precision_loss = deviation_diff > 0.0001  # 允许0.01%的误差

                # 输出结果
                status_emoji = "✓" if is_color_match else "❌"
                precision_emoji = "⚠️" if has_precision_loss else " "

                if not is_color_match or has_precision_loss:
                    print(f"{status_emoji} {precision_emoji} {row['name']:<20} ({row['symbol']:<15}) "
                          f"偏离: {current_deviation*100:>6.2f}% → {sparkline_deviation*100:>6.2f}%  "
                          f"预期:{expected_color} 实际:{actual_color}")

                    if not is_color_match:
                        inconsistent_count += 1
                    if has_precision_loss:
                        precision_loss_count += 1

    cursor.close()
    conn.close()

    print("=" * 100)
    print(f"检查完成！")
    print(f"  - 总资产数: {len(results)}")
    print(f"  - 颜色不一致: {inconsistent_count} 个")
    print(f"  - 精度损失: {precision_loss_count} 个")

    if inconsistent_count == 0 and precision_loss_count == 0:
        print("\n🎉 所有资产颜色逻辑完全一致，无精度损失！")
    else:
        print("\n⚠️  发现问题，请检查上述资产")

    print("=" * 100)

if __name__ == "__main__":
    check_all_assets()
