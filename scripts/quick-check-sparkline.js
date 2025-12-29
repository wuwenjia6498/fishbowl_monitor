// 快速检查 sparkline_json 数据状态
const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({ connectionString: process.env.DATABASE_URL });

async function checkSparkline() {
  const client = await pool.connect();
  
  try {
    console.log('=' .repeat(60));
    console.log('检查 sparkline_json 数据状态');
    console.log('='.repeat(60));
    
    // 1. 检查最新日期
    const dateQuery = 'SELECT MAX(date) as latest_date FROM fishbowl_daily';
    const dateResult = await client.query(dateQuery);
    const latestDate = dateResult.rows[0].latest_date;
    console.log(`\n📅 数据库最新日期: ${latestDate}\n`);
    
    // 2. 检查所有资产的 sparkline 状态
    const query = `
      SELECT 
        c.name,
        d.symbol,
        d.date,
        CASE 
          WHEN d.sparkline_json IS NULL THEN '❌ NULL'
          WHEN jsonb_array_length(d.sparkline_json) = 0 THEN '⚠️ 空数组'
          ELSE '✅ 有数据 (' || jsonb_array_length(d.sparkline_json)::text || ' 个点)'
        END as status,
        CASE 
          WHEN d.sparkline_json IS NOT NULL AND jsonb_array_length(d.sparkline_json) > 0
          THEN d.sparkline_json->-1->>'date'
          ELSE NULL
        END as last_point_date
      FROM fishbowl_daily d
      JOIN monitor_config c ON d.symbol = c.symbol
      WHERE d.date = $1
        AND c.category = 'broad'
      ORDER BY c.sort_rank
      LIMIT 15
    `;
    
    const result = await client.query(query, [latestDate]);
    
    console.log('宽基指数的趋势图数据状态:\n');
    console.log('名称'.padEnd(15) + '代码'.padEnd(15) + '状态'.padEnd(25) + '最后数据点日期');
    console.log('-'.repeat(70));
    
    for (const row of result.rows) {
      console.log(
        row.name.padEnd(15) + 
        row.symbol.padEnd(15) + 
        row.status.padEnd(25) + 
        (row.last_point_date || 'N/A')
      );
    }
    
    // 3. 抽查一条完整数据
    if (result.rows.length > 0) {
      const sampleSymbol = result.rows[0].symbol;
      console.log(`\n🔬 抽查 ${result.rows[0].name} (${sampleSymbol}) 的完整数据:\n`);
      
      const detailQuery = `
        SELECT sparkline_json
        FROM fishbowl_daily
        WHERE symbol = $1 AND date = $2
      `;
      const detailResult = await client.query(detailQuery, [sampleSymbol, latestDate]);
      
      if (detailResult.rows[0]?.sparkline_json) {
        const data = detailResult.rows[0].sparkline_json;
        console.log(`  数据点总数: ${data.length}`);
        if (data.length > 0) {
          console.log(`  第一个点: ${JSON.stringify(data[0])}`);
          console.log(`  最后一个点: ${JSON.stringify(data[data.length - 1])}`);
          console.log(`  预期日期: ${latestDate}`);
          console.log(`  实际日期: ${data[data.length - 1].date}`);
          console.log(`  ${data[data.length - 1].date === latestDate.toISOString().split('T')[0] ? '✅' : '❌'} 日期匹配`);
        }
      } else {
        console.log('  ❌ sparkline_json 为空或 NULL');
      }
    }
    
  } catch (error) {
    console.error('❌ 查询失败:', error.message);
  } finally {
    client.release();
    await pool.end();
  }
}

checkSparkline();

