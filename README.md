# 数据分析学习

使用 AI 工具辅助进行数据处理、统计分析与可视化学习，数据集来自 [Kaggle](https://www.kaggle.com/)。

---

## 项目列表

| 项目 | 数据来源 | 内容 |
|------|----------|------|
| [laptop_analysis/](./laptop_analysis/) | [Laptop Price Dataset](https://www.kaggle.com/datasets/ionaskel/laptop-prices) | 印度市场 1,274 款笔记本规格与价格分析 |
| [superstore_analysis/](./superstore_analysis/) | [Superstore Sales Dataset](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final) | 美国超市 9,994 笔订单销售与利润分析 |
| [news_analysis/](./news_analysis/) | Fake/Real News Dataset | 45,757 条新闻真假文本特征对比分析 |

---

## laptop_analysis 速览

印度市场 1,274 款笔记本电脑的规格与价格统计分析。

| 指标 | 数值 |
|------|------|
| 均价 | ₹60,503（中位数 ₹52,694） |
| 价格区间 | ₹9,271 — ₹324,955 |
| 样本量 | 1,274 款，覆盖 19 个品牌 |

- **品牌溢价显著**：Razer 均价 ₹178,282，Apple ₹83,341，MSI ₹92,116；Acer 最亲民 ₹33,751
- **Intel 绝对主导**：95.2% 机型使用 Intel CPU，AMD 仅 4.7%（集中于低端市场）
- **SSD 溢价**：SSD 机型比 HDD 机型平均贵 2.3 倍（p < 0.001）
- **独显溢价**：Nvidia 独显机型均价 ₹79,747 vs Intel 集显 ₹54,415（p < 0.001）
- **内存是强价格信号**：Pearson r = 0.62，每增加 1GB 内存价格上升约 ₹2,600
- IQR 方法检出 **28 条离群值**（2.2%），多为高端工作站和游戏本

生成 15 张分析图表，完整分析见 [laptop_analysis/README.md](./laptop_analysis/README.md)。

---

## superstore_analysis 速览

美国大型连锁超市 2014-2017 年 9,994 笔订单的销售与利润分析。

| 指标 | 数值 |
|------|------|
| 总销售额 | $2,297,201 |
| 总利润 | $286,397（利润率 12.5%） |
| 亏损订单占比 | 18.7% |

- **Technology 品类利润最高**（$145,455，利润率 17.4%）；Furniture 利润率仅 2.5%
- **Copiers 子品类一骑绝尘**：$55,618 利润，是第 2 名 Phones 的 1.25 倍
- **Tables 子品类亏损最大**（-$17,725），Furniture 子品类 3/4 亏损
- **West + East 贡献 70% 利润**，Central 利润率仅 7.9%
- **折扣是利润头号杀手**：高折扣（>40%）订单 **100% 亏损**，中折扣（21-40%）亏损率 90.2%
- **打折不能提升销售额**：Discount 与 Sales 几乎零相关（Pearson r = -0.03）

生成 11 张分析图表，完整分析见 [superstore_analysis/README.md](./superstore_analysis/README.md)。

---

## news_analysis 速览

45,757 条新闻文本的真假对比分析，提取 19 个文本特征，量化真假新闻的语言学差异。

| 指标 | 数值 |
|------|------|
| 样本量 | 45,757 条（真假各 50%） |
| 真新闻来源 | 94.9% 含 Reuters 引用 |

- **停用词比例**是最大效应量特征（d=+0.86）：假新闻 42.0% vs 真 37.6%
- **每句词数差异巨大**：假新闻每句 138 词 vs 真新闻 18.5 词（d=+0.41），假新闻长句拼接无断句
- **感叹号密度差 16 倍**（d=+0.39），问号 9 倍（d=+0.52）—— 假新闻情绪化标点泛滥
- **全大写词 2.4 倍**（d=+0.40）：假新闻大量使用 BREAKING、SHOCKING 等标题党格式
- **假新闻 69.3% 含图片引用**（"image via"、"screen capture"），真新闻仅 9.6%
- **Reuters 引用几乎完美区分真假**：真 94.9% vs 假 1.3%

生成 10 张分析图表，完整分析见 [news_analysis/README.md](./news_analysis/README.md)。

---

## 技术栈

| 项目 | 核心依赖 | 统计方法 |
|------|----------|----------|
| laptop_analysis | numpy, matplotlib | Pearson r, Welch's t-test, IQR, OLS（纯 Python 实现） |
| superstore_analysis | pandas, matplotlib, numpy | 分组聚合、折扣分档、相关性矩阵、趋势分析 |
