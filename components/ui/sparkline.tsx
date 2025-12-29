'use client';

import React from 'react';
import { SparklineDataPoint } from '@/types';

interface SparklineProps {
  data: SparklineDataPoint[];
  width?: number;
  height?: number;
  showMA20?: boolean;
  className?: string;
  status?: 'YES' | 'NO';  // 可选：直接传递状态，避免判断不一致
}

/**
 * Sparkline 迷你趋势图组件
 * 使用 SVG 绘制价格和 MA20 的折线图
 */
export const Sparkline: React.FC<SparklineProps> = ({
  data,
  width = 120,
  height = 40,
  showMA20 = true,
  className = '',
  status,  // 接收可选的状态参数
}) => {
  if (!data || data.length === 0) {
    return (
      <div
        className={`flex items-center justify-center ${className}`}
        style={{ width, height }}
      >
        <span className="text-xs text-gray-400">暂无数据</span>
      </div>
    );
  }

  // 提取价格和 MA20 数据
  const prices = data.map(d => d.price);
  const ma20s = data.map(d => d.ma20);

  // 计算数据范围
  const allValues = showMA20 ? [...prices, ...ma20s] : prices;
  const minValue = Math.min(...allValues);
  const maxValue = Math.max(...allValues);
  const valueRange = maxValue - minValue || 1; // 避免除以0

  // 计算坐标点
  const padding = 2; // SVG 内边距
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  const getX = (index: number) => {
    return padding + (index / (data.length - 1 || 1)) * chartWidth;
  };

  const getY = (value: number) => {
    return padding + chartHeight - ((value - minValue) / valueRange) * chartHeight;
  };

  // 生成价格线路径
  const pricePath = data
    .map((point, index) => {
      const x = getX(index);
      const y = getY(point.price);
      return `${index === 0 ? 'M' : 'L'} ${x},${y}`;
    })
    .join(' ');

  // 生成 MA20 线路径
  const ma20Path = showMA20
    ? data
        .map((point, index) => {
          const x = getX(index);
          const y = getY(point.ma20);
          return `${index === 0 ? 'M' : 'L'} ${x},${y}`;
        })
        .join(' ')
    : '';

  // v6.3 System Audit: 颜色判断基于偏离度正负
  // Rule of Truth: deviation > 0 (price > ma20) -> 红色(多头), deviation < 0 -> 绿色(空头)
  // 不再依赖status参数（因缓冲带逻辑会滞后），而是直接基于最后一个点的真实偏离度
  const lastPoint = data[data.length - 1];
  const isBullish = lastPoint.price > lastPoint.ma20;

  // 中国习惯：多头红色，空头绿色
  const lineColor = isBullish ? '#ef4444' : '#10b981';

  return (
    <div 
      className={`relative overflow-visible ${className}`} 
      style={{ 
        width: `${width}px`, 
        height: `${height}px`,
        minWidth: `${width}px`,
        minHeight: `${height}px`
      }}
    >
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="overflow-visible"
        style={{
          display: 'block',
          width: '100%',
          height: '100%'
        }}
      >
        {/* MA20 线（灰色虚线） */}
        {showMA20 && ma20Path && (
          <path
            d={ma20Path}
            fill="none"
            stroke="#94a3b8"
            strokeWidth="1"
            strokeDasharray="2,2"
            opacity="0.6"
          />
        )}

        {/* 价格线（根据趋势显示不同颜色） */}
        {pricePath && (
          <path
            d={pricePath}
            fill="none"
            stroke={lineColor}
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {/* 最后一个点（圆点） */}
        <circle
          cx={getX(data.length - 1)}
          cy={getY(lastPoint.price)}
          r="2"
          fill={lineColor}
        />
      </svg>
    </div>
  );
};

export default Sparkline;
