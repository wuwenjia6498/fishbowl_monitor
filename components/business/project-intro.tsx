"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { HelpCircle, TrendingUp, Layers, Activity, MousePointerClick, AlertTriangle, ShieldAlert } from 'lucide-react';

/**
 * 项目使用指南组件
 * 提供鱼盆模型核心逻辑、数据来源及指标含义的详细说明
 */
export default function ProjectIntro() {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" className="gap-2">
          <HelpCircle className="h-4 w-4" />
          <span className="hidden md:inline">使用指南</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">鱼盆·ETF 趋势罗盘 - 使用指南</DialogTitle>
          <DialogDescription>
            了解鱼盆模型的核心逻辑、数据来源及指标含义
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-8 pt-4">
          {/* 板块1: 核心模型 */}
          <section className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <TrendingUp className="h-5 w-5 text-primary" />
              </div>
              <h3 className="text-xl font-semibold">核心模型：鱼盆策略</h3>
            </div>
            <div className="pl-11 space-y-3 text-muted-foreground leading-relaxed">
              <p>
                本系统基于经典的 <span className="font-semibold text-foreground">20日均线 (MA20)</span> 趋势跟踪策略。
                为了过滤震荡市的假突破信号，我们引入了 <span className="font-semibold text-foreground">±1% 缓冲带机制</span>：
              </p>
              <ul className="space-y-2 ml-4">
                <li className="flex items-start gap-2">
                  <span className="inline-flex items-center justify-center w-16 h-6 rounded text-xs font-medium bg-green-500/10 text-green-600 dark:text-green-400 shrink-0">
                    YES
                  </span>
                  <span>价格有效站上 MA20 上方 1%，确立上涨趋势（多头信号）</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="inline-flex items-center justify-center w-16 h-6 rounded text-xs font-medium bg-red-500/10 text-red-600 dark:text-red-400 shrink-0">
                    NO
                  </span>
                  <span>价格有效跌破 MA20 下方 1%，确立下跌趋势（空头信号）</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="inline-flex items-center justify-center w-16 h-6 rounded text-xs font-medium bg-gray-500/10 text-gray-600 dark:text-gray-400 shrink-0">
                    缓冲带
                  </span>
                  <span>在 ±1% 区间内，继续维持原有 YES 或 NO 状态（防止震荡频繁切换）</span>
                </li>
              </ul>
            </div>
          </section>

          {/* 板块2: 数据双轨制 */}
          <section className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/10">
                <Layers className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-xl font-semibold">数据双轨制</h3>
            </div>
            <div className="pl-11">
              <div className="grid md:grid-cols-2 gap-4">
                {/* 宽基大势 */}
                <div className="p-4 rounded-lg border bg-card space-y-2">
                  <h4 className="font-semibold">宽基大势（标尺）</h4>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    监控原生指数（如沪深300）。仅作为<span className="font-medium text-foreground">大盘风向标</span>，
                    用来决定总仓位和择时，不提供直接交易建议。
                  </p>
                </div>

                {/* 行业轮动 */}
                <div className="p-4 rounded-lg border bg-card space-y-2">
                  <h4 className="font-semibold">行业轮动（标的）</h4>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    监控精选 ETF（如半导体ETF）。这是<span className="font-medium text-foreground">实战交易对象</span>，
                    数据经过前复权处理，信号可直接跟随。
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* 板块3: 关键指标解读 */}
          <section className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-violet-500/10">
                <Activity className="h-5 w-5 text-violet-600 dark:text-violet-400" />
              </div>
              <h3 className="text-xl font-semibold">关键指标解读</h3>
            </div>
            <div className="pl-11 space-y-3">
              <div className="space-y-1">
                <h4 className="font-medium">区间涨幅 (Trend Perf.)</h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  从当前趋势信号发出那一刻起，持有至今的累计盈亏。
                  用于验证趋势的真实性和盈利空间。
                </p>
              </div>
              <div className="space-y-1">
                <h4 className="font-medium">偏离度 (Deviation)</h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  现价距离 MA20 的乖离程度。
                  <span className="font-medium text-orange-600 dark:text-orange-400"> {'>15%'} </span>
                  代表短期过热（风险），
                  <span className="font-medium text-blue-600 dark:text-blue-400"> {'<-15%'} </span>
                  代表严重超跌（机会）。
                </p>
              </div>
            </div>
          </section>

          {/* 板块4: 交互操作 */}
          <section className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-500/10">
                <MousePointerClick className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              </div>
              <h3 className="text-xl font-semibold">交互操作</h3>
            </div>
            <div className="pl-11 space-y-3">
              <div className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 shrink-0" />
                <div>
                  <span className="text-sm">
                    点击 <span className="font-medium text-foreground">ETF 代码</span>：
                    可直接复制到剪贴板，方便交易软件下单。
                  </span>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 shrink-0" />
                <div>
                  <span className="text-sm">
                    点击 <span className="font-medium text-foreground">i 图标</span>：
                    查看该 ETF 的<span className="font-medium text-foreground">深度投资逻辑</span>、规模及持仓分析。
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* 板块5: 核心风险与免责声明 */}
          <div className="border-t pt-6 mt-6">
            <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg border border-red-100 dark:border-red-900/50">
              <h3 className="font-bold flex items-center gap-2 text-red-700 dark:text-red-400 mb-3 text-lg">
                <ShieldAlert className="h-5 w-5" /> ⚠️ 风险揭示
              </h3>

              <div className="space-y-3 text-sm text-red-600/90 dark:text-red-300/90 leading-relaxed">
                <p>
                  鱼盆模型基于 <strong>MA20 均线趋势跟随策略</strong>。它不是水晶球，无法预测未来。它本质上是用"胜率"换"赔率"，在趋势行情中获利，但在震荡行情中可能会回撤。
                </p>

                <ul className="list-disc list-inside space-y-2 pl-1 opacity-90 mt-2">
                  <li>
                    <strong>震荡市磨损风险：</strong>当市场处于无趋势的横盘震荡时，价格可能频繁穿梭于 MA20 上下。尽管有 1% 缓冲带，仍可能遭遇"左右挨耳光"的频繁止损，导致本金磨损。
                  </li>
                  <li>
                    <strong>信号滞后性风险：</strong>MA20 是滞后指标。在"V型"反转时，买入信号会晚于最低点；在"A型"暴跌时，卖出信号会晚于最高点。<strong>本模型无法买在最低、卖在最高。</strong>理解趋势交易赚的是"鱼身"，放弃"鱼头和鱼尾"。
                  </li>
                  <li>
                    <strong>ETF 标的风险：</strong>个别 ETF 可能出现流动性不足、大幅折溢价或跟踪误差，导致实际交易价格偏离理论信号价格（滑点风险）。
                  </li>
                  <li>
                    <strong>模型失效风险：</strong>历史数据的有效性不代表未来。市场风格的剧烈切换可能导致模型在特定时期内持续失效。
                  </li>
                </ul>

                <p className="font-bold mt-3 pt-2 border-t border-red-200/50 dark:border-red-800/50">
                  "不预测，只跟随" 是本系统的核心哲学，但跟随是有成本的。请务必在能够承受震荡期回撤的前提下参考本系统信号。投资有风险，入市需谨慎。
                </p>
              </div>
            </div>
          </div>

          {/* 底部提示 */}
          <div className="pt-4 border-t">
            <p className="text-sm text-center text-muted-foreground">
              💡 提示：鱼盆模型适合中长期趋势跟踪，不适合短线择时
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
