#!/usr/bin/env node
/**
 * 验证 sparkline 数据点数量
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
        jsonb_array_length(sparkline_json) as data_points
      FROM fishbowl_daily
      WHERE sparkline_json IS NOT NULL
      ORDER BY date DESC, symbol
      LIMIT 10;
    `;

    console.log('📊 查询 sparkline 数据点数量...\n');
    const result = await client.query(query);

    if (result.rows.length === 0) {
      console.log('⚠️  没有找到 sparkline 数据');
      return;
    }

    console.log(`✅ 找到 ${result.rows.length} 条记录\n`);
    console.log('数据点数量统计:');
    console.log('='.repeat(60));

    const dataPointCounts = {};
    result.rows.forEach((row) => {
      const count = row.data_points;
      if (!dataPointCounts[count]) {
        dataPointCounts[count] = 0;
      }
      dataPointCounts[count]++;
      console.log(`${row.symbol.padEnd(20)} | ${row.data_points} 个数据点`);
    });

    console.log('\n' + '='.repeat(60));
    console.log('\n统计汇总:');
    Object.entries(dataPointCounts).forEach(([count, num]) => {
      console.log(`  ${count} 个数据点: ${num} 条记录`);
    });

    const avgPoints = result.rows.reduce((sum, row) => sum + row.data_points, 0) / result.rows.length;
    console.log(`  平均数据点: ${avgPoints.toFixed(1)}`);

    if (avgPoints >= 240) {
      console.log('\n✅ 数据已成功扩展到约250天！');
    } else if (avgPoints >= 80) {
      console.log('\n⚠️  数据扩展中，目前约90天');
    } else {
      console.log('\n⚠️  数据点较少，可能需要重新运行 ETL');
    }

  } catch (error) {
    console.error('❌ 验证失败:', error.message);
    console.error(error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

verifySparklineData();
