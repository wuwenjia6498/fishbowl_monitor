import os
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

# 加载环境变量
load_dotenv()

def execute_schema():
    """执行数据库 schema"""
    try:
        # 读取 schema.sql 文件
        with open('schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
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
        
        # 分割并执行 SQL 语句
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    cursor.execute(statement)
                    print(f"[{i}/{len(statements)}] Executed: {statement[:50]}...")
                except Exception as e:
                    print(f"[{i}/{len(statements)}] Error in statement: {e}")
                    print(f"Statement: {statement[:100]}...")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n[OK] Database schema setup completed!")
        
    except Exception as e:
        print(f"[ERROR] Database setup failed: {str(e)}")

if __name__ == "__main__":
    print("=== Setting up Fishbowl Monitor Database ===")
    execute_schema()