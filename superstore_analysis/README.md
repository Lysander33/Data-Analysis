# Superstore 超市销售数据分析

> 一家美国大型连锁超市的 4 年销售数据（2014-2017），分析哪些产品、地区、品类和客户群体值得重点关注，哪些需要避免。

## 快速开始

```bash
pip install -r requirements.txt
python data_analysis.py
```

## 数据概览

| 指标 | 数值 |
|------|------|
| 数据规模 | 9,994 条订单记录，21 个字段 |
| 时间跨度 | 2014-01 ~ 2017-12（48 个月） |
| 品类 | 3 大类（Furniture / Office Supplies / Technology） |
| 子品类 | 17 个子品类 |
| 地区 | 4 大区域（West / East / Central / South） |
| 客户细分 | Consumer / Corporate / Home Office |

## 核心发现

### 整体指标

| 指标 | 数值 |
|------|------|
| 总销售额 | $2,297,201 |
| 总利润 | $286,397 |
| 整体利润率 | 12.5% |
| 亏损订单占比 | 18.7%（约 1,871 笔订单） |

### 品类分析

| 品类 | 总利润 | 利润率 | 定位 |
|------|--------|--------|------|
| Technology | $145,455 | 17.4% | 核心盈利引擎 |
| Office Supplies | $122,491 | 17.0% | 稳定利润来源 |
| Furniture | $18,451 | 2.5% | 高销售额低利润，问题品类 |

Technology 以最高利润率和第二高销售额成为最佳品类。Furniture 利润率仅 2.5%，但其销售额居首 —— 高销售额低利润，说明 Furniture 成本结构或折扣管理存在严重问题。

### 子品类利润排名（17 个完整排名）

| 排名 | 子品类 | 总利润 | 所属品类 |
|------|--------|--------|----------|
| 1 | Copiers | $55,618 | Technology |
| 2 | Phones | $44,516 | Technology |
| 3 | Accessories | $41,937 | Technology |
| 4 | Paper | $34,054 | Office Supplies |
| 5 | Binders | $30,222 | Office Supplies |
| 6 | Chairs | $26,597 | Furniture |
| 7 | Storage | $22,416 | Office Supplies |
| 8 | Appliances | $18,142 | Office Supplies |
| 9 | Envelopes | $6,349 | Office Supplies |
| 10 | Labels | $5,232 | Office Supplies |
| 11 | Art | $3,900 | Office Supplies |
| 12 | Machines | $3,385 | Technology |
| 13 | Fasteners | $950 | Office Supplies |
| 14 | Furnishings | -$694 | Furniture |
| 15 | Supplies | -$1,189 | Office Supplies |
| 16 | Bookcases | -$3,473 | Furniture |
| 17 | Tables | -$17,725 | Furniture |

**关键洞察**：Copiers 一骑绝尘，利润超过第二名的 Phones 25%。Furniture 品类的 4 个子品类中，仅 Chairs 盈利，Tables、Bookcases、Furnishings 全线亏损。

### 地区分析

| 地区 | 总利润 | 利润率 | 建议 |
|------|--------|--------|------|
| West | $108,418 | 14.9% | 加大投入 |
| East | $91,523 | 13.5% | 加大投入 |
| South | $46,749 | 11.9% | 维持 |
| Central | $39,706 | 7.9% | 关注运营效率 |

**West 和 East 贡献了 70% 的总利润**，且利润率高于公司平均水平。Central 利润率仅 7.9%，显著偏低，需检查该区域是否存在额外的物流成本或过度打折。

### 客户细分

| 客户群体 | 总利润 | 利润率 | 客单价 | 建议 |
|----------|--------|--------|--------|------|
| Consumer | $134,119 | 11.6% | $224 | 量大但利薄 |
| Corporate | $91,979 | 13.0% | $234 | 利润稳定 |
| Home Office | $60,299 | 14.0% | $241 | 利润率最高 |

Home Office 利润率最高（14.0%），Corporate 次之。Consumer 虽然利润总额最大但利润率最低 —— 建议加大 Home Office 和 Corporate 群体的精准营销，对 Consumer 群体加强折扣管控。

### 折扣影响 —— 利润头号杀手

| 折扣档位 | 亏损率 | 订单占比 | 影响 |
|----------|--------|----------|------|
| 无折扣 | 0.0% | 48.0% | 零风险 |
| 低折扣 (1-20%) | 13.8% | 38.0% | 少量亏损 |
| 中折扣 (21-40%) | 90.2% | 4.6% | 绝大部分亏损 |
| 高折扣 (>40%) | **100.0%** | 9.3% | 必然亏损 |

中高折扣订单（>20%）仅占订单总量的 13.9%，却造成了几乎所有亏损。**高折扣（>40%）订单的亏损率是 100%，无一例外**。严格控制折扣审批是扭转亏损最直接、最有效的杠杆。

### 月度趋势

销售额呈明显的季节性波动模式：

| 时期 | 特征 |
|------|------|
| Q1（1-3 月） | 淡季，销售额全年最低 |
| Q2（4-6 月） | 温和回升 |
| Q3（7-9 月） | 旺季开始，8-9 月为销售高峰 |
| Q4（10-12 月） | 旺季延续，全年销售最高点 |

但利润趋势并非与销售额完全同步 —— 部分高销售月份利润反而低迷，说明旺季促销折扣侵蚀了利润。累计利润曲线在促销旺季出现明显的增速放缓甚至平台期。

### 数值相关性矩阵

| Pearson r | Sales | Profit | Discount | Quantity |
|-----------|-------|--------|----------|----------|
| **Sales** | 1.00 | — | — | — |
| **Profit** | 0.48 | 1.00 | — | — |
| **Discount** | -0.03 | **-0.22** | 1.00 | — |
| **Quantity** | 0.20 | 0.07 | 0.01 | 1.00 |

**Key takeaways**：
- Sales 与 Profit 仅 0.48 的中等相关 —— 高销售额并不保证高利润
- Discount 与 Profit 负相关（-0.22）—— 打折直接侵蚀利润
- **Discount 与 Sales 几乎零相关（-0.03）** —— 打折并不能有效提升销售额，这个发现颠覆了"薄利多销"的假设

---

## 建议关注

### Top 盈利产品

| 产品 | 子品类 | 利润 |
|------|--------|------|
| Canon imageCLASS 2200 Advanced Copier | Copiers | $25,200 |
| Fellowes PB500 Electric Punch | Binders | $7,753 |
| HP LaserJet 3310 Copier | Copiers | $6,984 |
| Canon PC1060 Personal Laser Copier | Copiers | $4,571 |
| HP Designjet T520 Inkjet Printer | Machines | $4,095 |
| Ativa V4110MDD Micro-Cut Shredder | Machines | $3,773 |
| 3D Systems Cube Printer 2nd Gen | Machines | $3,718 |
| Plantronics Savi W720 Headset | Accessories | $3,696 |
| Ibico EPK-21 Electric Binding System | Binders | $3,345 |
| Zebra ZM400 Thermal Label Printer | Machines | $3,344 |

**建议**：对 Copiers 和 Binders 子品类加大库存和营销投入，明星单品集中于此。

### 战略重点

1. **Copiers 子品类**：总利润 $55,618，是第 2 名 Phones 的 1.25 倍，核心中的核心
2. **West + East 地区**：贡献 70% 利润，作为基本盘稳固投入
3. **Home Office 客群**：利润率最高，精准营销扩大覆盖
4. **无折扣订单**：占 48% 订单量且零亏损，维护好这部分自然流量

---

## 风险提示

### Top 亏损产品

| 产品 | 子品类 | 亏损 |
|------|--------|------|
| Cubify CubeX 3D Printer Double Head | Machines | -$8,880 |
| Lexmark MX611dhe Laser Printer | Machines | -$4,590 |
| Cubify CubeX 3D Printer Triple Head | Machines | -$3,840 |
| Chromcraft Bull-Nose Conference Tables | Tables | -$2,876 |
| Bush Advantage Racetrack Conference Tables | Tables | -$1,934 |
| GBC DocuBind P400 Electric Binding System | Binders | -$1,878 |
| Cisco TelePresence System EX90 | Machines | -$1,811 |
| Martin Yale Chadless Electric Letter Opener | Supplies | -$1,299 |
| Balt Solid Wood Round Tables | Tables | -$1,201 |
| BoxOffice By Design Meeting Tables | Tables | -$1,148 |

### 重点风险

1. **Tables 子品类**：总亏损 $17,725，需全面复盘定价和成本结构
2. **高折扣（>40%）订单**：亏损率 100%，应立即建立折扣审批上限机制
3. **Cubify 3D 打印机系列**：两款产品合计亏损 $12,720，考虑下架或调整供货策略
4. **Machines 子品类**：虽整体盈利但多款 3D 打印机和高端设备严重亏损，需单品逐一审核

---

## 项目结构

```
superstore_analysis/
├── superstore.csv                  # 数据集（9,994 行 × 21 列）
├── data_analysis.py                # 分析脚本（单一入口）
├── requirements.txt                # Python 依赖
├── README.md                       # 本文档
└── outputs/
    └── charts/
        ├── analysis_results.json   # 结构化分析结果（JSON）
        └── 11 张分析图表 (PNG)      # 运行脚本自动生成
```
