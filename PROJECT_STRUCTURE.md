# 项目文件结构说明

## 📁 目录结构（清理后）

```
fishbowl_monitor/
├── 📁 app/                         # Next.js App Router
│   ├── api/                        # API 路由
│   │   ├── market-overview/        # 市场概览 API
│   │   └── etf-codes/              # ETF 代码 API
│   ├── globals.css                 # 全局样式
│   ├── layout.tsx                  # 根布局
│   └── page.tsx                    # 主页面
│
├── 📁 components/                   # React 组件
│   ├── business/                   # 业务组件
│   │   ├── fishbowl-table.tsx      # 核心表格组件
│   │   └── project-intro.tsx       # 项目介绍弹窗
│   ├── ui/                         # UI 基础组件（shadcn/ui）
│   │   ├── badge.tsx
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── hover-card.tsx
│   │   ├── sparkline.tsx           # 趋势图组件
│   │   ├── table.tsx
│   │   ├── tabs.tsx
│   │   └── ...
│   ├── footer.tsx                  # 页脚
│   ├── market-header.tsx           # 市场概览头部
│   ├── trend-lens.tsx              # 趋势图放大镜
│   └── MarkdownRenderer.tsx        # Markdown 渲染
│
├── 📁 lib/                          # 工具函数
│   ├── db.ts                       # 数据库连接
│   └── utils.ts                    # 通用工具
│
├── 📁 scripts/                      # Python 脚本
│   ├── etl.py                      # 🔥 主 ETL 脚本
│   ├── init_db.py                  # 数据库初始化
│   ├── fix_sparkline_v7.py         # v7.0 修复工具
│   ├── update_holdings.py          # ETF 持仓更新
│   ├── init_market_overview.py     # 市场概览初始化
│   ├── migrate.py                  # 数据库迁移
│   ├── run_migration.py            # 迁移执行器
│   ├── run_migration_holdings.py   # 持仓迁移
│   ├── requirements.txt            # Python 依赖
│   ├── add_investment_logic_column.sql  # SQL 迁移
│   ├── add_sort_rank.sql           # SQL 迁移
│   └── create_market_overview.sql  # SQL 迁移
│
├── 📁 sql/                          # 数据库脚本
│   ├── schema.sql                  # 完整表结构
│   └── migrations/                 # 数据库迁移
│       ├── add_change_and_trend_pct.sql
│       ├── add_sparkline_json.sql
│       └── add_top_holdings.sql
│
├── 📄 配置文件
│   ├── .env                        # 环境变量（不提交）
│   ├── .gitignore                  # Git 忽略规则
│   ├── .gitattributes              # Git 属性
│   ├── components.json             # shadcn/ui 配置
│   ├── next.config.mjs             # Next.js 配置
│   ├── package.json                # Node.js 依赖
│   ├── postcss.config.js           # PostCSS 配置
│   ├── tailwind.config.ts          # Tailwind CSS 配置
│   ├── tsconfig.json               # TypeScript 配置
│   └── types.ts                    # 全局类型定义
│
├── 📄 文档
│   ├── README.md                   # 🔥 项目说明
│   ├── CHANGELOG_v7.0.md           # v7.0 更新日志
│   ├── v7.0_troubleshooting.md     # 问题排查指南
│   └── PROJECT_STRUCTURE.md        # 本文件
│
└── 📄 工具脚本
    ├── git-push.bat                # Git 推送脚本
    ├── run_etl.bat                 # ETL 快捷方式
    ├── start-dev.ps1               # 开发服务器启动
    ├── restart.ps1                 # 服务器重启
    └── cleanup-project.bat         # 项目清理脚本

```

## 🔑 核心文件说明

### 前端核心

| 文件 | 说明 | 重要性 |
|------|------|--------|
| `app/page.tsx` | 主页面，服务端渲染 | ⭐⭐⭐⭐⭐ |
| `components/business/fishbowl-table.tsx` | 核心表格组件（900+ 行） | ⭐⭐⭐⭐⭐ |
| `components/market-header.tsx` | 市场概览组件 | ⭐⭐⭐⭐ |
| `components/trend-lens.tsx` | 趋势图放大功能 | ⭐⭐⭐⭐ |
| `components/ui/sparkline.tsx` | SVG 趋势图渲染 | ⭐⭐⭐⭐ |

### 后端核心

| 文件 | 说明 | 重要性 |
|------|------|--------|
| `scripts/etl.py` | 主 ETL 脚本（1280+ 行） | ⭐⭐⭐⭐⭐ |
| `scripts/init_db.py` | 数据库初始化 | ⭐⭐⭐⭐ |
| `scripts/fix_sparkline_v7.py` | v7.0 修复工具 | ⭐⭐⭐⭐ |
| `scripts/update_holdings.py` | ETF 持仓更新 | ⭐⭐⭐ |
| `sql/schema.sql` | 完整数据库结构 | ⭐⭐⭐⭐⭐ |

### 配置文件

| 文件 | 说明 | 重要性 |
|------|------|--------|
| `.env` | 环境变量（数据库连接、API Token） | ⭐⭐⭐⭐⭐ |
| `package.json` | Node.js 依赖和脚本 | ⭐⭐⭐⭐⭐ |
| `next.config.mjs` | Next.js 配置 | ⭐⭐⭐⭐ |
| `tailwind.config.ts` | Tailwind CSS 配置 | ⭐⭐⭐⭐ |
| `.gitignore` | Git 忽略规则 | ⭐⭐⭐⭐⭐ |

### 文档

| 文件 | 说明 | 重要性 |
|------|------|--------|
| `README.md` | 项目完整说明 | ⭐⭐⭐⭐⭐ |
| `CHANGELOG_v7.0.md` | v7.0 更新日志 | ⭐⭐⭐⭐ |
| `v7.0_troubleshooting.md` | 问题排查指南 | ⭐⭐⭐⭐ |

## 🗑️ 已清理的文件类型

### 1. 调试脚本（20+ 个）
- `debug_*.py` - 开发调试脚本
- `test_*.py` - 测试脚本
- `check_*.py` - 检查脚本

### 2. 日志和临时文件
- `etl_log.txt`, `etl_log_test.txt`
- `*.db` - 本地数据库文件
- `nul`, `=0.2.0` - 无用文件

### 3. 临时文档
- `task_v7.*.md` - 开发任务文档
- `BUGFIX_*.md` - Bug 修复文档
- `audit_report_*.md` - 审计报告

### 4. 过时文档
- `SETUP_GUIDE.md` - 已合并到 README
- `project_brief.md` - 已合并到 README
- `schema.sql` (根目录) - 使用 sql/schema.sql

### 5. scripts/ 下的临时文件（30+ 个）
- `check-*.js`, `test-*.py`, `debug-*.py`
- `verify-*.js`, `simulate-*.py`
- `manual-*.py`, `quick-*.py`

## 📦 生产部署文件清单

部署到 Vercel 时，实际需要的文件：

```
核心代码：
- app/
- components/
- lib/
- public/ (如果有静态资源)

配置文件：
- next.config.mjs
- package.json
- tailwind.config.ts
- tsconfig.json

环境变量（Vercel 后台配置）：
- POSTGRES_URL
- TUSHARE_TOKEN
```

**不需要部署的文件：**
- `scripts/` - 后端 Python 脚本（本地运行）
- `sql/` - 数据库脚本（一次性初始化）
- `*.bat`, `*.ps1` - 本地工具脚本
- `*.md` - 文档文件

## 🎯 开发工作流

### 日常更新数据
```bash
# Windows
run_etl.bat

# 或直接运行
python scripts/etl.py
```

### 修复趋势图数据
```bash
python scripts/fix_sparkline_v7.py
```

### 更新 ETF 持仓
```bash
python scripts/update_holdings.py
```

### 启动开发服务器
```bash
npm run dev

# 或使用 PowerShell 脚本
.\start-dev.ps1
```

### 推送到 GitHub
```bash
# 双击运行
git-push.bat

# 或手动
git add .
git commit -m "feat: 新功能"
git push
```

## 📊 项目统计

- **总代码行数**: ~15,000 行
- **前端组件**: 20+ 个
- **核心 ETL 脚本**: 1,280+ 行
- **监控资产**: 38 个（8 宽基 + 25 行业 + 5 其他）
- **数据表**: 3 个（monitor_config, fishbowl_daily, market_overview）

---

**最后更新**: 2025-12-29  
**版本**: v7.2.0  
**维护者**: wuwenjia6498

