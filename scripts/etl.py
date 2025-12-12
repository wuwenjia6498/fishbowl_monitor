#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鱼盆趋势雷达 - ETL 每日更新脚本 v4.4 (指数+ETF混合双轨)
功能：
1. 宽基大势：获取原生指数数据 (使用 index_daily)
2. 行业轮动：获取 ETF 日线数据 (使用 fund_daily + qfq 前复权)
3. 计算鱼盆信号（20日均线策略）
4. 按 sort_rank 排序，保证固定顺序
5. 只处理 is_active=true 或 is_system_bench=true 的资产
"""

import os
import sys
import pandas as pd
import tushare as ts
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv
import time

# 设置标准输出编码为UTF-8（解决Windows编码问题）
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
        self.connection_url = os.getenv('DATABASE_URL')
        if not self.connection_url:
            raise ValueError("环境变量 DATABASE_URL 未设置")

    def get_connection(self):
        """获取数据库连接"""
        try:
            return psycopg2.connect(self.connection_url)
        except Exception as e:
            print(f"数据库连接失败: {str(e)}")
            raise

    def query_data(self, sql: str, params: tuple = None) -> List[Dict]:
        """执行查询并返回数据"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return results
        except Exception as e:
            print(f"查询操作失败: {str(e)}")
            return []


# ================================================
# Tushare 数据获取器
# ================================================
class DataFetcher:
    """数据获取器，使用Tushare API获取指数数据"""

    def __init__(self):
        self.token = os.getenv('TUSHARE_TOKEN')
        if not self.token:
            raise ValueError("环境变量 TUSHARE_TOKEN 未设置")
        ts.set_token(self.token)
        self.pro = ts.pro_api()

    def get_index_daily_data(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """
        获取指数日线数据 (用于宽基指数)
        使用index_daily接口
        """
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

            # 指数数据
            df = self.pro.index_daily(ts_code=symbol, start_date=start_date, end_date=end_date)
            time.sleep(0.35)

            if df.empty:
                print(f"  ⚠️  警告: 没有获取到指数 {symbol} 的数据")
                return pd.DataFrame()

            # 按日期升序排列
            df = df.sort_values('trade_date').reset_index(drop=True)
            df['date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')

            return df[['date', 'close']]

        except Exception as e:
            print(f"  ❌ 获取指数 {symbol} 数据时出错: {str(e)}")
            return pd.DataFrame()

    def get_etf_daily_data(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """
        获取ETF日线数据
        使用fund_daily接口 + 前复权(qfq)消除分红缺口

        Args:
            symbol: 代码，格式如 '512480.SH' (ETF)
            days: 获取最近N天的数据

        Returns:
            DataFrame 包含日期和收盘价数据
        """
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

            # 所有ETF统一使用fund_daily接口，必须使用前复权
            df = self.pro.fund_daily(ts_code=symbol, start_date=start_date, end_date=end_date, adj='qfq')
            time.sleep(0.35)

            if df.empty:
                print(f"  ⚠️  警告: 没有获取到 {symbol} 的数据")
                return pd.DataFrame()

            # 按日期升序排列
            df = df.sort_values('trade_date').reset_index(drop=True)
            df['date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')

            return df[['date', 'close']]

        except Exception as e:
            print(f"  ❌ 获取 {symbol} 数据时出错: {str(e)}")
            return pd.DataFrame()


# ================================================
# 鱼盆趋势计算器
# ================================================
class FishbowlCalculator:
    """鱼盆趋势计算器，实现20日均线策略"""

    @staticmethod
    def calculate_all_metrics(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有鱼盆指标：MA20、状态、偏离度、持续天数、信号标签
        """
        if df.empty:
            return df

        df = df.copy()

        # 1. 计算MA20
        df['ma20_price'] = df['close'].rolling(window=20, min_periods=1).mean()

        # 2. 计算状态（±1%缓冲带逻辑）
        statuses = []
        durations = []

        for i in range(len(df)):
            close = df.loc[i, 'close']
            ma20 = df.loc[i, 'ma20_price']
            deviation = (close - ma20) / ma20

            if i == 0:
                # 第一天初始化
                status = 'YES' if deviation > 0.01 else 'NO'
                duration = 1
            else:
                prev_status = statuses[-1]
                prev_duration = durations[-1]

                if deviation > 0.01:
                    # 突破上轨
                    status = 'YES'
                    duration = 1 if prev_status != 'YES' else prev_duration + 1
                elif deviation < -0.01:
                    # 跌破下轨
                    status = 'NO'
                    duration = 1 if prev_status != 'NO' else prev_duration + 1
                else:
                    # 缓冲带内，维持原状态
                    status = prev_status
                    duration = prev_duration + 1

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

            # 回溯到状态起始点 (i - duration + 1)
            start_index = i - duration + 1

            if start_index >= 0:
                # 可以追溯到起始点
                start_price = df.loc[start_index, 'close']
                trend_pct = (current_close - start_price) / start_price
            else:
                # 无法追溯（数据不够），设为 None
                trend_pct = None

            trend_pcts.append(trend_pct)

        df['trend_pct'] = trend_pcts

        # 6. 生成信号标签
        signal_tags = []
        for _, row in df.iterrows():
            status = row['status']
            duration = row['duration_days']
            deviation = row['deviation_pct']

            if status == 'YES':
                if duration <= 3:
                    tag = 'BREAKOUT'
                elif deviation > 0.15:
                    tag = 'OVERHEAT'
                else:
                    tag = 'STRONG'
            else:  # NO
                if deviation < -0.15:
                    tag = 'EXTREME_BEAR'
                else:
                    tag = 'SLUMP'

            signal_tags.append(tag)

        df['signal_tag'] = signal_tags

        return df


# ================================================
# 主ETL流程
# ================================================
def process_symbol(symbol: str, name: str, category: str, fetcher: DataFetcher) -> Optional[pd.DataFrame]:
    """
    处理单个ETF/指数：获取数据 -> 计算指标

    Args:
        symbol: 代码
        name: 名称
        category: 类别 (用于判断调用哪个接口)
        fetcher: 数据获取器
    """
    try:
        print(f"  处理: {name} ({symbol}) [{category}]")

        # 根据类别选择获取数据的方法
        if category in ['宽基', 'broad']:
            df = fetcher.get_index_daily_data(symbol)
        else:
            df = fetcher.get_etf_daily_data(symbol)
            
        if df.empty:
            return None

        # 计算指标
        df = FishbowlCalculator.calculate_all_metrics(df)

        # 添加symbol列
        df['symbol'] = symbol

        # 返回最新一天
        return df.iloc[[-1]]

    except Exception as e:
        print(f"  ❌ 处理 {symbol} 时出错: {str(e)}")
        return None


def batch_upsert_daily_data(conn, data_list: List[Dict]):
    """批量插入/更新每日数据"""
    if not data_list:
        return

    cursor = conn.cursor()

    insert_query = """
        INSERT INTO fishbowl_daily
            (date, symbol, close_price, ma20_price, status, deviation_pct, duration_days, signal_tag, change_pct, trend_pct)
        VALUES %s
        ON CONFLICT (symbol, date)
        DO UPDATE SET
            close_price = EXCLUDED.close_price,
            ma20_price = EXCLUDED.ma20_price,
            status = EXCLUDED.status,
            deviation_pct = EXCLUDED.deviation_pct,
            duration_days = EXCLUDED.duration_days,
            signal_tag = EXCLUDED.signal_tag,
            change_pct = EXCLUDED.change_pct,
            trend_pct = EXCLUDED.trend_pct,
            created_at = CURRENT_TIMESTAMP
    """

    values = [
        (
            d['date'], d['symbol'], d['close_price'], d['ma20_price'],
            d['status'], d['deviation_pct'], d['duration_days'], d['signal_tag'],
            d['change_pct'], d['trend_pct']
        )
        for d in data_list
    ]

    execute_values(cursor, insert_query, values)
    conn.commit()
    cursor.close()


def update_sort_rankings(conn, date):
    """更新固定排序（按配置的sort_rank排序）"""
    cursor = conn.cursor()

    # 按配置的sort_rank更新trend_rank，保持固定顺序
    update_query = """
        UPDATE fishbowl_daily
        SET trend_rank = c.sort_rank
        FROM monitor_config c
        WHERE fishbowl_daily.symbol = c.symbol
          AND fishbowl_daily.date = %s
          AND c.sort_rank IS NOT NULL
    """

    cursor.execute(update_query, (date,))
    conn.commit()
    cursor.close()


def main():
    """主执行函数"""
    print("=" * 60)
    print("鱼盆趋势雷达 - ETL 更新 v4.4 (指数+ETF混合双轨)")
    print("=" * 60)

    try:
        # 初始化连接
        db_conn = DatabaseConnection()
        fetcher = DataFetcher()

        # 获取所有需要更新的资产（按sort_rank排序）
        query = """
            SELECT symbol, name, category, sort_rank
            FROM monitor_config
            WHERE is_active = true OR is_system_bench = true
            ORDER BY sort_rank ASC, symbol
        """
        assets = db_conn.query_data(query)

        if not assets:
            print("❌ 没有找到需要更新的资产")
            return

        print(f"\n✓ 找到 {len(assets)} 个需要更新的资产")
        print("-" * 60)

        # 批量处理
        all_results = []
        success_count = 0

        for asset in assets:
            result_df = process_symbol(asset['symbol'], asset['name'], asset['category'], fetcher)
            if result_df is not None:
                all_results.append(result_df)
                success_count += 1

        if not all_results:
            print("\n❌ 没有成功获取任何数据")
            return

        # 合并所有结果
        final_df = pd.concat(all_results, ignore_index=True)

        # 转换为字典列表
        data_list = []
        for _, row in final_df.iterrows():
            data_list.append({
                'date': row['date'].date(),
                'symbol': row['symbol'],
                'close_price': float(row['close']),
                'ma20_price': float(row['ma20_price']),
                'status': row['status'],
                'deviation_pct': float(row['deviation_pct']),
                'duration_days': int(row['duration_days']),
                'signal_tag': row['signal_tag'],
                'change_pct': float(row['change_pct']) if pd.notna(row['change_pct']) else None,
                'trend_pct': float(row['trend_pct']) if pd.notna(row['trend_pct']) else None
            })

        # 批量入库
        conn = db_conn.get_connection()
        batch_upsert_daily_data(conn, data_list)
        print(f"\n✓ 批量入库成功: {len(data_list)} 条记录")

        # 更新固定排序
        latest_date = final_df['date'].max().date()
        update_sort_rankings(conn, latest_date)
        print(f"✓ 更新固定排序完成: {latest_date}")

        conn.close()

        # 输出摘要
        yes_count = len([d for d in data_list if d['status'] == 'YES'])
        no_count = len([d for d in data_list if d['status'] == 'NO'])

        print("\n" + "=" * 60)
        print("ETL 更新完成！")
        print(f"  - 成功处理: {success_count}/{len(assets)} 个资产")
        print(f"  - 多头 (YES): {yes_count}")
        print(f"  - 空头 (NO): {no_count}")
        print(f"  - 最新日期: {latest_date}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ETL 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
