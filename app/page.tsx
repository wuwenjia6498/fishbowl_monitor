import React from 'react';
import pool from '@/lib/db';
import FishbowlTable from '@/components/business/fishbowl-table';
import { EtfCardProps } from '@/components/EtfCard';
import ProjectIntro from '@/components/business/project-intro';
import MarketHeader from '@/components/market-header';
import Footer from '@/components/footer';

// 强制动态渲染，因为数据每天会变，我们需要获取最新 DB 状态
export const dynamic = 'force-dynamic';

async function getLatestMarketData(): Promise<EtfCardProps[]> {
  const client = await pool.connect();
  try {
    // 核心查询逻辑：
    // 1. 联表 monitor_config 获取名称 (c.name)
    // 2. 使用 DISTINCT ON (symbol) 获取每个代码最新的一条记录
    // 3. 筛选 is_active = true 的配置
    // 4. 按日期降序排列，确保最新的日期排在前面
    // 5. v4.6: 包含 investment_logic 投资逻辑说明
    // 6. v5.4: 包含 top_holdings 核心持仓数据
    // 7. v5.9: 包含 sparkline_json 趋势图数据
    const query = `
      SELECT DISTINCT ON (d.symbol)
        TO_CHAR(d.date, 'YYYY-MM-DD') as date,
        d.symbol,
        d.close_price,
        d.ma20_price,
        d.status,
        d.deviation_pct,
        d.duration_days,
        d.trend_rank,
        d.signal_tag,
        d.change_pct,
        d.trend_pct,
        d.sparkline_json,
        c.name,
        c.category,
        c.industry_level,
        c.dominant_etf,
        c.sort_rank,
        c.investment_logic,
        c.top_holdings,
        c.holdings_updated_at
      FROM fishbowl_daily d
      JOIN monitor_config c ON d.symbol = c.symbol
      WHERE c.is_active = true
      ORDER BY d.symbol, d.date DESC;
    `;

    const result = await client.query(query);

    // 数据清洗/转换：确保数字类型正确 (pg driver 有时返回 string)
    const data: EtfCardProps[] = result.rows.map(row => {
      // 处理日期，使用本地时区避免 UTC 转换问题
      let dateStr: string;
      if (row.date instanceof Date) {
        const year = row.date.getFullYear();
        const month = String(row.date.getMonth() + 1).padStart(2, '0');
        const day = String(row.date.getDate()).padStart(2, '0');
        dateStr = `${year}-${month}-${day}`;
      } else {
        dateStr = String(row.date);
      }

      // v5.9: 解析 sparkline_json 数据
      let sparklineData = undefined;
      if (row.sparkline_json) {
        try {
          // PostgreSQL JSONB 字段可能已经是对象或字符串
          sparklineData = typeof row.sparkline_json === 'string'
            ? JSON.parse(row.sparkline_json)
            : row.sparkline_json;
        } catch (e) {
          console.error(`Failed to parse sparkline_json for ${row.symbol}:`, e);
        }
      }

      return {
        ...row,
        date: dateStr,
        close_price: Number(row.close_price),
        ma20_price: Number(row.ma20_price),
        deviation_pct: Number(row.deviation_pct),
        trend_rank: row.trend_rank ? Number(row.trend_rank) : undefined,
        sort_rank: row.sort_rank ? Number(row.sort_rank) : 0,
        change_pct: row.change_pct !== null ? Number(row.change_pct) : null,
        trend_pct: row.trend_pct !== null ? Number(row.trend_pct) : null,
        sparkline_data: sparklineData,
      };
    });

    // 按 sort_rank 排序（v5.3 支持全球指数与贵金属）
    return data.sort((a, b) => {
      // 先按 category 排序（宽基在前）
      if (a.category !== b.category) {
        const isBroadA = a.category === 'broad';
        const isBroadB = b.category === 'broad';
        if (isBroadA && !isBroadB) return -1;
        if (!isBroadA && isBroadB) return 1;
      }
      // 同category内按 sort_rank 排序
      return (a.sort_rank || 0) - (b.sort_rank || 0);
    });

  } catch (error) {
    console.error('Database Query Error:', error);
    return [];
  } finally {
    client.release();
  }
}

export default async function Home() {
  // 获取市场数据
  const marketData = await getLatestMarketData();
  
  // 获取最新的数据更新日期 - 从数据库直接查询最大日期
  let latestDate = new Date().toISOString().split('T')[0];
  const client = await pool.connect();
  try {
    const result = await client.query(`
      SELECT TO_CHAR(MAX(date), 'YYYY-MM-DD') as latest_date
      FROM fishbowl_daily d
      JOIN monitor_config c ON d.symbol = c.symbol
      WHERE c.is_active = true
    `);
    
    if (result.rows.length > 0 && result.rows[0].latest_date) {
      if (result.rows[0].latest_date instanceof Date) {
        // 使用本地时区格式化日期，避免 UTC 时区转换问题
        const date = result.rows[0].latest_date;
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        latestDate = `${year}-${month}-${day}`;
      } else {
        latestDate = String(result.rows[0].latest_date);
      }
    }
  } catch (error) {
    console.error('Error getting latest date:', error);
  } finally {
    client.release();
  }

  return (
    <div className="min-h-screen bg-muted/30 flex flex-col">
      {/* 主内容区 */}
      <main className="flex-1">
        {/* 顶部 Header: 更新为鱼盆趋势雷达标题 */}
        <div className="container mx-auto py-10 space-y-8">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
            <div className="space-y-2">
              <h1 className="text-4xl font-bold tracking-tight">
                鱼盆·ETF 趋势罗盘
              </h1>
              <p className="text-muted-foreground text-lg">
                基于鱼盆模型的ETF轮动与大势择时系统
              </p>
              <p className="text-sm text-muted-foreground/80">
                数据更新日期：{latestDate}
              </p>
            </div>
            <div className="flex items-center gap-4">
              {/* 使用指南按钮 */}
              <ProjectIntro />
            </div>
          </div>

          {/* 全景战术驾驶舱 */}
          <MarketHeader />

          {/* 鱼盆表格 - 分组渲染 */}
          <FishbowlTable data={marketData} />
        </div>
      </main>

      {/* 页脚 */}
      <Footer />
    </div>
  );
}
