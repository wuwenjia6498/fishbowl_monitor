import { Pool } from 'pg';

// 确保在生产环境中只创建一个连接池实例 (Next.js Hot Reload 兼容)
const globalForDb = globalThis as unknown as { conn: Pool | undefined };

const conn = globalForDb.conn ?? new Pool({
  connectionString: process.env.POSTGRES_URL, // 确保 .env 中配置了此变量
  // 生产环境建议配置 ssl
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : undefined,
});

if (process.env.NODE_ENV !== 'production') globalForDb.conn = conn;

export default conn;





