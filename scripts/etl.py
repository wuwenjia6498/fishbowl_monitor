#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鱼盆趋势雷达 - ETL 每日更新脚本 v7.0 (增量追加模式 - Stability Upgrade)
功能：
1. 宽基大势：获取原生指数 + 全球指数 + 贵金属现货数据
2. 行业轮动：获取 ETF 日线数据 (使用 fund_daily + qfq 前复权)
3. 多接口路由：index_daily(A股) + index_global(全球) + sge_daily(贵金属)
4. 计算鱼盆信号（20日均线策略）
5. 按 sort_rank 排序，保证固定顺序
6. 只处理 is_active=true 或 is_system_bench=true 的资产
7. [v5.8] 生成全景战术驾驶舱数据：A股基准、美股风向、避险资产、领涨先锋
8. [NEW v7.0] 趋势图增量追加模式：
   - 从数据库读取已有 sparkline_json
   - 只追加今日数据点，避免每日全量拉取历史数据
   - 自动去重、滑动窗口裁剪（保持最近250天）
   - 只在首次初始化时调用 Tushare 历史接口
   - 极大提升稳定性，减少对外部 API 的依赖
"""

import os
import sys
import pandas as pd
import tushare as ts
import yfinance as yf  # v6.4: 用于获取实时美股指数数据
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv
import time
import json

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
        base_url = os.getenv('DATABASE_URL')
        if not base_url:
            raise ValueError("环境变量 DATABASE_URL 未设置")

        # 设置时区为Asia/Shanghai，确保DATE字段不被时区转换
        # URL编码：空格=%20, =/=%3D
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

    def get_existing_sparkline(self, symbol: str) -> Optional[str]:
        """
        v7.0: 从数据库获取指定标的的现有 sparkline_json 数据

        Args:
            symbol: 标的代码

        Returns:
            sparkline_json 字符串，如果不存在则返回 None
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 查询该标的最新的 sparkline_json
            query = """
                SELECT sparkline_json 
                FROM fishbowl_daily 
                WHERE symbol = %s 
                  AND sparkline_json IS NOT NULL
                ORDER BY date DESC 
                LIMIT 1
            """
            cursor.execute(query, (symbol,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result and result[0]:
                return result[0]
            return None
            
        except Exception as e:
            print(f"  ⚠️  读取 {symbol} 的 sparkline 失败: {str(e)}")
            return None


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

    def get_us_index_data_yfinance(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """
        v6.4: 使用 yfinance 获取美股指数数据（解决 Tushare 数据滞后问题）

        Args:
            symbol: Tushare 代码（如 IXIC, SPX, DJI）
            days: 获取最近N天的数据

        Returns:
            DataFrame 包含日期和收盘价数据
        """
        # Tushare 代码映射到 Yahoo Finance 代码
        symbol_mapping = {
            'IXIC': '^IXIC',   # 纳斯达克综合指数
            'NDX': '^NDX',     # 纳斯达克100指数
            'SPX': '^GSPC',    # 标普500
            'DJI': '^DJI',     # 道琼斯工业平均指数
        }

        yahoo_symbol = symbol_mapping.get(symbol)
        if not yahoo_symbol:
            print(f"  ⚠️  未找到 {symbol} 的 Yahoo Finance 映射")
            return pd.DataFrame()

        try:
            print(f"  🇺🇸 使用 yfinance 获取美股数据: {symbol} -> {yahoo_symbol}")

            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 使用 yfinance 获取数据
            ticker = yf.Ticker(yahoo_symbol)
            df = ticker.history(start=start_date, end=end_date)

            if df.empty:
                print(f"  ⚠️  yfinance 未返回数据: {yahoo_symbol}")
                return pd.DataFrame()

            # 数据清洗：转换为标准格式 ['date', 'close']
            df = df.reset_index()
            df = df.rename(columns={'Date': 'date', 'Close': 'close'})

            # 只保留需要的列
            df = df[['date', 'close']].copy()

            # 确保日期格式正确
            df['date'] = pd.to_datetime(df['date'])

            # 按日期升序排列
            df = df.sort_values('date').reset_index(drop=True)

            print(f"  ✓ yfinance 成功获取 {len(df)} 条数据，最新日期: {df['date'].iloc[-1].strftime('%Y-%m-%d')}")

            return df

        except Exception as e:
            print(f"  ⚠️  yfinance 获取失败: {str(e)}")
            return pd.DataFrame()

    def fetch_history(self, symbol: str, category: str) -> pd.DataFrame:
        """
        多接口路由：根据资产类型自动选择对应的数据接口
        v5.3: 支持 A股指数 + 全球指数 + 贵金属现货
        v6.4: 美股指数优先使用 yfinance（解决 Tushare 数据滞后问题）
        """
        try:
            # 1. 行业轮动 -> 基金接口 (ETF)
            if category == 'industry':
                return self.get_etf_daily_data(symbol)

            # 2. 宽基大势 -> 混合接口路由
            # A. 贵金属 (代码特征: Au, Ag 开头) -> 上海金交所接口
            if symbol.startswith('Au') or symbol.startswith('Ag'):
                print(f"  🔸 使用贵金属接口: {symbol}")
                df = self.pro.sge_daily(ts_code=symbol)
                time.sleep(0.35)

            # B. 美股指数 -> 优先使用 yfinance，失败时回退到 Tushare
            elif symbol in ['IXIC', 'SPX', 'DJI', 'NDX']:
                # 尝试使用 yfinance（实时数据）
                df = self.get_us_index_data_yfinance(symbol)

                # 如果 yfinance 失败，回退到 Tushare（可能滞后）
                # v6.5 注意: NDX (纳指100) Tushare 不支持，只能依赖 yfinance
                if df.empty:
                    # NDX 不支持 Tushare 回退（Tushare 只有 IXIC 综合指数）
                    if symbol == 'NDX':
                        print(f"  ⚠️  yfinance 失败且 Tushare 不支持 {symbol}，跳过本次更新")
                        return pd.DataFrame()

                    # 其他美股指数可以回退到 Tushare
                    print(f"  🔄 yfinance 失败，回退到 Tushare 接口: {symbol}")
                    df = self.pro.index_global(ts_code=symbol)
                    time.sleep(0.35)

                    # 对于 Tushare 数据，需要进行格式转换
                    if not df.empty:
                        if 'trade_date' in df.columns:
                            df = df.rename(columns={'trade_date': 'date'})
                        df['date'] = pd.to_datetime(df['date'])
                        df['close'] = pd.to_numeric(df['close'])
                        df = df.sort_values('date').reset_index(drop=True)
                        df = df[['date', 'close']]

                # yfinance 成功，直接返回（已经是标准格式）
                else:
                    return df

            # C. 其他全球指数（港股等）-> Tushare 全球指数接口
            elif symbol in ['HSI', 'HKTECH']:
                print(f"  🌍 使用全球指数接口: {symbol}")
                df = self.pro.index_global(ts_code=symbol)
                time.sleep(0.35)

            # D. A股指数 (代码特征: 数字开头) -> A股指数接口
            else:
                print(f"  🇨🇳 使用A股指数接口: {symbol}")
                df = self.pro.index_daily(ts_code=symbol)
                time.sleep(0.35)

            # --- 数据清洗标准化 (Normalization) ---
            # 必须确保返回的 DataFrame 包含且仅包含: ['date', 'close'] 且按日期升序
            if df.empty:
                print(f"  ⚠️  警告: 没有获取到 {symbol} 的数据")
                return pd.DataFrame()

            # 统一列名 (Tushare 不同接口返回的日期列名可能不同)
            if 'trade_date' in df.columns:
                df = df.rename(columns={'trade_date': 'date'})

            # 格式转换
            df['date'] = pd.to_datetime(df['date'])
            df['close'] = pd.to_numeric(df['close'])
            df = df.sort_values('date').reset_index(drop=True)

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
            # duration=1 表示今天是第1天，应该用昨天的价格作为基准
            start_index = i - duration

            if start_index >= 0:
                # 可以追溯到起始点前一天
                start_price = df.loc[start_index, 'close']
                trend_pct = (current_close - start_price) / start_price
            else:
                # 无法追溯（数据不够），设为 None
                trend_pct = None

            trend_pcts.append(trend_pct)

        df['trend_pct'] = trend_pcts

        # 6. 生成信号标签
        # v6.1 Bug修复：信号标签必须严格基于当前偏离度，而不是status
        # Rule of Truth: deviation > 0 -> 多头信号, deviation < 0 -> 空头信号
        signal_tags = []
        for _, row in df.iterrows():
            status = row['status']
            duration = row['duration_days']
            deviation = row['deviation_pct']

            # 核心修复：信号判断完全基于当前偏离度，确保逻辑一致性
            if deviation > 0:
                # 偏离度为正 -> 多头信号
                if duration <= 3 and status == 'YES':
                    tag = 'BREAKOUT'  # 启动（刚突破且持续天数短）
                elif deviation > 0.15:
                    tag = 'OVERHEAT'  # 过热（偏离度>15%）
                else:
                    tag = 'STRONG'    # 主升（稳健上涨）
            else:
                # 偏离度为负或零 -> 空头信号
                if deviation < -0.15:
                    tag = 'EXTREME_BEAR'  # 超跌（偏离度<-15%）
                else:
                    tag = 'SLUMP'         # 弱势（下跌或震荡）

            signal_tags.append(tag)

        df['signal_tag'] = signal_tags

        return df

    @staticmethod
    def generate_sparkline_json(df: pd.DataFrame, days: int = 250,
                               today_date: str = None,
                               today_price: float = None,
                               today_ma20: float = None) -> str:
        """
        生成近N天的 Sparkline JSON 数据（v6.9: 支持手动拼接今日数据）
        v7.0: 该方法保留用于初始化场景（无历史数据时）

        Args:
            df: 完整的历史数据 DataFrame（已计算好 MA20）
            days: 需要的天数（默认250天，约一年）
            today_date: 今日日期字符串（可选，格式：YYYY-MM-DD）
            today_price: 今日收盘价（可选）
            today_ma20: 今日MA20值（可选）

        Returns:
            JSON 字符串，格式：[{"date": "2024-12-01", "price": 3000.12, "ma20": 2980.45}, ...]
        """
        if df.empty:
            return json.dumps([])

        # 取最近 N 天的数据
        recent_df = df.tail(days).copy()

        # 构建 sparkline 数据数组
        sparkline_data = []
        for _, row in recent_df.iterrows():
            # 完整日期格式 YYYY-MM-DD
            date_str = row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date'])
            # v6.3 Bug修复：增加精度到4位小数，避免小数值时精度丢失导致偏离度被抹平
            sparkline_data.append({
                "date": date_str,
                "price": round(float(row['close']), 4),      # 4位小数
                "ma20": round(float(row['ma20_price']), 4)  # 4位小数
            })

        # v6.9: 手动拼接今日数据（如果提供了今日数据且历史数据未包含今天）
        if today_date and today_price is not None and today_ma20 is not None:
            # 检查历史数据的最后一条日期
            if sparkline_data:
                last_date = sparkline_data[-1]['date']
                if last_date != today_date:
                    # 历史数据不包含今天，手动追加
                    sparkline_data.append({
                        "date": today_date,
                        "price": round(float(today_price), 4),
                        "ma20": round(float(today_ma20), 4)
                    })
            else:
                # 历史数据为空，直接添加今日数据
                sparkline_data.append({
                    "date": today_date,
                    "price": round(float(today_price), 4),
                    "ma20": round(float(today_ma20), 4)
                })

        return json.dumps(sparkline_data)

    @staticmethod
    def append_to_sparkline(current_chart_json: str, today_date: str, 
                           today_price: float, today_ma20: float, 
                           max_days: int = 250) -> str:
        """
        v7.0: 增量追加模式 - 将今日数据追加到已有的 sparkline 中

        核心逻辑：
        1. 读取现有数据
        2. 追加今日数据点（或更新同日数据）
        3. 去重并裁剪到最近 N 天
        4. 返回更新后的 JSON

        Args:
            current_chart_json: 数据库中已有的 sparkline JSON 字符串
            today_date: 今日日期（格式：YYYY-MM-DD）
            today_price: 今日收盘价
            today_ma20: 今日 MA20
            max_days: 保留的最大天数（默认250天）

        Returns:
            更新后的 JSON 字符串
        """
        # 1. 解析现有数据（带异常保护）
        try:
            if current_chart_json:
                current_chart = json.loads(current_chart_json)
                if not isinstance(current_chart, list):
                    print(f"  ⚠️  Sparkline 格式错误（非数组），重置为空")
                    current_chart = []
            else:
                current_chart = []
        except (json.JSONDecodeError, TypeError) as e:
            print(f"  ⚠️  Sparkline 解析失败: {str(e)}，重置为空")
            current_chart = []

        # 2. 构造今日数据点
        new_point = {
            "date": today_date,
            "price": round(float(today_price), 4),
            "ma20": round(float(today_ma20), 4)
        }

        # 3. 增量追加与去重
        if current_chart:
            # 检查最后一个点的日期
            last_date = current_chart[-1].get('date', '')
            
            if last_date == today_date:
                # 同一天，更新（覆盖）最后一个点
                current_chart[-1] = new_point
                print(f"  🔄 更新同日数据: {today_date}")
            else:
                # 不同天，追加新数据点
                current_chart.append(new_point)
                print(f"  ➕ 追加新数据点: {today_date}")
        else:
            # 空数组，直接添加
            current_chart.append(new_point)
            print(f"  🆕 创建首个数据点: {today_date}")

        # 4. 滑动窗口裁剪（只保留最近 N 天）
        final_chart = current_chart[-max_days:]

        # 5. 返回 JSON 字符串
        return json.dumps(final_chart)


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

    Returns:
        完整的历史数据 DataFrame（包含 sparkline 所需的30天数据）
    """
    try:
        print(f"  处理: {name} ({symbol}) [{category}]")

        # 使用新的多接口路由方法
        df = fetcher.fetch_history(symbol, category)

        if df.empty:
            return None

        # 计算指标
        df = FishbowlCalculator.calculate_all_metrics(df)

        # 添加symbol列
        df['symbol'] = symbol

        # 返回完整数据框（v5.9: 用于生成 sparkline）
        return df

    except Exception as e:
        print(f"  ❌ 处理 {symbol} 时出错: {str(e)}")
        return None


def batch_upsert_daily_data(conn, data_list: List[Dict]):
    """批量插入/更新每日数据（v6.9: sparkline_json 非空保护）

    使用CAST(%s AS DATE)强制类型转换，避免时区问题
    v6.9: 如果 sparkline_json 为 None，则不更新该字段，保留数据库中的旧数据
    """
    if not data_list:
        return

    cursor = conn.cursor()

    # 逐条插入
    for d in data_list:
        # v6.9: 根据 sparkline_json 是否有效，动态构建 SQL
        if d.get('sparkline_json') is not None:
            # 有效的 sparkline，更新所有字段（包括 sparkline_json）
            insert_query = """
                INSERT INTO fishbowl_daily
                    (date, symbol, close_price, ma20_price, status, deviation_pct, duration_days, signal_tag, change_pct, trend_pct, sparkline_json)
                VALUES
                    (CAST(%s AS DATE), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    sparkline_json = EXCLUDED.sparkline_json,
                    created_at = CURRENT_TIMESTAMP
            """
            cursor.execute(insert_query, (
                d['date'],
                d['symbol'],
                d['close_price'],
                d['ma20_price'],
                d['status'],
                d['deviation_pct'],
                d['duration_days'],
                d['signal_tag'],
                d['change_pct'],
                d['trend_pct'],
                d['sparkline_json']
            ))
        else:
            # sparkline 无效或生成失败，不更新 sparkline_json 字段（保留数据库旧数据）
            insert_query = """
                INSERT INTO fishbowl_daily
                    (date, symbol, close_price, ma20_price, status, deviation_pct, duration_days, signal_tag, change_pct, trend_pct)
                VALUES
                    (CAST(%s AS DATE), %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            cursor.execute(insert_query, (
                d['date'],
                d['symbol'],
                d['close_price'],
                d['ma20_price'],
                d['status'],
                d['deviation_pct'],
                d['duration_days'],
                d['signal_tag'],
                d['change_pct'],
                d['trend_pct']
            ))

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


# ================================================
# v5.8 全景战术驾驶舱数据聚合
# ================================================
def update_market_overview(fetcher: DataFetcher, db_conn: DatabaseConnection):
    """
    聚合生成市场概览数据：A股基准、美股风向、避险资产、领涨先锋
    """
    print("\n" + "=" * 60)
    print("🎯 生成全景战术驾驶舱数据...")
    print("=" * 60)
    
    overview_data = {}
    
    # ========================================
    # 1. A股基准 (上证 + 深证)
    # ========================================
    print("\n📊 1/4 获取 A股基准数据...")
    try:
        # 获取上证和深证的最新数据
        sh_df = fetcher.fetch_history('000001.SH', 'broad')
        sz_df = fetcher.fetch_history('399001.SZ', 'broad')
        
        # 计算鱼盆状态
        if not sh_df.empty:
            sh_df = FishbowlCalculator.calculate_all_metrics(sh_df)
            sh_latest = sh_df.iloc[-1]
            
            # 计算5日均量 (需要获取成交量数据)
            sh_vol_df = fetcher.pro.index_daily(ts_code='000001.SH', 
                                                 end_date=datetime.now().strftime('%Y%m%d'))
            time.sleep(0.35)
            if not sh_vol_df.empty:
                sh_vol_df = sh_vol_df.sort_values('trade_date', ascending=False).head(6)
                today_amount = float(sh_vol_df.iloc[0]['amount']) if len(sh_vol_df) > 0 else 0
                ma5_amount = float(sh_vol_df.iloc[1:6]['amount'].mean()) if len(sh_vol_df) >= 6 else today_amount
            else:
                today_amount = 0
                ma5_amount = 1
        
        if not sz_df.empty:
            sz_df = FishbowlCalculator.calculate_all_metrics(sz_df)
            sz_latest = sz_df.iloc[-1]
            
            # 计算深证成交量
            sz_vol_df = fetcher.pro.index_daily(ts_code='399001.SZ',
                                                 end_date=datetime.now().strftime('%Y%m%d'))
            time.sleep(0.35)
            if not sz_vol_df.empty:
                sz_vol_df = sz_vol_df.sort_values('trade_date', ascending=False).head(6)
                sz_amount = float(sz_vol_df.iloc[0]['amount']) if len(sz_vol_df) > 0 else 0
            else:
                sz_amount = 0
        
        # 汇总两市成交额
        total_amount = today_amount + sz_amount
        vol_ratio = total_amount / ma5_amount if ma5_amount > 0 else 1.0
        vol_tag = "放量" if vol_ratio > 1.0 else "缩量"
        
        overview_data['a_share'] = {
            'sh': {
                'price': float(sh_latest['close']),
                'change': float(sh_latest['change_pct'] * 100) if pd.notna(sh_latest['change_pct']) else 0.0,
                'status': sh_latest['status']
            },
            'sz': {
                'price': float(sz_latest['close']),
                'change': float(sz_latest['change_pct'] * 100) if pd.notna(sz_latest['change_pct']) else 0.0,
                'status': sz_latest['status']
            },
            'volume': {
                'amount': round(total_amount / 100000, 2),  # 转换为亿元（千元除以10万）
                'tag': vol_tag,
                'ratio': round(vol_ratio, 2)
            }
        }
        print(f"  ✓ 上证指数: {overview_data['a_share']['sh']['price']:.2f} ({overview_data['a_share']['sh']['change']:+.2f}%)")
        print(f"  ✓ 深证成指: {overview_data['a_share']['sz']['price']:.2f} ({overview_data['a_share']['sz']['change']:+.2f}%)")
        print(f"  ✓ 两市成交: {overview_data['a_share']['volume']['amount']:.0f}亿 ({vol_tag})")
        
    except Exception as e:
        print(f"  ❌ A股基准数据获取失败: {str(e)}")
        overview_data['a_share'] = None
    
    # ========================================
    # 2. 美股风向 (T-1)
    # ========================================
    print("\n🌎 2/4 获取美股风向数据...")
    try:
        us_indices = [
            ('IXIC', '纳斯达克'),
            ('SPX', '标普500'),
            ('DJI', '道琼斯')
        ]
        
        us_data = []
        for symbol, name in us_indices:
            try:
                df = fetcher.pro.index_global(ts_code=symbol)
                time.sleep(0.35)
                
                if not df.empty:
                    df = df.sort_values('trade_date', ascending=False)
                    latest = df.iloc[0]
                    
                    us_data.append({
                        'name': name,
                        'price': float(latest['close']),
                        'change': float(latest['pct_chg']) if 'pct_chg' in latest and pd.notna(latest['pct_chg']) else 0.0
                    })
                    print(f"  ✓ {name}: {latest['close']:.2f} ({latest.get('pct_chg', 0):+.2f}%)")
            except Exception as e:
                print(f"  ⚠️  {name} 数据获取失败: {str(e)}")
                us_data.append({'name': name, 'price': 0, 'change': 0})
        
        overview_data['us_share'] = us_data
        
    except Exception as e:
        print(f"  ❌ 美股数据获取失败: {str(e)}")
        overview_data['us_share'] = []
    
    # ========================================
    # 3. 避险资产 (国际黄金价格)
    # ========================================
    print("\n🥇 3/4 获取黄金数据...")
    try:
        # v7.0.1: 优先使用 Tushare 的上海金交所数据（稳定可靠）
        # 备用方案：yfinance 获取国际金价
        
        # 方案1：从数据库读取已更新的上海金交所黄金现货数据
        try:
            conn = db_conn.get_connection()
            cursor = conn.cursor()
            
            # 获取最近2天的Au99.99数据（计算涨跌幅）
            cursor.execute("""
                SELECT date, close_price, change_pct
                FROM fishbowl_daily
                WHERE symbol = 'Au99.99'
                ORDER BY date DESC
                LIMIT 2
            """)
            gold_rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if gold_rows and len(gold_rows) >= 1:
                latest = gold_rows[0]
                gold_price = float(latest[1])  # close_price
                price_change = float(latest[2] * 100) if latest[2] else 0.0  # change_pct
                
                overview_data['gold'] = {
                    'name': '上海金 (CNY)',
                    'price': round(gold_price, 2),
                    'change': round(price_change, 2),
                    'unit': '¥'
                }
                print(f"  ✅ 上海金 (CNY): ¥{gold_price:.2f}/克 ({'+' if price_change >= 0 else ''}{price_change:.2f}%)")
            else:
                raise Exception("数据库无黄金数据")
                
        except Exception as db_error:
            print(f"  ⚠️  从数据库读取黄金数据失败: {str(db_error)}, 尝试 yfinance")
            
            # 方案2：使用 yfinance 获取国际金价（备用）
            import yfinance as yf
            import time as time_module

            try:
                # v7.0.1: 增加延迟到5秒，避免API限流（之前美股数据也用了yfinance）
                print("  ⏳ 等待 5 秒避免 API 限流...")
                time_module.sleep(5)

                # v6.8 主要方案：获取 XAUUSD=X (伦敦金现货) 数据
                xau = yf.Ticker("XAUUSD=X")
                xau_hist = xau.history(period="5d")  # 获取最近5天数据

                if not xau_hist.empty and len(xau_hist) >= 2:
                    # 获取最新交易日数据和前一日数据
                    latest = xau_hist.iloc[-1]
                    prev = xau_hist.iloc[-2]

                    gold_price = float(latest['Close'])
                    prev_close = float(prev['Close'])

                    # v6.8 修复：正确计算涨跌幅
                    price_change = ((gold_price - prev_close) / prev_close) * 100

                    # 验证价格合理性 (1500-3500美元/盎司)
                    if gold_price < 1500 or gold_price > 3500:
                        print(f"  ⚠️  伦敦金价格异常: ${gold_price:.2f}, 使用备用方案")
                        raise Exception("价格超出合理范围")

                    overview_data['gold'] = {
                        'name': '伦敦金 (USD)',  # v6.8: 明确标注为伦敦金
                        'price': round(gold_price, 2),
                        'change': round(price_change, 2),
                        'unit': '$'
                    }
                    print(f"  ✅ 伦敦金 (USD): ${gold_price:.2f}/盎司 ({'+' if price_change >= 0 else ''}{price_change:.2f}%)")

                else:
                    raise Exception("伦敦金数据不足")

            except Exception as xau_error:
                print(f"  ⚠️  yfinance 伦敦金获取失败: {str(xau_error)}, 尝试黄金期货数据")

                # 备用方案1：使用黄金期货 (GC=F) 数据
                try:
                    time_module.sleep(5)  # v7.0.1: 增加延迟到5秒避免限流
                    gc = yf.Ticker("GC=F")
                    gc_hist = gc.history(period="5d")

                    if not gc_hist.empty and len(gc_hist) >= 2:
                        latest = gc_hist.iloc[-1]
                        prev = gc_hist.iloc[-2]

                        gold_price = float(latest['Close'])
                        prev_close = float(prev['Close'])
                        price_change = ((gold_price - prev_close) / prev_close) * 100

                        overview_data['gold'] = {
                            'name': '黄金期货 (COMEX)',
                            'price': round(gold_price, 2),
                            'change': round(price_change, 2),
                            'unit': '$'
                        }
                        print(f"  ✅ 黄金期货: ${gold_price:.2f}/盎司 ({'+' if price_change >= 0 else ''}{price_change:.2f}%)")
                    else:
                        raise Exception("黄金期货数据不足")

                except Exception as gc_error:
                    print(f"  ⚠️  黄金期货获取失败: {str(gc_error)}, 尝试 GLD ETF")

                    # 备用方案2：使用 GLD ETF 数据
                    try:
                        time_module.sleep(5)  # v7.0.1: 增加延迟到5秒避免限流
                        gld = yf.Ticker("GLD")
                        gld_hist = gld.history(period="5d")

                        if not gld_hist.empty and len(gld_hist) >= 2:
                            latest = gld_hist.iloc[-1]
                            prev = gld_hist.iloc[-2]

                            gld_price = float(latest['Close'])
                            prev_close = float(prev['Close'])

                            # GLD 与黄金价格的换算关系（约1/10盎司黄金）
                            conversion_factor = 10.87
                            gold_price = gld_price * conversion_factor

                            # v6.8: 基于换算后的黄金价格计算涨跌幅
                            prev_gold_price = prev_close * conversion_factor
                            price_change = ((gold_price - prev_gold_price) / prev_gold_price) * 100

                            overview_data['gold'] = {
                                'name': '黄金 (GLD)',
                                'price': round(gold_price, 2),
                                'change': round(price_change, 2),
                                'unit': '$'
                            }
                            print(f"  ✅ 黄金 (GLD): ${gold_price:.2f}/盎司 ({'+' if price_change >= 0 else ''}{price_change:.2f}%)")
                        else:
                            raise Exception("GLD数据不足")

                    except Exception as gld_error:
                        print(f"  ⚠️  GLD获取失败: {str(gld_error)}, 使用默认值")
                        # 最后的备用方案：使用估算值（涨跌幅为0）
                        overview_data['gold'] = {
                            'name': '国际黄金',
                            'price': 2650.0,  # 更新为更合理的估算值
                            'change': 0.0,
                            'unit': '$'
                        }

    except Exception as e:
        print(f"  ⚠️  黄金数据获取失败，使用默认值: {str(e)}")
        overview_data['gold'] = {
            'name': '国际黄金',
            'price': 2650.0,
            'change': 0.0,
            'unit': '$'
        }

    # ========================================
    # 4. 领涨先锋 (Top 3 行业板块)
    # ========================================
    print("\n🚀 4/4 获取领涨先锋...")
    try:
        conn = db_conn.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 从数据库获取当日所有行业ETF数据，按涨幅降序
        query = """
            SELECT 
                c.name,
                c.symbol,
                d.change_pct
            FROM fishbowl_daily d
            JOIN monitor_config c ON d.symbol = c.symbol
            WHERE c.category = 'industry'
              AND d.date = (SELECT MAX(date) FROM fishbowl_daily)
              AND d.change_pct IS NOT NULL
            ORDER BY d.change_pct DESC
            LIMIT 3
        """
        
        cursor.execute(query)
        leaders = cursor.fetchall()
        
        leaders_data = []
        for leader in leaders:
            # 提取ETF代码（去掉后缀）
            code = leader['symbol'].split('.')[0]
            leaders_data.append({
                'name': leader['name'],
                'change': float(leader['change_pct'] * 100),
                'code': code
            })
            print(f"  ✓ {leader['name']}: +{leader['change_pct']*100:.2f}% (代码: {code})")
        
        overview_data['leaders'] = leaders_data
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"  ❌ 领涨先锋数据获取失败: {str(e)}")
        overview_data['leaders'] = []
    
    # ========================================
    # 5. 存入数据库
    # ========================================
    print("\n💾 保存到数据库...")
    try:
        conn = db_conn.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        upsert_query = """
            INSERT INTO market_overview (date, data, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (date)
            DO UPDATE SET
                data = EXCLUDED.data,
                updated_at = CURRENT_TIMESTAMP
        """
        
        cursor.execute(upsert_query, (today, json.dumps(overview_data, ensure_ascii=False)))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"  ✓ 市场概览数据已保存: {today}")
        
    except Exception as e:
        print(f"  ❌ 数据保存失败: {str(e)}")
    
    print("=" * 60)
    print("✅ 全景战术驾驶舱数据生成完成！")
    print("=" * 60)


def main():
    """主执行函数"""
    print("=" * 60)
    print("鱼盆趋势雷达 - ETL 更新 v7.0 (增量追加模式)")
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
            print("\n⚠️  没有成功获取任何数据,可能是非交易日")
            print("ℹ️  这属于正常情况，脚本将正常退出")
            return

        # v7.0: 增量追加模式 - 只在无历史数据时才全量拉取
        print("\n" + "=" * 60)
        print("📈 v7.0 增量追加模式：生成趋势图数据...")
        print("=" * 60)
        
        data_list = []
        for result_df in all_results:
            if result_df.empty:
                continue

            # 只取最后一天的数据
            last_row = result_df.iloc[-1]
            symbol = last_row['symbol']

            # 使用strftime生成字符串，避免psycopg2时区转换
            date_str = last_row['date'].strftime('%Y-%m-%d') if hasattr(last_row['date'], 'strftime') else str(last_row['date'])

            # v7.0: 核心逻辑 - 先读取数据库已有数据，决定增量还是全量
            existing_sparkline = db_conn.get_existing_sparkline(symbol)
            sparkline_to_save = None

            # v7.0.1: 检查现有数据是否充足（至少需要20个点才有意义）
            needs_reinit = False
            if existing_sparkline:
                try:
                    existing_data = json.loads(existing_sparkline)
                    if len(existing_data) < 20:
                        print(f"  ⚠️  [{symbol}] 现有数据仅 {len(existing_data)} 个点，需要重新初始化")
                        needs_reinit = True
                        existing_sparkline = None  # 强制进入全量模式
                except:
                    needs_reinit = True
                    existing_sparkline = None

            if existing_sparkline and not needs_reinit:
                # ✅ 增量模式：已有历史数据，只追加今日数据点
                print(f"  📊 [{symbol}] 增量追加模式")
                try:
                    sparkline_json = FishbowlCalculator.append_to_sparkline(
                        current_chart_json=existing_sparkline,
                        today_date=date_str,
                        today_price=float(last_row['close']),
                        today_ma20=float(last_row['ma20_price']),
                        max_days=250
                    )
                    
                    # 验证生成的数据
                    sparkline_array = json.loads(sparkline_json)
                    if len(sparkline_array) > 0:
                        sparkline_to_save = sparkline_json
                    else:
                        print(f"  ⚠️  追加后数据为空，保留旧数据")
                        sparkline_to_save = None
                        
                except Exception as e:
                    print(f"  ⚠️  增量追加失败: {str(e)}，保留旧数据")
                    sparkline_to_save = None
            else:
                # 🆕 全量模式：无历史数据，调用 Tushare 初始化
                print(f"  🔄 [{symbol}] 首次初始化，全量拉取历史数据...")
                print(f"      历史数据总行数: {len(result_df)}")
                try:
                    sparkline_json = FishbowlCalculator.generate_sparkline_json(
                        result_df,
                        days=250,
                        today_date=date_str,
                        today_price=float(last_row['close']),
                        today_ma20=float(last_row['ma20_price'])
                    )
                    
                    # v7.0: 降低初始化要求 - 只要有数据就保存（从 >1 改为 >0）
                    sparkline_array = json.loads(sparkline_json)
                    if len(sparkline_array) > 0:
                        sparkline_to_save = sparkline_json
                        print(f"  ✅ 初始化成功，生成 {len(sparkline_array)} 个数据点")
                    else:
                        print(f"  ⚠️  初始化失败，数据为空")
                        sparkline_to_save = None
                        
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"  ⚠️  初始化失败: {str(e)}")
                    sparkline_to_save = None

            data_list.append({
                'date': date_str,  # 字符串格式，避免时区转换
                'symbol': symbol,
                'close_price': float(last_row['close']),
                'ma20_price': float(last_row['ma20_price']),
                'status': last_row['status'],
                'deviation_pct': float(last_row['deviation_pct']),
                'duration_days': int(last_row['duration_days']),
                'signal_tag': last_row['signal_tag'],
                'change_pct': float(last_row['change_pct']) if pd.notna(last_row['change_pct']) else None,
                'trend_pct': float(last_row['trend_pct']) if pd.notna(last_row['trend_pct']) else None,
                'sparkline_json': sparkline_to_save  # v7.0: 增量追加或全量初始化
            })

        # 批量入库
        conn = db_conn.get_connection()
        batch_upsert_daily_data(conn, data_list)
        print(f"\n✓ 批量入库成功: {len(data_list)} 条记录")

        # 更新固定排序（从 data_list 获取最新日期）
        latest_date = max(d['date'] for d in data_list)
        update_sort_rankings(conn, latest_date)
        print(f"✓ 更新固定排序完成: {latest_date}")

        conn.close()

        # v5.8 新增：生成全景战术驾驶舱数据
        update_market_overview(fetcher, db_conn)

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
        
        # 判断是否为非交易日或API限制等可接受的错误
        error_msg = str(e).lower()
        acceptable_errors = [
            '无数据', 'no data', 'empty', 'tushare', 'api', '限制', 'limit',
            '非交易日', 'holiday', '周末', 'weekend', '休息', 'closed'
        ]
        
        # 如果错误消息包含可接受的错误关键词，则正常退出
        if any(err in error_msg for err in acceptable_errors):
            print("ℹ️  可能是非交易日或API限制，属于正常情况")
            exit(0)
        else:
            print("❌ 严重错误，请检查系统配置")
            exit(1)


if __name__ == "__main__":
    main()
