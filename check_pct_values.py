#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查数据库中百分比字段的实际存储值"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from lib import db_conn

def check_percentage_values():
    """查询数据库中的百分比字段实际值"""
    conn = db_conn.get_connection()
    cursor = conn.cursor()
    
    # 查询最近的几条数据
    query = """
        SELECT 
            symbol,
            date,
            close_price,
            trend_pct,
            change_pct,
            deviation_pct
        FROM fishbowl_daily
        WHERE trend_pct IS NOT NULL
        ORDER BY date DESC
        LIMIT 10;
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print("=" * 80)
    print("数据库中百分比字段的实际存储值检查")
    print("=" * 80)
    print()
    print(f"{'Symbol':<12} {'Date':<12} {'Close':<10} {'trend_pct':<15} {'change_pct':<15} {'deviation_pct':<15}")
    print("-" * 80)
    
    for row in rows:
        symbol, date, close, trend, change, deviation = row
        print(f"{symbol:<12} {str(date):<12} {close:<10.2f} {trend if trend else 'NULL':<15} {change if change else 'NULL':<15} {deviation:<15.6f}")
    
    print()
    print("=" * 80)
    print("结论说明:")
    print("=" * 80)
    print("1. 如果 trend_pct 值是 0.01 左右 → 表示1%，前端需要 *100")
    print("2. 如果 trend_pct 值是 1 左右 → 表示1%，前端不需要 *100")
    print()
    print("从 ETL 计算公式: trend_pct = (current_price - start_price) / start_price")
    print("这是标准的小数形式，0.01 = 1%，所以前端 formatPercentage 需要 *100 ✓")
    print("=" * 80)
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    check_percentage_values()






