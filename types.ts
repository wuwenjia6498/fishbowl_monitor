// 鱼盆趋势雷达 (Fishbowl Monitor) 前端接口定义
// 适配 Vercel Postgres 数据库

// v5.9 Sparkline 数据点
export interface SparklineDataPoint {
  date: string;      // 日期 (格式: "MM-DD")
  price: number;     // 收盘价
  ma20: number;      // 20日均线
  change: number;    // v7.1: 当日涨幅 (百分比形式，如 1.52 表示 +1.52%)
}

// 信号标签枚举
export enum SignalTag {
  BREAKOUT = 'BREAKOUT',          // 启动：状态=YES 且 持续天数<=3
  STRONG = 'STRONG',              // 主升：状态=YES 且 0.02<=偏离率<=0.15
  OVERHEAT = 'OVERHEAT',          // 过热：状态=YES 且 偏离率>0.15
  SLUMP = 'SLUMP',                // 弱势：状态=NO 且 偏离率>-0.15
  EXTREME_BEAR = 'EXTREME_BEAR'   // 超跌：状态=NO 且 偏离率<-0.15
}

// 趋势状态枚举
export enum TrendStatus {
  YES = 'YES',    // 看多
  NO = 'NO'       // 看空
}

// 监控配置表接口
export interface MonitorConfig {
  symbol: string;                    // 指数代码，如 '000300.SH'
  name: string;                      // 指数名称，如 '沪深300'
  category: string;                  // 指数类别，如 '大盘指数'
  is_active: boolean;                // 是否激活监控
  created_at: string;                // 创建时间 (ISO 8601)
  updated_at: string;                // 更新时间 (ISO 8601)
}

// 鱼盆日线数据表接口
export interface FishbowlDaily {
  id?: number;                       // 主键ID (后端生成)
  date: string;                      // 交易日期 (YYYY-MM-DD)
  symbol: string;                    // 指数代码
  close_price: number;               // 收盘价
  ma20_price: number;                // 20日均线价格
  status: TrendStatus;               // 趋势状态 (看多/看空)
  deviation_pct: number;             // 偏离率百分比 (小数形式，如 0.05 表示 5%)
  duration_days: number;             // 当前状态持续天数
  trend_rank?: number;               // 趋势排名 (按偏离率绝对值排序)
  signal_tag: SignalTag;             // 信号标签
  change_pct?: number | null;        // v4.7: 当日涨幅 (小数形式，如 0.023 表示 2.3%)
  trend_pct?: number | null;         // v4.7: 区间涨幅 (从当前状态起始点到现在的涨幅)
  sparkline_data?: SparklineDataPoint[];  // v5.9: 近30日趋势数据（用于迷你图展示）
  created_at: string;                // 创建时间 (ISO 8601)
  updated_at: string;                // 更新时间 (ISO 8601)
}

// API 响应基础结构
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// 仪表盘数据接口
export interface DashboardData {
  date: string;                      // 数据日期
  summary: {
    total_monitored: number;         // 总监控数量
    bullish_count: number;           // 看多数量 (status='YES')
    bearish_count: number;           // 看空数量 (status='NO')
    strongest_signal: SignalTag;     // 最强信号标签统计
    average_deviation: number;       // 平均偏离率
  };
  indices: IndexData[];              // 指数数据列表
}

// 单个指数数据
export interface IndexData {
  symbol: string;
  name: string;
  close_price: number;
  ma20_price: number;
  status: TrendStatus;
  deviation_pct: number;
  duration_days: number;
  trend_rank: number;
  signal_tag: SignalTag;
}

// 历史趋势数据
export interface TrendHistory {
  symbol: string;
  data: HistoricalDataPoint[];
  metadata: {
    start_date: string;
    end_date: string;
    total_records: number;
  };
}

// 历史数据点
export interface HistoricalDataPoint {
  date: string;
  close_price: number;
  ma20_price: number;
  status: TrendStatus;
  deviation_pct: number;
  signal_tag: SignalTag;
  duration_days: number;
}

// 实时数据推送 (WebSocket)
export interface RealtimeUpdate {
  type: 'price_update' | 'signal_change' | 'ranking_update';
  symbol: string;
  timestamp: string;
  data: Partial<FishbowlDaily>;
}

// 筛选和排序参数
export interface FilterParams {
  symbol?: string[];                 // 指定指数代码列表
  status?: TrendStatus;              // 状态筛选
  signal_tag?: SignalTag;            // 信号标签筛选
  start_date?: string;               // 开始日期
  end_date?: string;                 // 结束日期
  min_deviation?: number;            // 最小偏离率
  max_deviation?: number;            // 最大偏离率
  category?: string;                 // 指数类别筛选
  is_active?: boolean;               // 是否激活状态
}

// 排序参数
export interface SortParams {
  field: keyof IndexData | 'created_at' | 'updated_at';  // 排序字段
  direction: 'asc' | 'desc';        // 排序方向
}

// 分页参数
export interface PaginationParams {
  page: number;                      // 页码 (从1开始)
  limit: number;                     // 每页数量
}

// 请求参数组合
export interface QueryParams extends FilterParams, SortParams, PaginationParams {}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
  total_pages: number;
}

// ETL 任务状态
export interface ETLTaskStatus {
  task_id: string;
  symbol: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;                  // 0-100
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  records_processed: number;
}

// 数据库统计信息
export interface DatabaseStats {
  total_configs: number;
  active_configs: number;
  total_daily_records: number;
  latest_data_date: string;
  records_by_signal: Record<SignalTag, number>;
  records_by_status: Record<TrendStatus, number>;
}

// ETF 操作建议接口
export interface ETFRecommendation {
  symbol: string;
  action: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;               // 置信度 0-100
  reason: string;                    // 操作理由
  target_price?: number;             // 目标价格
  stop_loss?: number;                // 止损价格
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  expected_return?: number;          // 预期收益率
}

// 市场整体情绪接口
export interface MarketSentiment {
  date: string;
  overall_sentiment: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  sentiment_score: number;           // -100 到 100
  bullish_indices: string[];
  bearish_indices: string[];
  market_breath: {
    advancers: number;               // 上涨指数数量
    decliners: number;               // 下跌指数数量
    unchanged: number;               // 不变指数数量
    bullish_percentage: number;      // 看多占比
  };
  volatility_index: number;          // 市场波动率指数
}

// 风险提示接口
export interface RiskAlert {
  symbol: string;
  alert_type: 'OVERHEAT' | 'EXTREME_DROP' | 'TREND_REVERSAL' | 'HIGH_VOLATILITY';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  message: string;
  timestamp: string;
  trigger_value: number;             // 触发阈值
  current_value: number;             // 当前值
  is_resolved: boolean;              // 是否已解决
  resolved_at?: string;
}

// 技术指标接口
export interface TechnicalIndicators {
  symbol: string;
  date: string;
  rsi: number;                       // RSI 指标
  macd: {
    macd: number;
    signal: number;
    histogram: number;
  };
  bollinger_bands: {
    upper: number;
    middle: number;
    lower: number;
  };
  volume_ratio: number;              // 成交量比率
}

// 性能指标接口
export interface PerformanceMetrics {
  symbol: string;
  period: string;                    // 时间周期，如 '1M', '3M', '6M', '1Y'
  return_rate: number;               // 收益率
  max_drawdown: number;              // 最大回撤
  volatility: number;                // 波动率
  sharpe_ratio: number;              // 夏普比率
  win_rate: number;                  // 胜率
}