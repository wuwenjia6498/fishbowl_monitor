# 鱼盆·ETF 趋势罗盘

<div align="center">

**基于 20 日均线策略的 ETF 轮动与大势择时系统**

[![Next.js](https://img.shields.io/badge/Next.js-16.0-black)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

</div>

## 📊 功能特性

### 核心功能

- ✅ **宽基指数监控**：A股指数、全球指数、贵金属现货
- ✅ **行业 ETF 轮动**：25+ 行业 ETF 分组展示，自动分类
- ✅ **鱼盆信号系统**：基于 20 日均线的 YES/NO 趋势判断
- ✅ **全景战术驾驶舱**：A股基准、美股风向、领涨板块
- ✅ **趋势图可视化**：90 天价格走势图，支持 3M/6M/1Y 切换

### 数据指标

| 指标 | 说明 |
|------|------|
| **现价 & MA20** | 最新点位与 20 日均线 |
| **当日涨幅** | 相对前一交易日的涨跌幅 |
| **状态** | YES（多头）/ NO（空头），含 ±1% 缓冲带 |
| **持续天数** | 当前趋势连续维持的交易日数量 |
| **区间涨幅** | 从信号发出日至今的累计涨跌幅 |
| **偏离度** | 现价距离 MA20 的乖离程度 |

## 🚀 快速开始

### 前置要求

- Node.js >= 18.0.0
- npm >= 9.0.0
- PostgreSQL 数据库
- Python 3.8+
- Tushare Pro Token（数据源）

### 安装步骤

1. **克隆项目**

```bash
git clone https://github.com/wuwenjia6498/fishbowl_monitor.git
cd fishbowl_monitor
```

2. **安装依赖**

```bash
# 前端依赖
npm install

# Python 依赖
pip install -r scripts/requirements.txt
```

3. **配置环境变量**

创建 `.env` 文件：

```env
# 数据库连接
DATABASE_URL=postgresql://user:password@localhost:5432/fishbowl_db

# Tushare Pro Token
TUSHARE_TOKEN=your_tushare_token_here
```

4. **初始化数据库**

```bash
# 运行数据库迁移
python scripts/init_db.py
```

5. **运行 ETL 更新**

```bash
# 首次运行会初始化所有数据
python scripts/etl.py
```

6. **启动开发服务器**

```bash
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000) 查看应用。

## 🛠️ 技术栈

### 前端
- **框架**: Next.js 16 (App Router)
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **UI 组件**: Shadcn UI
- **图表**: Recharts

### 后端
- **API**: Next.js API Routes
- **数据库**: PostgreSQL
- **ORM**: 直接 SQL（psycopg2）

### 数据处理
- **语言**: Python 3.8+
- **数据源**: Tushare Pro API, yfinance
- **库**: pandas, psycopg2, python-dotenv

## 📁 项目结构

```
fishbowl_monitor/
├── app/                    # Next.js App Router
│   ├── page.tsx           # 主页面
│   └── api/               # API 路由
├── components/            # React 组件
│   ├── business/          # 业务组件
│   │   └── fishbowl-table.tsx  # 主表格组件
│   ├── ui/                # UI 组件（Shadcn）
│   └── trend-lens.tsx     # 趋势图放大组件
├── scripts/               # Python ETL 脚本
│   ├── etl.py            # 主 ETL 脚本
│   ├── init_db.py        # 数据库初始化
│   └── requirements.txt  # Python 依赖
├── sql/                   # SQL 脚本
│   ├── schema.sql        # 数据库结构
│   └── migrations/       # 数据库迁移
└── public/               # 静态资源
```

## 📈 数据更新

### 手动更新

```bash
# 更新所有数据
python scripts/etl.py

# 仅更新宽基指数
python scripts/etl.py --category broad

# 仅更新行业 ETF
python scripts/etl.py --category industry
```

### 自动定时更新（推荐）

配置 cron job（Linux/Mac）：

```bash
# 每天下午 4:00 运行
0 16 * * 1-5 cd /path/to/fishbowl_monitor && python scripts/etl.py
```

或使用 Windows 任务计划程序（见 `scripts/SCHEDULER_SETUP.md`）

## 🔄 版本历史

### v7.2 (2025-12-29)
- ✨ 行业板块新增"持续天数"字段
- 📊 支持按持续天数排序

### v7.1 (2025-12-29)
- ✨ 行业板块新增"区间涨幅"字段
- 🎨 与宽基指数保持完全一致的样式

### v7.0 (2025-12-29)
- 🚀 **重大升级**：趋势图增量追加模式
- ⚡ 性能优化：减少 95% 的 API 调用
- 🔧 修复：数据点不足自动重新初始化
- 🎨 前端：移除黄金数据展示（API 限流问题）

### v6.x
- 完善鱼盆信号系统
- 添加全景战术驾驶舱
- 支持全球指数和贵金属

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- [Tushare Pro](https://tushare.pro/) - 数据源
- [Next.js 文档](https://nextjs.org/docs)
- [Shadcn UI](https://ui.shadcn.com/)

---

<div align="center">
Made with ❤️ by AI Assistant
</div>
