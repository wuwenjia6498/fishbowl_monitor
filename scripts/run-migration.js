#!/usr/bin/env node
/**
 * 数据库迁移脚本
 * 用于执行 SQL 迁移文件
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
        const value = match[2].trim().replace(/^["']|["']$/g, ''); // 移除引号
        process.env[key] = value;
      }
    });
  } catch (error) {
    console.error('警告: 无法读取 .env 文件');
  }
}

loadEnv();

async function runMigration(migrationFile) {
  const client = new Client({
    connectionString: process.env.DATABASE_URL,
  });

  try {
    console.log('🔌 连接到数据库...');
    await client.connect();
    console.log('✅ 数据库连接成功\n');

    // 读取迁移文件
    const migrationPath = join(__dirname, '..', 'sql', 'migrations', migrationFile);
    console.log(`📄 读取迁移文件: ${migrationFile}`);
    const sql = readFileSync(migrationPath, 'utf8');

    // 执行 SQL
    console.log('🚀 执行迁移...\n');
    console.log('SQL 内容:');
    console.log('-'.repeat(60));
    console.log(sql);
    console.log('-'.repeat(60));
    console.log();

    await client.query(sql);

    console.log('✅ 迁移执行成功！\n');
  } catch (error) {
    console.error('❌ 迁移执行失败:', error.message);
    console.error('\n详细错误信息:');
    console.error(error);
    process.exit(1);
  } finally {
    await client.end();
    console.log('🔌 数据库连接已关闭');
  }
}

// 从命令行参数获取迁移文件名
const migrationFile = process.argv[2] || 'add_sparkline_json.sql';

console.log('='.repeat(60));
console.log('数据库迁移工具');
console.log('='.repeat(60));
console.log();

runMigration(migrationFile);
