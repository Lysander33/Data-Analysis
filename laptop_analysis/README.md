# 印度笔记本电脑规格与价格数据分析

数据来源 [Kaggle Laptop Price Dataset](https://www.kaggle.com/datasets/ionaskel/laptop-prices)，涵盖印度市场 1,274 款笔记本的规格和价格信息。价格单位为印度卢比 (₹, INR)，1 USD ≈ 83 INR (2024)。

## 快速开始

```bash
pip install -r requirements.txt
python data_analysis.py
```

脚本默认自动扫描 `outputs/` 下最新的 `my_cleaned_data.jsonl`，也可手动指定输入：

```bash
python data_analysis.py --input outputs/<job_id>/my_cleaned_data.jsonl
```

## 核心发现

| 指标 | 数值 |
|------|------|
| 样本量 | 1,274 款机型 |
| 均价 | ₹60,503（中位数 ₹52,694） |
| 价格区间 | ₹9,271 — ₹324,955 |
| 离群值 | 28 条（IQR 方法，1.5× 乘数） |

![价格分布](images/01_价格分布.png)

- **品牌溢价显著**：Razer 均价 ₹178,282，Apple ₹83,340，MSI ₹92,116，Acer 最亲民 ₹33,751

![各品牌均价](images/02_各品牌均价.png)

- **Intel 绝对主导**：95.2% 的机型使用 Intel CPU，AMD 仅占 4.8%
- **SSD 溢价显著**：SSD 机型比 HDD 机型平均贵 2.3 倍 (Welch's t-test, p < 0.001)
- **独显溢价**：独立显卡机型均价 ₹79,747 vs 集显 ₹54,415 (p < 0.001)
- **内存是强价格信号**：Pearson r = 0.62，每增加 1GB 内存价格上升约 ₹2,600

![屏幕尺寸与价格](images/06_屏幕尺寸与价格.png)

![相关性热力图](images/14_相关性热力图.png)

![价格与内存回归](images/15_价格与内存回归.png)

## 分析内容

### 终端输出（19 项统计）

价格统计、品牌/类型/CPU/GPU 对比、内存与存储分析、屏幕与重量趋势、相关性矩阵、OLS 线性回归、Welch's t-test 假设检验、IQR 离群值检测、品牌×类型交叉统计。

### 可视化图表（15 张）

直方图、条形图、箱线图、饼图、散点图、热力图 — 覆盖价格分布、品牌对比、硬件配置与价格关系、相关性分析等维度。

## 数据清洗流水线

`my_config.yaml` 定义清洗步骤（依赖 `mini-dataset-processing` 框架）：

1. **文本长度过滤** — 丢弃过短/过长记录
2. **链接清洗** — 移除文本中的 URL
3. **文档去重** — 移除重复记录

清洗产出流向 `outputs/<job_id>/my_cleaned_data.jsonl`。

## 技术说明

- 统计方法：Pearson 相关系数、Welch's t-test（正态近似）、IQR 离群值检测、OLS 线性回归 — 纯 Python + numpy 实现，不依赖 scipy
- 编码处理：Win32 平台自动重配 stdout/stderr 为 UTF-8，确保 ₹ 符号正常输出
- 图表字体：运行时自动探测系统可用的中文字体

## 目录结构

```
laptop_analysis/
├── laptop_data.csv
├── laptop_data_text.jsonl
├── my_config.yaml
├── data_analysis.py
├── requirements.txt
├── images/                     # 精选成果图
├── outputs/
│   ├── charts/                 # 15 张分析图表 (PNG)
│   │   └── analysis_results.json
│   └── <job_id>/               # 清洗流水线产出
│       ├── my_cleaned_data.jsonl
│       └── logs/
└── README.md
```
