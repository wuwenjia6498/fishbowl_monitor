import os
import sys
import psycopg2
import tushare as ts
from dotenv import load_dotenv
from urllib.parse import urlparse

# 加载环境变量
load_dotenv()

def test_tushare_connection():
    """测试 Tushare 连接"""
    try:
        token = os.getenv('TUSHARE_TOKEN')
        print(f"[OK] TUSHARE_TOKEN 已设置: {token[:20]}...")
        
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 测试获取基础信息
        df = pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20240105')
        print(f"[OK] Tushare API 连接成功，获取到 {len(df)} 条交易日数据")
        return True
        
    except Exception as e:
        print(f"[ERROR] Tushare 连接失败: {str(e)}")
        return False

def test_database_connection():
    """测试数据库连接"""
    try:
        connection_url = os.getenv('POSTGRES_URL')
        print(f"[OK] POSTGRES_URL 已设置: {connection_url[:50]}...")
        
        # 解析连接URL
        parsed_url = urlparse(connection_url)
        db_config = {
            'host': parsed_url.hostname,
            'port': parsed_url.port or 5432,
            'database': parsed_url.path[1:],
            'user': parsed_url.username,
            'password': parsed_url.password,
            'sslmode': 'require',
        }
        
        # 测试连接
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 测试查询
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"[OK] 数据库连接成功: {version[0][:50]}...")
        
        # 测试表是否存在
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'monitor_config';
        """)
        
        result = cursor.fetchone()
        if result:
            print("[OK] monitor_config 表已存在")
        else:
            print("[WARN] monitor_config 表不存在，需要运行 schema.sql")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {str(e)}")
        return False

def test_index_data_fetch():
    """测试获取指数数据"""
    try:
        token = os.getenv('TUSHARE_TOKEN')
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 获取少量测试数据
        df = pro.index_daily(ts_code='000300.SH', start_date='20241201', end_date='20241205')
        print(f"[OK] 成功获取沪深300数据: {len(df)} 条记录")
        
        if not df.empty:
            latest = df.iloc[0]
            print(f"  最新数据: {latest['trade_date']}, 收盘价: {latest['close']}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 获取指数数据失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Fishbowl Monitor System Connection Test ===\n")
    
    print("1. Testing Tushare API connection...")
    tushare_ok = test_tushare_connection()
    print()
    
    print("2. Testing database connection...")
    db_ok = test_database_connection()
    print()
    
    if tushare_ok:
        print("3. Testing index data fetch...")
        data_ok = test_index_data_fetch()
        print()
    
    print("=== Test Results ===")
    print(f"Tushare API: {'OK' if tushare_ok else 'ERROR'}")
    print(f"Database Connection: {'OK' if db_ok else 'ERROR'}")
    print(f"Data Fetch: {'OK' if tushare_ok and (data_ok if 'data_ok' in locals() else False) else 'ERROR'}")
    
    if tushare_ok and db_ok:
        print("\n[OK] System connection test passed, ready to run full ETL script")
    else:
        print("\n[ERROR] System connection has issues, please check configuration")