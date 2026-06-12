# -*- coding: utf-8 -*-
"""
印度笔记本电脑规格与价格数据分析

数据来源: 印度笔记本电脑市场
价格单位: 印度卢比 (₹, INR)
汇率参考: 1 USD ≈ 83 INR (2024年)

注意:
- 原始价格数据带 4 位小数（如 71378.6832），疑为美元按浮动汇率换算产物
- 分析中展示时四舍五入到整数卢比，内部计算保留原始精度
- 印度卢比的货币符号为 ₹ (U+20B9)，部分终端可能不显示
"""

import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# ── 0. 编码配置 ──
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# 脚本所在目录，所有相对路径基于此目录
SCRIPT_DIR = Path(__file__).resolve().parent

CURRENCY = "₹"
PRICE_UNIT = "印度卢比 (INR)"
# 图表中 ₹ 符号在微软雅黑等中文字体中可能不显示，使用文字替代
CHART_CURRENCY = "INR "


# ══════════════════════════════════════════════════════════════════════
# ── 工具函数 ──
# ══════════════════════════════════════════════════════════════════════

def find_latest_cleaned_data(base_dir: Path | None = None) -> Path | None:
    """扫描 outputs/ 目录，返回最新的 my_cleaned_data.jsonl 路径。
    按目录名中的时间戳排序 (YYYYMMDD_HHMMSS_xxxxxx 格式)。
    """
    if base_dir is None:
        base_dir = SCRIPT_DIR / "outputs"
    outputs = Path(base_dir)
    if not outputs.exists() or not outputs.is_dir():
        return None
    dirs = [d for d in outputs.iterdir() if d.is_dir() and d.name != "charts"]
    if not dirs:
        return None
    # 按目录名降序排列（时间戳自然排序即可）
    dirs.sort(key=lambda d: d.name, reverse=True)
    for d in dirs:
        candidate = d / "my_cleaned_data.jsonl"
        if candidate.exists():
            return candidate
    return None


def detect_chinese_font() -> str:
    """探测可用的中文字体，返回字体名称。失败时返回 'sans-serif'。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    candidates = [
        "Microsoft YaHei", "SimHei", "Noto Sans CJK SC",
        "WenQuanYi Micro Hei", "Noto Sans SC", "sans-serif",
    ]
    out_dir = SCRIPT_DIR / "outputs" / "charts"
    out_dir.mkdir(parents=True, exist_ok=True)

    for font_name in candidates:
        try:
            plt.rcParams["font.family"] = font_name
            fig = plt.figure(figsize=(1, 1), dpi=10)
            fig.text(0.5, 0.5, "中文", fontsize=8)
            test_path = out_dir / "_font_test.png"
            fig.savefig(str(test_path), dpi=10)
            plt.close(fig)
            if test_path.exists():
                test_path.unlink()
            return font_name
        except Exception:
            continue
    return "sans-serif"


def classify_storage(storage_str: str) -> dict:
    """统一分类存储类型，返回 {'type': str, 'has_ssd': bool, 'has_hdd': bool}。

    分类规则（按优先级从高到低）：
    1. 同时含 SSD 和 HDD → "混合"
    2. 含 hybrid 关键词 → "混合"
    3. 纯 Flash（含 flash 不含 ssd/hdd）→ "Flash 闪存"
    4. 纯 SSD → "SSD 固态"
    5. 纯 HDD → "HDD 机械"
    6. 其他组合 → "混合"
    """
    s = storage_str.lower()
    has_ssd = "ssd" in s
    has_hdd = "hdd" in s
    has_flash = "flash" in s
    has_hybrid = "hybrid" in s

    if has_ssd and has_hdd:
        return {"type": "混合", "has_ssd": True, "has_hdd": True}
    if has_hybrid and not (has_ssd and has_hdd):
        return {"type": "混合", "has_ssd": has_ssd, "has_hdd": has_hdd}
    if has_flash and not has_ssd and not has_hdd:
        return {"type": "Flash 闪存", "has_ssd": False, "has_hdd": False}
    if has_flash and has_hdd:
        return {"type": "混合", "has_ssd": False, "has_hdd": True}
    if has_flash and has_ssd:
        return {"type": "混合", "has_ssd": True, "has_hdd": False}
    if has_ssd:
        return {"type": "SSD 固态", "has_ssd": True, "has_hdd": False}
    if has_hdd:
        return {"type": "HDD 机械", "has_ssd": False, "has_hdd": True}
    return {"type": "其他", "has_ssd": False, "has_hdd": False}


def classify_cpu(cpu_str: str) -> dict:
    """解析 CPU 字符串，提取品牌、系列、频率。
    返回 {'brand': str, 'series': str, 'freq_ghz': float|None}
    """
    result = {"brand": "其他", "series": "其他", "freq_ghz": None}
    s = cpu_str.lower()

    # 品牌
    if "intel" in s:
        result["brand"] = "Intel"
    elif "amd" in s:
        result["brand"] = "AMD"
    else:
        return result

    # 频率: 匹配 X.XGHz 或 XGHz
    m = re.search(r"(\d+\.?\d*)\s*GHz", cpu_str, re.IGNORECASE)
    if m:
        result["freq_ghz"] = float(m.group(1))

    # 系列细分
    if result["brand"] == "Intel":
        m = re.search(r"core\s+(i\d|m\s*\d?)", s)
        if m:
            core = m.group(1).upper().replace(" ", "")
            result["series"] = f"Core {core}"
        elif "atom" in s:
            result["series"] = "Atom"
        elif "celeron" in s:
            result["series"] = "Celeron"
        elif "pentium" in s:
            result["series"] = "Pentium"
        elif "xeon" in s:
            result["series"] = "Xeon"
        elif "core m" in s:
            result["series"] = "Core M"
        else:
            result["series"] = "Intel 其他"
    elif result["brand"] == "AMD":
        if "ryzen" in s:
            result["series"] = "Ryzen"
        elif "fx" in s:
            result["series"] = "FX"
        elif re.search(r"(a\d|a-series)", s):
            result["series"] = "A-Series"
        elif re.search(r"(e\d|e-series)", s):
            result["series"] = "E-Series"
        else:
            result["series"] = "AMD 其他"

    return result


def classify_gpu(gpu_str: str) -> dict:
    """解析 GPU 字符串，提取品牌、类型、型号家族。
    返回 {'brand': str, 'type': str, 'model_family': str}
    """
    result = {"brand": "其他", "type": "未知", "model_family": "其他"}
    s = gpu_str.lower()

    # 品牌识别 + 类型判断
    if "nvidia" in s or "geforce" in s or "gtx" in s or "quadro" in s:
        result["brand"] = "Nvidia"
        result["type"] = "独立"
        if "gtx" in s:
            result["model_family"] = "GeForce GTX"
        elif "rtx" in s:
            result["model_family"] = "GeForce RTX"
        elif "mx" in s:
            result["model_family"] = "GeForce MX"
        elif "quadro" in s:
            result["model_family"] = "Quadro"
        else:
            result["model_family"] = "GeForce GT"
    elif "amd" in s or "radeon" in s:
        result["brand"] = "AMD"
        if any(x in s for x in ["rx", "pro", "firepro", "r9", "r7", "r5", "r3"]):
            result["type"] = "独立"
        elif "vega" in s:
            result["type"] = "独立"
        else:
            result["type"] = "集成"
        if "rx" in s:
            result["model_family"] = "Radeon RX"
        elif "pro" in s or "firepro" in s:
            result["model_family"] = "Radeon Pro"
        elif "vega" in s:
            result["model_family"] = "Radeon Vega"
        else:
            result["model_family"] = "Radeon R"
    elif "intel" in s:
        result["brand"] = "Intel"
        result["type"] = "集成"
        if "iris" in s:
            result["model_family"] = "Iris"
        elif "uhd" in s:
            result["model_family"] = "UHD Graphics"
        else:
            result["model_family"] = "HD Graphics"
    elif "arm" in s or "mali" in s or "adreno" in s:
        result["brand"] = "ARM"
        result["type"] = "集成"
        if "mali" in s:
            result["model_family"] = "Mali"
        elif "adreno" in s:
            result["model_family"] = "Adreno"
        else:
            result["model_family"] = "ARM GPU"

    return result


def detect_outliers_iqr(values: list, multiplier: float = 1.5) -> tuple:
    """IQR 方法检测离群值。
    返回 (离群值索引列表, 下界, 上界, Q1, Q3, IQR)
    """
    arr = sorted(values)
    n = len(arr)

    def percentile(sorted_data, pct):
        k = (len(sorted_data) - 1) * pct / 100
        f = int(k)
        c = k - f
        if f + 1 < len(sorted_data):
            return sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f])
        return sorted_data[f]

    q1 = percentile(arr, 25)
    q3 = percentile(arr, 75)
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    outlier_indices = [i for i, v in enumerate(values) if v < lower or v > upper]
    return outlier_indices, lower, upper, q1, q3, iqr


def pearson_r(x: list, y: list) -> float:
    """纯 Python 实现 Pearson 相关系数。"""
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
    if std_x == 0 or std_y == 0:
        return 0.0
    return cov / (std_x * std_y)


def welch_ttest(a: list, b: list) -> dict:
    """纯 Python 实现 Welch's t-test（不等方差两样本均值比较）。
    返回 {'t_stat': float, 'p_value': float, 'df': float, 'mean_a': float, 'mean_b': float}
    p-value 用 math.erf 近似计算，在 n>30 时精度足够。
    """
    n1, n2 = len(a), len(b)
    m1 = sum(a) / n1
    m2 = sum(b) / n2
    v1 = sum((x - m1) ** 2 for x in a) / (n1 - 1)
    v2 = sum((x - m2) ** 2 for x in b) / (n2 - 1)
    se = math.sqrt(v1 / n1 + v2 / n2)
    if se == 0:
        return {"t_stat": 0, "p_value": 1.0, "df": float("inf"), "mean_a": m1, "mean_b": m2}
    t_stat = (m1 - m2) / se
    df_num = (v1 / n1 + v2 / n2) ** 2
    df_den = (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    df = df_num / df_den
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))
    return {"t_stat": t_stat, "p_value": p_value, "df": df, "mean_a": m1, "mean_b": m2}


# ══════════════════════════════════════════════════════════════════════
# ── 主程序 ──
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # ── CLI 参数解析 ──
    input_arg = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--input" and i + 1 < len(args):
            input_arg = args[i + 1]
            i += 2
        elif args[i] == "--output-dir" and i + 1 < len(args):
            # 仅用于参考，实际使用 outputs/charts
            i += 2
        else:
            i += 1

    # ── 数据加载 ──
    if input_arg:
        input_file = Path(input_arg)
    else:
        input_file = find_latest_cleaned_data()

    if input_file is None or not input_file.exists():
        print("错误: 未找到清洗后的数据文件。")
        print("  用法: python data_analysis.py [--input <path>]")
        print("  默认: 自动扫描 outputs/ 下最新的 my_cleaned_data.jsonl")
        sys.exit(1)

    data = []
    with open(input_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))

    print(f"数据来源: 印度笔记本电脑市场")
    print(f"价格单位: {PRICE_UNIT}, 1 USD ≈ 83 INR (2024)")
    print(f"货币符号: {CURRENCY}")
    print(f"已加载 {len(data)} 条数据，来源: {input_file}")

    # ── 文本解析 ──
    pattern = re.compile(
        r"^(?P<company>\S+)\s+"
        r"(?P<type>.+?), "
        r"(?P<inches>[\d.]+) inch, "
        r"(?P<screen>.+?) display, "
        r"(?P<cpu>.+?) CPU, "
        r"(?P<ram>\d+)GB RAM, "
        r"(?P<storage>.+?) storage, "
        r"(?P<gpu>.+?) GPU, "
        r"(?P<os>.+?) OS, "
        r"(?P<weight>[\d.]+)kg weight, "
        r"price (?P<price>[\d.]+)$"
    )

    parse_errors = []
    parsed = []
    for idx, item in enumerate(data):
        m = pattern.match(item["text"])
        if m:
            d = m.groupdict()
            try:
                d["inches"] = float(d["inches"])
                d["ram"] = int(d["ram"])
                d["weight"] = float(d["weight"])
                d["price"] = float(d["price"])
                d["price_k"] = d["price"] / 1000
                d["price_display"] = round(d["price"], 0)  # 显示用整数卢比
                # 附加分类信息
                d["cpu_info"] = classify_cpu(d["cpu"])
                d["gpu_info"] = classify_gpu(d["gpu"])
                d["storage_info"] = classify_storage(d["storage"])
                # 合理性验证
                if not (10 <= d["inches"] <= 19):
                    parse_errors.append((idx, f"屏幕尺寸异常: {d['inches']}\""))
                if not (0.5 <= d["weight"] <= 5.5):
                    parse_errors.append((idx, f"重量异常: {d['weight']}kg"))
                if d["price"] <= 0:
                    parse_errors.append((idx, f"价格异常: {d['price']}"))
                parsed.append(d)
            except (ValueError, TypeError) as e:
                parse_errors.append((idx, f"类型转换失败: {e}"))
        else:
            parse_errors.append((idx, "正则不匹配"))

    print(f"解析成功 {len(parsed)} 条 ({len(data) - len(parsed)} 条解析失败)")
    if parse_errors:
        print(f"  (前5条错误: {parse_errors[:5]})")
    if len(parsed) == 0:
        sys.exit(1)

    # ══════════════════════════════════════════════════════════════════
    # ── 分析 ──
    # ══════════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("印度笔记本电脑规格与价格数据分析")
    print(f"价格单位: {PRICE_UNIT}")
    print("=" * 60)

    prices = [d["price"] for d in parsed]
    prices_k = [d["price_k"] for d in parsed]
    n = len(prices)

    # ── 1. 价格整体统计 ──
    print("\n─── 1. 价格整体统计 ───")
    sorted_prices = sorted(prices)
    print(f"  样本数量:          {n}")
    print(f"  均价:              {CURRENCY}{sum(prices)/n:,.0f}")
    print(f"  中位数:            {CURRENCY}{sorted_prices[n//2]:,.0f}")
    print(f"  最低价:            {CURRENCY}{min(prices):,.0f}")
    print(f"  最高价:            {CURRENCY}{max(prices):,.0f}")
    print(f"  标准差:            {CURRENCY}{(sum((p - sum(prices)/n)**2 for p in prices) / n) ** 0.5:,.0f}")

    # IQR 离群值检测
    outlier_idx, o_lower, o_upper, o_q1, o_q3, o_iqr = detect_outliers_iqr(prices)
    print(f"\n  离群值检测 (IQR 方法, multiplier=1.5):")
    print(f"    Q1={CURRENCY}{o_q1:,.0f}  Q3={CURRENCY}{o_q3:,.0f}  IQR={CURRENCY}{o_iqr:,.0f}")
    print(f"    下界={CURRENCY}{o_lower:,.0f}  上界={CURRENCY}{o_upper:,.0f}")
    print(f"    离群值: {len(outlier_idx)} 条 ({len(outlier_idx)/n*100:.1f}%)")

    # 价格分桶
    buckets = [
        ("入门 (< ₹2万)", 0, 20),
        ("中低端 (₹2-4万)", 20, 40),
        ("中端 (₹4-6万)", 40, 60),
        ("中高端 (₹6-9万)", 60, 90),
        ("高端 (₹9-13万)", 90, 130),
        ("旗舰 (> ₹13万)", 130, float("inf")),
    ]
    print(f"\n  价格分布:")
    for label, lo, hi in buckets:
        cnt = sum(1 for p in prices_k if lo <= p < hi)
        print(f"    {label:24s}  {cnt:3d} 台 ({cnt/n*100:5.1f}%)")

    # ── 2. 各品牌价格 ──
    brands = defaultdict(list)
    for d in parsed:
        brands[d["company"]].append(d["price"])
    print("\n─── 2. 各品牌价格对比 ───")
    for brand in sorted(brands, key=lambda b: sum(brands[b]) / len(brands[b]), reverse=True):
        ps = brands[brand]
        print(f"  {brand:12s}  数量={len(ps):3d}  均价={CURRENCY}{sum(ps)/len(ps):>10,.0f}  "
              f"最低={CURRENCY}{min(ps):>8,.0f}  最高={CURRENCY}{max(ps):>10,.0f}")

    # ── 3. 各类型价格 ──
    types = defaultdict(list)
    for d in parsed:
        types[d["type"]].append(d["price"])
    type_names_cn = {
        "Workstation": "工作站", "Gaming": "游戏本", "Ultrabook": "超极本",
        "2 in 1 Convertible": "二合一", "Notebook": "普通笔记本", "Netbook": "上网本",
    }
    print("\n─── 3. 各类型价格对比 ───")
    for t in sorted(types, key=lambda t: sum(types[t]) / len(types[t]), reverse=True):
        ps = types[t]
        cn = type_names_cn.get(t, t)
        print(f"  {cn:10s} ({t:25s})  数量={len(ps):3d}  均价={CURRENCY}{sum(ps)/len(ps):>10,.0f}")

    # ── 4. CPU 分析 ──
    cpu_brands = defaultdict(list)
    cpu_series = defaultdict(list)
    for d in parsed:
        ci = d["cpu_info"]
        cpu_brands[ci["brand"]].append(d["price"])
        cpu_series[ci["series"]].append(d["price"])

    print("\n─── 4. CPU 品牌分析 ───")
    for brand in sorted(cpu_brands, key=lambda b: len(cpu_brands[b]), reverse=True):
        ps = cpu_brands[brand]
        print(f"  {brand:8s}  数量={len(ps):4d} ({len(ps)/n*100:5.1f}%)  "
              f"均价={CURRENCY}{sum(ps)/len(ps):>10,.0f}  "
              f"最低={CURRENCY}{min(ps):>8,.0f}  最高={CURRENCY}{max(ps):>10,.0f}")

    print("\n─── 5. CPU 系列分析 (数量>=10) ───")
    for series in sorted(cpu_series, key=lambda s: sum(cpu_series[s]) / len(cpu_series[s]), reverse=True):
        ps = cpu_series[series]
        if len(ps) >= 10:
            print(f"  {series:15s}  数量={len(ps):3d}  均价={CURRENCY}{sum(ps)/len(ps):>10,.0f}")

    # CPU 品牌统计（不含"其他"）
    cpu_brands_valid = {b: len(ps) for b, ps in cpu_brands.items() if b != "其他"}

    # ── 5. GPU 分析 ──
    gpu_brands = defaultdict(list)
    gpu_types = defaultdict(list)
    for d in parsed:
        gi = d["gpu_info"]
        gpu_brands[gi["brand"]].append(d["price"])
        gpu_types[gi["type"]].append(d["price"])

    print("\n─── 6. GPU 品牌分析 ───")
    for brand in sorted(gpu_brands, key=lambda b: len(gpu_brands[b]), reverse=True):
        ps = gpu_brands[brand]
        print(f"  {brand:8s}  数量={len(ps):4d} ({len(ps)/n*100:5.1f}%)  "
              f"均价={CURRENCY}{sum(ps)/len(ps):>10,.0f}")

    print("\n─── 7. 集成 vs 独立显卡 ───")
    for gt in sorted(gpu_types, key=lambda t: sum(gpu_types[t]) / len(gpu_types[t]), reverse=True):
        ps = gpu_types[gt]
        print(f"  {gt:6s}  数量={len(ps):4d} ({len(ps)/n*100:5.1f}%)  "
              f"均价={CURRENCY}{sum(ps)/len(ps):>10,.0f}")

    # ── 6. 内存 vs 价格 ──
    ram_groups = defaultdict(list)
    for d in parsed:
        ram_groups[d["ram"]].append(d["price"])
    print("\n─── 8. 内存容量与价格关系 ───")
    for ram in sorted(ram_groups):
        ps = ram_groups[ram]
        print(f"  {ram:2d}GB  数量={len(ps):3d}  均价={CURRENCY}{sum(ps)/len(ps):>10,.0f}")

    # ── 7. 存储类型分析 ──
    storage_stats = defaultdict(list)
    for d in parsed:
        st = d["storage_info"]["type"]
        storage_stats[st].append(d["price"])
    print("\n─── 9. 存储类型分析 ───")
    for st in sorted(storage_stats, key=lambda s: len(storage_stats[s]), reverse=True):
        ps = storage_stats[st]
        print(f"  {st:10s}  数量={len(ps):3d}  均价={CURRENCY}{sum(ps)/len(ps):,.0f}")

    # ── 8. 屏幕尺寸 vs 价格 ──
    size_groups = defaultdict(list)
    for d in parsed:
        size_groups[d["inches"]].append(d["price"])
    print("\n─── 10. 屏幕尺寸与价格关系 ───")
    for sz in sorted(size_groups):
        ps = size_groups[sz]
        print(f"  {sz:.1f}\"  数量={len(ps):3d}  均价={CURRENCY}{sum(ps)/len(ps):>10,.0f}")

    # ── 9. 操作系统分布 ──
    os_groups = defaultdict(list)
    for d in parsed:
        os_groups[d["os"]].append(d["price"])
    print("\n─── 11. 操作系统分布 ───")
    for os_name in sorted(os_groups, key=lambda o: len(os_groups[o]), reverse=True):
        ps = os_groups[os_name]
        print(f"  {os_name:15s}  数量={len(ps):4d} ({len(ps)/n*100:5.1f}%)  均价={CURRENCY}{sum(ps)/len(ps):,.0f}")

    # ── 10. 重量 vs 价格 ──
    weight_bins = {
        "轻薄 (<1.5kg)": [], "中等 (1.5-2.0kg)": [],
        "偏重 (2.0-2.5kg)": [], "厚重 (>2.5kg)": [],
    }
    for d in parsed:
        w = d["weight"]
        if w < 1.5:
            weight_bins["轻薄 (<1.5kg)"].append(d["price"])
        elif w < 2.0:
            weight_bins["中等 (1.5-2.0kg)"].append(d["price"])
        elif w < 2.5:
            weight_bins["偏重 (2.0-2.5kg)"].append(d["price"])
        else:
            weight_bins["厚重 (>2.5kg)"].append(d["price"])
    print("\n─── 12. 重量与价格关系 ───")
    for label, ps in weight_bins.items():
        if ps:
            print(f"  {label:20s}  数量={len(ps):3d}  均价={CURRENCY}{sum(ps)/len(ps):,.0f}")

    # ── 11. 统计相关性 ──
    print("\n─── 13. 统计相关性分析 ───")
    inches_vals = [d["inches"] for d in parsed]
    ram_vals = [d["ram"] for d in parsed]
    weight_vals = [d["weight"] for d in parsed]
    features = {"价格": prices, "英寸": inches_vals, "内存(GB)": ram_vals, "重量(kg)": weight_vals}
    names = list(features.keys())
    print(f"  {'':>12s}", end="")
    for name in names:
        print(f"  {name:>10s}", end="")
    print()
    for n1 in names:
        print(f"  {n1:>12s}", end="")
        for n2 in names:
            r = pearson_r(features[n1], features[n2])
            # 标注显著性
            marker = ""
            if n1 != n2:
                if abs(r) > 0.5:
                    marker = " ★"
                elif abs(r) > 0.3:
                    marker = " ·"
            print(f"  {r:>8.3f}{marker}", end="")
        print()
    print("  ★ 强相关 (|r|>0.5)  · 中等相关 (|r|>0.3)")

    # ── 12. 假设检验 ──
    print("\n─── 15. 假设检验 (Welch's t-test) ───")
    # SSD vs HDD
    ssd_prices_test = storage_stats.get("SSD 固态", [])
    hdd_prices_test = storage_stats.get("HDD 机械", [])
    if ssd_prices_test and hdd_prices_test:
        t_result = welch_ttest(ssd_prices_test, hdd_prices_test)
        sig = "***" if t_result["p_value"] < 0.001 else ("**" if t_result["p_value"] < 0.01 else ("*" if t_result["p_value"] < 0.05 else "n.s."))
        print(f"  SSD vs HDD 价格差异:")
        print(f"    SSD 均价={CURRENCY}{t_result['mean_a']:,.0f}  HDD 均价={CURRENCY}{t_result['mean_b']:,.0f}")
        print(f"    t={t_result['t_stat']:.2f}  df={t_result['df']:.1f}  p={t_result['p_value']:.4f}  {sig}")
        if sig == "***":
            print(f"    结论: 差异极其显著 (p<0.001)，SSD 机型明显更贵")

    # Intel vs AMD CPU
    intel_prices = cpu_brands.get("Intel", [])
    amd_prices = cpu_brands.get("AMD", [])
    if intel_prices and amd_prices:
        t_result2 = welch_ttest(intel_prices, amd_prices)
        sig2 = "***" if t_result2["p_value"] < 0.001 else ("**" if t_result2["p_value"] < 0.01 else ("*" if t_result2["p_value"] < 0.05 else "n.s."))
        print(f"  Intel vs AMD CPU 价格差异:")
        print(f"    Intel 均价={CURRENCY}{t_result2['mean_a']:,.0f}  AMD 均价={CURRENCY}{t_result2['mean_b']:,.0f}")
        print(f"    t={t_result2['t_stat']:.2f}  df={t_result2['df']:.1f}  p={t_result2['p_value']:.4f}  {sig2}")

    # 集成 vs 独立显卡
    integrated = gpu_types.get("集成", [])
    discrete = gpu_types.get("独立", [])
    if integrated and discrete:
        t_result3 = welch_ttest(discrete, integrated)
        sig3 = "***" if t_result3["p_value"] < 0.001 else ("**" if t_result3["p_value"] < 0.01 else ("*" if t_result3["p_value"] < 0.05 else "n.s."))
        print(f"  独显 vs 集显 价格差异:")
        print(f"    独显均价={CURRENCY}{t_result3['mean_a']:,.0f}  集显均价={CURRENCY}{t_result3['mean_b']:,.0f}")
        print(f"    t={t_result3['t_stat']:.2f}  df={t_result3['df']:.1f}  p={t_result3['p_value']:.4f}  {sig3}")

    # ── 14. Top 5 最贵 & 最便宜 ──
    sorted_data = sorted(parsed, key=lambda d: d["price"], reverse=True)
    print("\n─── 16. 最贵的 5 款 ───")
    for d in sorted_data[:5]:
        is_outlier = " ⚠离群" if d["price"] > o_upper else ""
        print(f"  {CURRENCY}{d['price_display']:>10,.0f}  {d['company']} {type_names_cn.get(d['type'], d['type'])}  "
              f"{d['cpu_info']['series']}  {d['ram']}GB  {d['inches']:.1f}\"{is_outlier}")

    print("\n─── 17. 最便宜的 5 款 ───")
    for d in sorted_data[-5:]:
        is_outlier = " ⚠离群" if d["price"] < o_lower else ""
        print(f"  {CURRENCY}{d['price_display']:>10,.0f}  {d['company']} {type_names_cn.get(d['type'], d['type'])}  "
              f"{d['cpu_info']['series']}  {d['ram']}GB  {d['inches']:.1f}\"{is_outlier}")

    # ── 15. 离群值详细报告 ──
    if outlier_idx:
        print(f"\n─── 18. 离群值详细报告 (共 {len(outlier_idx)} 条) ───")
        print(f"  检测方法: IQR, 上界={CURRENCY}{o_upper:,.0f}, 下界={CURRENCY}{o_lower:,.0f}")
        for i in outlier_idx[:10]:  # 最多显示 10 条
            d = parsed[i]
            print(f"  {CURRENCY}{d['price_display']:>10,.0f}  {d['company']:12s}  "
                  f"{type_names_cn.get(d['type'], d['type']):8s}  "
                  f"{d['cpu_info']['series']:12s}  {d['ram']}GB  {d['inches']:.1f}\"  {d['weight']}kg")
        if len(outlier_idx) > 10:
            print(f"  ... 还有 {len(outlier_idx) - 10} 条")

    # ── 16. 品牌 × 类型交叉统计 ──
    brand_type = defaultdict(int)
    for d in parsed:
        cn = type_names_cn.get(d["type"], d["type"])
        brand_type[f"{d['company']} {cn}"] += 1
    print("\n─── 19. 品牌 × 类型 数量统计 (>=5) ───")
    for bt, c in sorted(brand_type.items(), key=lambda x: x[1], reverse=True):
        if c >= 5:
            print(f"  {bt:28s}  {c} 台")

    # ── 17. 结果持久化 ──
    analysis_results = {
        "data_source": "印度笔记本电脑市场",
        "currency": "INR",
        "currency_symbol": "₹",
        "sample_size": n,
        "price_summary": {
            "mean": round(sum(prices) / n, 2),
            "median": sorted_prices[n // 2],
            "min": min(prices),
            "max": max(prices),
            "std": round((sum((p - sum(prices) / n) ** 2 for p in prices) / n) ** 0.5, 2),
        },
        "outlier_detection": {
            "method": "IQR",
            "multiplier": 1.5,
            "q1": round(o_q1, 2),
            "q3": round(o_q3, 2),
            "iqr": round(o_iqr, 2),
            "lower_bound": round(o_lower, 2),
            "upper_bound": round(o_upper, 2),
            "outlier_count": len(outlier_idx),
        },
        "brand_stats": {
            brand: {
                "count": len(ps),
                "avg_price": round(sum(ps) / len(ps), 2),
                "min_price": min(ps),
                "max_price": max(ps),
            }
            for brand, ps in brands.items()
        },
        "type_stats": {
            t: {"count": len(ps), "avg_price": round(sum(ps) / len(ps), 2)}
            for t, ps in types.items()
        },
        "cpu_brand_stats": {
            b: {"count": len(ps), "avg_price": round(sum(ps) / len(ps), 2)}
            for b, ps in cpu_brands.items()
        },
        "gpu_brand_stats": {
            b: {"count": len(ps), "avg_price": round(sum(ps) / len(ps), 2)}
            for b, ps in gpu_brands.items()
        },
        "os_stats": {
            os: {"count": len(ps), "avg_price": round(sum(ps) / len(ps), 2)}
            for os, ps in os_groups.items()
        },
    }
    result_path = SCRIPT_DIR / "outputs" / "charts" / "analysis_results.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n分析结果已保存至: {result_path.resolve()}")

    print("\n" + "=" * 60)
    print("终端分析完成，正在生成图表...")
    print("=" * 60)

    # ══════════════════════════════════════════════════════════════════
    # ── 可视化图表 ──
    # ══════════════════════════════════════════════════════════════════
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np

    out_dir = SCRIPT_DIR / "outputs" / "charts"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 中文字体
    chosen_font = detect_chinese_font()
    print(f"\n图表字体: {chosen_font}")
    plt.rcParams["font.family"] = chosen_font
    plt.rcParams["axes.unicode_minus"] = False

    # 价格格式化器
    rupee_fmt = mticker.FuncFormatter(lambda x, _: f"{CHART_CURRENCY}{x:.0f}k")

    # ── 线性回归分析 (需要 numpy) ──
    print("\n─── 14. 线性回归: 价格 ~ 内存 + 英寸 + 重量 ───")
    X = np.column_stack([
        np.ones(n),
        ram_vals,
        inches_vals,
        weight_vals,
    ])
    y = np.array(prices)
    try:
        coeffs, residuals, rank, singular = np.linalg.lstsq(X, y, rcond=None)
        y_pred = X @ coeffs
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        print(f"  R² = {r_squared:.3f}")
        print(f"  截距 (基准价):      {CURRENCY}{coeffs[0]:>10,.0f}")
        print(f"  内存系数:            {CURRENCY}{coeffs[1]:>10,.0f} / GB")
        print(f"  英寸系数:            {CURRENCY}{coeffs[2]:>10,.0f} / inch")
        print(f"  重量系数:            {CURRENCY}{coeffs[3]:>10,.0f} / kg")
    except Exception as e:
        print(f"  回归计算失败: {e}")

    # ── 4.1 价格分布直方图 ──
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    ax = axes[0]
    ax.hist(prices_k, bins=40, color="#4A90D9", edgecolor="white", alpha=0.85)
    ax.set_xlabel("价格 (千卢比)")
    ax.set_ylabel("数量")
    ax.set_title(f"价格分布直方图 (离群值: {len(outlier_idx)}条)")

    ax = axes[1]
    ax.hist(prices_k, bins=40, color="#4A90D9", edgecolor="white", alpha=0.85, cumulative=True)
    ax.set_xlabel("价格 (千卢比)")
    ax.set_ylabel("累计数量")
    ax.set_title("价格累计分布图")

    fig.tight_layout()
    fig.savefig(out_dir / "01_价格分布.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [1/15] 价格分布图")

    # ── 4.2 各品牌均价条形图 ──
    brand_avg = [(b, sum(ps) / len(ps), len(ps)) for b, ps in brands.items()]
    brand_avg.sort(key=lambda x: x[1], reverse=True)
    top_brands = brand_avg[:12]
    names = [x[0] for x in top_brands]
    avgs = [x[1] for x in top_brands]
    counts = [x[2] for x in top_brands]

    fig, ax = plt.subplots(figsize=(12, 6))
    bar_colors = ["#E63946" if i < 3 else "#457B9D" for i in range(len(names))]
    bars = ax.bar(names, [v / 1000 for v in avgs], color=bar_colors, edgecolor="white")
    for bar, cnt in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"n={cnt}", ha="center", va="bottom", fontsize=8, color="#555555")
    ax.set_ylabel("均价 (千卢比)")
    ax.set_title("各品牌均价对比 (Top 12)")
    ax.yaxis.set_major_formatter(rupee_fmt)
    fig.tight_layout()
    fig.savefig(out_dir / "02_各品牌均价.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [2/15] 各品牌均价图")

    # ── 4.3 各类型均价条形图 ──
    type_avg = [(t, sum(ps) / len(ps), len(ps)) for t, ps in types.items()]
    type_avg.sort(key=lambda x: x[1], reverse=True)
    t_labels = [type_names_cn.get(x[0], x[0]) for x in type_avg]
    t_avgs = [x[1] for x in type_avg]
    t_counts = [x[2] for x in type_avg]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(t_labels, [v / 1000 for v in t_avgs], color="#2A9D8F", edgecolor="white")
    for bar, cnt in zip(bars, t_counts):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"n={cnt}", va="center", fontsize=9, color="#333333")
    ax.set_xlabel("均价 (千卢比)")
    ax.set_title("各类型笔记本均价对比")
    ax.xaxis.set_major_formatter(rupee_fmt)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(out_dir / "03_各类型均价.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [3/15] 各类型均价图")

    # ── 4.4 内存 vs 价格箱线图 ──
    ram_order = sorted(ram_groups.keys())
    ram_data = [[p / 1000 for p in ram_groups[r]] for r in ram_order]
    ram_labels = [f"{r}GB\n(n={len(ram_groups[r])})" for r in ram_order]

    fig, ax = plt.subplots(figsize=(12, 6))
    bp = ax.boxplot(ram_data, patch_artist=True,
                    medianprops={"color": "#E63946", "linewidth": 2})
    ax.set_xticklabels(ram_labels)
    for patch in bp["boxes"]:
        patch.set_facecolor("#A8DADC")
        patch.set_alpha(0.85)
    ax.set_ylabel("价格 (千卢比)")
    ax.set_title("不同内存容量的价格分布")
    ax.yaxis.set_major_formatter(rupee_fmt)
    fig.tight_layout()
    fig.savefig(out_dir / "04_内存与价格箱线图.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [4/15] 内存与价格箱线图")

    # ── 4.5 存储类型分析 ──
    storage_labels = list(storage_stats.keys())
    storage_counts_st = [len(storage_stats.get(k, [])) for k in storage_labels]
    storage_prices = [sum(v) / len(v) / 1000 if v else 0 for v in storage_stats.values()]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    colors_st = ["#457B9D", "#E63946", "#F4A261", "#2A9D8F", "#9B5DE5", "#F15BB5"]

    ax = axes[0]
    wedges, texts, autotexts = ax.pie(storage_counts_st, labels=storage_labels, autopct="%1.1f%%",
                                       colors=colors_st[:len(storage_labels)], startangle=90, pctdistance=0.6)
    for at in autotexts:
        at.set_fontsize(10)
    ax.set_title("存储类型分布")

    ax = axes[1]
    # 只对比有明确价格的类型（SSD vs HDD vs Flash）
    bar_labels = [f"{l}\n(n={c})" for l, c in zip(storage_labels, storage_counts_st)]
    bars = ax.bar(bar_labels, storage_prices, color=colors_st[:len(storage_labels)], edgecolor="white")
    for bar, v in zip(bars, storage_prices):
        if v > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    f"{CHART_CURRENCY}{v:.0f}k", ha="center", fontsize=10)
    ax.set_ylabel("均价 (千卢比)")
    ax.set_title("各存储类型均价对比")
    ax.yaxis.set_major_formatter(rupee_fmt)
    fig.tight_layout()
    fig.savefig(out_dir / "05_存储类型分析.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [5/15] 存储类型分析图")

    # ── 4.6 屏幕尺寸 vs 价格散点图 ──
    fig, ax = plt.subplots(figsize=(10, 6))
    # 正常点
    normal_x = [d["inches"] for i, d in enumerate(parsed) if i not in set(outlier_idx)]
    normal_y = [d["price"] / 1000 for i, d in enumerate(parsed) if i not in set(outlier_idx)]
    ax.scatter(normal_x, normal_y, alpha=0.4, c="#457B9D", edgecolors="white", s=30, label="正常值")
    # 离群值高亮
    if outlier_idx:
        out_x = [parsed[i]["inches"] for i in outlier_idx]
        out_y = [parsed[i]["price"] / 1000 for i in outlier_idx]
        ax.scatter(out_x, out_y, alpha=0.8, c="#E63946", edgecolors="#333333",
                   s=50, marker="X", label=f"离群值 ({len(outlier_idx)}条)")
    ax.set_xlabel("屏幕尺寸 (英寸)")
    ax.set_ylabel("价格 (千卢比)")
    ax.set_title("屏幕尺寸与价格关系 (离群值已标注)")
    ax.legend(fontsize=9)
    ax.yaxis.set_major_formatter(rupee_fmt)
    fig.tight_layout()
    fig.savefig(out_dir / "06_屏幕尺寸与价格.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [6/15] 屏幕尺寸与价格散点图")

    # ── 4.7 操作系统分布饼图 ──
    os_items = sorted(os_groups.items(), key=lambda x: len(x[1]), reverse=True)
    os_labels = [f"{o} ({len(ps)}台)" for o, ps in os_items]
    os_counts = [len(ps) for _, ps in os_items]
    os_colors = ["#457B9D", "#E63946", "#F4A261", "#2A9D8F", "#9B5DE5",
                 "#F15BB5", "#00BBF9", "#FEE440", "#6C757D"]

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(os_counts, labels=os_labels, autopct="%1.1f%%",
                                       colors=os_colors[:len(os_labels)], startangle=140,
                                       pctdistance=0.75)
    for at in autotexts:
        at.set_fontsize(8)
    ax.set_title("操作系统分布")
    fig.tight_layout()
    fig.savefig(out_dir / "07_操作系统分布.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [7/15] 操作系统分布图")

    # ── 4.8 重量与价格散点图 (分品牌着色) ──
    major_brands = {
        "Apple": "#E63946", "Dell": "#457B9D", "Lenovo": "#F4A261",
        "HP": "#2A9D8F", "Asus": "#9B5DE5", "Acer": "#F15BB5",
        "MSI": "#00BBF9", "Razer": "#FB8500",
    }
    other_color = "#CCCCCC"

    fig, ax = plt.subplots(figsize=(10, 6))
    outlier_set = set(outlier_idx)
    for brand in sorted(set(d["company"] for d in parsed)):
        subset_w = []
        subset_p = []
        subset_w_out = []
        subset_p_out = []
        for i, d in enumerate(parsed):
            if d["company"] != brand:
                continue
            if i in outlier_set:
                subset_w_out.append(d["weight"])
                subset_p_out.append(d["price"] / 1000)
            else:
                subset_w.append(d["weight"])
                subset_p.append(d["price"] / 1000)
        c = major_brands.get(brand, other_color)
        alpha = 0.7 if brand in major_brands else 0.2
        z = 5 if brand in major_brands else 2
        if subset_w:
            ax.scatter(subset_w, subset_p, c=c, alpha=alpha, s=20, zorder=z,
                       label=brand if brand in major_brands else "")
        if subset_w_out:
            ax.scatter(subset_w_out, subset_p_out, c=c, alpha=1.0, s=50, zorder=z + 1,
                       edgecolors="#333333", linewidths=0.8, marker="X")

    ax.set_xlabel("重量 (kg)")
    ax.set_ylabel("价格 (千卢比)")
    ax.set_title("重量与价格关系 (按品牌着色, X=离群值)")
    ax.legend(markerscale=1.5, fontsize=8, loc="upper right")
    ax.yaxis.set_major_formatter(rupee_fmt)
    fig.tight_layout()
    fig.savefig(out_dir / "08_重量与价格_分品牌.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [8/15] 重量与价格散点图")

    # ── 4.9 内存 × 存储类型 热力图 ──
    ram_storage = defaultdict(lambda: defaultdict(list))
    for d in parsed:
        st = d["storage_info"]["type"]
        ram_storage[d["ram"]][st].append(d["price"])

    ram_list = sorted(ram_storage.keys())
    s_types = list(storage_stats.keys())
    heatmap = np.zeros((len(ram_list), len(s_types)))
    heatmap_counts = np.zeros((len(ram_list), len(s_types)), dtype=int)

    for i, ram in enumerate(ram_list):
        for j, st in enumerate(s_types):
            ps = ram_storage[ram].get(st, [])
            if ps:
                heatmap[i][j] = sum(ps) / len(ps) / 1000
                heatmap_counts[i][j] = len(ps)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    masked = np.ma.masked_where(heatmap_counts == 0, heatmap)
    im = ax.imshow(masked, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(s_types)))
    ax.set_xticklabels(s_types, fontsize=8)
    ax.set_yticks(range(len(ram_list)))
    ax.set_yticklabels([f"{r}GB" for r in ram_list])
    for i in range(len(ram_list)):
        for j in range(len(s_types)):
            if heatmap_counts[i, j] > 0:
                txt = f"{CHART_CURRENCY}{heatmap[i, j]:.0f}k\nn={heatmap_counts[i, j]}"
                ax.text(j, i, txt, ha="center", va="center", fontsize=7,
                        color="white" if heatmap[i, j] > 60 else "#333333")
    ax.set_title(f"均价热力图: 内存 × 存储类型 ({CURRENCY})")
    fig.colorbar(im, ax=ax, label="千卢比")

    ax = axes[1]
    im2 = ax.imshow(np.ma.masked_where(heatmap_counts == 0, heatmap_counts),
                    cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(s_types)))
    ax.set_xticklabels(s_types, fontsize=8)
    ax.set_yticks(range(len(ram_list)))
    ax.set_yticklabels([f"{r}GB" for r in ram_list])
    for i in range(len(ram_list)):
        for j in range(len(s_types)):
            if heatmap_counts[i, j] > 0:
                ax.text(j, i, str(heatmap_counts[i, j]), ha="center", va="center", fontsize=9)
    ax.set_title("样本数量: 内存 × 存储类型")
    fig.colorbar(im2, ax=ax, label="数量")

    fig.tight_layout()
    fig.savefig(out_dir / "09_内存与存储热力图.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [9/15] 内存与存储热力图")

    # ── 4.10 CPU 品牌饼图 ──
    if cpu_brands_valid:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        ax = axes[0]
        cb_labels = list(cpu_brands_valid.keys())
        cb_counts = [cpu_brands_valid[k] for k in cb_labels]
        cb_colors = ["#457B9D", "#E63946", "#F4A261"]
        ax.pie(cb_counts, labels=cb_labels, autopct="%1.1f%%",
               colors=cb_colors[:len(cb_labels)], startangle=90, pctdistance=0.6)
        ax.set_title("CPU 品牌分布")

        ax = axes[1]
        cb_avgs = [sum(cpu_brands[k]) / len(cpu_brands[k]) / 1000 for k in cb_labels]
        bars = ax.bar(cb_labels, cb_avgs, color=cb_colors[:len(cb_labels)], edgecolor="white")
        for bar, v, k in zip(bars, cb_avgs, cb_labels):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    f"{CHART_CURRENCY}{v:.0f}k\n({len(cpu_brands[k])}台)", ha="center", fontsize=9)
        ax.set_ylabel("均价 (千卢比)")
        ax.set_title("CPU 品牌均价对比")
        ax.yaxis.set_major_formatter(rupee_fmt)
        fig.tight_layout()
        fig.savefig(out_dir / "10_cpu_brand_pie.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
    print("  [10/15] CPU 品牌分析图")

    # ── 4.11 CPU 系列均价条形图 ──
    cpu_series_top = [(s, sum(ps) / len(ps), len(ps))
                      for s, ps in cpu_series.items() if len(ps) >= 10]
    cpu_series_top.sort(key=lambda x: x[1], reverse=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    cs_labels = [x[0] for x in cpu_series_top]
    cs_avgs = [x[1] / 1000 for x in cpu_series_top]
    cs_counts = [x[2] for x in cpu_series_top]
    bars = ax.barh(cs_labels, cs_avgs, color="#457B9D", edgecolor="white")
    for bar, cnt in zip(bars, cs_counts):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"n={cnt}", va="center", fontsize=9, color="#333333")
    ax.set_xlabel("均价 (千卢比)")
    ax.set_title("CPU 系列均价对比 (数量>=10)")
    ax.xaxis.set_major_formatter(rupee_fmt)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(out_dir / "11_cpu_series_price.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [11/15] CPU 系列均价图")

    # ── 4.12 GPU 品牌饼图 ──
    gpu_brands_valid = {b: len(ps) for b, ps in gpu_brands.items() if b != "其他"}
    if gpu_brands_valid:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        ax = axes[0]
        gb_labels = list(gpu_brands_valid.keys())
        gb_counts = [gpu_brands_valid[k] for k in gb_labels]
        gb_colors = ["#2A9D8F", "#E63946", "#457B9D", "#F4A261"]
        ax.pie(gb_counts, labels=gb_labels, autopct="%1.1f%%",
               colors=gb_colors[:len(gb_labels)], startangle=90, pctdistance=0.6)
        ax.set_title("GPU 品牌分布")

        ax = axes[1]
        gb_avgs = [sum(gpu_brands[k]) / len(gpu_brands[k]) / 1000 for k in gb_labels]
        bars = ax.bar(gb_labels, gb_avgs, color=gb_colors[:len(gb_labels)], edgecolor="white")
        for bar, v, k in zip(bars, gb_avgs, gb_labels):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    f"{CHART_CURRENCY}{v:.0f}k", ha="center", fontsize=10)
        ax.set_ylabel("均价 (千卢比)")
        ax.set_title("GPU 品牌均价对比")
        ax.yaxis.set_major_formatter(rupee_fmt)
        fig.tight_layout()
        fig.savefig(out_dir / "12_gpu_brand_pie.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
    print("  [12/15] GPU 品牌分析图")

    # ── 4.13 集成 vs 独立显卡箱线图 ──
    if "集成" in gpu_types and "独立" in gpu_types:
        fig, ax = plt.subplots(figsize=(8, 6))
        gpu_type_data = [[p / 1000 for p in gpu_types["集成"]],
                         [p / 1000 for p in gpu_types["独立"]]]
        gpu_type_labels = [f"集成显卡\n(n={len(gpu_types['集成'])})",
                           f"独立显卡\n(n={len(gpu_types['独立'])})"]
        bp = ax.boxplot(gpu_type_data, patch_artist=True,
                        medianprops={"color": "#E63946", "linewidth": 2})
        ax.set_xticklabels(gpu_type_labels)
        for patch, color in zip(bp["boxes"], ["#457B9D", "#2A9D8F"]):
            patch.set_facecolor(color)
            patch.set_alpha(0.85)
        ax.set_ylabel("价格 (千卢比)")
        ax.set_title("集成显卡 vs 独立显卡 价格分布")
        ax.yaxis.set_major_formatter(rupee_fmt)
        fig.tight_layout()
        fig.savefig(out_dir / "13_gpu_type_boxplot.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
    print("  [13/15] 集显 vs 独显箱线图")

    # ── 4.14 相关性热力图 ──
    corr_names = ["价格", "英寸", "内存(GB)", "重量(kg)"]
    corr_data = [prices, inches_vals, ram_vals, weight_vals]
    corr_matrix = np.zeros((4, 4))
    for i in range(4):
        for j in range(4):
            corr_matrix[i, j] = pearson_r(corr_data[i], corr_data[j])

    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(corr_matrix, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(4))
    ax.set_xticklabels(corr_names, fontsize=11)
    ax.set_yticks(range(4))
    ax.set_yticklabels(corr_names, fontsize=11)
    for i in range(4):
        for j in range(4):
            color = "white" if abs(corr_matrix[i, j]) > 0.5 else "#333333"
            ax.text(j, i, f"{corr_matrix[i, j]:.3f}", ha="center", va="center",
                    fontsize=12, fontweight="bold", color=color)
    ax.set_title("特征相关性热力图 (Pearson)")
    fig.colorbar(im, ax=ax, label="相关系数")
    fig.tight_layout()
    fig.savefig(out_dir / "14_correlation_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [14/15] 相关性热力图")

    # ── 4.15 价格 vs 内存 散点+回归线 ──
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(ram_vals, [p / 1000 for p in prices], alpha=0.3,
               c="#457B9D", edgecolors="white", s=30)
    # 回归线
    slope, intercept = np.polyfit(ram_vals, [p / 1000 for p in prices], 1)
    x_line = np.linspace(min(ram_vals), max(ram_vals), 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, color="#E63946", linewidth=2,
            label=f"y = {slope:.1f}x + {intercept:.0f}\nPearson r = {pearson_r(ram_vals, [p/1000 for p in prices]):.3f}")
    ax.set_xlabel("内存 (GB)")
    ax.set_ylabel("价格 (千卢比)")
    ax.set_title("价格 vs 内存 散点图与回归线")
    ax.legend(fontsize=10)
    ax.yaxis.set_major_formatter(rupee_fmt)
    fig.tight_layout()
    fig.savefig(out_dir / "15_price_vs_ram_regression.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [15/15] 价格 vs 内存回归图")

    # ── 完成 ──
    print(f"\n全部图表已保存至: {out_dir.resolve()}/")
    for fname in sorted(out_dir.glob("*.png")):
        print(f"  {fname.name}")
    print(f"\n分析结果 JSON: {result_path.resolve()}")
    print(f"数据说明: 印度市场笔记本电脑, 价格单位={PRICE_UNIT}")
