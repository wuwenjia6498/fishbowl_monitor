# 🚀 市场概览功能设置指南

## 问题诊断

当前错误：`relation "market_overview" does not exist`

**原因**：数据库中还没有创建 `market_overview` 表。

---

## 解决方案

### 方法1️⃣：使用 Python 脚本（推荐）

在项目根目录运行：

```bash
python scripts/init_market_overview.py
```

### 方法2️⃣：手动执行 SQL

如果 Python 脚本失败，可以手动执行 SQL：

#### 步骤 A：检查数据库连接

打开 `.env` 文件，确认 `DATABASE_URL` 已正确配置：

```env
DATABASE_URL=postgresql://用户名:密码@主机:端口/数据库名
```

#### 步骤 B：使用数据库客户端执行

**选项1：使用 psql 命令行**

```bash
# 方式1：直接执行 SQL 文件
psql -d 数据库名 -f scripts/create_market_overview.sql

# 方式2：使用环境变量中的连接字符串
psql $DATABASE_URL -f scripts/create_market_overview.sql
```

**选项2：使用 pgAdmin 或其他数据库工具**

1. 打开你的 PostgreSQL 数据库管理工具
2. 连接到数据库
3. 执行以下 SQL：

```sql
-- 创建市场概览表
DROP TABLE IF EXISTS market_overview CASCADE;

CREATE TABLE market_overview (
    date DATE PRIMARY KEY,
    data JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_market_overview_date ON market_overview(date DESC);
```

#### 步骤 C：验证表已创建

在数据库中运行：

```sql
SELECT * FROM market_overview;
```

如果没有报错（结果为空是正常的），说明表创建成功！

---

### 方法3️⃣：检查数据库服务

如果连接失败，可能是数据库服务未启动：

**Windows:**
```bash
# 检查 PostgreSQL 服务状态
Get-Service -Name postgresql*

# 启动服务（如果已停止）
Start-Service -Name postgresql-x64-[版本号]
```

**Mac/Linux:**
```bash
# 检查服务状态
pg_ctl status

# 启动服务
brew services start postgresql  # Mac (Homebrew)
sudo service postgresql start    # Linux
```

---

## 完成后的步骤

### 1. 运行 ETL 脚本生成数据

```bash
python scripts/etl.py
```

这会：
- 更新所有 ETF/指数数据
- 自动生成市场概览数据并写入 `market_overview` 表

### 2. 刷新浏览器

访问 http://localhost:3001（或 3000），你将看到全新的 **全景战术驾驶舱**！

---

## 故障排除

### 问题：Python 找不到文件

**解决方案**：确保在项目根目录运行命令

```bash
# 先切换到项目目录
cd e:\000-cursor学习\fishbowl_monitor

# 再运行脚本
python scripts/init_market_overview.py
```

### 问题：数据库连接被拒绝

**可能原因：**
1. PostgreSQL 服务未启动
2. `.env` 中的 `DATABASE_URL` 配置错误
3. 防火墙阻止连接

**解决方案：**
1. 检查并启动 PostgreSQL 服务
2. 验证 `.env` 中的连接字符串格式
3. 确保端口（默认 5432）可访问

### 问题：表已存在但数据为空

**解决方案**：运行 ETL 脚本生成数据

```bash
python scripts/etl.py
```

---

## 需要帮助？

如果以上方法都不行，请提供：
1. 错误信息截图
2. 数据库类型和版本
3. `.env` 文件配置（隐藏敏感信息）

祝你使用愉快！🎉






