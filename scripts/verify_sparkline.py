#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 v6.9 sparkline 修复效果"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from etl import DatabaseConnection
import json

def verify_sparkline_data():
    """验证 sparkline_json 数据完整性"""
    db_conn = DatabaseConnection()
    conn = db_conn.get_connection()
    cursor = conn.cursor()

    # 检查最新日期的 sparkline 数据
    query = """
        SELECT
            symbol,
            date,
            CASE
                WHEN sparkline_json IS NULL THEN 0
                ELSE json_array_length(sparkline_json::json)
            END as point_count,
            CASE
                WHEN sparkline_json IS NOT NULL AND json_array_length(sparkline_json::json) > 0
                THEN sparkline_json::json->-1->>'date'
                ELSE NULL
            END as last_date
        FROM fishbowl_daily
        WHERE date = (SELECT MAX(date) FROM fishbowl_daily)
        ORDER BY symbol;
    """

    cursor.execute(query)
    results = cursor.fetchall()

    print('\n🔍 v6.9 Sparkline 数据验证结果:')
    print('=' * 90)
    print(f"{'符号':<18} {'记录日期':<15} {'数据点数':<10} {'最后日期':<15} {'状态':<10}")
    print('-' * 90)

    total = 0
    success = 0
    failed = 0

    latest_date_str = str(results[0][1]) if results else 'N/A'
    
    for row in results:
        symbol, date, point_count, last_date = row
        total += 1

        # 判断状态
        if point_count > 1 and last_date == latest_date_str:
            status = '✅ 正常'
            success += 1
        elif point_count == 0:
            status = '❌ 为空'
            failed += 1
        elif last_date != latest_date_str:
            status = '⚠️  日期旧'
            failed += 1
        else:
            status = '⚠️  数据少'
            failed += 1

        print(f"{symbol:<18} {str(date):<15} {point_count:<10} {last_date or 'N/A':<15} {status:<10}")

    print('=' * 90)
    print(f'\n📊 统计:')
    print(f'  总数: {total}')
    print(f'  正常: {success} ({success/total*100:.1f}%)' if total > 0 else '  正常: 0')
    print(f'  异常: {failed} ({failed/total*100:.1f}%)' if total > 0 else '  异常: 0')

    # 随机抽查一条完整数据
    if results:
        latest_date_str = str(results[0][1])
        print(f'\n🔬 随机抽查一条完整数据: {results[0][0]}')
        query_detail = """
            SELECT sparkline_json
            FROM fishbowl_daily
            WHERE symbol = %s AND date = (SELECT MAX(date) FROM fishbowl_daily)
        """
        cursor.execute(query_detail, (results[0][0],))
        sparkline_raw = cursor.fetchone()[0]

        if sparkline_raw:
            # PostgreSQL 的 JSON 类型会返回 Python 对象，不需要 json.loads
            if isinstance(sparkline_raw, str):
                sparkline_data = json.loads(sparkline_raw)
            else:
                sparkline_data = sparkline_raw

            print(f'  数据点总数: {len(sparkline_data)}')
            if len(sparkline_data) > 0:
                print(f'  第一个点: {sparkline_data[0]}')
                print(f'  最后一个点: {sparkline_data[-1]}')

                # 验证今日数据是否存在
                if sparkline_data[-1]['date'] == latest_date_str:
                    print(f'  ✅ 确认包含最新日期数据: {latest_date_str}')
                else:
                    print(f'  ⚠️  最后日期: {sparkline_data[-1]["date"]}（最新日期: {latest_date_str}）')
            else:
                print('  ⚠️  数据数组为空')
        else:
            print('  ❌ sparkline_json 为空')

    cursor.close()
    conn.close()

if __name__ == '__main__':
    verify_sparkline_data()
