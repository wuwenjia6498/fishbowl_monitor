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

async function cleanUSData() {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });

  try {
    console.log('清理所有美股指数数据，准备重新获取...\n');

    const symbols = ['IXIC', 'SPX', 'DJI'];

    for (const symbol of symbols) {
      const result = await pool.query('DELETE FROM fishbowl_daily WHERE symbol = $1', [symbol]);
      console.log(`${symbol}: 删除了 ${result.rowCount} 条记录`);
    }

    console.log('\n✅ 清理完成！现在可以运行ETL重新获取数据。');

  } finally {
    await pool.end();
  }
}

cleanUSData();
