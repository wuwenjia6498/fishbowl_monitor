#!/usr/bin/env node
/**
 * 验证 sparkline 数据是否正确生成
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

async function verifySparklineData() {
  const client = new Client({
    connectionString: process.env.DATABASE_URL,
  });

  try {
    console.log('🔌 连接到数据库...');
    await client.connect();
    console.log('✅ 数据库连接成功\n');

    // 查询 sparkline 数据
    const query = `
      SELECT
        symbol,
        date,
        sparkline_json,
        jsonb_array_length(sparkline_json) as data_points
      FROM fishbowl_daily
      WHERE sparkline_json IS NOT NULL
      ORDER BY date DESC, symbol
      LIMIT 5;
    `;

    console.log('📊 查询 sparkline 数据...\n');
    const result = await client.query(query);

    if (result.rows.length === 0) {
      console.log('⚠️  没有找到 sparkline 数据');
      return;
    }

    console.log(`✅ 找到 ${result.rows.length} 条记录\n`);
    console.log('示例数据:');
    console.log('='.repeat(80));

    result.rows.forEach((row, index) => {
      console.log(`\n${index + 1}. ${row.symbol} (${row.date})`);
      console.log(`   数据点数量: ${row.data_points}`);

      if (row.sparkline_json) {
        const data = row.sparkline_json;
        console.log(`   首个数据点: ${JSON.stringify(data[0])}`);
        console.log(`   最后数据点: ${JSON.stringify(data[data.length - 1])}`);
      }
    });

    console.log('\n' + '='.repeat(80));
    console.log('\n✅ sparkline 数据验证完成！');

  } catch (error) {
    console.error('❌ 验证失败:', error.message);
    console.error(error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

verifySparklineData();
