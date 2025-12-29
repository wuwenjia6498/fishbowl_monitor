#!/usr/bin/env node
/**
 * 查询黄金价格及其日期
 */

const { readFileSync } = require('fs');
const { Client } = require('pg');
const { join } = require('path');

// 手动读取 .env 文件
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
    console.error('警告: 无法读取 .env 文件');
  }
}

loadEnv();

async function checkGoldData() {
  const client = new Client({
    connectionString: process.env.DATABASE_URL,
  });

  try {
    console.log('🔌 连接到数据库...');
    await client.connect();
    console.log('✅ 数据库连接成功\n');

    // 查询黄金相关数据
    const query = `
      SELECT
        m.symbol,
        m.name,
        d.date,
        d.close_price,
        d.change_pct,
        d.status
      FROM fishbowl_daily d
      JOIN monitor_config m ON d.symbol = m.symbol
      WHERE m.symbol IN ('Au99.99', '518880.SH')
      ORDER BY d.symbol, d.date DESC
      LIMIT 10;
    `;

    console.log('💰 查询黄金数据...\n');
    const result = await client.query(query);

    if (result.rows.length === 0) {
      console.log('⚠️  没有找到黄金数据');
      return;
    }

    console.log('='.repeat(80));
    console.log('黄金价格数据：');
    console.log('='.repeat(80));

    result.rows.forEach((row, index) => {
      const dateStr = row.date instanceof Date
        ? row.date.toISOString().split('T')[0]
        : row.date;

      console.log(`\n${index + 1}. ${row.name} (${row.symbol})`);
      console.log(`   日期: ${dateStr}`);
      console.log(`   价格: ${row.close_price}`);
      console.log(`   涨跌: ${row.change_pct ? (row.change_pct * 100).toFixed(2) + '%' : 'N/A'}`);
      console.log(`   状态: ${row.status}`);
    });

    console.log('\n' + '='.repeat(80));

    // 查询市场概览中的黄金数据
    const overviewQuery = `
      SELECT
        date,
        data->'goldPrice' as gold_price
      FROM market_overview
      ORDER BY date DESC
      LIMIT 1;
    `;

    console.log('\n📊 查询市场概览中的黄金数据...\n');
    const overviewResult = await client.query(overviewQuery);

    if (overviewResult.rows.length > 0) {
      const overview = overviewResult.rows[0];
      const dateStr = overview.date instanceof Date
        ? overview.date.toISOString().split('T')[0]
        : overview.date;

      console.log(`市场概览日期: ${dateStr}`);
      console.log(`国际黄金数据:`, overview.gold_price);
    }

    console.log('\n='.repeat(80));

  } catch (error) {
    console.error('❌ 查询失败:', error.message);
    console.error(error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

checkGoldData();
