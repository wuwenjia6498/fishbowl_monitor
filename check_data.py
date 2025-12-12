import os
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

# 加载环境变量
load_dotenv()

def check_database_data():
    """检查数据库中的数据"""
    try:
        # 连接数据库
        connection_url = os.getenv('POSTGRES_URL')
        parsed_url = urlparse(connection_url)
        db_config = {
            'host': parsed_url.hostname,
            'port': parsed_url.port or 5432,
            'database': parsed_url.path[1:],
            'user': parsed_url.username,
            'password': parsed_url.password,
            'sslmode': 'require',
        }
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 检查配置表
        cursor.execute("SELECT * FROM monitor_config ORDER BY symbol;")
        configs = cursor.fetchall()
        print(f"\nMonitor Config ({len(configs)} records):")
        for config in configs:
            print(f"  {config[0]}: {config[1]} ({config[2]}) - Active: {config[3]}")
        
        # 检查最新数据
        cursor.execute("""
            SELECT symbol, date, close_price, ma20_price, status, deviation_pct, signal_tag
            FROM fishbowl_daily 
            WHERE symbol = '000300.SH'
            ORDER BY date DESC 
            LIMIT 10;
        """)
        
        records = cursor.fetchall()
        print(f"\nLatest Fishbowl Data for 000300.SH (10 records):")
        for record in records:
            print(f"  {record[1]}: Close={record[2]:.2f}, MA20={record[3]:.2f}, Status={record[4]}, Deviation={record[5]:.2%}, Signal={record[6]}")
        
        # 统计信息
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT symbol) as symbols_count,
                COUNT(DISTINCT date) as dates_count,
                MIN(date) as earliest_date,
                MAX(date) as latest_date
            FROM fishbowl_daily;
        """)
        
        stats = cursor.fetchone()
        print(f"\nDatabase Statistics:")
        print(f"  Total records: {stats[0]}")
        print(f"  Symbols: {stats[1]}")
        print(f"  Dates: {stats[2]}")
        print(f"  Date range: {stats[3]} to {stats[4]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {str(e)}")

if __name__ == "__main__":
    print("=== Fishbowl Monitor Database Check ===")
    check_database_data()