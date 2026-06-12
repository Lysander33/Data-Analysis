# 印度笔记本电脑规格与价格数据分析

数据来源 [Kaggle Laptop Price Dataset](https://www.kaggle.com/datasets/ionaskel/laptop-prices)，涵盖印度市场 1,274 款笔记本的规格和价格信息。价格单位为印度卢比 (₹, INR)，1 USD ≈ 83 INR (2024)。

## 目录结构

```
laptop_analysis/
├── laptop_data.csv            # 原始 CSV 数据 (1,304 行)
├── laptop_data_text.jsonl     # JSONL 格式文本数据
├── my_config.yaml             # 数据清洗流水线配置
├── data_analysis.py           # 主分析脚本 (终端输出 + 图表生成)
├── requirements.txt           # Python 依赖
├── outputs/
│   ├── charts/                # 15 张分析图表 (PNG)
│   │   └── analysis_results.json  # 分析结果 (JSON)
│   └── <job_id>/              # 清洗流水线产出
│       ├── my_cleaned_data.jsonl      # 清洗后的数据
│       └── logs/                      # 运行日志
└── README.md
```

## 快速开始

```bash
pip install -r requirements.txt
python data_analysis.py
```

脚本默认自动扫描 `outputs/` 下最新的 `my_cleaned_data.jsonl`。也可手动指定输入：

```bash
python data_analysis.py --input outputs/20260612_045525_6be183/my_cleaned_data.jsonl
```

## 分析内容

### 终端输出 (18 项统计)

| # | 分析项 | 说明 |
|---|--------|------|
| 1 | 价格整体统计 | 均值、中位数、标准差、价格分桶分布 |
| 2 | 各品牌价格对比 | 19 个品牌的均价/最低/最高 |
| 3 | 各类型价格对比 | 超极本、游戏本、工作站等 6 类 |
| 4-5 | CPU 分析 | Intel/AMD 品牌占比与系列均价 |
| 6-7 | GPU 分析 | 品牌分布 + 集成 vs 独立显卡 |
| 8 | 内存与价格 | 2GB–64GB 各档位价格分布 |
| 9 | 存储类型 | SSD/HDD/Flash/混合存储 |
| 10 | 屏幕尺寸 | 10.1"–18.4" 价格趋势 |
| 11 | 操作系统 | 9 种 OS 的数量与均价 |
| 12 | 重量与价格 | 按重量分桶统计 |
| 13 | 相关性分析 | Pearson 相关系数矩阵 |
| 14 | 线性回归 | 价格 ~ 内存 + 英寸 + 重量 (最小二乘) |
| 15 | 假设检验 | Welch's t-test: SSD vs HDD、Intel vs AMD、独显 vs 集显 |
| 16-17 | Top 5 最贵/最便宜 | 含离群值标注 |
| 18 | 离群值报告 | IQR 方法，1.5 倍乘数 |
| 19 | 品牌×类型交叉统计 | 数量 >= 5 的组合 |

### 可视化图表 (15 张)

| # | 图表 | 类型 |
|---|------|------|
| 01 | 价格分布 + 累计分布 | 直方图 |
| 02 | 各品牌均价对比 Top 12 | 条形图 |
| 03 | 各类型笔记本均价 | 横向条形图 |
| 04 | 内存容量 vs 价格 | 箱线图 |
| 05 | 存储类型分布 + 均价 | 饼图 + 条形图 |
| 06 | 屏幕尺寸 vs 价格 (离群值高亮) | 散点图 |
| 07 | 操作系统分布 | 饼图 |
| 08 | 重量 vs 价格 (按品牌着色) | 散点图 |
| 09 | 内存 × 存储类型 | 热力图 (均价 + 样本量) |
| 10 | CPU 品牌分布 + 均价 | 饼图 + 条形图 |
| 11 | CPU 系列均价 (数量>=10) | 横向条形图 |
| 12 | GPU 品牌分布 + 均价 | 饼图 + 条形图 |
| 13 | 集成显卡 vs 独立显卡 | 箱线图 |
| 14 | 特征相关性热力图 | Pearson r |
| 15 | 价格 vs 内存 散点 + 回归线 | 散点 + 线性回归 |

## 核心发现

- **均价** ₹60,503，中位数 ₹52,694，样本偏右分布（高价机拉高均值）
- **Strong brand premium**: Apple (₹83,340)、Razer (₹178,282)、MSI (₹92,116)
- **存储溢价显著**: SSD 机型比 HDD 机型平均贵 2.3 倍 (p < 0.001)
- **独显溢价**: 独立显卡机型均价 ₹79,747 vs 集显 ₹54,415
- **内存是强价格信号**: Pearson r = 0.62, 每增加 1GB 内存价格上升约 ₹2,600
- **IQR 检测到 28 条离群值** (2.2%)，多为高端工作站和游戏本
- **Intel 绝对主导**：95.2% 的机型使用 Intel CPU

## 数据清洗流水线

`my_config.yaml` 定义了清洗步骤（依赖 `mini-dataset-processing` 框架）：

1. **文本长度过滤** — 丢弃过短/过长记录
2. **链接清洗** — 移除文本中的 URL
3. **文档去重** — 移除重复记录

清洗产物流向 `outputs/<job_id>/my_cleaned_data.jsonl`，供分析脚本消费。

## 技术说明

- 统计方法：Pearson 相关系数、Welch's t-test（正态近似）、IQR 离群值检测、OLS 线性回归 — 均使用纯 Python + numpy 实现，不依赖 scipy
- 编码处理：Win32 平台自动重配 stdout/stderr 为 UTF-8，确保 ₹ 符号正常输出
- 图表字体：运行时自动探测系统可用的中文字体（微软雅黑 > 黑体 > Noto Sans > 降级 sans-serif）
- 价格精度：原始数据带 4 位小数（疑为美元按浮动汇率换算），分析中展示四舍五入到整数卢比
