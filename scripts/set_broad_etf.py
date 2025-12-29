#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宽基指数 ETF 映射设置脚本
功能：为宽基指数设置对应的龙头ETF
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

# 宽基指数 -> 龙头ETF 映射
BROAD_ETF_MAPPING = {
    # 上证指数和深证成指：无对应ETF（综合指数，不可交易）
    '000001.SH': None,      # 上证指数
    '399001.SZ': None,      # 深证成指
    
    # 其他宽基指数：有对应ETF产品
    '000300.SH': '510300',  # 沪深300 -> 沪深300ETF
    '000905.SH': '510500',  # 中证500 -> 中证500ETF
    '000852.SH': '512100',  # 中证1000 -> 中证1000ETF
    '399006.SZ': '159915',  # 创业板指 -> 创业板ETF
    '000016.SH': '510050',  # 上证50 -> 上证50ETF
    '399005.SZ': '159902',  # 中小100 -> 中小板ETF
    '000688.SH': '588000',  # 科创50 -> 科创50ETF
}


def get_db_connection():
    """连接到 Supabase PostgreSQL"""
    connection_string = os.getenv('DATABASE_URL')
    if not connection_string:
        raise ValueError("环境变量 DATABASE_URL 未设置")
    
    return psycopg2.connect(connection_string)


def set_broad_etf():
    """设置宽基指数的 ETF 映射"""
    print("=" * 60)
    print("宽基指数 ETF 映射设置")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n正在设置宽基指数的 ETF 映射...")
        
        updated_count = 0
        for symbol, etf_code in BROAD_ETF_MAPPING.items():
            # 检查指数是否存在
            cursor.execute("""
                SELECT name FROM monitor_config WHERE symbol = %s
            """, (symbol,))
            
            result = cursor.fetchone()
            if result:
                name = result[0]
                
                # 更新 ETF 映射
                cursor.execute("""
                    UPDATE monitor_config 
                    SET dominant_etf = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE symbol = %s
                """, (etf_code, symbol))
                
                etf_display = etf_code if etf_code else "无"
                print(f"  ✓ {name:12} ({symbol:12}) -> ETF: {etf_display}")
                updated_count += 1
            else:
                print(f"  ⚠ 指数不存在: {symbol}")
        
        conn.commit()
        
        print(f"\n✓ 成功更新 {updated_count} 个宽基指数的 ETF 映射")
        
        # 验证结果
        print("\n" + "=" * 60)
        print("验证结果：")
        print("=" * 60)
        
        cursor.execute("""
            SELECT symbol, name, dominant_etf 
            FROM monitor_config 
            WHERE category = 'broad'
            ORDER BY symbol
        """)
        
        broad_indices = cursor.fetchall()
        
        print("\n宽基指数 ETF 映射列表：")
        print("-" * 60)
        for symbol, name, etf in broad_indices:
            etf_display = etf if etf else "无（综合指数）"
            print(f"  {name:12} ({symbol:12}) | ETF: {etf_display}")
        
        print("\n" + "=" * 60)
        print("设置完成！")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    set_broad_etf()









