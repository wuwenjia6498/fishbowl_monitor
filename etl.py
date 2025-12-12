import os
import json
import pandas as pd
import tushare as ts
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class DatabaseConnection:
    """Vercel Postgres 数据库连接管理"""
    
    def __init__(self):
        self.connection_url = os.getenv('POSTGRES_URL')
        if not self.connection_url:
            raise ValueError("环境变量 POSTGRES_URL 未设置")
        
        # 解析连接URL，确保SSL模式
        parsed_url = urlparse(self.connection_url)
        self.db_config = {
            'host': parsed_url.hostname,
            'port': parsed_url.port or 5432,
            'database': parsed_url.path[1:],  # 去掉开头的 '/'
            'user': parsed_url.username,
            'password': parsed_url.password,
            'sslmode': 'require',  # Vercel Postgres 强制要求SSL
            'sslcert': None,
            'sslkey': None,
            'sslrootcert': None,
        }
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"数据库连接失败: {str(e)}")
            raise
    
    def execute_upsert(self, table: str, data: Dict, conflict_columns: List[str]) -> bool:
        """
        执行 UPSERT 操作
        
        Args:
            table: 表名
            data: 要插入/更新的数据字典
            conflict_columns: 冲突检测的列名列表
            
        Returns:
            操作是否成功
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 构建列名和占位符
            columns = list(data.keys())
            placeholders = ['%s'] * len(columns)
            values = list(data.values())
            
            # 构建 ON CONFLICT 子句
            conflict_cols = ', '.join(conflict_columns)
            update_cols = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in conflict_columns])
            
            # 构建完整的SQL语句
            sql = f"""
                INSERT INTO {table} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT ({conflict_cols}) 
                DO UPDATE SET {update_cols}
            """
            
            cursor.execute(sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"UPSERT 操作失败: {str(e)}")
            return False
    
    def query_data(self, sql: str, params: Tuple = None) -> List[Dict]:
        """
        执行查询并返回数据
        
        Args:
            sql: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
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


class DataFetcher:
    """数据获取器，使用Tushare API获取指数数据"""
    
    def __init__(self):
        self.token = os.getenv('TUSHARE_TOKEN')
        if not self.token:
            raise ValueError("环境变量 TUSHARE_TOKEN 未设置")
        ts.set_token(self.token)
        self.pro = ts.pro_api()
    
    def get_index_daily_data(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取指数日线数据
        
        Args:
            symbol: 指数代码，格式如 '000300.SH'
            start_date: 开始日期，格式 '20230101'
            end_date: 结束日期，格式 '20231231'
            
        Returns:
            DataFrame 包含日期和收盘价数据
        """
        try:
            # 默认获取最近250个交易日数据
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            # 获取指数日线数据
            df = self.pro.index_daily(ts_code=symbol, start_date=start_date, end_date=end_date)
            
            if df.empty:
                print(f"警告: 没有获取到 {symbol} 的数据")
                return pd.DataFrame()
            
            # 按日期升序排列，确保MA计算正确
            df = df.sort_values('trade_date').reset_index(drop=True)
            
            # 转换日期格式
            df['date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            
            return df[['date', 'close']]
            
        except Exception as e:
            print(f"获取 {symbol} 数据时出错: {str(e)}")
            return pd.DataFrame()


class FishbowlCalculator:
    """鱼盆趋势计算器，实现20日均线策略"""
    
    @staticmethod
    def calculate_ma20(df: pd.DataFrame) -> pd.DataFrame:
        """计算20日简单移动平均线"""
        df = df.copy()
        df['ma20_price'] = df['close'].rolling(window=20, min_periods=1).mean()
        return df
    
    @staticmethod
    def calculate_fishbowl_signals(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算鱼盆信号
        
        核心逻辑：
        - 转YES (看多): 收盘价 > MA20 * 1.01
        - 转NO (看空): 收盘价 < MA20 * 0.99  
        - 维持 (Hold): 价格在±1%之间，维持昨日状态
        """
        df = df.copy()
        
        # 初始化状态列表
        statuses = []
        durations = []
        
        for i in range(len(df)):
            close_price = df.loc[i, 'close']
            ma20_price = df.loc[i, 'ma20_price']
            
            # 计算价格偏离MA20的百分比
            deviation = (close_price - ma20_price) / ma20_price
            
            if i == 0:
                # 第一天，基于偏离度确定初始状态
                if deviation > 0.01:
                    status = 'YES'
                elif deviation < -0.01:
                    status = 'NO'
                else:
                    status = 'NO'  # 初始默认为看空
                duration = 1
            else:
                # 后续天数，应用±1%缓冲带逻辑
                prev_status = statuses[-1]
                prev_duration = durations[-1]
                
                if deviation > 0.01:
                    # 超过上轨，转看多
                    status = 'YES'
                    duration = 1 if prev_status != 'YES' else prev_duration + 1
                elif deviation < -0.01:
                    # 低于下轨，转看空
                    status = 'NO'
                    duration = 1 if prev_status != 'NO' else prev_duration + 1
                else:
                    # 在缓冲带内，维持昨日状态
                    status = prev_status
                    duration = prev_duration + 1
            
            statuses.append(status)
            durations.append(duration)
        
        df['status'] = statuses
        df['duration_days'] = durations
        df['deviation_pct'] = (df['close'] - df['ma20_price']) / df['ma20_price']
        
        return df
    
    @staticmethod
    def generate_signal_tags(df: pd.DataFrame) -> pd.DataFrame:
        """
        生成信号标签
        
        1. BREAKOUT (启动): 状态=YES 且 持续天数<=3
        2. STRONG (主升): 状态=YES 且 0.02<=偏离率<=0.15
        3. OVERHEAT (过热): 状态=YES 且 偏离率>0.15
        4. SLUMP (弱势): 状态=NO 且 偏离率>-0.15
        5. EXTREME_BEAR (超跌): 状态=NO 且 偏离率<-0.15
        """
        df = df.copy()
        signal_tags = []
        
        for _, row in df.iterrows():
            status = row['status']
            duration = row['duration_days']
            deviation = row['deviation_pct']
            
            if status == 'YES':
                if duration <= 3:
                    signal_tag = 'BREAKOUT'
                elif 0.02 <= deviation <= 0.15:
                    signal_tag = 'STRONG'
                elif deviation > 0.15:
                    signal_tag = 'OVERHEAT'
                else:
                    signal_tag = 'STRONG'  # YES状态的默认标签
            else:  # status == 'NO'
                if deviation > -0.15:
                    signal_tag = 'SLUMP'
                elif deviation < -0.15:
                    signal_tag = 'EXTREME_BEAR'
                else:
                    signal_tag = 'SLUMP'  # NO状态的默认标签
            
            signal_tags.append(signal_tag)
        
        df['signal_tag'] = signal_tags
        return df


def update_rankings(db_conn: DatabaseConnection, date: str) -> bool:
    """
    更新特定日期的趋势排名
    
    Args:
        db_conn: 数据库连接对象
        date: 特定日期
        
    Returns:
        操作是否成功
    """
    try:
        # 获取该日期的所有数据，按偏离率绝对值降序排列
        sql = """
            SELECT symbol, ABS(deviation_pct) as abs_deviation
            FROM fishbowl_daily 
            WHERE date = %s
            ORDER BY ABS(deviation_pct) DESC
        """
        
        results = db_conn.query_data(sql, (date,))
        
        if not results:
            print(f"没有找到 {date} 的数据")
            return False
        
        # 更新排名
        for rank, row in enumerate(results, 1):
            symbol = row['symbol']
            update_sql = """
                UPDATE fishbowl_daily 
                SET trend_rank = %s 
                WHERE symbol = %s AND date = %s
            """
            conn = db_conn.get_connection()
            cursor = conn.cursor()
            cursor.execute(update_sql, (rank, symbol, date))
            conn.commit()
            cursor.close()
            conn.close()
        
        print(f"已更新 {date} 的趋势排名，共 {len(results)} 条记录")
        return True
        
    except Exception as e:
        print(f"更新排名失败: {str(e)}")
        return False


def process_symbol(symbol: str, db_conn: DatabaseConnection) -> bool:
    """
    处理单个指数的完整流程：获取数据 -> 计算 -> 入库
    
    Args:
        symbol: 指数代码
        db_conn: 数据库连接对象
        
    Returns:
        处理是否成功
    """
    try:
        print(f"\n处理指数: {symbol}")
        
        # 获取数据
        fetcher = DataFetcher()
        df = fetcher.get_index_daily_data(symbol)
        if df.empty:
            print(f"跳过 {symbol}，无有效数据")
            return False
        
        # 计算MA20
        df = FishbowlCalculator.calculate_ma20(df)
        
        # 计算鱼盆信号
        df = FishbowlCalculator.calculate_fishbowl_signals(df)
        
        # 生成信号标签
        df = FishbowlCalculator.generate_signal_tags(df)
        
        # 转换数据格式并入库
        success_count = 0
        for _, row in df.iterrows():
            data = {
                'date': row['date'].date(),
                'symbol': symbol,
                'close_price': float(row['close']),
                'ma20_price': float(row['ma20_price']),
                'status': row['status'],
                'deviation_pct': float(row['deviation_pct']),
                'duration_days': int(row['duration_days']),
                'signal_tag': row['signal_tag']
            }
            
            if db_conn.execute_upsert('fishbowl_daily', data, ['symbol', 'date']):
                success_count += 1
        
        # 输出最新一天的信息
        latest_data = df.iloc[-1]
        print(f"  - 收盘价: {latest_data['close']:.2f}")
        print(f"  - MA20: {latest_data['ma20_price']:.2f}")
        print(f"  - 状态: {latest_data['status']}")
        print(f"  - 偏离率: {latest_data['deviation_pct']:.2%}")
        print(f"  - 持续天数: {latest_data['duration_days']}")
        print(f"  - 信号标签: {latest_data['signal_tag']}")
        print(f"  - 入库成功: {success_count}/{len(df)} 条记录")
        
        return True
        
    except Exception as e:
        print(f"处理 {symbol} 时出错: {str(e)}")
        return False


def main():
    """主执行函数"""
    # 示例处理单个指数
    symbol = '000300.SH'
    
    print("开始执行鱼盆趋势雷达 ETL 流程...")
    
    try:
        # 初始化数据库连接
        db_conn = DatabaseConnection()
        
        # 处理指定指数
        success = process_symbol(symbol, db_conn)
        
        if success:
            # 获取最新日期并更新排名
            latest_date_sql = "SELECT MAX(date) as latest_date FROM fishbowl_daily WHERE symbol = %s"
            results = db_conn.query_data(latest_date_sql, (symbol,))
            
            if results:
                latest_date = results[0]['latest_date']
                print(f"\n最新数据日期: {latest_date}")
                update_rankings(db_conn, latest_date)
        
        print("\nETL 流程执行完成")
        
    except Exception as e:
        print(f"ETL 流程执行失败: {str(e)}")


if __name__ == "__main__":
    main()