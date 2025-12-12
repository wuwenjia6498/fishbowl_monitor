#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鱼盆趋势雷达 - 数据库初始化脚本 v4.6 (指数+ETF混合双轨 + 投资逻辑深度解析)
功能：
1. 宽基大势：监控原生指数 (Indices)
2. 行业轮动：监控交易型 ETF
3. 每个资产有固定的 sort_rank，保证顺序稳定
4. 每个 ETF 包含定制化的投资逻辑说明（Markdown格式）
"""

import os
import sys
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# 设置标准输出编码为UTF-8（解决Windows编码问题）
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# 加载环境变量
load_dotenv()

# ================================================
# [核心] 宽基指数池 - 使用原生指数代码
# ================================================
BROAD_INDICES = [
    {"sort_id": 1, "code": "000016.SH", "name": "上证50", "group": "宽基指数", "etf_label": "上证50"},
    {"sort_id": 2, "code": "000300.SH", "name": "沪深300", "group": "宽基指数", "etf_label": "沪深300"},
    {"sort_id": 3, "code": "399006.SZ", "name": "创业板指", "group": "宽基指数", "etf_label": "创业板"},
    {"sort_id": 4, "code": "000688.SH", "name": "科创50", "group": "宽基指数", "etf_label": "科创50"},
    {"sort_id": 5, "code": "000905.SH", "name": "中证500", "group": "宽基指数", "etf_label": "中证500"},
    {"sort_id": 6, "code": "000852.SH", "name": "中证1000", "group": "宽基指数", "etf_label": "中证1000"},
    {"sort_id": 7, "code": "932000.CSI", "name": "中证2000", "group": "宽基指数", "etf_label": "中证2000"},
    {"sort_id": 8, "code": "899050.BJ", "name": "北证50", "group": "宽基指数", "etf_label": "北证50"},
]

# ================================================
# [核心] 行业 ETF 资产池 - 交易型 ETF (v4.6 含投资逻辑)
# ================================================
INDUSTRY_ETFS = [
    # --- 科技 (TMT) ---
    {
        "sort_id": 101, "code": "159819.SZ", "name": "人工智能(AI)", "group": "科技 (TMT)", "etf_label": "人工智能ETF",
        "investment_logic": """**规模与地位**

该基金在同类人工智能主题ETF中规模稳居第一梯队，最新规模约233亿元，凭借其先发优势汇聚了大量流动性。其日均成交额常维持在数亿元级别，盘口深度足以容纳机构资金的进出。

**持仓逻辑**

该ETF跟踪中证人工智能主题指数，其成分股覆盖了从上游芯片设计（如寒武纪、海光信息）、中游算法大模型（如科大讯飞、三六零）到下游应用场景（如金山办公）的全产业链龙头。这种全覆盖策略有效规避了单一技术路线失败的风险，捕捉行业整体贝塔。

**市场情绪指标**

作为AI板块的风向标，该ETF的溢价率变动往往预示着板块的短期热度。在AI概念爆发期，该ETF往往能获得显著的超额收益。"""
    },
    {
        "sort_id": 102, "code": "159998.SZ", "name": "计算机/软件", "group": "科技 (TMT)", "etf_label": "计算机ETF",
        "investment_logic": """**规模优势**

在该细分领域占据规模首位，最新流通规模接近30亿元。

**持仓解析**

跟踪中证计算机主题指数，广泛覆盖信息技术服务（如中国软件）、应用软件（如金山办公、用友网络）及电脑硬件。它是信创板块的晴雨表，每当政府采购或信创政策出台时，该ETF往往率先反应。"""
    },
    {
        "sort_id": 103, "code": "512480.SH", "name": "半导体/芯片", "group": "科技 (TMT)", "etf_label": "半导体ETF",
        "investment_logic": """**绝对霸主**

作为该领域的旗舰产品，其最新规模已突破200亿元大关（约230亿），日均成交额极高，是全市场流动性最好的半导体ETF。

**指数特征**

跟踪中证全指半导体指数，该指数不仅覆盖了高弹性的芯片设计龙头（如韦尔股份、卓胜微），还囊括了重资产的制造环节（如中芯国际）以及设备材料环节（如北方华创）。这种全产业链布局使得该ETF能够完整捕捉行业复苏的红利，且波动性相对纯设计类指数略低。"""
    },
    {
        "sort_id": 104, "code": "512760.SH", "name": "芯片设计", "group": "科技 (TMT)", "etf_label": "芯片ETF",
        "investment_logic": """**细分差异**

CES半导体芯片ETF（512760）规模也接近百亿元级别，在机构投资者中拥有较高认可度。其持仓更聚焦于产业链核心技术环节。对于追求更高锐度的投资者，芯片ETF往往在反弹行情中表现出更强的进攻性。"""
    },
    {
        "sort_id": 105, "code": "159869.SZ", "name": "游戏传媒", "group": "科技 (TMT)", "etf_label": "游戏ETF",
        "investment_logic": """**流动性之王**

目前市场上规模最大、流动性最好的游戏主题ETF，规模一度突破90亿元，且资金呈现持续净流入态势。

**资金青睐**

该ETF连续13个交易日获得资金净流入，累计吸金能力达27亿元，显示出市场资金对板块底部反转的强烈共识。

**持仓逻辑**

持仓高度集中于三七互娱、恺英网络、世纪华通等行业龙头。这些企业不仅受益于版号发放常态化带来的供给侧改善，更承载了市场对"AI+游戏"新玩法的估值重塑预期。"""
    },
    {
        "sort_id": 106, "code": "515880.SH", "name": "通信设备", "group": "科技 (TMT)", "etf_label": "通信ETF",
        "investment_logic": """暂无详细数据"""
    },

    # --- 高端制造 ---
    {
        "sort_id": 201, "code": "515790.SH", "name": "光伏", "group": "高端制造", "etf_label": "光伏ETF",
        "investment_logic": """**左侧布局**

规模稳定在140-150亿元区间。当前光伏行业正经历惨烈的价格战，产业链利润受压，但也加速了落后产能的淘汰。对于长线资金而言，当前位置的估值性价比极高，ETF成为左侧布局、博弈行业周期反转的标准工具。其持仓如隆基绿能、通威股份等，一旦行业供需格局改善，弹性巨大。"""
    },
    {
        "sort_id": 202, "code": "515030.SH", "name": "新能源车", "group": "高端制造", "etf_label": "新能车ETF",
        "investment_logic": """**行业标杆**

作为华夏基金旗下的旗舰产品，规模庞大（约50-60亿元），流动性极佳。

**持仓逻辑**

持仓覆盖宁德时代、比亚迪等全球具备绝对竞争力的巨头。尽管行业整体增速放缓，但龙头企业凭借技术壁垒和规模效应，市占率仍在提升。该ETF是捕捉行业格局优化的最佳工具。"""
    },
    {
        "sort_id": 203, "code": "562500.SH", "name": "机器人", "group": "高端制造", "etf_label": "机器人ETF",
        "investment_logic": """**规模里程碑**

作为全市场规模最大的机器人主题ETF，规模增长速度惊人，最新数据已显示其资产规模突破200亿元，毫无争议地成为该赛道的"巨无霸"。

**核心持仓**

紧密跟踪中证机器人指数，成分股包括汇川技术（工控龙头）、科大讯飞（AI语音交互）、大族激光（激光设备）等。这些企业覆盖了伺服系统、减速器、控制器及系统集成等机器人核心产业链环节。

**投资逻辑**

资金对该板块的持续加仓，反映了市场对"高端装备底座"长期价值的认可。特别是在特斯拉Optimus人形机器人进展的催化下，该板块具备极强的事件驱动属性。"""
    },
    {
        "sort_id": 204, "code": "159667.SZ", "name": "工业母机", "group": "高端制造", "etf_label": "工业母机ETF",
        "investment_logic": """**稀缺性**

作为细分赛道的代表性产品，凭借其稀缺性获得了市场的高度关注。

**持仓特色**

跟踪中证机床指数，重点布局华中数控、纽威数控、科德数控等国产机床龙头。这些企业在五轴联动数控机床等高端领域不断取得突破，正逐步替代进口产品。

**交易机会**

在"大规模设备更新"政策指引下，该板块具备显著的政策博弈价值，往往在政策发布窗口期表现出超越大盘的涨幅。"""
    },
    {
        "sort_id": 205, "code": "159378.SZ", "name": "通用航空/低空", "group": "高端制造", "etf_label": "通航ETF",
        "investment_logic": """**首发优势与规模**

作为全市场首只且同类规模最大的通用航空ETF，其规模已迅速突破12亿元（截至2025年初）。这反映了市场资金对这一新兴赛道的强烈抢筹意愿。

**投资逻辑**

低空经济被明确写入政府工作报告，成为新质生产力的代表。该ETF跟踪国证通用航空产业指数，成分股覆盖了飞行器制造（如中直股份）、空管系统（如莱斯信息）、运营维护等全产业链。

**市场地位**

在低空经济概念爆发时，该ETF往往成为场内资金博弈的核心工具，具有极高关注度。"""
    },

    # --- 医药消费 ---
    {
        "sort_id": 301, "code": "512170.SH", "name": "医药医疗", "group": "医药消费", "etf_label": "医疗ETF",
        "investment_logic": """**巨头地位**

规模超过230亿元，是医疗板块的绝对巨头。

**全覆盖**

其持仓覆盖CXO（医药研发外包）、医疗器械（如迈瑞医疗）及民营医院龙头（如爱尔眼科）。由于覆盖面广，适合作为医药板块的底仓配置，以平滑单一细分赛道的波动。"""
    },
    {
        "sort_id": 302, "code": "159992.SZ", "name": "创新药", "group": "医药消费", "etf_label": "创新药ETF",
        "investment_logic": """**历史新高**

在板块调整的大背景下，该ETF的规模与份额却逆势创出历史新高，突破114亿元，显示资金持续关注并布局。

**基本面支撑**

其跟踪中证创新药产业指数，成分股如恒瑞医药、百济神州等，正逐步兑现研发管线的商业价值。随着美联储降息预期的升温，全球生物医药板块的投融资环境有望改善，创新药作为高贝塔资产，反弹弹性极大。"""
    },
    {
        "sort_id": 303, "code": "560080.SH", "name": "中药", "group": "医药消费", "etf_label": "中药ETF",
        "investment_logic": """**同类最大**

是该细分领域规模最大的产品，且份额增长显著。

**避险属性**

中药板块受益于国企改革、品牌提价能力及国家政策的持续扶持，业绩确定性较强。在市场防御情绪浓厚时，中药ETF往往能获得显著的相对收益，是医药板块中的稳健力量。"""
    },
    {
        "sort_id": 304, "code": "512690.SH", "name": "白酒", "group": "医药消费", "etf_label": "酒ETF",
        "investment_logic": """**规模优势**

规模近200亿元，是消费板块的定海神针。

**投资逻辑**

白酒行业拥有A股最优异的商业模式（高毛利、强现金流、库存耐储存）。尽管面临消费降级的担忧，但高端白酒（茅台、五粮液）的品牌护城河依然稳固。该ETF是博弈宏观经济复苏的最直接工具。"""
    },
    {
        "sort_id": 305, "code": "159996.SZ", "name": "家电", "group": "医药消费", "etf_label": "家电ETF",
        "investment_logic": """**资金流入**

连续获得资金净流入，显示市场对其关注度提升。

**双重红利**

受益于国内"以旧换新"政策带来的需求释放，以及家电企业（如海尔、美的）出海带来的二次增长曲线。中国家电企业在全球范围内的品牌力和制造优势，使其成为极具韧性的价值资产。"""
    },
    {
        "sort_id": 306, "code": "562900.SH", "name": "养殖", "group": "医药消费", "etf_label": "农业ETF",
        "investment_logic": """**周期反转**

重点博弈猪周期反转。生猪养殖行业权重占比高，在产能去化背景下，价格反弹预期强烈。该类ETF管理费率较低，是低成本布局养殖行业复苏的利器。"""
    },

    # --- 周期资源 ---
    {
        "sort_id": 401, "code": "518880.SH", "name": "黄金", "group": "周期资源", "etf_label": "黄金ETF",
        "investment_logic": """**规模新高**

规模持续创新高，突破680亿元（截至2025年三季度末），稳居亚洲最大黄金ETF地位。

**配置价值**

作为全球央行购金与避险资金的首选，黄金ETF不仅跟踪金价，更代表了一种对美元信用体系的对冲。在宏观不确定性加大的当下，它是资产配置中不可或缺的"压舱石"。"""
    },
    {
        "sort_id": 402, "code": "512400.SH", "name": "有色金属", "group": "周期资源", "etf_label": "有色ETF",
        "investment_logic": """**顺周期弹性**

规模约155亿元。铜、铝等工业金属受供给刚性与新兴领域（新能源、AI数据中心对铜的需求）需求拉动，具备长牛基础。"""
    },
    {
        "sort_id": 403, "code": "515220.SH", "name": "煤炭", "group": "周期资源", "etf_label": "煤炭ETF",
        "investment_logic": """**高股息**

规模约60亿元，股息率长期维持在6%左右的高位。

**类债属性**

煤炭企业资本开支减少，现金流充裕，通过高分红回馈股东。在震荡市中，其类债属性吸引了大量险资与追求绝对收益的稳健资金。"""
    },
    {
        "sort_id": 404, "code": "159870.SZ", "name": "化工", "group": "周期资源", "etf_label": "化工ETF",
        "investment_logic": """**规模领先**

份额超200亿份，规模约185亿元，是布局顺周期复苏的重要工具。

**竞争优势**

化工行业处于库存周期底部，万华化学等龙头企业具有极强的成本优势和全球竞争力。一旦宏观需求好转，化工板块的利润弹性将非常可观。"""
    },

    # --- 金融 ---
    {
        "sort_id": 501, "code": "512880.SH", "name": "证券", "group": "金融", "etf_label": "证券ETF",
        "investment_logic": """**旗舰地位**

是全市场规模最大的行业ETF之一，规模近600亿元。

**投资逻辑**

券商板块被称为"牛市旗手"，其高Beta属性使其在市场情绪好转时往往率先启动。在活跃资本市场政策的推动下，头部券商的并购重组预期（如国泰君安与海通证券的合并传闻）也为板块带来了巨大的交易性机会。"""
    },
    {
        "sort_id": 502, "code": "512800.SH", "name": "银行", "group": "金融", "etf_label": "银行ETF",
        "investment_logic": """**百亿规模**

规模突破百亿元。

**红利核心**

银行股凭借低估值（通常破净）和稳定的高分红，成为红利资产的核心。特别是在"中特估"（中国特色估值体系）逻辑下，国有大行的估值修复空间被市场看好。"""
    },
    {
        "sort_id": 503, "code": "512070.SH", "name": "非银金融", "group": "金融", "etf_label": "非银ETF",
        "investment_logic": """**规模大**

规模约120-124亿元，主要覆盖保险与券商。

**戴维斯双击**

保险行业资产端受益于股市回暖带来的投资收益提升，负债端保费增速回升。2025年数据显示，险资正大幅加仓权益资产，自身也成为行情的受益者。"""
    },
]

# ================================================
# 数据库连接
# ================================================
def get_db_connection():
    """连接到 Supabase PostgreSQL"""
    connection_string = os.getenv('DATABASE_URL')
    if not connection_string:
        raise ValueError("环境变量 DATABASE_URL 未设置")

    return psycopg2.connect(connection_string)


# ================================================
# 清空旧数据
# ================================================
def clean_old_data(conn):
    """
    清空所有旧数据（宽基指数 + 行业ETF）
    """
    print("\n正在清理旧数据...")
    cursor = conn.cursor()

    # 删除宽基指数数据
    cursor.execute("DELETE FROM monitor_config WHERE category = 'broad'")
    broad_deleted = cursor.rowcount
    
    # 删除行业ETF数据
    cursor.execute("DELETE FROM monitor_config WHERE category = 'industry'")
    industry_deleted = cursor.rowcount
    
    conn.commit()

    print(f"✓ 已清理宽基指数: {broad_deleted} 条")
    print(f"✓ 已清理行业ETF: {industry_deleted} 条")
    cursor.close()


# ================================================
# 初始化宽基指数池
# ================================================
def init_broad_indices(conn):
    """
    初始化宽基指数（原生指数代码）
    """
    print(f"\n正在初始化宽基指数池...")
    print(f"✓ 包含 {len(BROAD_INDICES)} 个宽基指数")

    # 准备插入数据
    insert_data = []

    for idx in BROAD_INDICES:
        insert_data.append((
            idx['code'],           # symbol (指数代码，如 000300.SH)
            idx['name'],           # name (指数名称，如 "沪深300")
            'broad',               # category
            idx['group'],          # industry_level (固定为"宽基指数")
            idx['etf_label'],      # dominant_etf (显示用标签)
            idx['sort_id'],        # sort_rank (固定排序ID)
            True,                  # is_active
            True                   # is_system_bench (宽基指数标记为系统基准)
        ))

    # 批量插入
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO monitor_config
            (symbol, name, category, industry_level, dominant_etf, sort_rank, is_active, is_system_bench)
        VALUES %s
        ON CONFLICT (symbol)
        DO UPDATE SET
            name = EXCLUDED.name,
            category = EXCLUDED.category,
            industry_level = EXCLUDED.industry_level,
            dominant_etf = EXCLUDED.dominant_etf,
            sort_rank = EXCLUDED.sort_rank,
            is_active = EXCLUDED.is_active,
            is_system_bench = EXCLUDED.is_system_bench,
            updated_at = CURRENT_TIMESTAMP
    """

    execute_values(cursor, insert_query, insert_data)
    conn.commit()

    print(f"✓ 宽基指数初始化完成: {len(BROAD_INDICES)} 个")
    cursor.close()


# ================================================
# 初始化行业 ETF 池
# ================================================
def init_industry_etfs(conn):
    """
    初始化行业 ETF 池（交易型 ETF）
    v4.6: 包含投资逻辑说明
    """
    print(f"\n正在初始化行业 ETF 池...")
    print(f"✓ 包含 {len(INDUSTRY_ETFS)} 个行业 ETF")

    # 准备插入数据
    insert_data = []

    for etf in INDUSTRY_ETFS:
        insert_data.append((
            etf['code'],                    # symbol (ETF代码)
            etf['name'],                    # name (板块名称，如"人工智能(AI)")
            'industry',                     # category
            etf['group'],                   # industry_level (分组名，如"科技 (TMT)")
            etf['etf_label'],               # dominant_etf (复用为ETF标签)
            etf['sort_id'],                 # sort_rank (固定排序ID)
            etf.get('investment_logic'),    # investment_logic (投资逻辑说明，Markdown格式)
            True,                           # is_active
            False                           # is_system_bench
        ))

    # 批量插入
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO monitor_config
            (symbol, name, category, industry_level, dominant_etf, sort_rank, investment_logic, is_active, is_system_bench)
        VALUES %s
        ON CONFLICT (symbol)
        DO UPDATE SET
            name = EXCLUDED.name,
            category = EXCLUDED.category,
            industry_level = EXCLUDED.industry_level,
            dominant_etf = EXCLUDED.dominant_etf,
            sort_rank = EXCLUDED.sort_rank,
            investment_logic = EXCLUDED.investment_logic,
            is_active = EXCLUDED.is_active,
            updated_at = CURRENT_TIMESTAMP
    """

    execute_values(cursor, insert_query, insert_data)
    conn.commit()

    # 按分组统计
    group_stats = {}
    for etf in INDUSTRY_ETFS:
        group = etf['group']
        group_stats[group] = group_stats.get(group, 0) + 1

    print("\n✓ 行业 ETF 池初始化完成！")
    print("=" * 60)
    print("📊 分组统计（按显示顺序）：")
    # 按分组顺序显示
    group_order = ["科技 (TMT)", "高端制造", "医药消费", "周期资源", "金融"]
    for group in group_order:
        if group in group_stats:
            print(f"  - {group}: {group_stats[group]} 个")
    print(f"\n总计: {len(INDUSTRY_ETFS)} 个行业 ETF")
    print("=" * 60)

    cursor.close()


# ================================================
# 主函数
# ================================================
def main():
    print("=" * 60)
    print("鱼盆趋势雷达 - 数据库初始化 v4.6")
    print("指数+ETF混合双轨 + 投资逻辑深度解析")
    print("=" * 60)

    try:
        # 连接数据库
        conn = get_db_connection()
        print("✓ 数据库连接成功")

        # 清理旧数据
        clean_old_data(conn)

        # 初始化宽基指数池
        init_broad_indices(conn)

        # 初始化行业 ETF 池
        init_industry_etfs(conn)

        # 查询统计
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM monitor_config WHERE category='broad'")
        broad_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM monitor_config WHERE category='industry'")
        industry_count = cursor.fetchone()[0]

        print("\n" + "=" * 60)
        print("初始化完成！数据统计：")
        print(f"  - 宽基指数: {broad_count} 个")
        print(f"  - 行业 ETF: {industry_count} 个")
        print(f"  - 总资产数: {broad_count + industry_count} 个")
        print("=" * 60)
        print("\n💡 提示：")
        print("  - 宽基指数使用原生指数代码 (index_daily)")
        print("  - 行业 ETF 使用交易型 ETF 代码 (fund_daily + qfq)")
        print("=" * 60)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    main()
