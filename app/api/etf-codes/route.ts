import pool from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET() {
  const client = await pool.connect();
  try {
    const query = `
      SELECT DISTINCT 
        c.symbol,
        c.name,
        c.dominant_etf,
        c.category
      FROM monitor_config c
      WHERE c.is_active = true 
        AND c.dominant_etf IS NOT NULL
      ORDER BY c.category, c.symbol
    `;
    
    const result = await client.query(query);
    
    return Response.json({
      success: true,
      data: result.rows
    });
  } catch (error) {
    console.error('Database Query Error:', error);
    return Response.json({
      success: false,
      error: 'Failed to fetch ETF codes'
    }, { status: 500 });
  } finally {
    client.release();
  }
}