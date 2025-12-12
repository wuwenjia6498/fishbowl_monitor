import React from 'react';
import pool from '@/lib/db';
import FishbowlTable from '@/components/fishbowl-table';
import { EtfCardProps } from '@/components/EtfCard';
import ProjectIntro from '@/components/project-intro';

// 强制动态渲染，因为数据每天会变，我们需要获取最新 DB 状态
export const dynamic = 'force-dynamic';

async function getLatestMarketData(): Promise<EtfCardProps[]> {
  const client = await pool.connect();
  try {
    // 核心查询逻辑：
    // 1. 联表 monitor_config 获取名称 (c.name)
    // 2. 使用 DISTINCT ON (symbol) 获取每个代码最新的一条记录
    // 3. 筛选 is_active = true 的配置
    // 4. v4.6: 包含 investment_logic 投资逻辑说明
    const query = `
      SELECT DISTINCT ON (d.symbol)
        d.date,
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
        c.name,
        c.category as market,
        c.industry_level,
        c.dominant_etf,
        c.sort_rank,
        c.investment_logic
      FROM fishbowl_daily d
      JOIN monitor_config c ON d.symbol = c.symbol
      WHERE c.is_active = true
      ORDER BY d.symbol, d.date DESC;
    `;

    const result = await client.query(query);

    // 数据清洗/转换：确保数字类型正确 (pg driver 有时返回 string)
    const data: EtfCardProps[] = result.rows.map(row => ({
      ...row,
      date: new Date(row.date).toISOString().split('T')[0], // 格式化日期
      close_price: Number(row.close_price),
      ma20_price: Number(row.ma20_price),
      deviation_pct: Number(row.deviation_pct),
      trend_rank: row.trend_rank ? Number(row.trend_rank) : undefined,
      sort_rank: row.sort_rank ? Number(row.sort_rank) : 0,
      change_pct: row.change_pct !== null ? Number(row.change_pct) : null,
      trend_pct: row.trend_pct !== null ? Number(row.trend_pct) : null,
    }));

    // 按 sort_rank 排序（v4.2 纯ETF模式，保证固定顺序）
    return data.sort((a, b) => {
      // 先按 category 排序（宽基在前）
      if (a.market !== b.market) {
        const isBroadA = a.market === '宽基' || a.market === 'broad';
        const isBroadB = b.market === '宽基' || b.market === 'broad';
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
  const marketData = await getLatestMarketData();
  const updateDate = marketData[0]?.date || new Date().toISOString().split('T')[0];

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
            </div>
            <div className="flex items-center gap-4">
              {/* 使用指南按钮 */}
              <ProjectIntro />
            </div>
          </div>
          
          {/* 数据分隔线 */}
          <div className="w-full h-px bg-border" />

          {/* 鱼盆表格 - 分组渲染 */}
          <FishbowlTable data={marketData} />
        </div>
      </main>

      {/* 底部 Footer: 苹果风格简约设计 */}
      <footer className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col items-center justify-center gap-3">
            {/* 数据更新时间 */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                width="16" 
                height="16" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round"
                className="opacity-60"
              >
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              <span>数据更新于：</span>
              <span className="font-mono font-medium text-foreground">{updateDate}</span>
            </div>

            {/* 版权信息 */}
            <div className="text-sm text-muted-foreground">
              <span className="opacity-60">©</span> {new Date().getFullYear()} 鱼盆·ETF 趋势罗盘
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
