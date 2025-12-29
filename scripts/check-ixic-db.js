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
      process.env[match[1].trim()] = match[2].trim().replace(/^["']|["']$/g, '');
    }
  });
}

loadEnv();

async function checkIXICRecords() {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });

  try {
    const query = `
      SELECT date, close_price, ma20_price, status, created_at
      FROM fishbowl_daily
      WHERE symbol = 'IXIC'
      ORDER BY date DESC
      LIMIT 10
    `;

    const result = await pool.query(query);

    console.log('IXIC 数据库记录（最近10条）：\n');
    result.rows.forEach(row => {
      const dateStr = row.date.toISOString().split('T')[0];
      const createdStr = new Date(row.created_at).toISOString().replace('T', ' ').slice(0, 19);
      console.log(`日期: ${dateStr}, 收盘: ${row.close_price}, MA20: ${row.ma20_price}, 状态: ${row.status}, 创建时间: ${createdStr}`);
    });

  } finally {
    await pool.end();
  }
}

checkIXICRecords();
