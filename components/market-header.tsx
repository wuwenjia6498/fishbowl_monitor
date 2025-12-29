'use client';

import React, { useEffect, useState } from 'react';
import { Copy, Check, TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

// 数据类型定义
interface AShareData {
  sh: { price: number; change: number; status: 'YES' | 'NO' };
  sz: { price: number; change: number; status: 'YES' | 'NO' };
  volume: { amount: number; tag: string; ratio: number };
}

interface USShareData {
  name: string;
  price: number;
  change: number;
}

interface GoldData {
  name: string;
  price: number;
  change: number;
  unit: string;
}

interface LeaderData {
  name: string;
  change: number;
  code: string;
}

interface MarketOverviewData {
  a_share: AShareData | null;
  us_share: USShareData[];
  gold: GoldData;
  leaders: LeaderData[];
}

interface MarketOverviewResponse {
  success: boolean;
  data?: {
    date: string;
    overview: MarketOverviewData;
    updatedAt: string;
  };
  error?: string;
}

/**
 * 全景战术驾驶舱 - 市场概览组件
 * 展示 A股基准、美股风向、避险资产、领涨先锋四大战术卡片
 */
const MarketHeader: React.FC = () => {
  const [data, setData] = useState<MarketOverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  // 获取市场概览数据
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/market-overview');
        const result: MarketOverviewResponse = await response.json();
        
        if (result.success && result.data) {
          setData(result.data.overview);
        }
      } catch (error) {
        console.error('Failed to fetch market overview:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // 复制ETF代码到剪贴板
  const copyToClipboard = async (code: string) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopiedCode(code);
      setTimeout(() => setCopiedCode(null), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  // 格式化价格
  const formatPrice = (price: number, decimals: number = 2) => {
    return price.toLocaleString('zh-CN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  // 格式化涨跌幅
  const formatChange = (change: number) => {
    const sign = change > 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  // 获取涨跌颜色
  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-red-600';
    if (change < 0) return 'text-green-600';
    return 'text-gray-500';
  };

  if (loading) {
    return (
      <div className="w-full bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-3xl p-8 shadow-sm border border-slate-200/50">
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-4">
            <div className="h-4 bg-slate-200 rounded w-3/4"></div>
            <div className="h-4 bg-slate-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="w-full mb-8">
      {/* 3个战术卡片：A股、美股、领涨板块 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        
        {/* 卡片 1: A股 */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">
              A股
            </h3>
          </div>
          
          {data.a_share && (
            <div className="space-y-3">
              {/* 上证指数 */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">上证指数</span>
                <div className="text-right">
                  <div className="font-mono text-sm font-medium text-gray-900">
                    {formatPrice(data.a_share.sh.price)}
                  </div>
                  <div className={`text-xs font-medium ${getChangeColor(data.a_share.sh.change)}`}>
                    {formatChange(data.a_share.sh.change)}
                  </div>
                </div>
              </div>

              {/* 深证成指 */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">深证成指</span>
                <div className="text-right">
                  <div className="font-mono text-sm font-medium text-gray-900">
                    {formatPrice(data.a_share.sz.price)}
                  </div>
                  <div className={`text-xs font-medium ${getChangeColor(data.a_share.sz.change)}`}>
                    {formatChange(data.a_share.sz.change)}
                  </div>
                </div>
              </div>

              {/* 成交量 */}
              <div className="pt-3 border-t border-gray-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">两市成交</span>
                  <div>
                    <span className="font-mono text-sm font-medium text-gray-900">
                      {formatPrice(data.a_share.volume.amount, 0)}亿
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 卡片 2: 美股 */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
          <div className="mb-4">
            <h3 className="font-semibold text-gray-900">
              美股
            </h3>
          </div>
          
          <div className="space-y-3">
            {data.us_share.map((item, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm text-gray-600">
                  {/* v7.1: 后端已统一返回"纳指100"，直接显示即可 */}
                  {item.name}
                </span>
                <div className="text-right">
                  <div className="font-mono text-sm font-medium text-gray-900">
                    {formatPrice(item.price)}
                  </div>
                  <div className={`text-xs font-medium ${getChangeColor(item.change)}`}>
                    {formatChange(item.change)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 卡片 3: 黄金 - v7.0.2 已隐藏（yfinance API 限流问题）*/}
        {/* 如需恢复，取消注释以下代码块 */}
        {/* 
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">
              黄金
            </h3>
          </div>
          
          <div className="flex flex-col items-center justify-center space-y-2">
            <div className="text-xs text-gray-600">{data.gold.name}</div>
            <div className="flex items-baseline gap-1">
              <span className="text-sm text-gray-500">{data.gold.unit}</span>
              <span className="text-2xl font-bold text-gray-900 font-mono">
                {formatPrice(data.gold.price)}
              </span>
            </div>
            <div className={`text-base font-semibold ${getChangeColor(data.gold.change)}`}>
              {formatChange(data.gold.change)}
            </div>
          </div>
        </div>
        */}

        {/* 卡片 3: 领涨板块 */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">
              领涨板块
            </h3>
            <span className="text-xs text-gray-400">Top 3</span>
          </div>
          
          <div className="space-y-3">
            {data.leaders.map((leader, index) => (
              <div key={index} className="flex items-center justify-between group">
                <div className="flex items-center gap-2">
                  <span className="flex items-center justify-center w-5 h-5 rounded-full bg-rose-100 text-rose-600 text-xs font-bold">
                    {index + 1}
                  </span>
                  <span className="text-sm text-gray-700 font-medium">{leader.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-red-600">
                    +{leader.change.toFixed(2)}%
                  </span>
                  <button
                    onClick={() => copyToClipboard(leader.code)}
                    className="p-1.5 rounded-lg hover:bg-white/80 transition-colors"
                    title={`复制代码: ${leader.code}`}
                  >
                    {copiedCode === leader.code ? (
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <Copy className="w-3.5 h-3.5 text-gray-400 group-hover:text-gray-600" />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketHeader;








