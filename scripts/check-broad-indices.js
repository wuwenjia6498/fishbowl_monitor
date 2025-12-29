#!/usr/bin/env node
/**
 * 检查宽基指数版块的表达一致性
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

async function checkBroadIndices() {
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL
  });

  try {
    console.log('🔍 检查宽基指数版块的表达一致性\n');

    const query = `
      SELECT
        d.symbol,
        c.name,
        c.category,
        d.date,
        d.status,
        d.close_price,
        d.ma20_price,
        d.deviation_pct,
        d.signal_tag,
        d.sparkline_json
      FROM fishbowl_daily d
      JOIN monitor_config c ON d.symbol = c.symbol
      WHERE c.category = 'broad'
        AND c.is_active = true
      ORDER BY c.sort_rank, d.date DESC
    `;

    const result = await pool.query(query);

    // 按symbol分组，只取每个symbol的最新记录
    const latestRecords = new Map();
    for (const row of result.rows) {
      if (!latestRecords.has(row.symbol)) {
        latestRecords.set(row.symbol, row);
      }
    }

    console.log(`找到 ${latestRecords.size} 个宽基指数\n`);
    console.log('='.repeat(100));

    let inconsistentCount = 0;

    for (const [symbol, row] of latestRecords) {
      const closePrice = parseFloat(row.close_price);
      const ma20Price = parseFloat(row.ma20_price);
      const dbDeviation = parseFloat(row.deviation_pct);

      // 实际计算
      const actualDeviation = (closePrice - ma20Price) / ma20Price;
      const actualIsBullish = closePrice > ma20Price;

      // 状态字段判断
      const statusIsBullish = row.status === 'YES';

      // 偏离度符号判断
      const deviationIsPositive = dbDeviation > 0;

      // 信号标签判断
      const signalIsBullish = ['BREAKOUT', 'STRONG', 'OVERHEAT'].includes(row.signal_tag);

      // 解析sparkline
      let sparklineIsBullish = null;
      let sparklineLastDate = null;
      if (row.sparkline_json) {
        const sparklineData = typeof row.sparkline_json === 'string'
          ? JSON.parse(row.sparkline_json)
          : row.sparkline_json;

        if (sparklineData && sparklineData.length > 0) {
          const lastPoint = sparklineData[sparklineData.length - 1];
          sparklineIsBullish = lastPoint.price > lastPoint.ma20;
          sparklineLastDate = lastPoint.date;
        }
      }

      // 检查一致性
      const allBullish = [statusIsBullish, deviationIsPositive, signalIsBullish, sparklineIsBullish];
      const bullishCount = allBullish.filter(v => v === true).length;
      const bearishCount = allBullish.filter(v => v === false).length;

      const isInconsistent = bullishCount > 0 && bearishCount > 0;

      if (isInconsistent) {
        inconsistentCount++;
        console.log(`\n⚠️  ${row.name} (${row.symbol})`);
      } else {
        console.log(`\n✅ ${row.name} (${row.symbol})`);
      }

      console.log(`   日期: ${row.date.toISOString().split('T')[0]}`);
      console.log(`   收盘价: ${closePrice.toFixed(2)}, MA20: ${ma20Price.toFixed(2)}`);
      console.log(`   实际偏离: ${(actualDeviation * 100).toFixed(4)}%`);
      console.log(`   数据库偏离: ${(dbDeviation * 100).toFixed(4)}%`);

      console.log('\n   【各组件判断】');
      console.log(`   - 状态字段(${row.status}): ${statusIsBullish ? '多头🔴' : '空头🟢'}`);
      console.log(`   - 偏离度(${(dbDeviation * 100).toFixed(2)}%): ${deviationIsPositive ? '正🔴' : '负🟢'}`);
      console.log(`   - 信号标签(${row.signal_tag}): ${signalIsBullish ? '多头🔴' : '空头🟢'}`);
      console.log(`   - Sparkline判断: ${sparklineIsBullish !== null ? (sparklineIsBullish ? '多头🔴' : '空头🟢') : '无数据'}`);

      if (isInconsistent) {
        console.log('\n   【不一致原因】');

        // 检查价格和MA20的关系
        const priceDiff = closePrice - ma20Price;
        const priceDiffPct = (priceDiff / ma20Price) * 100;

        console.log(`   价格差: ${priceDiff.toFixed(4)} (${priceDiffPct.toFixed(4)}%)`);

        if (Math.abs(priceDiffPct) <= 1) {
          console.log(`   ⚠️  价格在±1%缓冲带内，可能触发缓冲带逻辑`);
        }

        // 检查status和实际判断
        if (statusIsBullish !== actualIsBullish) {
          console.log(`   ⚠️  状态字段(${row.status})与实际判断(${actualIsBullish ? 'YES' : 'NO'})不一致`);
          console.log(`       → 这是缓冲带逻辑的结果，状态维持之前的值`);
        }

        // 检查偏离度和status
        if (statusIsBullish !== deviationIsPositive) {
          console.log(`   ⚠️  状态字段和偏离度符号不一致`);
          console.log(`       → 状态: ${row.status} (${statusIsBullish ? '多头' : '空头'})`);
          console.log(`       → 偏离度: ${(dbDeviation * 100).toFixed(4)}% (${deviationIsPositive ? '正' : '负'})`);
        }

        // 检查sparkline日期
        if (sparklineLastDate) {
          const dbDate = row.date.toISOString().split('T')[0];
          if (dbDate !== sparklineLastDate) {
            console.log(`   ⚠️  Sparkline数据日期不一致: DB(${dbDate}) vs Sparkline(${sparklineLastDate})`);
          }
        }
      }

      console.log('-'.repeat(100));
    }

    console.log(`\n📊 统计: 共 ${latestRecords.size} 个宽基指数，其中 ${inconsistentCount} 个存在不一致`);

  } catch (error) {
    console.error('❌ 错误:', error);
  } finally {
    await pool.end();
  }
}

checkBroadIndices();
