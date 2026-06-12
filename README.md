# 数据分析学习

使用 AI 工具辅助进行数据处理、统计分析与可视化学习，数据集来自 [Kaggle](https://www.kaggle.com/)。

---

## 项目列表

| 项目 | 数据来源 | 内容 |
|------|----------|------|
| [laptop_analysis/](./laptop_analysis/) | [Laptop Price Dataset](https://www.kaggle.com/datasets/ionaskel/laptop-prices) | 印度市场 1,274 款笔记本规格与价格分析 |

### laptop_analysis 分析结果速览

- **样本量** 1,274 款机型，均价 ₹60,503（中位数 ₹52,694），分布右偏
- **品牌溢价显著**：Razer 均价 ₹178,282，Apple ₹83,340，MSI ₹92,116
- **Intel 绝对主导**：95.2% 的机型使用 Intel CPU
- **SSD 溢价**：SSD 机型比 HDD 机型平均贵 2.3 倍（p < 0.001）
- **独立显卡溢价**：独显机型均价 ₹79,747 vs 集显 ₹54,415
- **内存是强价格信号**：Pearson r = 0.62，每增加 1GB 内存价格上升约 ₹2,600
- IQR 方法检出 **28 条离群值**（2.2%），多为高端工作站和游戏本

生成 15 张分析图表，完整分析见 [laptop_analysis/README.md](./laptop_analysis/README.md)。

