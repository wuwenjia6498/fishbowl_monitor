#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鱼盆趋势雷达 - 数据库历史数据重算脚本 (v6.3 System Audit)
功能：
1. 读取数据库中现有的历史 close_price 数据
2. 按照新的"真理标准"重新计算 MA20、Status、Deviation
3. 更新回数据库，修复历史遗留的脏数据

使用方法：
    python scripts/recalculate_history.py --confirm  # 自动确认
    python scripts/recalculate_history.py            # 交互式确认
"""

import os
import sys
import argparse
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

# 设置标准输出编码为UTF-8
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# 加载环境变量
load_dotenv()


# ================================================
# 数据库连接管理
# ================================================
class DatabaseConnection:
    """数据库连接管理"""

    def __init__(self):
        base_url = os.getenv('DATABASE_URL')
        if not base_url:
            raise ValueError("环境变量 DATABASE_URL 未设置")

        if '?' in base_url:
            self.connection_url = f"{base_url}&options=-c%20timezone%3DAsia/Shanghai"
        else:
            self.connection_url = f"{base_url}?options=-c%20timezone%3DAsia/Shanghai"

    def get_connection(self):
        """获取数据库连接"""
        try:
            return psycopg2.connect(self.connection_url)
        except Exception as e:
            print(f"数据库连接失败: {str(e)}")
            raise


# ================================================
# 鱼盆趋势计算器 (v6.3 标准算法)
# ================================================
class FishbowlCalculator:
    """鱼盆趋势计算器，实现20日均线策略 + ±1% 缓冲带"""

    @staticmethod
    def calculate_all_metrics(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有鱼盆指标：MA20、状态、偏离度、持续天数
        v6.3 System Audit: 严格遵守 ±1% 缓冲带逻辑
        """
        if df.empty:
            return df

        df = df.copy()

        # 1. 计算MA20
        df['ma20_price'] = df['close'].rolling(window=20, min_periods=1).mean()

        # 2. 计算状态 (v6.3 System Audit: 实现严格的 ±1% 缓冲带逻辑)
        # Rule of Truth (The Constitution):
        # - Close > MA20 * 1.01 → YES (突破缓冲带上沿)
        # - Close < MA20 * 0.99 → NO  (跌破缓冲带下沿)
        # - 在 ±1% 区间内   → 维持昨日状态 (防止震荡)
        # - 第一天无历史状态时: Close >= MA20 → YES, 否则 → NO
        statuses = []
        durations = []

        for i in range(len(df)):
            close = df.loc[i, 'close']
            ma20 = df.loc[i, 'ma20_price']

            # 计算缓冲带边界
            upper_band = ma20 * 1.01  # 上沿: MA20 + 1%
            lower_band = ma20 * 0.99  # 下沿: MA20 - 1%

            if i == 0:
                # 第一天初始化：无历史状态，简单判断
                status = 'YES' if close >= ma20 else 'NO'
                duration = 1
            else:
                prev_status = statuses[-1]
                prev_duration = durations[-1]

                # 应用缓冲带逻辑
                if close > upper_band:
                    # 突破上沿 → 强制多头
                    status = 'YES'
                elif close < lower_band:
                    # 跌破下沿 → 强制空头
                    status = 'NO'
                else:
                    # 在缓冲带内 → 维持昨日状态（防震荡）
                    status = prev_status

                # 计算持续天数
                duration = 1 if prev_status != status else prev_duration + 1

            statuses.append(status)
            durations.append(duration)

        df['status'] = statuses
        df['duration_days'] = durations

        # 3. 计算偏离度
        df['deviation_pct'] = (df['close'] - df['ma20_price']) / df['ma20_price']

        # 4. 计算当日涨幅 (change_pct)
        df['change_pct'] = df['close'].pct_change()

        # 5. 计算区间涨幅 (trend_pct) - 从当前状态起始点到现在的涨幅
        trend_pcts = []
        for i in range(len(df)):
            duration = df.loc[i, 'duration_days']
            current_close = df.loc[i, 'close']

            # 回溯到状态起始点的前一天（变盘前一天）
            start_index = i - duration

            if start_index >= 0:
                start_price = df.loc[start_index, 'close']
                trend_pct = (current_close - start_price) / start_price
            else:
                trend_pct = None

            trend_pcts.append(trend_pct)

        df['trend_pct'] = trend_pcts

        # 6. 生成信号标签 (v6.3: 基于偏离度判断)
        signal_tags = []
        for _, row in df.iterrows():
            status = row['status']
            duration = row['duration_days']
            deviation = row['deviation_pct']

            # 核心修复：信号判断完全基于当前偏离度
            if deviation > 0:
                # 偏离度为正 → 多头信号
                if duration <= 3 and status == 'YES':
                    tag = 'BREAKOUT'  # 启动（刚突破且持续天数短）
                elif deviation > 0.15:
                    tag = 'OVERHEAT'  # 过热（偏离度>15%）
                else:
                    tag = 'STRONG'    # 主升（稳健上涨）
            else:
                # 偏离度为负或零 → 空头信号
                if deviation < -0.15:
                    tag = 'EXTREME_BEAR'  # 超跌（偏离度<-15%）
                else:
                    tag = 'SLUMP'         # 弱势（下跌或震荡）

            signal_tags.append(tag)

        df['signal_tag'] = signal_tags

        return df


# ================================================
# 重算主流程
# ================================================
def recalculate_symbol_history(conn, symbol: str, name: str) -> int:
    """
    重算单个标的的历史数据

    Args:
        conn: 数据库连接
        symbol: 标的代码
        name: 标的名称

    Returns:
        更新的记录数
    """
    try:
        print(f"\n  处理: {name} ({symbol})")

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 1. 从数据库读取该标的的所有历史数据（按日期升序）
        query = """
            SELECT date, close_price
            FROM fishbowl_daily
            WHERE symbol = %s
            ORDER BY date ASC
        """
        cursor.execute(query, (symbol,))
        results = cursor.fetchall()

        if not results:
            print(f"    ⚠️  没有历史数据")
            cursor.close()
            return 0

        # 2. 转换为DataFrame并进行类型转换
        df = pd.DataFrame(results)
        df['date'] = pd.to_datetime(df['date'])
        df = df.rename(columns={'close_price': 'close'})
        # 关键修复：将 Decimal 类型转换为 float，避免 pandas 运算错误
        df['close'] = df['close'].astype(float)

        print(f"    📊 读取 {len(df)} 条历史记录")

        # 3. 重新计算所有指标
        df = FishbowlCalculator.calculate_all_metrics(df)

        # 4. 批量更新回数据库
        update_query = """
            UPDATE fishbowl_daily
            SET
                ma20_price = %s,
                status = %s,
                deviation_pct = %s,
                duration_days = %s,
                signal_tag = %s,
                change_pct = %s,
                trend_pct = %s,
                created_at = CURRENT_TIMESTAMP
            WHERE symbol = %s AND date = %s
        """

        update_count = 0
        for _, row in df.iterrows():
            cursor.execute(update_query, (
                float(row['ma20_price']),
                row['status'],
                float(row['deviation_pct']),
                int(row['duration_days']),
                row['signal_tag'],
                float(row['change_pct']) if pd.notna(row['change_pct']) else None,
                float(row['trend_pct']) if pd.notna(row['trend_pct']) else None,
                symbol,
                row['date'].strftime('%Y-%m-%d')
            ))
            update_count += 1

        conn.commit()
        cursor.close()

        print(f"    ✓ 成功更新 {update_count} 条记录")
        return update_count

    except Exception as e:
        print(f"    ❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    """主执行函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='重新计算鱼盆历史数据')
    parser.add_argument('--confirm', action='store_true', help='自动确认,跳过交互式提示')
    args = parser.parse_args()

    print("=" * 60)
    print("鱼盆趋势雷达 - 历史数据重算 (v6.3 System Audit)")
    print("=" * 60)
    print("\n⚠️  警告: 此操作将重新计算并覆盖数据库中的所有历史指标数据！")
    print("    包括: MA20、Status、Deviation、Duration、Signal Tag\n")

    # 确认操作
    if not args.confirm:
        confirm = input("确认继续？(输入 YES 继续): ")
        if confirm != "YES":
            print("\n❌ 操作已取消")
            return
    else:
        print("✓ 自动确认模式已启用\n")

    try:
        # 初始化连接
        db_conn = DatabaseConnection()
        conn = db_conn.get_connection()

        # 获取所有需要重算的标的
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT DISTINCT symbol, name
            FROM monitor_config
            WHERE is_active = true OR is_system_bench = true
            ORDER BY symbol
        """
        cursor.execute(query)
        assets = cursor.fetchall()
        cursor.close()

        if not assets:
            print("\n❌ 没有找到需要重算的标的")
            conn.close()
            return

        print(f"\n✓ 找到 {len(assets)} 个标的需要重算")
        print("-" * 60)

        # 逐个处理
        total_updates = 0
        success_count = 0

        for asset in assets:
            updated = recalculate_symbol_history(conn, asset['symbol'], asset['name'])
            if updated > 0:
                total_updates += updated
                success_count += 1

        conn.close()

        # 输出摘要
        print("\n" + "=" * 60)
        print("重算完成！")
        print(f"  - 处理成功: {success_count}/{len(assets)} 个标的")
        print(f"  - 更新记录: {total_updates} 条")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 重算失败: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
