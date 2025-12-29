#!/usr/bin/env node
/**
 * 调试脚本:检查数据库中各指数的 sparkline_json 数据
 */

const { Pool } = require('pg');
const { readFileSync } = require('fs');
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
    console.error('❌ 无法读取 .env 文件:', error.message);
    process.exit(1);
  }
}

loadEnv();

if (!process.env.DATABASE_URL) {
  console.error('❌ DATABASE_URL 环境变量未设置');
  process.exit(1);
}

async function checkSparklineData() {
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL
  });

  try {
    console.log('🔍 检查 sparkline_json 数据...\n');

    const query = `
      SELECT DISTINCT ON (d.symbol)
        d.symbol,
        c.name,
        c.category,
        d.date,
        d.sparkline_json,
        CASE
          WHEN d.sparkline_json IS NULL THEN 'NULL'
          WHEN d.sparkline_json::text = '[]' THEN 'EMPTY_ARRAY'
          WHEN d.sparkline_json::text = '' THEN 'EMPTY_STRING'
          ELSE 'HAS_DATA'
        END as data_status,
        LENGTH(d.sparkline_json::text) as json_length
      FROM fishbowl_daily d
      JOIN monitor_config c ON d.symbol = c.symbol
      WHERE c.is_active = true
      ORDER BY d.symbol, d.date DESC
    `;

    const result = await pool.query(query);

    console.log(`总共找到 ${result.rows.length} 个指数:\n`);

    let hasDataCount = 0;
    let noDataCount = 0;
    let emptyDataCount = 0;

    for (const row of result.rows) {
      let statusEmoji = '';
      if (row.data_status === 'HAS_DATA') {
        statusEmoji = '✅';
        hasDataCount++;

        // 尝试解析JSON看看数据点数量
        try {
          const data = typeof row.sparkline_json === 'string'
            ? JSON.parse(row.sparkline_json)
            : row.sparkline_json;
          console.log(`${statusEmoji} ${row.name} (${row.symbol})`);
          console.log(`   日期: ${row.date}, 数据点: ${data.length}, 字节: ${row.json_length}`);

          // 显示第一个和最后一个数据点
          if (data.length > 0) {
            console.log(`   第一个点: ${JSON.stringify(data[0])}`);
            console.log(`   最后一个点: ${JSON.stringify(data[data.length - 1])}`);
          }
        } catch (e) {
          console.log(`${statusEmoji} ${row.name} (${row.symbol}) - 解析错误: ${e.message}`);
        }
      } else if (row.data_status === 'EMPTY_ARRAY') {
        statusEmoji = '⚠️';
        emptyDataCount++;
        console.log(`${statusEmoji} ${row.name} (${row.symbol}) - 空数组`);
      } else {
        statusEmoji = '❌';
        noDataCount++;
        console.log(`${statusEmoji} ${row.name} (${row.symbol}) - ${row.data_status}`);
      }
      console.log(`   分类: ${row.category}, 最新日期: ${row.date}\n`);
    }

    console.log('\n📊 统计:');
    console.log(`  ✅ 有数据: ${hasDataCount}`);
    console.log(`  ⚠️  空数组: ${emptyDataCount}`);
    console.log(`  ❌ 无数据: ${noDataCount}`);

  } catch (error) {
    console.error('❌ 错误:', error);
  } finally {
    await pool.end();
  }
}

checkSparklineData();
