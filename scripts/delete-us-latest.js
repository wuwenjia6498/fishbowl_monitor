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

async function deleteUSLatest() {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });

  try {
    console.log('删除美股指数的最新记录...\n');

    const symbols = ['IXIC', 'SPX', 'DJI'];

    for (const symbol of symbols) {
      // 查找最新日期
      const findQuery = 'SELECT date FROM fishbowl_daily WHERE symbol = $1 ORDER BY date DESC LIMIT 1';
      const result = await pool.query(findQuery, [symbol]);

      if (result.rows.length > 0) {
        const latestDate = result.rows[0].date;
        console.log(`${symbol}: 最新日期 ${latestDate.toISOString().split('T')[0]}`);

        // 删除
        const deleteQuery = 'DELETE FROM fishbowl_daily WHERE symbol = $1 AND date = $2';
        await pool.query(deleteQuery, [symbol, latestDate]);
        console.log(`  ✓ 已删除\n`);
      } else {
        console.log(`${symbol}: 没有数据\n`);
      }
    }

    console.log('完成！现在可以重新运行ETL。');

  } finally {
    await pool.end();
  }
}

deleteUSLatest();
