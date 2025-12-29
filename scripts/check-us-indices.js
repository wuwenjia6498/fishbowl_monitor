#!/usr/bin/env node
/**
 * 检查美股指数的更新情况
 */

const { Pool } = require('pg');
const { readFileSync } = require('fs');
const { join } = require('path');

function loadEnv() {
  try {
    const envPath = join(__dirname, '..', '.env');
    const envContent = readFileSync(envPath, 'utf8');
    envContent.split('\n').forEach(line => {
      const match = line.match(/^([^=:#]+)=(.*)$/);
      if (match) {
        const key = match[1].trim();
        const value = match[2].trim().replace(/^["']|["']$/g, '');
        process.env[key] = value;
      }
    });
  } catch (error) {
    console.error('❌ 无法读取 .env 文件:', error.message);
    process.exit(1);
  }
}

loadEnv();

async function checkUSIndices() {
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL
  });

  try {
    console.log('🔍 检查美股指数的更新情况\n');
    console.log('='.repeat(80));

    // 查询美股指数的最近5条记录
    const symbols = ['IXIC', 'SPX', 'DJI'];

    for (const symbol of symbols) {
      const query = `
        SELECT
          d.date,
          d.symbol,
          c.name,
          d.close_price,
          d.ma20_price,
          d.status,
          d.sparkline_json
        FROM fishbowl_daily d
        JOIN monitor_config c ON d.symbol = c.symbol
        WHERE d.symbol = $1
        ORDER BY d.date DESC
        LIMIT 5
      `;

      const result = await pool.query(query, [symbol]);

      console.log(`\n📊 ${result.rows[0]?.name || symbol} (${symbol})`);
      console.log('-'.repeat(80));

      if (result.rows.length === 0) {
        console.log('❌ 没有数据');
        continue;
      }

      console.log('最近5条记录：');
      result.rows.forEach((row, idx) => {
        const dateStr = row.date.toISOString().split('T')[0];
        console.log(`  ${idx + 1}. ${dateStr} - 收盘: ${parseFloat(row.close_price).toFixed(2)}, MA20: ${parseFloat(row.ma20_price).toFixed(2)}, 状态: ${row.status}`);
      });

      // 检查sparkline_json
      if (result.rows[0].sparkline_json) {
        const sparklineData = typeof result.rows[0].sparkline_json === 'string'
          ? JSON.parse(result.rows[0].sparkline_json)
          : result.rows[0].sparkline_json;

        if (sparklineData && sparklineData.length > 0) {
          const lastPoint = sparklineData[sparklineData.length - 1];
          console.log(`\nSparkline最后一个点: ${lastPoint.date} (共 ${sparklineData.length} 个点)`);
        }
      } else {
        console.log('\n❌ 没有sparkline数据');
      }
    }

    console.log('\n' + '='.repeat(80));

    // 检查ETL日志或最后更新时间
    console.log('\n🔍 检查配置表中的更新时间\n');
    const configQuery = `
      SELECT
        symbol,
        name,
        is_active,
        updated_at
      FROM monitor_config
      WHERE symbol IN ('IXIC', 'SPX', 'DJI')
      ORDER BY symbol
    `;

    const configResult = await pool.query(configQuery);
    configResult.rows.forEach(row => {
      console.log(`${row.name} (${row.symbol}): is_active=${row.is_active}, updated_at=${row.updated_at}`);
    });

  } catch (error) {
    console.error('❌ 错误:', error);
  } finally {
    await pool.end();
  }
}

checkUSIndices();
