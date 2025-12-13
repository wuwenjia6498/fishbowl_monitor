# 任务：为表格字段增加 Tooltip 解释 (v4.8 UX Polish)

用户希望增强界面的可解释性。请在 DataTable 的表头 (Header) 增加 **Tooltip (工具提示)**，解释每个字段的含义和用法。

## 1. 前端组件准备

请确保项目中已安装 Shadcn UI 的 `Tooltip` 组件。
如果未安装，请执行：`npx shadcn-ui@latest add tooltip`

## 2. 修改列定义 (`columns.tsx` 或 `fishbowl-table.tsx`)

请创建一个辅助组件 `HeaderWithTooltip`，用于统一渲染带图标的表头：

```tsx
// 示例组件结构
const HeaderWithTooltip = ({ title, content }: { title: string, content: string }) => (
  <div className="flex items-center space-x-1">
    <span>{title}</span>
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          <InfoIcon className="h-3 w-3 text-muted-foreground/70 hover:text-primary" />
        </TooltipTrigger>
        <TooltipContent className="max-w-[200px] text-xs bg-gray-800 text-white">
          <p>{content}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  </div>
)

3. 配置文案 (Copywriting)
请根据以下映射表，更新两个 Tab 的 columns 定义，将原本的纯文本 Title 替换为 HeaderWithTooltip。

Tab A: 宽基大势 (Category='broad')

现价: "上方为最新点位，下方为20日均线(MA20)。"

状态: "鱼盆核心信号：价格站上20日线为YES(多)，跌破为NO(空)。含±1%缓冲。"

持续天数: "当前趋势连续维持的交易日数量。"

区间涨幅: "从信号发出日(变盘日)至今的累计涨跌幅，用于验证趋势盈利性。"

偏离度: "现价距离MA20的乖离程度。>15%代表过热风险，<-15%代表超跌。"

Tab B: 行业轮动 (Category='industry')

ETF 标的: "该板块对应的龙头ETF。点击代码复制，点击图标查看深度逻辑。"

热度: "即偏离度。反映短期资金拥挤程度，颜色越深代表越偏离均线。"

信号: "战术标签：启动(刚突破)、主升(稳健)、过热(乖离大)、超跌(负乖离大)。"

执行指令
Frontend: 修改 columns.tsx，引入 Tooltip 组件。

Frontend: 封装表头组件，并应用上述文案。

UI: 确保小图标 (InfoIcon 或 HelpCircle) 样式低调，不要喧宾夺主。