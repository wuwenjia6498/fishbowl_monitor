#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证脚本：检查修改效果
功能：
1. 验证宽基指数无 ETF 映射
2. 验证行业指数有正确的 ETF 映射
3. 输出示例数据供前端测试
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# 设置标准输出编码为UTF-8（解决Windows编码问题）
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# 加载环境变量
load_dotenv()


def get_db_connection():
    """连接到 Supabase PostgreSQL"""
    connection_string = os.getenv('DATABASE_URL')
    if not connection_string:
        raise ValueError("环境变量 DATABASE_URL 未设置")
    
    return psycopg2.connect(connection_string)


def verify_changes():
    """验证修改效果"""
    print("=" * 80)
    print("验证修改效果：UI 细节优化与数据清洗")
    print("=" * 80)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. 检查宽基指数
        print("\n【1】宽基指数检查")
        print("-" * 80)
        cursor.execute("""
            SELECT symbol, name, dominant_etf, is_active
            FROM monitor_config 
            WHERE category = 'broad'
            ORDER BY symbol
        """)
        
        broad_indices = cursor.fetchall()
        print(f"共 {len(broad_indices)} 个宽基指数：\n")
        
        broad_with_etf = []
        for symbol, name, etf, is_active in broad_indices:
            status = "✓" if etf is None else "✗"
            etf_display = etf if etf else "无"
            active_display = "激活" if is_active else "未激活"
            print(f"  {status} {name:12} ({symbol:12}) | ETF: {etf_display:8} | {active_display}")
            
            if etf is not None:
                broad_with_etf.append((symbol, name, etf))
        
        if broad_with_etf:
            print(f"\n⚠️  发现 {len(broad_with_etf)} 个宽基指数仍有 ETF 映射（需要清理）")
        else:
            print("\n✓ 所有宽基指数的 ETF 映射均为空，数据正确！")
        
        # 2. 检查行业指数（有 ETF 映射的）
        print("\n【2】行业指数 ETF 映射检查")
        print("-" * 80)
        cursor.execute("""
            SELECT symbol, name, dominant_etf, industry_level, is_active
            FROM monitor_config 
            WHERE category = 'industry' AND dominant_etf IS NOT NULL
            ORDER BY industry_level, name
            LIMIT 20
        """)
        
        industry_with_etf = cursor.fetchall()
        print(f"共 {len(industry_with_etf)} 个行业指数有 ETF 映射（显示前20个）：\n")
        
        for symbol, name, etf, level, is_active in industry_with_etf:
            active_display = "激活" if is_active else "未激活"
            print(f"  [{level}] {name:15} ({symbol}) | ETF: {etf} | {active_display}")
        
        # 3. 统计汇总
        print("\n【3】数据统计汇总")
        print("-" * 80)
        
        cursor.execute("SELECT COUNT(*) FROM monitor_config WHERE category='broad'")
        broad_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM monitor_config WHERE category='broad' AND dominant_etf IS NOT NULL")
        broad_with_etf_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM monitor_config WHERE category='industry'")
        industry_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM monitor_config WHERE category='industry' AND dominant_etf IS NOT NULL")
        industry_with_etf_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM monitor_config WHERE is_active=true")
        active_count = cursor.fetchone()[0]
        
        print(f"  宽基指数总数:        {broad_count}")
        print(f"  宽基指数有ETF:       {broad_with_etf_count} {'✓ 正确' if broad_with_etf_count == 0 else '✗ 需要清理'}")
        print(f"  行业指数总数:        {industry_count}")
        print(f"  行业指数有ETF:       {industry_with_etf_count}")
        print(f"  激活监控总数:        {active_count}")
        
        # 4. 获取最新交易日数据示例
        print("\n【4】最新交易日数据示例")
        print("-" * 80)
        
        cursor.execute("""
            SELECT MAX(date) FROM fishbowl_daily
        """)
        latest_date = cursor.fetchone()[0]
        
        if latest_date:
            print(f"最新交易日: {latest_date}\n")
            
            # 宽基指数示例
            cursor.execute("""
                SELECT 
                    mc.name, 
                    fd.symbol, 
                    fd.close_price, 
                    fd.ma20_price, 
                    fd.status,
                    fd.deviation_pct,
                    mc.dominant_etf
                FROM fishbowl_daily fd
                JOIN monitor_config mc ON fd.symbol = mc.symbol
                WHERE fd.date = %s AND mc.category = 'broad'
                ORDER BY mc.symbol
                LIMIT 5
            """, (latest_date,))
            
            broad_data = cursor.fetchall()
            
            if broad_data:
                print("宽基指数示例数据：")
                for name, symbol, close, ma20, status, dev, etf in broad_data:
                    etf_display = etf if etf else "-"
                    print(f"  {name:12} | 价格: {close:8.2f} | MA20: {ma20:8.2f} | 状态: {status:3} | 偏离: {dev:6.2%} | ETF: {etf_display}")
            
            # 行业指数示例（有ETF的）
            cursor.execute("""
                SELECT 
                    mc.name, 
                    fd.symbol, 
                    fd.close_price, 
                    fd.ma20_price, 
                    fd.status,
                    fd.deviation_pct,
                    mc.dominant_etf,
                    fd.signal_tag
                FROM fishbowl_daily fd
                JOIN monitor_config mc ON fd.symbol = mc.symbol
                WHERE fd.date = %s AND mc.category = 'industry' AND mc.dominant_etf IS NOT NULL
                ORDER BY fd.trend_rank
                LIMIT 5
            """, (latest_date,))
            
            industry_data = cursor.fetchall()
            
            if industry_data:
                print("\n行业指数示例数据（有ETF映射）：")
                for name, symbol, close, ma20, status, dev, etf, signal in industry_data:
                    signal_display = signal if signal else "-"
                    print(f"  {name:15} | 价格: {close:8.2f} | MA20: {ma20:8.2f} | 状态: {status:3} | 偏离: {dev:6.2%} | ETF: {etf} | 信号: {signal_display}")
        else:
            print("暂无交易日数据")
        
        print("\n" + "=" * 80)
        print("验证完成！")
        print("=" * 80)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    verify_changes()









