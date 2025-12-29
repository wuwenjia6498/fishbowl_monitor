#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鱼盆趋势雷达 - ETF 持仓更新脚本 v5.4
功能：
1. 从 Tushare 获取 ETF 前十大重仓股数据
2. 生成 Markdown 格式的持仓列表
3. 更新数据库 monitor_config.top_holdings 字段

使用方法：
    python scripts/update_holdings.py

依赖：
    - tushare (需要 fund_portfolio 接口权限)
    - psycopg2
    - python-dotenv
"""

import os
import sys
import pandas as pd
import tushare as ts
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
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
            print(f"❌ 数据库连接失败: {str(e)}")
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
            print(f"❌ 查询操作失败: {str(e)}")
            return []

    def execute(self, sql: str, params: tuple = None) -> bool:
        """执行更新操作"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ 执行操作失败: {str(e)}")
            return False


# ================================================
# Tushare 数据获取器
# ================================================
class HoldingsFetcher:
    """ETF 持仓数据获取器"""

    def __init__(self):
        self.token = os.getenv('TUSHARE_TOKEN')
        if not self.token:
            raise ValueError("环境变量 TUSHARE_TOKEN 未设置")
        ts.set_token(self.token)
        self.pro = ts.pro_api()
        
        # 股票基础信息缓存 (用于获取股票中文名)
        self._stock_names_cache: Dict[str, str] = {}

    def _get_stock_name(self, stock_code: str) -> str:
        """
        获取股票中文名称
        
        Args:
            stock_code: 股票代码，如 '600519.SH'
            
        Returns:
            股票名称，如 '贵州茅台'
        """
        # 如果缓存为空，先加载股票基础信息
        if not self._stock_names_cache:
            try:
                print("📊 正在加载股票基础信息...")
                df = self.pro.stock_basic(
                    exchange='',
                    list_status='L',
                    fields='ts_code,name'
                )
                self._stock_names_cache = dict(zip(df['ts_code'], df['name']))
                print(f"✅ 已加载 {len(self._stock_names_cache)} 只股票信息")
            except Exception as e:
                print(f"⚠️ 加载股票信息失败: {e}")
                return stock_code
        
        return self._stock_names_cache.get(stock_code, stock_code)

    def get_etf_holdings(self, ts_code: str) -> Optional[pd.DataFrame]:
        """
        获取 ETF 持仓数据
        
        Args:
            ts_code: ETF 代码，如 '159819.SZ'
            
        Returns:
            持仓数据 DataFrame，包含前十大重仓股
        """
        try:
            # 调用 Tushare fund_portfolio 接口
            df = self.pro.fund_portfolio(ts_code=ts_code)
            
            if df is None or df.empty:
                print(f"⚠️ {ts_code}: 无持仓数据")
                return None
            
            # 获取最新一期公告日的数据
            latest_date = df['ann_date'].max()
            df = df[df['ann_date'] == latest_date]
            
            # 按持仓市值占比降序排序，取前10
            if 'stk_mkv_ratio' in df.columns:
                df = df.sort_values('stk_mkv_ratio', ascending=False).head(10)
            elif 'mkv' in df.columns:
                df = df.sort_values('mkv', ascending=False).head(10)
            else:
                df = df.head(10)
            
            return df
            
        except Exception as e:
            print(f"❌ 获取 {ts_code} 持仓失败: {e}")
            return None

    def generate_markdown(self, df: pd.DataFrame) -> str:
        """
        将持仓数据转换为 Markdown 表格
        
        Args:
            df: 持仓数据 DataFrame
            
        Returns:
            Markdown 格式的表格字符串
        """
        md_lines = [
            "| 股票名称 | 代码 | 占比 |",
            "| :--- | :--- | ---: |"
        ]
        
        for _, row in df.iterrows():
            # 获取股票代码
            stock_code = row.get('symbol', '')
            
            # 尝试获取股票名称
            stock_name = row.get('name', '')
            if not stock_name and stock_code:
                # 如果 Tushare 返回没有 name 字段，尝试从缓存获取
                stock_name = self._get_stock_name(stock_code)
            if not stock_name:
                stock_name = stock_code
            
            # 获取持仓占比
            ratio = row.get('stk_mkv_ratio', row.get('mkv_ratio', 0))
            if ratio is None:
                ratio = 0
            
            # 格式化占比显示
            ratio_str = f"{float(ratio):.2f}%" if ratio else "-"
            
            md_lines.append(f"| {stock_name} | {stock_code} | {ratio_str} |")
        
        # 添加更新时间
        update_time = datetime.now().strftime('%Y-%m-%d')
        md_lines.append(f"\n*(数据更新于 {update_time})*")
        
        return "\n".join(md_lines)


# ================================================
# 持仓更新管理器
# ================================================
class HoldingsUpdater:
    """ETF 持仓更新管理器"""

    def __init__(self):
        self.db = DatabaseConnection()
        self.fetcher = HoldingsFetcher()

    def get_industry_etfs(self) -> List[Dict]:
        """
        获取所有行业 ETF 列表
        
        Returns:
            ETF 列表，每个元素包含 symbol 和 name
        """
        sql = """
            SELECT symbol, name 
            FROM monitor_config 
            WHERE category = 'industry' 
              AND is_active = true
            ORDER BY symbol
        """
        return self.db.query_data(sql)

    def update_holdings(self, symbol: str, markdown: str) -> bool:
        """
        更新单个 ETF 的持仓数据
        
        Args:
            symbol: ETF 代码
            markdown: Markdown 格式的持仓数据
            
        Returns:
            是否更新成功
        """
        sql = """
            UPDATE monitor_config 
            SET top_holdings = %s,
                holdings_updated_at = %s,
                updated_at = %s
            WHERE symbol = %s
        """
        now = datetime.now()
        return self.db.execute(sql, (markdown, now, now, symbol))

    def run(self, symbols: List[str] = None):
        """
        运行持仓更新任务
        
        Args:
            symbols: 可选，指定要更新的 ETF 代码列表。若为 None，则更新所有行业 ETF。
        """
        print("=" * 60)
        print("🐟 鱼盆趋势雷达 - ETF 持仓更新脚本 v5.4")
        print("=" * 60)
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 获取 ETF 列表
        if symbols:
            etfs = [{"symbol": s, "name": s} for s in symbols]
        else:
            etfs = self.get_industry_etfs()
        
        if not etfs:
            print("⚠️ 未找到需要更新的 ETF")
            return
        
        print(f"📋 待更新 ETF 数量: {len(etfs)}")
        print()

        success_count = 0
        fail_count = 0

        for i, etf in enumerate(etfs, 1):
            symbol = etf['symbol']
            name = etf['name']
            
            print(f"[{i}/{len(etfs)}] 正在处理: {name} ({symbol})")
            
            try:
                # 获取持仓数据
                df = self.fetcher.get_etf_holdings(symbol)
                
                if df is not None and not df.empty:
                    # 生成 Markdown
                    markdown = self.fetcher.generate_markdown(df)
                    
                    # 更新数据库
                    if self.update_holdings(symbol, markdown):
                        print(f"    ✅ 更新成功，共 {len(df)} 只重仓股")
                        success_count += 1
                    else:
                        print(f"    ❌ 数据库更新失败")
                        fail_count += 1
                else:
                    print(f"    ⚠️ 无持仓数据")
                    fail_count += 1
                    
            except Exception as e:
                print(f"    ❌ 处理失败: {e}")
                fail_count += 1
            
            # Tushare 接口频率限制：每分钟200次，这里保守设置
            time.sleep(0.5)
        
        print()
        print("=" * 60)
        print(f"✅ 更新完成！成功: {success_count}, 失败: {fail_count}")
        print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)


# ================================================
# 主入口
# ================================================
def main():
    """主入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ETF 持仓数据更新脚本')
    parser.add_argument(
        '--symbols', 
        nargs='+',
        help='指定要更新的 ETF 代码列表（如：159819.SZ 512480.SH）'
    )
    
    args = parser.parse_args()
    
    updater = HoldingsUpdater()
    updater.run(symbols=args.symbols)


if __name__ == "__main__":
    main()






