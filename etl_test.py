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
            'database': parsed_url.path[1:],
            'user': parsed_url.username,
            'password': parsed_url.password,
            'sslmode': 'require',
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
        """执行 UPSERT 操作"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            columns = list(data.keys())
            placeholders = ['%s'] * len(columns)
            values = list(data.values())
            
            conflict_cols = ', '.join(conflict_columns)
            update_cols = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in conflict_columns])
            
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


def process_symbol_small(symbol: str, db_conn: DatabaseConnection) -> bool:
    """处理少量测试数据"""
    try:
        print(f"\nProcessing symbol: {symbol}")
        
        # 获取少量测试数据 (最近10天)
        token = os.getenv('TUSHARE_TOKEN')
        ts.set_token(token)
        pro = ts.pro_api()
        
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        df = pro.index_daily(ts_code=symbol, start_date=start_date, end_date=end_date)
        
        if df.empty:
            print(f"No data for {symbol}")
            return False
        
        df = df.sort_values('trade_date').reset_index(drop=True)
        df['date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        
        # 只使用最后20条数据进行测试
        df = df.tail(20).copy()
        
        # 计算MA20 (使用最后20条数据)
        df['ma20_price'] = df['close'].mean()  # 简化为平均值
        
        # 简化的信号计算
        df['deviation_pct'] = (df['close'] - df['ma20_price']) / df['ma20_price']
        df['status'] = df['deviation_pct'].apply(lambda x: 'YES' if x > 0.01 else 'NO')
        df['duration_days'] = 1  # 简化处理
        
        # 生成信号标签
        def get_signal_tag(row):
            if row['status'] == 'YES':
                if row['deviation_pct'] > 0.15:
                    return 'OVERHEAT'
                else:
                    return 'STRONG'
            else:
                return 'SLUMP'
        
        df['signal_tag'] = df.apply(get_signal_tag, axis=1)
        
        print(f"Processing {len(df)} records...")
        
        # 插入数据库
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
        print(f"  Latest data: {latest_data['date'].date()}")
        print(f"  Close price: {latest_data['close']:.2f}")
        print(f"  MA20: {latest_data['ma20_price']:.2f}")
        print(f"  Status: {latest_data['status']}")
        print(f"  Deviation: {latest_data['deviation_pct']:.2%}")
        print(f"  Signal: {latest_data['signal_tag']}")
        print(f"  Database records: {success_count}/{len(df)}")
        
        return True
        
    except Exception as e:
        print(f"Error processing {symbol}: {str(e)}")
        return False


def main():
    """主执行函数"""
    print("=== Fishbowl Monitor ETL Test (Small Dataset) ===")
    
    try:
        # 初始化数据库连接
        db_conn = DatabaseConnection()
        
        # 只测试一个指数
        symbol = '000300.SH'
        print(f"Testing with symbol: {symbol}")
        
        success = process_symbol_small(symbol, db_conn)
        
        if success:
            print("\n[OK] ETL test completed successfully!")
        else:
            print("\n[ERROR] ETL test failed!")
        
    except Exception as e:
        print(f"ETL test failed: {str(e)}")


if __name__ == "__main__":
    main()