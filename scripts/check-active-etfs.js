const pool = require('./lib/db').pool;

async function checkActiveETFs() {
  const client = await pool.connect();
  try {
    const result = await client.query(`
      SELECT DISTINCT ON (d.symbol)
        d.symbol,
        d.date,
        d.sparkline_json,
        c.name,
        c.category,
        c.is_active
      FROM fishbowl_daily d
      JOIN monitor_config c ON d.symbol = c.symbol
      WHERE c.is_active = true
      ORDER BY d.symbol, d.date DESC
    `);
    
    console.log('所有活跃ETF及其分类:');
    console.log('=====================================');
    result.rows.forEach(row => {
      const sparklineData = typeof row.sparkline_json === 'string' ? JSON.parse(row.sparkline_json) : row.sparkline_json;
      console.log(`${row.symbol} | ${row.category || 'N/A'} | ${sparklineData?.length || 0} 数据点 | ${row.name}`);
    });
    console.log(`总计: ${result.rows.length} 个ETF`);
  } catch (error) {
    console.error('Error:', error);
  } finally {
    client.release();
    await pool.end();
  }
}

checkActiveETFs();