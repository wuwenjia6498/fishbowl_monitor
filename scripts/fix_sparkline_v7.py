#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v7.0 修复脚本：重新初始化所有资产的 sparkline_json
适用场景：数据库中 sparkline_json 为空或数据不足
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from etl import DatabaseConnection, DataFetcher, FishbowlCalculator
import pandas as pd

def fix_sparkline():
    """重新初始化所有资产的 sparkline_json"""
    print("=" * 60)
    print("v7.0 Sparkline 修复脚本")
    print("=" * 60)
    
    db_conn = DatabaseConnection()
    fetcher = DataFetcher()
    
    # 1. 获取所有需要修复的资产
    query = """
        SELECT symbol, name, category
        FROM monitor_config
        WHERE is_active = true OR is_system_bench = true
        ORDER BY sort_rank
    """
    assets = db_conn.query_data(query)
    
    print(f"\n找到 {len(assets)} 个资产需要检查\n")
    
    # 2. 逐个检查并修复
    conn = db_conn.get_connection()
    cursor = conn.cursor()
    
    fixed_count = 0
    skipped_count = 0
    failed_count = 0
    
    for asset in assets:
        symbol = asset['symbol']
        name = asset['name']
        category = asset['category']
        
        print(f"处理: {name} ({symbol})")
        
        # 检查是否需要修复
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN sparkline_json IS NULL THEN 0
                    ELSE json_array_length(sparkline_json::json)
                END as point_count
            FROM fishbowl_daily
            WHERE symbol = %s
            ORDER BY date DESC
            LIMIT 1
        """, (symbol,))
        
        result = cursor.fetchone()
        if result and result[0] > 20:  # 只有超过20个点才跳过（确保有足够数据）
            print(f"  ✓ 已有 {result[0]} 个数据点，跳过\n")
            skipped_count += 1
            continue
        elif result and result[0] > 0:
            print(f"  ⚠️  仅有 {result[0]} 个数据点（不足），需要重新初始化")
        
        # 需要修复：获取历史数据并生成 sparkline
        try:
            print(f"  🔄 获取历史数据...")
            df = fetcher.fetch_history(symbol, category)
            
            if df.empty:
                print(f"  ⚠️  无法获取历史数据，跳过\n")
                failed_count += 1
                continue
            
            # 计算指标
            df = FishbowlCalculator.calculate_all_metrics(df)
            print(f"  📊 获取到 {len(df)} 天的历史数据")
            
            # 生成 sparkline
            if len(df) > 0:
                last_row = df.iloc[-1]
                date_str = last_row['date'].strftime('%Y-%m-%d') if hasattr(last_row['date'], 'strftime') else str(last_row['date'])
                
                sparkline_json = FishbowlCalculator.generate_sparkline_json(
                    df,
                    days=250,
                    today_date=date_str,
                    today_price=float(last_row['close']),
                    today_ma20=float(last_row['ma20_price'])
                )
                
                # 更新数据库
                cursor.execute("""
                    UPDATE fishbowl_daily
                    SET sparkline_json = %s::jsonb
                    WHERE symbol = %s
                      AND date = (SELECT MAX(date) FROM fishbowl_daily WHERE symbol = %s)
                """, (sparkline_json, symbol, symbol))
                
                conn.commit()
                print(f"  ✅ 修复成功，生成 sparkline\n")
                fixed_count += 1
            else:
                print(f"  ⚠️  数据不足，跳过\n")
                failed_count += 1
                
        except Exception as e:
            print(f"  ❌ 修复失败: {str(e)}\n")
            failed_count += 1
            continue
    
    cursor.close()
    conn.close()
    
    # 3. 输出统计
    print("=" * 60)
    print("修复完成！")
    print(f"  总计: {len(assets)} 个资产")
    print(f"  修复: {fixed_count} 个")
    print(f"  跳过: {skipped_count} 个（已有数据）")
    print(f"  失败: {failed_count} 个")
    print("=" * 60)

if __name__ == '__main__':
    fix_sparkline()

