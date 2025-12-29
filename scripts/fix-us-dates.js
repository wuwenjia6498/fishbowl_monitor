#!/usr/bin/env node
const { Pool } = require('pg');
const { readFileSync } = require('fs');
const { join } = require('path');

function loadEnv() {
  const envPath = join(__dirname, '..', '.env');
  const envContent = readFileSync(envPath, 'utf8');
  envContent.split('\n').forEach(line => {
    const match = line.match(/^([^=:#]+)=(.*)$/);
    if (match) {
      process.env[match[1].trim()] = match[2].trim().replace(/^[\"']|[\"']$/g, '');
    }
  });
}

loadEnv();

async function fixUSDates() {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });

  try {
    console.log('修正美股指数日期（加1天与sparkline对齐）\n');

    const symbols = ['IXIC', 'SPX', 'DJI'];

    for (const symbol of symbols) {
      console.log(`处理 ${symbol}...`);

      // 更新所有记录的date字段，加1天
      const updateQuery = `
        UPDATE fishbowl_daily
        SET date = date + INTERVAL '1 day'
        WHERE symbol = $1
      `;

      const result = await pool.query(updateQuery, [symbol]);
      console.log(`  ✓ 更新了 ${result.rowCount} 条记录\n`);
    }

    console.log('完成！现在检查结果：\n');

    // 验证结果
    for (const symbol of symbols) {
      const checkQuery = `
        SELECT date, close_price
        FROM fishbowl_daily
        WHERE symbol = $1
        ORDER BY date DESC
        LIMIT 2
      `;

      const result = await pool.query(checkQuery, [symbol]);
      console.log(`${symbol}:`);
      result.rows.forEach(row => {
        console.log(`  ${row.date.toISOString().split('T')[0]}: ${row.close_price}`);
      });
      console.log();
    }

  } finally {
    await pool.end();
  }
}

fixUSDates();
