'use client';

import React, { useState, useMemo } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Area,
} from 'recharts';
import { SparklineDataPoint } from '@/types';
import { Sparkline } from '@/components/ui/sparkline';

interface TrendLensProps {
  data: SparklineDataPoint[];
  name: string;
  symbol: string;
  status?: 'YES' | 'NO';  // 可选：直接传递状态
}

type TimeRange = '3M' | '6M' | '1Y';

/**
 * 自定义 Tooltip 内容
 */
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const price = payload.find((p: any) => p.dataKey === 'price')?.value;
  const ma20 = payload.find((p: any) => p.dataKey === 'ma20')?.value;

  // 计算偏离度
  const deviation = ma20 ? ((price - ma20) / ma20) * 100 : 0;

  return (
    <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border shadow-lg">
      <p className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">
        {label}
      </p>
      <div className="space-y-1 text-xs">
        <div className="flex items-center justify-between gap-4">
          <span className="text-gray-600 dark:text-gray-400">收盘价:</span>
          <span className="font-mono font-semibold text-gray-900 dark:text-white">
            {price?.toFixed(2)}
          </span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-gray-600 dark:text-gray-400">MA20:</span>
          <span className="font-mono text-gray-700 dark:text-gray-300">
            {ma20?.toFixed(2)}
          </span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-gray-600 dark:text-gray-400">偏离度:</span>
          <span
            className={`font-mono font-medium ${
              deviation > 0 ? 'text-red-500' : deviation < 0 ? 'text-green-500' : 'text-gray-500'
            }`}
          >
            {deviation > 0 ? '+' : ''}
            {deviation.toFixed(2)}%
          </span>
        </div>
      </div>
    </div>
  );
};

/**
 * TrendLens 组件 - 多周期趋势图点击放大查看
 * v5.11 功能：支持 3M/6M/1Y 时间周期切换
 */
export function TrendLens({ data, name, symbol, status }: TrendLensProps) {
  const [range, setRange] = useState<TimeRange>('3M');

  if (!data || data.length === 0) {
    return (
      <div className="h-[40px] w-[120px] flex items-center justify-center">
        <span className="text-xs text-muted-foreground">暂无数据</span>
      </div>
    );
  }

  // 根据选择的时间范围切片数据
  const displayData = useMemo(() => {
    const len = data.length;
    switch (range) {
      case '3M':
        return data.slice(-90); // 近90天
      case '6M':
        return data.slice(-120); // 近半年
      case '1Y':
        return data; // 全部数据（最多250天）
      default:
        return data.slice(-90);
    }
  }, [data, range]);

  // 迷你图数据（固定显示90天）
  const miniData = useMemo(() => data.slice(-90), [data]);

  // v6.3 System Audit: 颜色判断基于偏离度正负
  // Rule of Truth: deviation > 0 (price > ma20) -> 红色(多头), deviation < 0 -> 绿色(空头)
  // 不再依赖status参数（因缓冲带逻辑会滞后），而是直接基于最后一个点的真实偏离度
  const lastPoint = displayData[displayData.length - 1];
  const isUp = lastPoint.price > lastPoint.ma20;
  const lineColor = isUp ? '#ef4444' : '#10b981'; // 多头红色，空头绿色
  const areaColor = isUp ? '#ef4444' : '#10b981';

  return (
    <Dialog>
      <DialogTrigger asChild>
        <div
          className="cursor-pointer hover:opacity-80 transition-opacity"
          title="点击查看详情"
        >
          {/* 复用迷你 Sparkline 作为触发器，固定显示90天 */}
          <Sparkline data={miniData} width={120} height={40} showMA20={true} />
        </div>
      </DialogTrigger>

      <DialogContent className="sm:max-w-[750px]">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold">{name}</span>
              <span className="text-sm font-mono text-muted-foreground">{symbol}</span>
            </div>

            {/* 时间周期切换按钮 */}
            <div className="flex items-center gap-1 bg-muted rounded-lg p-1">
              {(['3M', '6M', '1Y'] as TimeRange[]).map((r) => (
                <button
                  key={r}
                  onClick={() => setRange(r)}
                  className={`px-3 py-1 text-xs font-medium rounded transition-all ${
                    range === r
                      ? 'bg-primary text-primary-foreground shadow'
                      : 'hover:bg-muted-foreground/10 text-muted-foreground'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </DialogTitle>
          <p className="text-xs text-muted-foreground mt-1">
            {range === '3M' && '近3个月价格走势'}
            {range === '6M' && '近6个月价格走势'}
            {range === '1Y' && '近一年价格走势'} • 鼠标悬浮查看详情
          </p>
        </DialogHeader>

        <div className="h-[380px] w-full mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={displayData}
              margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
              {/* 网格线 */}
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke="#e5e7eb"
                opacity={0.5}
              />

              {/* X 轴 */}
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12, fill: '#6b7280' }}
                minTickGap={30}
                tickFormatter={(val) => {
                  // 根据数据量动态调整显示格式
                  if (range === '1Y') {
                    // 一年数据只显示月份
                    return val.slice(5, 7) + '月';
                  }
                  // 其他显示 MM-DD
                  return val.slice(5);
                }}
                axisLine={{ stroke: '#d1d5db' }}
              />

              {/* Y 轴 */}
              <YAxis
                domain={['auto', 'auto']}
                tick={{ fontSize: 12, fill: '#6b7280' }}
                width={50}
                axisLine={{ stroke: '#d1d5db' }}
                tickFormatter={(val) => val.toFixed(0)}
              />

              {/* 滑动定位线与详情提示 */}
              <Tooltip
                cursor={{ stroke: '#3b82f6', strokeWidth: 1.5, strokeDasharray: '5 5' }} // 蓝色虚线定位
                content={<CustomTooltip />}
              />

              {/* 区域填充（可选，增加美感） */}
              <Area
                type="monotone"
                dataKey="price"
                fill={areaColor}
                fillOpacity={0.1}
                stroke="none"
              />

              {/* MA20 虚线 */}
              <Line
                type="monotone"
                dataKey="ma20"
                stroke="#9ca3af"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                name="MA20"
              />

              {/* 价格实线 */}
              <Line
                type="monotone"
                dataKey="price"
                stroke={lineColor}
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 6, fill: lineColor }}
                name="收盘价"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* 图例说明 */}
        <div className="flex items-center justify-center gap-6 mt-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <div
              className="w-6 h-0.5"
              style={{ backgroundColor: lineColor }}
            />
            <span>收盘价</span>
          </div>
          <div className="flex items-center gap-2">
            <div
              className="w-6 h-0.5 border-t-2 border-dashed"
              style={{ borderColor: '#9ca3af' }}
            />
            <span>MA20均线</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-blue-500 border-t-2 border-dashed" />
            <span>滑动定位线</span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default TrendLens;
