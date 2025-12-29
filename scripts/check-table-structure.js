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

async function checkTableStructure() {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });

  try {
    // 查询表结构
    const query = `
      SELECT
        column_name,
        data_type,
        is_nullable,
        column_default
      FROM information_schema.columns
      WHERE table_name = 'fishbowl_daily'
      ORDER BY ordinal_position
    `;

    const result = await pool.query(query);
    console.log('fishbowl_daily 表结构:\n');
    result.rows.forEach(row => {
      console.log(`${row.column_name}: ${row.data_type} (nullable: ${row.is_nullable})`);
    });

  } finally {
    await pool.end();
  }
}

checkTableStructure();
