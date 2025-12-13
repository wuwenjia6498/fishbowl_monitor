import React from 'react';
import { MonitorConfig, FishbowlDaily, TrendStatus, SignalTag } from '@/types'; // 假设 types.ts 在根目录或 @/types
import { ArrowUpRight, TrendingUp, TrendingDown, Activity, Hash } from 'lucide-react'; // 需安装: npm install lucide-react

// 组合类型：包含配置信息的日报数据
export interface EtfCardProps extends FishbowlDaily {
  name: string; // 来自 monitor_config
  category: string; // 来自 monitor_config (broad/industry)
  industry_level?: string; // 行业层级：分组名称
  dominant_etf?: string | null; // 龙头ETF代码
  investment_logic?: string | null; // 投资逻辑说明（Markdown格式）
  top_holdings?: string | null; // v5.4: 核心持仓（Markdown格式的前十大重仓股）
  holdings_updated_at?: string | null; // v5.4: 持仓数据更新时间
  sort_rank?: number; // 排序等级
}

const EtfCard: React.FC<{ data: EtfCardProps }> = ({ data }) => {
  const isBullish = data.status === TrendStatus.YES;
  
  // 格式化百分比
  const formatPct = (val: number) => `${(val * 100).toFixed(2)}%`;
  
  // 状态颜色映射
  const statusColors = isBullish
    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
    : "bg-slate-50 text-slate-600 border-slate-200";

  const statusText = isBullish ? "多头" : "空头";
  const StatusIcon = isBullish ? TrendingUp : TrendingDown;

  return (
    <div className="group relative flex flex-col justify-between p-5 bg-white border border-gray-100 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 ease-out hover:-translate-y-0.5">
      {/* 顶部：名称与代码 */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="font-semibold text-gray-900 text-lg tracking-tight">{data.name}</h3>
          <p className="text-xs text-gray-400 font-mono mt-0.5">{data.symbol}</p>
        </div>
        
        {/* 状态徽章 (Badge) */}
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium ${statusColors}`}>
          <StatusIcon className="w-3.5 h-3.5" />
          <span>{statusText}</span>
        </div>
      </div>

      {/* 中部：价格核心数据 */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-400 mb-1">收盘价</p>
          <div className="text-xl font-bold text-gray-900 tabular-nums">
            {data.close_price.toLocaleString()}
          </div>
        </div>
        <div>
          <p className="text-xs text-gray-400 mb-1">MA20</p>
          <div className="text-sm font-medium text-gray-500 tabular-nums mt-1.5">
            {Number(data.ma20_price).toLocaleString()}
          </div>
        </div>
      </div>

      {/* 底部：信号与排名 */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-50 mt-auto">
        {/* 左侧：信号标签 (如果有) */}
        <div className="flex gap-2">
          {data.signal_tag && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-blue-50 text-blue-600 border border-blue-100">
              <Activity className="w-3 h-3 mr-1" />
              {data.signal_tag}
            </span>
          )}
        </div>

        {/* 右侧：排名 */}
        {data.trend_rank && (
          <div className="flex items-center text-gray-400 text-xs" title="趋势强度排名">
            <Hash className="w-3 h-3 mr-0.5" />
            <span className="font-medium">{data.trend_rank}</span>
          </div>
        )}
      </div>
      
      {/* 装饰：偏离率指示条 (可选视觉增强) */}
      <div className="absolute bottom-0 left-5 right-5 h-0.5 bg-gray-100 overflow-hidden rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
         <div 
           className={`h-full ${isBullish ? 'bg-emerald-400' : 'bg-gray-300'}`} 
           style={{ width: `${Math.min(Math.abs(data.deviation_pct) * 500, 100)}%` }} // 简单可视化偏离度
         />
      </div>
    </div>
  );
};

export default EtfCard;




