# 鱼盆趋势雷达 (Fishbowl Monitor)

> 基于 20 日均线策略的 A 股指数与行业 ETF 趋势跟踪系统

[![Version](https://img.shields.io/badge/version-7.2.0-blue.svg)](https://github.com/wuwenjia6498/fishbowl_monitor)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Next.js](https://img.shields.io/badge/Next.js-16.0-black.svg)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)

## 🎯 系统概述

鱼盆趋势雷达是一个基于 20 日均线策略的市场监控应用，通过 ±1% 缓冲带机制防抖动，提供交易信号和 ETF 操作建议。

**核心特性：**
- ✅ 宽基指数与行业 ETF 全覆盖
- ✅ 实时趋势图表展示（支持 3M/6M/1Y 切换）
- ✅ 智能信号识别（启动/主升/过热/超跌）
- ✅ 增量数据更新（v7.0 稳定性升级）
- ✅ 全景战术驾驶舱（A股基准、美股风向、领涨先锋）

## 📊 核心业务逻辑

### 1. 技术指标

- **MA20**: 20 日简单移动平均线
- **偏离率**: `(收盘价 - MA20) / MA20`
- **持续天数**: 当前趋势连续维持的交易日数量
- **区间涨幅**: 从信号发出日至今的累计涨跌幅

### 2. 信号判定（带缓冲带）

- **转多**: `Price > MA20 × 1.01`
- **转空**: `Price < MA20 × 0.99`
- **维持**: 价格在 ±1% 之间保持昨日状态

### 3. 信号标签

| 标签 | 条件 | 说明 |
|------|------|------|
| **BREAKOUT** | 状态=YES 且 持续天数≤3 | 🚀 启动信号（刚突破） |
| **STRONG** | 状态=YES 且 2%≤偏离率≤15% | 📈 主升浪（稳健上涨） |
| **OVERHEAT** | 状态=YES 且 偏离率>15% | 🔥 过热警告（可能回调） |
| **SLUMP** | 状态=NO 且 偏离率>-15% | 📉 弱势（下跌或震荡） |
| **EXTREME_BEAR** | 状态=NO 且 偏离率<-15% | 💎 超跌（可能反弹） |

## 🆕 版本更新

### v7.2.0 (2025-12-29)
- ✨ **行业板块增加持续天数字段**
- 🎯 支持排序功能，方便筛选老妖股或新启动板块
- 🎨 BREAKOUT 信号红色高亮显示

### v7.1.1 (2025-01-29)
- ✅ **配置 GitHub Actions 定时任务**（Python 3.11）
- 📊 优化美股数据获取逻辑和容错机制
- 💡 明确指数用途：市场概览用 IXIC（市场情绪），全球指数表格用 NDX（投资标的）
- 📝 完善项目文档和技术说明

### v7.1.0 (2025-12-29)
- ✨ **行业板块增加区间涨幅字段**
- 📊 与宽基指数功能对齐
- 🎨 红涨绿跌配色，等宽字体显示

### v7.0.2 (2025-12-29)
- 🗑️ **移除黄金板块展示**（yfinance API 限流问题）
- 🎨 优化市场概览布局为 3 卡片

### v7.0.1 (2025-12-29)
- 🔧 **自动检测并修复数据点不足问题**
- ⏱️ 优化 API 调用延迟（避免限流）
- 📊 优先使用数据库数据，减少 API 依赖

### v7.0.0 (2025-12-29) 🚀
- ✨ **趋势图增量追加模式**（核心升级）
- 🎯 稳定性大幅提升，不再每日全量拉取
- 💾 节省 95% 的 API 调用
- 🔄 自动去重和滑动窗口裁剪
- 📝 新增完整的问题排查文档

详细更新内容见 [CHANGELOG_v7.0.md](CHANGELOG_v7.0.md)

## 🛠️ 技术架构

### 后端

- **框架**: Next.js 16 (App Router)
- **数据库**: Vercel Postgres (Neon)
- **ETL**: Python 3.11+ + Tushare + psycopg2
- **数据源**: Tushare API + yfinance（美股实时数据）

### 前端

- **框架**: React 19 + TypeScript
- **UI 库**: Tailwind CSS + shadcn/ui
- **图表**: 自定义 SVG Sparkline
- **状态管理**: React Hooks

### 部署

- **平台**: Vercel
- **CI/CD**: GitHub Actions（定时任务：美股时段 08:00 / A股时段 19:00）
- **SSL**: 强制 SSL 连接，确保安全性

## 📁 项目结构

```
fishbowl_monitor/
├── app/                    # Next.js App Router
│   ├── page.tsx           # 主页面
│   └── api/               # API 路由
├── components/            # React 组件
│   ├── business/         # 业务组件
│   │   └── fishbowl-table.tsx
│   ├── ui/               # UI 组件
│   └── market-header.tsx # 市场概览
├── scripts/              # Python 脚本
│   ├── etl.py           # 主 ETL 脚本
│   ├── fix_sparkline_v7.py  # 修复脚本
│   └── requirements.txt  # Python 依赖
├── sql/                  # 数据库脚本
│   └── schema.sql       # 表结构
├── .env                 # 环境变量（不提交）
└── README.md            # 项目说明

```

## 🚀 快速开始

### 1. 环境配置

创建 `.env.local` 文件：

```env
# Vercel Postgres
POSTGRES_URL=postgresql://username:password@host:port/database?sslmode=require

# Tushare API
TUSHARE_TOKEN=your_tushare_token_here
```

### 2. 安装依赖

```bash
# 前端依赖
npm install

# 后端依赖（Python）
pip install -r scripts/requirements.txt
```

### 3. 数据库初始化

```bash
# 执行 SQL 脚本创建表结构
psql $POSTGRES_URL < sql/schema.sql

# 或使用 Python 脚本初始化（推荐）
python scripts/init_db.py
```

### 4. 运行 ETL 更新

```bash
# 首次运行或修复数据
python scripts/fix_sparkline_v7.py

# 每日更新（本地测试）
python scripts/etl.py
```

### 5. 配置 GitHub Actions（推荐）

将项目推送到 GitHub 后：
1. 进入 **Settings** → **Secrets and variables** → **Actions**
2. 添加以下 Secrets：
   - `DATABASE_URL`: Vercel Postgres 连接字符串
   - `TUSHARE_TOKEN`: Tushare API Token
3. 定时任务将自动运行：
   - 美股时段：北京时间 08:00（周二至周六）
   - A股时段：北京时间 19:00（周一至周五）

### 6. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000 查看应用。

## 📊 监控资产

### 宽基指数（13个）

- **A股指数**: 上证50、沪深300、创业板指、科创50、中证500、中证1000、中证2000、北证50
- **全球指数**: 纳指100（NDX）、标普500（SPX）、恒生指数（HSI）、恒生科技（HKTECH）
- **贵金属现货**: 上海金（Au99.99）、上海银（Ag(T+D)）

### 行业 ETF（25+个）

分为 5 大板块：

1. **科技 (TMT)**: 人工智能、半导体、新能源车、光伏等
2. **高端制造**: 军工、通信、电气设备等
3. **医药消费**: 医药、食品饮料、家电等
4. **周期资源**: 有色金属、煤炭、化工等
5. **金融**: 证券、银行、非银金融等

## 🔧 核心功能

### 1. 增量追加模式（v7.0）

- **旧逻辑**：每天全量拉取 250 天历史数据 ❌
- **新逻辑**：基于数据库已有数据增量追加 ✅

**优势**：
- 稳定性提升 95%
- API 调用减少 95%
- 更新速度提升 10x

### 2. 趋势图交互

- 点击趋势图可放大查看
- 支持 3M/6M/1Y 周期切换
- 实时数据更新（250 个数据点）

### 3. 智能排序与筛选

- **区间涨幅排序**：找到盈利最强的板块
- **持续天数排序**：找到稳固趋势或新启动板块
- **偏离度排序**：识别过热或超跌机会

### 4. 全景战术驾驶舱

- **A股基准**：上证指数 + 深证成指 + 两市成交额
- **美股风向**：纳斯达克（IXIC）+ 标普500（SPX）+ 道琼斯（DJI）
- **领涨先锋**：Top 3 行业 ETF（实时）

> 💡 **设计说明：** 市场概览展示**综合指数**（IXIC，3000+只股票，代表整体市场情绪），而全球指数表格展示**纳指100**（NDX，可投资标的）。两者用途不同，不是重复。

## 📈 使用场景

### 1. 趋势跟随策略
- 关注 **BREAKOUT** 信号（持续天数 1-3 天）
- 买入：状态转 YES 且偏离度 <5%
- 卖出：状态转 NO 或偏离度 >15%

### 2. 行业轮动策略
- 按**区间涨幅**降序排序，找到领涨板块
- 按**持续天数**升序排序，找到新启动板块
- 结合**状态**和**偏离度**确认趋势强度

### 3. 风险管理
- **过热警告**：偏离度 >15%，考虑减仓
- **超跌反弹**：偏离度 <-15%，可能超跌反弹
- **长期趋势**：持续天数 >30 天，注意获利了结

## 🛡️ 注意事项

⚠️ **重要提示**

1. **数据延迟**: 基于 Tushare 免费 API，数据为 T+1（非实时）
2. **API 限制**: Tushare 有调用频率限制，避免频繁运行 ETL
3. **投资风险**: 信号仅供参考，投资有风险，入市需谨慎
4. **数据质量**: 美股数据可能受 yfinance API 限流影响

## 📞 技术支持

### 问题排查

遇到问题请查看：
- [v7.0 问题排查指南](v7.0_troubleshooting.md)
- [v7.0 更新日志](CHANGELOG_v7.0.md)
- [v7.1 美股指数修复文档](docs/fix_us_index_inconsistency_v7.1.md)

### 常见问题

**Q1: 趋势图显示"暂无数据"？**  
A: 运行 `python scripts/fix_sparkline_v7.py` 修复

**Q2: ETL 运行报错？**  
A: 检查 `.env` 配置，确认 Tushare Token 有效

**Q3: 如何添加新的监控资产？**  
A: 修改 `sql/schema.sql` 中的 `monitor_config` 表

## 📄 开源协议

MIT License

## 🙏 致谢

- [Tushare](https://tushare.pro/) - 金融数据接口
- [Next.js](https://nextjs.org/) - React 框架
- [Vercel](https://vercel.com/) - 部署平台
- [shadcn/ui](https://ui.shadcn.com/) - UI 组件库

---

**系统准备就绪，可直接部署到 Vercel 平台 🚀**

如有问题或建议，欢迎提 Issue 或 PR！
