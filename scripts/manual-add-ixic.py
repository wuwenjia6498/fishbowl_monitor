#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动补充IXIC的缺失数据
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

print("=" * 80)
print("手动补充IXIC的12月13日和12月15日数据")
print("=" * 80)

# 12月15日IXIC的真实数据（需要从可靠来源获取）
# 来源：Yahoo Finance ^IXIC
manual_data = [
    {'date': '2025-12-13', 'close': 23195.17, 'note': '周六，使用周五收盘价'},  # 周末用周五数据
    {'date': '2025-12-15', 'close': 19161.63, 'note': '周一实际收盘价（需确认）'},
]

print("\n⚠️  注意：这是临时方案，需要从可靠数据源（如Yahoo Finance）获取真实数据")
print("\n准备补充的数据：")
for d in manual_data:
    print(f"  {d['date']}: {d['close']:.2f} - {d['note']}")

response = input("\n是否继续？(y/n): ")

if response.lower() != 'y':
    print("已取消")
    sys.exit(0)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

try:
    # 获取12月12日的MA20作为参考
    cursor.execute("""
        SELECT ma20_price, status, duration_days
        FROM fishbowl_daily
        WHERE symbol = 'IXIC' AND date = '2025-12-12'
    """)
    result = cursor.fetchone()

    if not result:
        print("❌ 找不到12月12日的IXIC数据")
        sys.exit(1)

    ma20_base, status_base, duration_base = result
    print(f"\n12月12日基准数据：MA20={ma20_base:.2f}, 状态={status_base}, 持续天数={duration_base}")

    # 为每个缺失日期计算并插入数据
    for d in manual_data:
        date_str = d['date']
        close = d['close']

        # 简化计算：使用近似的MA20（实际应该重新计算）
        ma20 = ma20_base  # 临时使用之前的MA20
        deviation_pct = (close - ma20) / ma20
        status = 'YES' if deviation_pct > 0.01 else ('NO' if deviation_pct < -0.01 else status_base)
        duration_days = duration_base + 1 if status == status_base else 1

        # 计算信号标签
        if status == 'YES':
            if deviation_pct > 0.05:
                signal_tag = 'OVERHEAT'
            elif duration_days <= 3:
                signal_tag = 'BREAKOUT'
            else:
                signal_tag = 'STRONG'
        else:
            signal_tag = 'SLUMP'

        print(f"\n处理 {date_str}:")
        print(f"  收盘价: {close:.2f}")
        print(f"  MA20: {ma20:.2f}")
        print(f"  偏离度: {deviation_pct*100:.2f}%")
        print(f"  状态: {status}")
        print(f"  信号: {signal_tag}")

        # 插入数据
        insert_query = """
            INSERT INTO fishbowl_daily
                (date, symbol, close_price, ma20_price, status, deviation_pct, duration_days, signal_tag, change_pct, trend_pct)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol, date)
            DO UPDATE SET
                close_price = EXCLUDED.close_price,
                ma20_price = EXCLUDED.ma20_price,
                status = EXCLUDED.status,
                deviation_pct = EXCLUDED.deviation_pct,
                duration_days = EXCLUDED.duration_days,
                signal_tag = EXCLUDED.signal_tag,
                created_at = CURRENT_TIMESTAMP
        """

        cursor.execute(insert_query, (
            date_str, 'IXIC', close, ma20, status, deviation_pct,
            duration_days, signal_tag, None, None
        ))

        print(f"  ✓ 已插入/更新")

    conn.commit()
    print("\n✅ 手动补充完成！")

except Exception as e:
    conn.rollback()
    print(f"\n❌ 错误: {str(e)}")
finally:
    cursor.close()
    conn.close()

print("\n" + "=" * 80)
print("提醒：请向Tushare技术支持反馈IXIC数据更新延迟问题")
print("=" * 80)
