#!/usr/bin/env node
/**
 * 检查趋势图颜色和信号标签颜色不一致的问题
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

async function checkMismatch() {
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL
  });

  try {
    console.log('🔍 检查趋势图颜色与信号标签颜色不一致的问题...\n');

    const query = `
      SELECT DISTINCT ON (d.symbol)
        d.symbol,
        c.name,
        d.date,
        d.status,
        d.close_price,
        d.ma20_price,
        d.deviation_pct,
        d.signal_tag,
        d.sparkline_json
      FROM fishbowl_daily d
      JOIN monitor_config c ON d.symbol = c.symbol
      WHERE c.is_active = true
        AND d.sparkline_json IS NOT NULL
      ORDER BY d.symbol, d.date DESC
    `;

    const result = await pool.query(query);

    console.log(`总共检查 ${result.rows.length} 个ETF:\n`);

    let mismatchCount = 0;

    for (const row of result.rows) {
      // 解析 sparkline_json
      const sparklineData = typeof row.sparkline_json === 'string'
        ? JSON.parse(row.sparkline_json)
        : row.sparkline_json;

      if (!sparklineData || sparklineData.length === 0) {
        continue;
      }

      // 获取趋势图最后一个点
      const lastSparkPoint = sparklineData[sparklineData.length - 1];

      // 判断趋势图颜色（基于最后一个点）
      const sparklineIsBullish = lastSparkPoint.price > lastSparkPoint.ma20;
      const sparklineColor = sparklineIsBullish ? '红色' : '绿色';

      // 判断当前记录的状态
      const currentIsBullish = row.status === 'YES';
      const currentPrice = parseFloat(row.close_price);
      const currentMa20 = parseFloat(row.ma20_price);
      const actualIsBullish = currentPrice > currentMa20;

      // 信号标签颜色
      let signalColor = '灰色';
      if (row.signal_tag === 'BREAKOUT' || row.signal_tag === 'STRONG') {
        signalColor = '红色';
      } else if (row.signal_tag === 'SLUMP') {
        signalColor = '绿色';
      } else if (row.signal_tag === 'OVERHEAT') {
        signalColor = '橙色';
      } else if (row.signal_tag === 'EXTREME_BEAR') {
        signalColor = '蓝色';
      }

      // 检查是否不一致
      const sparklineDate = lastSparkPoint.date;
      const currentDate = row.date.toISOString().split('T')[0];

      const hasDateMismatch = sparklineDate !== currentDate;
      const hasColorMismatch = sparklineIsBullish !== actualIsBullish;

      if (hasDateMismatch || hasColorMismatch) {
        mismatchCount++;
        console.log(`⚠️  ${row.name} (${row.symbol})`);
        console.log(`   当前记录日期: ${currentDate}`);
        console.log(`   趋势图最后点: ${sparklineDate}`);
        console.log(`   日期是否一致: ${hasDateMismatch ? '❌ 不一致' : '✅ 一致'}`);
        console.log(`   当前价格: ${currentPrice.toFixed(2)}, MA20: ${currentMa20.toFixed(2)}, 实际多空: ${actualIsBullish ? '多头' : '空头'}`);
        console.log(`   趋势图判断: ${lastSparkPoint.price.toFixed(2)} vs ${lastSparkPoint.ma20.toFixed(2)} = ${sparklineColor}`);
        console.log(`   状态字段: ${row.status} (${currentIsBullish ? '多头' : '空头'})`);
        console.log(`   信号标签: ${row.signal_tag} (${signalColor})`);
        console.log(`   偏离度: ${(row.deviation_pct * 100).toFixed(2)}%`);

        if (hasColorMismatch) {
          console.log(`   🚨 颜色逻辑不匹配！`);
        }
        console.log('');
      }
    }

    if (mismatchCount === 0) {
      console.log('✅ 所有ETF的趋势图颜色和信号标签颜色都一致！');
    } else {
      console.log(`\n📊 发现 ${mismatchCount} 个不一致的情况`);
    }

  } catch (error) {
    console.error('❌ 错误:', error);
  } finally {
    await pool.end();
  }
}

checkMismatch();
