#!/usr/bin/env node
/**
 * 查询市场概览的完整数据
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

async function checkMarketOverview() {
  const client = new Client({
    connectionString: process.env.DATABASE_URL,
  });

  try {
    console.log('🔌 连接到数据库...');
    await client.connect();
    console.log('✅ 数据库连接成功\n');

    // 查询最新的市场概览数据
    const query = `
      SELECT
        date,
        data,
        updated_at
      FROM market_overview
      ORDER BY date DESC
      LIMIT 1;
    `;

    console.log('📊 查询最新市场概览数据...\n');
    const result = await client.query(query);

    if (result.rows.length === 0) {
      console.log('⚠️  没有找到市场概览数据');
      return;
    }

    const overview = result.rows[0];
    const dateStr = overview.date instanceof Date
      ? overview.date.toISOString().split('T')[0]
      : overview.date;

    console.log('='.repeat(80));
    console.log(`市场概览日期: ${dateStr}`);
    console.log(`更新时间: ${overview.updated_at}`);
    console.log('='.repeat(80));
    console.log('\n完整数据:');
    console.log(JSON.stringify(overview.data, null, 2));
    console.log('\n' + '='.repeat(80));

    // 专门查看黄金数据
    if (overview.data && overview.data.gold) {
      console.log('\n💰 黄金数据:');
      console.log(`  名称: ${overview.data.gold.name}`);
      console.log(`  价格: ${overview.data.gold.unit}${overview.data.gold.price}/盎司`);
      console.log(`  涨跌: ${overview.data.gold.change > 0 ? '+' : ''}${overview.data.gold.change}`);
    } else {
      console.log('\n⚠️  市场概览中没有黄金数据');
    }

  } catch (error) {
    console.error('❌ 查询失败:', error.message);
    console.error(error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

checkMarketOverview();
