# 鱼盆趋势雷达 (Fishbowl Monitor)

基于 Tushare 数据和 Vercel Postgres 的 A 股指数趋势跟踪系统。

## 🎯 系统概述

鱼盆趋势雷达是一个基于 20 日均线策略的市场监控应用，通过±1%缓冲带机制防抖动，提供交易信号和 ETF 操作建议。

## 📊 核心业务逻辑

### 1. 技术指标
- **MA20**: 20日简单移动平均线
- **偏离率**: `(收盘价 - MA20) / MA20`

### 2. 信号判定 (带缓冲带)
- **转多**: `Price > MA20 * 1.01`
- **转空**: `Price < MA20 * 0.99`
- **维持**: 价格在±1%之间保持昨日状态

### 3. 信号标签
- **BREAKOUT**: 状态=YES 且 持续天数<=3
- **STRONG**: 状态=YES 且 0.02<=偏离率<=0.15
- **OVERHEAT**: 状态=YES 且 偏离率>0.15
- **SLUMP**: 状态=NO 且 偏离率>-0.15
- **EXTREME_BEAR**: 状态=NO 且 偏离率<-0.15

## 🛠️ 技术架构

### 后端
- **数据库**: Vercel Postgres (Neon)
- **ETL**: Python + Tushare + psycopg2
- **连接**: 强制 SSL 连接，确保安全性

### 前端接口
- **类型定义**: 完整的 TypeScript 接口
- **数据格式**: 支持分页、筛选、排序
- **实时更新**: WebSocket 支持

## 📁 文件结构

```
fishbowl_monitor/
├── schema.sql          # 数据库表结构
├── etl.py             # 完整 ETL 脚本
├── etl_test.py        # 简化测试版本
├── types.ts           # TypeScript 接口定义
├── test_connection.py # 连接测试脚本
├── setup_database.py  # 数据库初始化脚本
├── check_data.py      # 数据检查脚本
├── .env               # 环境变量配置
└── README.md          # 项目说明
```

## 🚀 快速开始

### 1. 环境配置
创建 `.env` 文件：
```env
POSTGRES_URL=postgresql://username:password@host:port/database?sslmode=require
TUSHARE_TOKEN=your_tushare_token_here
```

### 2. 依赖安装
```bash
pip install python-dotenv psycopg2-binary pandas tushare
```

### 3. 数据库初始化
```bash
python setup_database.py
```

### 4. 连接测试
```bash
python test_connection.py
```

### 5. 运行 ETL
```bash
# 完整版本 (可能较慢)
python etl.py

# 测试版本 (推荐)
python etl_test.py
```

### 6. 数据检查
```bash
python check_data.py
```

## 📊 当前状态

### 监控指数
- **000300.SH**: 沪深300
- **399006.SZ**: 创业板指  
- **000905.SH**: 中证500
- **000852.SH**: 中证1000

### 最新数据
- **数据日期**: 2025-12-05
- **总记录数**: 76条
- **覆盖率**: 沪深300指数 (2024-12-09 至 2025-12-05)
- **最新信号**: SLUMP (弱势)

### 沪深300最新状态
- **收盘价**: 4584.54
- **MA20**: 4569.38
- **状态**: NO (看空)
- **偏离率**: 0.33%
- **信号标签**: SLUMP

## 🔧 核心特性

### 1. 安全连接
- 强制 SSL 连接 Vercel Postgres
- 环境变量安全管理
- 幂等性 UPSERT 操作

### 2. 防抖动机制
- ±1% 缓冲带避免频繁信号切换
- 持续天数统计
- 智能信号生成

### 3. 完整类型系统
- TypeScript 枚举和接口
- 完整的 API 响应结构
- 分页和筛选支持

## 📈 使用场景

1. **市场监控**: 实时跟踪主要指数趋势
2. **ETF 投资**: 基于 20 日均线的操作建议
3. **风险管理**: 过热和超跌信号预警
4. **量化回测**: 历史信号分析和验证

## 🛡️ 注意事项

1. **数据来源**: 基于 Tushare 免费 API，有调用频率限制
2. **延迟**: 数据为 T+1，非实时数据
3. **风险**: 投资有风险，信号仅供参考
4. **扩展**: 可扩展支持更多指数和技术指标

## 📞 技术支持

系统已验证运行在 Vercel Postgres (Neon) 环境，支持：
- ✅ Tushare API 连接
- ✅ 数据库连接和操作  
- ✅ ETL 数据处理
- ✅ 信号计算逻辑
- ✅ 前端接口定义

系统准备就绪，可直接部署到 Vercel 平台。