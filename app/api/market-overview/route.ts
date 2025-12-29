import pool from '@/lib/db';

export const dynamic = 'force-dynamic';

/**
 * GET /api/market-overview
 * 获取全景战术驾驶舱数据
 * 返回最新的市场概览数据（A股基准、美股风向、避险资产、领涨先锋）
 */
export async function GET() {
  const client = await pool.connect();
  try {
    const query = `
      SELECT 
        date,
        data,
        updated_at
      FROM market_overview
      ORDER BY date DESC
      LIMIT 1
    `;
    
    const result = await client.query(query);
    
    if (result.rows.length === 0) {
      return Response.json({
        success: false,
        error: 'No market overview data available'
      }, { status: 404 });
    }
    
    const overview = result.rows[0];
    
    return Response.json({
      success: true,
      data: {
        date: overview.date,
        overview: overview.data,
        updatedAt: overview.updated_at
      }
    });
  } catch (error) {
    console.error('Database Query Error:', error);
    return Response.json({
      success: false,
      error: 'Failed to fetch market overview data'
    }, { status: 500 });
  } finally {
    client.release();
  }
}






