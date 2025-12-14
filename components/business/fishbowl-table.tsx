'use client';

import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Copy, Info, ChevronRight, HelpCircle, ListTree } from "lucide-react";
import { toast } from "sonner";
import { EtfCardProps } from '@/components/EtfCard';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { Button } from "@/components/ui/button";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface FishbowlTableProps {
  data: EtfCardProps[];
}

// 信号标签映射
const SIGNAL_TAG_CONFIG = {
  BREAKOUT: { badge: '启动', color: 'text-green-600', bgColor: 'bg-green-50 dark:bg-green-950' },
  STRONG: { badge: '主升', color: 'text-green-500', bgColor: 'bg-green-50 dark:bg-green-950' },
  OVERHEAT: { badge: '过热', color: 'text-orange-500', bgColor: 'bg-orange-50 dark:bg-orange-950' },
  SLUMP: { badge: '弱势', color: 'text-red-500', bgColor: 'bg-red-50 dark:bg-red-950' },
  EXTREME_BEAR: { badge: '超跌', color: 'text-blue-500', bgColor: 'bg-blue-50 dark:bg-blue-950' },
};

// 表头工具提示辅助组件
const HeaderWithTooltip: React.FC<{
  title: string;
  content: string;
  align?: 'left' | 'center' | 'right'
}> = ({ title, content, align = 'left' }) => {
  const alignClass = align === 'center' ? 'justify-center' : align === 'right' ? 'justify-end' : 'justify-start';

  return (
    <div className={`flex items-center gap-1 ${alignClass}`}>
      <span>{title}</span>
      <TooltipProvider delayDuration={200}>
        <Tooltip>
          <TooltipTrigger asChild>
            <HelpCircle className="h-3.5 w-3.5 text-muted-foreground/60 hover:text-muted-foreground cursor-help transition-colors" />
          </TooltipTrigger>
          <TooltipContent
            className="max-w-[240px] text-xs text-left bg-gray-900 dark:bg-gray-800 text-white border-gray-700"
            sideOffset={5}
          >
            <p className="leading-relaxed">{content}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
};

// ETF 代码到名称的映射
const ETF_NAME_MAPPING: Record<string, string> = {
  // 宽基指数ETF
  '510300': '华泰柏瑞沪深300ETF',
  '510500': '南方中证500ETF', 
  '512100': '南方中证1000ETF',
  '159915': '易方达创业板ETF',
  '510050': '华夏上证50ETF',
  '159902': '华夏中小板ETF',
  '588000': '华夏科创50ETF',
  
  // 行业ETF - 农业/养殖
  '159825': '广发中证全指农牧渔ETF',
  '159865': '鹏华中证畜牧养殖ETF',
  
  // 煤炭/石油
  '515220': '国泰中证煤炭ETF',
  '159934': '华夏能源ETF',
  
  // 基础化工
  '159870': '南方中证申万有色金属ETF',
  
  // 钢铁
  '515210': '国泰中证钢铁ETF',
  
  // 有色金属
  '512400': '南方中证申万有色金属ETF',
  '518880': '华安黄金ETF',
  
  // 工业/设备
  '159997': '富国中证工业母机ETF',
  '512720': '国泰中证计算机ETF',
  '512760': '国泰CES半导体芯片ETF',
  
  // 汽车相关
  '516110': '国泰中证汽车ETF',
  '159732': '汇添富中证智能汽车ETF',
  
  // 通信/计算机
  '515880': '国泰中证全指通信设备ETF',
  '515230': '华夏中证云计算与大数据ETF',
  
  // 家电/消费
  '159996': '广发中证全指家用电器ETF',
  '159736': '国联安中证消费ETF',
  '512690': '鹏华中证酒ETF',
  '159786': '嘉实中证主要消费ETF',
  
  // 医药生物
  '512010': '易方达沪深300医药ETF',
  '512290': '南方中证生物科技ETF',
  '159772': '永赢中证全指医疗器械ETF',
  '159828': '华泰柏瑞中证医疗服务ETF',
  
  // 公用事业/环保
  '159611': '广发中证全指电力公用事业ETF',
  '512580': '广发中证环保产业ETF',
  '159800': '华夏中证燃气ETF',
  
  // 交通运输
  '159806': '南方中证交通运输ETF',
  
  // 房地产
  '512200': '华夏中证全指房地产ETF',
  
  // 金融
  '512800': '华宝中证银行ETF',
  '512880': '国泰中证全指证券公司ETF',
  '512890': '平安中证港股通医药卫生ETF',
  
  // 商贸零售
  '159928': '华夏中证主要消费ETF',
  '159792': '华夏中证动漫游戏ETF',
  '159766': '富国中证旅游主题ETF',
  
  // 传媒
  '516010': '南方中证传媒ETF',
  
  // 电力设备
  '516260': '广发中证全指电力设备ETF',
  '515790': '华泰柏瑞中证光伏产业ETF',
  '159755': '嘉实中证新能源ETF',
  
  // 军工
  '512660': '富国中证军工ETF',
  
  // 其他
  '159745': '广发中证全指建筑材料ETF',
  '561310': '华夏中证储能产业ETF',
  '159867': '华宝中证细分食品饮料产业主题ETF',
  
  // 半导体相关
  '512480': '国泰中证全指半导体ETF',
};

// 获取ETF名称
const getEtfName = (etfCode: string): string => {
  return ETF_NAME_MAPPING[etfCode] || `ETF-${etfCode}`;
};

const FishbowlTable: React.FC<FishbowlTableProps> = ({ data }) => {
  // 分离宽基和行业数据
  const broadData = data.filter(item => item.category === 'broad');
  const industryData = data.filter(item => item.category === 'industry');

  // 分组：按 industry_level 分组
  const groupedIndustryData = React.useMemo(() => {
    const groups: Record<string, EtfCardProps[]> = {};
    industryData.forEach(item => {
      const groupName = item.industry_level || '其他';
      if (!groups[groupName]) {
        groups[groupName] = [];
      }
      groups[groupName].push(item);
    });
    return groups;
  }, [industryData]);

  // 分组：宽基数据按 industry_level 分组 (v5.3: 支持 A股指数 + 全球/商品)
  const groupedBroadData = React.useMemo(() => {
    const groups: Record<string, EtfCardProps[]> = {};
    broadData.forEach(item => {
      const groupName = item.industry_level || '其他';
      if (!groups[groupName]) {
        groups[groupName] = [];
      }
      groups[groupName].push(item);
    });
    return groups;
  }, [broadData]);

  // 固定分组顺序
  const groupOrder = ['科技 (TMT)', '高端制造', '医药消费', '周期资源', '金融'];
  
  // 宽基分组顺序 (v5.3.1 - 分离全球指数和贵金属)
  const broadGroupOrder = ['A股指数', '全球指数', '贵金属现货'];

  // 计算宽基大势指标
  const broadYesCount = broadData.filter(item => item.status === 'YES').length;
  const broadTotal = broadData.length;
  const broadYesRatio = broadTotal > 0 ? broadYesCount / broadTotal : 0;

  // 计算行业多头率
  const industryYesCount = industryData.filter(item => item.status === 'YES').length;
  const industryTotal = industryData.length;
  const industryYesRatio = industryTotal > 0 ? (industryYesCount / industryTotal) * 100 : 0;

  // 大势风向判断
  const getMarketTrend = () => {
    if (broadYesRatio > 0.6) {
      return { 
        label: '多头市场', 
        description: '宽基指数整体走强',
        variant: 'danger' as const, 
        color: 'text-red-600',
        bgColor: 'bg-red-50/80',
        borderColor: 'border-red-100',
        icon: '📈'
      };
    } else if (broadYesRatio < 0.4) {
      return { 
        label: '空头市场', 
        description: '宽基指数整体走弱',
        variant: 'success' as const, 
        color: 'text-green-600',
        bgColor: 'bg-green-50/80',
        borderColor: 'border-green-100',
        icon: '📉'
      };
    } else {
      return { 
        label: '震荡市场', 
        description: '宽基指数多空均衡',
        variant: 'warning' as const, 
        color: 'text-amber-600',
        bgColor: 'bg-amber-50/80',
        borderColor: 'border-amber-100',
        icon: '↔️'
      };
    }
  };

  const marketTrend = getMarketTrend();

  // 复制ETF代码到剪贴板
  const copyToClipboard = async (etfCode: string, industryName: string) => {
    try {
      await navigator.clipboard.writeText(etfCode);
      toast.success(`已复制 ${etfCode}`, {
        description: `${industryName} 龙头ETF代码`,
        duration: 2000,
      });
    } catch (err) {
      toast.error('复制失败', {
        description: '请手动复制代码',
      });
    }
  };

  // 格式化百分比
  const formatPercentage = (value: number) => `${(value * 100).toFixed(2)}%`;

  // 获取信号标签配置
  const getSignalTagConfig = (tag: string | null) => {
    return SIGNAL_TAG_CONFIG[tag as keyof typeof SIGNAL_TAG_CONFIG] || { badge: tag || '', color: 'text-muted-foreground', bgColor: 'bg-muted' };
  };

  // 格式化数字显示
  const formatNumber = (num: number | null | undefined, decimals: number = 2) => {
    if (num === null || num === undefined) return '-';
    return Number(num).toFixed(decimals);
  };

  return (
    <div className="space-y-6">
      {/* 分Tab展示：宽基指数 vs 行业板块 */}
      <Tabs defaultValue="broad" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="broad">宽基指数</TabsTrigger>
          <TabsTrigger value="industry">行业板块</TabsTrigger>
        </TabsList>

        {/* Tab 1: 宽基大势 */}
        <TabsContent value="broad">
          <div className="space-y-6">
            {/* 按分组渲染多个表格 */}
            {broadGroupOrder.map((groupName) => {
              const groupItems = groupedBroadData[groupName];
              if (!groupItems || groupItems.length === 0) return null;

              return (
                <div key={groupName}>
                  {/* 分组标题 */}
                  <h2 className="text-xl font-bold mb-4 px-2 border-l-4 border-blue-500 bg-gradient-to-r from-blue-50 to-transparent dark:from-blue-950/50">
                    {groupName}
                  </h2>

                  {/* 分组表格 */}
                  <Card>
                    <Table className="table-fixed">
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-[120px]">指数名称</TableHead>
                          <TableHead className="w-[160px]">
                            <HeaderWithTooltip
                              title="现价 & MA20"
                              content="上方为最新点位，下方为20日均线(MA20)。"
                              align="right"
                            />
                          </TableHead>
                          <TableHead className="w-[100px]">
                            <HeaderWithTooltip
                              title="当日涨幅"
                              content="相对于前一交易日的涨跌幅度。"
                              align="right"
                            />
                          </TableHead>
                          <TableHead className="w-[80px]">
                            <HeaderWithTooltip
                              title="状态"
                              content="鱼盆核心信号：价格站上20日线为YES(多)，跌破为NO(空)。含±1%缓冲。"
                              align="center"
                            />
                          </TableHead>
                          <TableHead className="w-[100px]">
                            <HeaderWithTooltip
                              title="持续天数"
                              content="当前趋势连续维持的交易日数量。"
                              align="center"
                            />
                          </TableHead>
                          <TableHead className="w-[100px]">
                            <HeaderWithTooltip
                              title="区间涨幅"
                              content="从信号发出日(变盘日)至今的累计涨跌幅，用于验证趋势盈利性。"
                              align="right"
                            />
                          </TableHead>
                          <TableHead className="w-[100px]">
                            <HeaderWithTooltip
                              title="偏离度"
                              content="现价距离MA20的乖离程度。>15%代表过热风险，<-15%代表超跌。"
                              align="right"
                            />
                          </TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {groupItems.map((item) => {
                          const isBullish = item.status === 'YES';

                          // 计算区间涨幅的颜色逻辑
                          const getTrendPctColor = () => {
                            if (!item.trend_pct) return 'text-muted-foreground';

                            // Status=YES 且 >0，显示红色 (盈利)
                            if (isBullish && item.trend_pct > 0) return 'text-red-500';

                            // Status=NO 且 <0，显示绿色 (避险/跌幅)
                            if (!isBullish && item.trend_pct < 0) return 'text-green-500';

                            // 其他情况：灰色
                            return 'text-muted-foreground';
                          };

                          return (
                            <TableRow key={`${item.symbol}-${item.date}`}>
                              {/* 指数名称 */}
                              <TableCell className="w-[120px]">
                                <div className="flex flex-col">
                                  <div className="flex items-center gap-1.5">
                                    <span className="font-medium text-foreground truncate">{item.name}</span>
                                    {/* 美股指数标注T-1数据 */}
                                    {(item.symbol === 'IXIC' || item.symbol === 'SPX') && (
                                      <Badge variant="outline" className="text-[10px] bg-amber-50 border-amber-200 text-amber-700 px-1 py-0 h-4">
                                        T-1
                                      </Badge>
                                    )}
                                  </div>
                                  <span className="text-xs text-muted-foreground font-mono truncate">{item.symbol}</span>
                                </div>
                              </TableCell>

                              {/* 现价 & MA20 合并列 */}
                              <TableCell className="w-[160px] text-right">
                                <div className="flex flex-col items-end">
                                  <span className={`font-mono text-base font-semibold ${isBullish ? 'text-red-500' : 'text-green-500'}`}>
                                    {formatNumber(item.close_price)}
                                  </span>
                                  <span className="text-xs text-muted-foreground font-mono">
                                    MA20: {formatNumber(item.ma20_price)}
                                  </span>
                                </div>
                              </TableCell>

                              {/* 当日涨幅 */}
                              <TableCell className="w-[100px] text-right">
                                <span className={`font-mono font-medium ${
                                  item.change_pct === null || item.change_pct === undefined ? 'text-muted-foreground' :
                                  item.change_pct > 0 ? 'text-red-500' :
                                  item.change_pct < 0 ? 'text-green-500' :
                                  'text-muted-foreground'
                                }`}>
                                  {item.change_pct !== null && item.change_pct !== undefined
                                    ? `${item.change_pct > 0 ? '+' : ''}${formatPercentage(item.change_pct)}`
                                    : '-'}
                                </span>
                              </TableCell>

                              {/* 状态 */}
                              <TableCell className="w-[80px] text-center">
                                <Badge
                                  variant={isBullish ? 'danger' : 'success'}
                                  className="min-w-[50px] justify-center"
                                >
                                  {item.status}
                                </Badge>
                              </TableCell>

                              {/* 持续天数 */}
                              <TableCell className="w-[100px] text-center">
                                <span className={`font-mono font-medium ${item.signal_tag === 'BREAKOUT' ? 'text-red-600' : ''}`}>
                                  {item.duration_days}
                                </span>
                              </TableCell>

                              {/* 区间涨幅 */}
                              <TableCell className="w-[100px] text-right">
                                <span className={`font-mono font-medium ${getTrendPctColor()}`}>
                                  {item.trend_pct !== null && item.trend_pct !== undefined
                                    ? `${item.trend_pct > 0 ? '+' : ''}${formatPercentage(item.trend_pct)}`
                                    : '-'}
                                </span>
                              </TableCell>

                              {/* 偏离度 */}
                              <TableCell className="w-[100px] text-right">
                                <span className={`font-mono font-medium ${Math.abs(item.deviation_pct) > 0.15 ? 'text-orange-600' : item.deviation_pct > 0 ? 'text-red-500' : 'text-green-500'}`}>
                                  {formatPercentage(item.deviation_pct)}
                                </span>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </Card>
                </div>
              );
            })}
          </div>
        </TabsContent>

        {/* Tab 2: 行业轮动 - 分组结构化 */}
        <TabsContent value="industry">
          <div className="space-y-6">
            {/* 按分组渲染多个表格 */}
            {groupOrder.map((groupName) => {
              const groupItems = groupedIndustryData[groupName];
              if (!groupItems || groupItems.length === 0) return null;

              return (
                <div key={groupName}>
                  {/* 分组标题 */}
                  <h2 className="text-xl font-bold mb-4 px-2 border-l-4 border-blue-500 bg-gradient-to-r from-blue-50 to-transparent dark:from-blue-950/50">
                    {groupName}
                  </h2>

                  {/* 分组表格 */}
                  <Card>
                    <Table className="table-fixed">
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-[110px]">板块名称</TableHead>
                          <TableHead className="w-[110px]">
                            <HeaderWithTooltip
                              title="ETF 标的"
                              content="该板块对应的龙头ETF。点击代码复制，悬浮图标查看深度逻辑。"
                              align="left"
                            />
                          </TableHead>
                          <TableHead className="w-[50px] text-center">逻辑</TableHead>
                          <TableHead className="w-[50px]">
                            <HeaderWithTooltip
                              title="持仓"
                              content="ETF 前十大重仓股，悬浮图标查看详情。数据来源于基金季报/半年报。"
                              align="center"
                            />
                          </TableHead>
                          <TableHead className="w-[150px]">
                            <HeaderWithTooltip
                              title="现价 & MA20"
                              content="上方为最新点位，下方为20日均线(MA20)。"
                              align="right"
                            />
                          </TableHead>
                          <TableHead className="w-[80px]">
                            <HeaderWithTooltip
                              title="状态"
                              content="鱼盆核心信号：价格站上20日线为YES(多)，跌破为NO(空)。含±1%缓冲。"
                              align="center"
                            />
                          </TableHead>
                          <TableHead className="w-[90px]">
                            <HeaderWithTooltip
                              title="偏离度"
                              content="价格相对MA20的乖离率。正值越大表示越偏离向上，负值越大表示偏离向下，可用于判断短期过热或超跌。"
                              align="right"
                            />
                          </TableHead>
                          <TableHead className="w-[90px]">
                            <HeaderWithTooltip
                              title="信号"
                              content="战术标签：启动(刚突破)、主升(稳健)、过热(乖离大)、超跌(负乖离大)。"
                              align="center"
                            />
                          </TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {groupItems.map((item) => {
                          const isBullish = item.status === 'YES';
                          const signalConfig = getSignalTagConfig(item.signal_tag);

                          return (
                            <TableRow key={`${item.symbol}-${item.date}`}>
                              {/* 板块名称 */}
                              <TableCell className="w-[110px]">
                                <span className="font-medium text-foreground truncate text-sm">{item.name}</span>
                              </TableCell>

                              {/* ETF标的代码 */}
                              <TableCell className="w-[110px]">
                                <button
                                  onClick={() => copyToClipboard(item.symbol, item.name)}
                                  className="inline-flex items-center gap-1.5 px-2 py-1 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded text-xs transition-colors cursor-pointer border border-blue-200"
                                >
                                  <span className="font-mono font-medium">{item.symbol}</span>
                                  <Copy className="w-3 h-3 flex-shrink-0" />
                                </button>
                              </TableCell>

                              {/* 投资逻辑按钮 */}
                              <TableCell className="w-[50px] text-center">
                                <HoverCard openDelay={200} closeDelay={100}>
                                  <HoverCardTrigger asChild>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      className="h-8 w-8 p-0 hover:bg-blue-50 hover:text-blue-600 cursor-pointer"
                                      title="查看投资逻辑"
                                    >
                                      <Info className="h-4 w-4" />
                                      <span className="sr-only">查看投资逻辑</span>
                                    </Button>
                                  </HoverCardTrigger>
                                  <HoverCardContent className="w-[500px] p-4 text-left" side="right" align="start">
                                    <div className="space-y-3">
                                      <div className="flex items-start gap-2 border-b pb-2">
                                        <span className="text-2xl">{signalConfig.badge === '启动' ? '🚀' : signalConfig.badge === '主升' ? '📈' : signalConfig.badge === '过热' ? '🔥' : signalConfig.badge === '弱势' ? '📉' : '💎'}</span>
                                        <div className="text-left">
                                          <h4 className="text-base font-bold">{item.name} ({item.symbol})</h4>
                                          <p className="text-xs text-muted-foreground">{item.dominant_etf || '暂无ETF标签'}</p>
                                        </div>
                                      </div>
                                      <div className="text-sm text-left">
                                        {item.investment_logic ? (
                                          <MarkdownRenderer content={item.investment_logic} />
                                        ) : (
                                          <p className="text-muted-foreground">暂无投资逻辑说明</p>
                                        )}
                                      </div>
                                    </div>
                                  </HoverCardContent>
                                </HoverCard>
                              </TableCell>

                              {/* 核心持仓 - HoverCard 悬浮弹窗 */}
                              <TableCell className="w-[50px] text-center">
                                {item.top_holdings ? (
                                  <HoverCard openDelay={200} closeDelay={100}>
                                    <HoverCardTrigger asChild>
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        className="h-8 w-8 p-0 hover:bg-muted"
                                        title="查看核心持仓"
                                      >
                                        <ListTree className="h-4 w-4" />
                                        <span className="sr-only">查看核心持仓</span>
                                      </Button>
                                    </HoverCardTrigger>
                                    <HoverCardContent 
                                      side="right" 
                                      align="center" 
                                      className="w-[400px] p-4"
                                    >
                                      <div className="space-y-3">
                                        {/* 标题区域 */}
                                        <div className="flex items-start gap-2 border-b pb-3">
                                          <ListTree className="h-4 w-4 text-muted-foreground mt-0.5" />
                                          <div className="flex-1">
                                            <h4 className="text-base font-semibold leading-tight">{item.name}</h4>
                                            <div className="flex items-center gap-2 mt-1">
                                              <span className="text-xs font-mono text-muted-foreground">{item.symbol}</span>
                                            </div>
                                          </div>
                                        </div>

                                        {/* 表格内容 */}
                                        <div>
                                          <MarkdownRenderer content={item.top_holdings} />
                                        </div>
                                      </div>
                                    </HoverCardContent>
                                  </HoverCard>
                                ) : (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-8 w-8 p-0 text-muted-foreground/30 cursor-not-allowed"
                                    title="暂无持仓数据"
                                    disabled
                                  >
                                    <ListTree className="h-4 w-4" />
                                    <span className="sr-only">暂无持仓数据</span>
                                  </Button>
                                )}
                              </TableCell>

                              {/* 现价 & MA20 合并列 */}
                              <TableCell className="w-[150px] text-right">
                                <div className="flex flex-col items-end">
                                  <span className={`font-mono text-base font-semibold ${isBullish ? 'text-red-500' : 'text-green-500'}`}>
                                    {formatNumber(item.close_price)}
                                  </span>
                                  <span className="text-xs text-muted-foreground font-mono">
                                    MA20: {formatNumber(item.ma20_price)}
                                  </span>
                                </div>
                              </TableCell>

                              {/* 状态 */}
                              <TableCell className="w-[80px] text-center">
                                <Badge
                                  variant={isBullish ? 'danger' : 'success'}
                                  className="min-w-[45px] justify-center text-xs"
                                >
                                  {item.status}
                                </Badge>
                              </TableCell>

                              {/* 偏离度 */}
                              <TableCell className="w-[90px] text-right">
                                <span className={`font-mono font-medium ${Math.abs(item.deviation_pct) > 0.15 ? 'text-orange-600' : item.deviation_pct > 0 ? 'text-red-500' : 'text-green-500'}`}>
                                  {formatPercentage(item.deviation_pct)}
                                </span>
                              </TableCell>

                              {/* 信号标签 */}
                              <TableCell className="w-[90px] text-center">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium ${signalConfig.color} ${signalConfig.bgColor} border border-current/20 w-fit`}>
                                  {signalConfig.badge}
                                </span>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </Card>
                </div>
              );
            })}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default FishbowlTable;
