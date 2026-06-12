# -*- coding: utf-8 -*-
import json
import warnings
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)
matplotlib.use("Agg")
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({
    "font.family": "Microsoft YaHei",
    "font.size": 10,
    "axes.titlesize": 15,
    "axes.labelsize": 11,
    "figure.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.3,
    "axes.unicode_minus": False,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.4,
    "grid.linestyle": "--",
    "grid.linewidth": 0.5,
    "xtick.bottom": False,
    "ytick.left": False,
})

C = {"pos": "#4A90D9", "neg": "#E05561", "green": "#3CB878", "amber": "#F5A623", "purple": "#9B7ED8", "dark": "#434A54", "grey": "#AAB2BD"}

BASE = Path(__file__).resolve().parent
OUT = BASE / "outputs" / "charts"
OUT.mkdir(parents=True, exist_ok=True)
CSV = BASE / "superstore.csv"


def load_data(path):
    df = pd.read_csv(path, parse_dates=["Order Date", "Ship Date"])
    df["Profit Margin"] = df["Profit"] / df["Sales"].replace(0, np.nan)
    df["Year-Month"] = df["Order Date"].dt.to_period("M")
    df["折扣档位"] = pd.cut(
        df["Discount"],
        bins=[-0.01, 0, 0.2, 0.4, float("inf")],
        labels=["无折扣", "低折扣 (1-20%)", "中折扣 (21-40%)", "高折扣 (>40%)"],
    )
    return df


def _analyze(df, col, **extra):
    g = df.groupby(col).agg(
        总利润=("Profit", "sum"),
        总销售额=("Sales", "sum"),
        订单数=("Row ID", "count"),
        平均利润率=("Profit Margin", "mean"),
        **extra,
    )
    g["利润率%"] = g["总利润"] / g["总销售额"] * 100
    return g.sort_values("总利润", ascending=False).round(2)


def analyze_discount(df):
    g = df.groupby("折扣档位", observed=False).agg(
        总利润=("Profit", "sum"),
        订单数=("Row ID", "count"),
        平均利润=("Profit", "mean"),
        平均利润率=("Profit Margin", "mean"),
        亏损订单数=("Profit", lambda x: (x < 0).sum()),
    )
    g["亏损率%"] = g["亏损订单数"] / g["订单数"] * 100
    g["利润率%"] = g["总利润"] / df.groupby("折扣档位", observed=False)["Sales"].sum() * 100
    return g.round(2)


def analyze_top_products(df):
    prod = df.groupby(["Product Name", "Sub-Category"]).agg(
        总利润=("Profit", "sum"), 总销售额=("Sales", "sum"), 订单数=("Row ID", "count"),
    )
    top10 = prod.sort_values("总利润", ascending=False).head(10).round(2)
    bottom10 = prod.sort_values("总利润", ascending=True).head(10).round(2)
    return top10, bottom10


def analyze_monthly(df):
    g = df.groupby("Year-Month").agg(销售额=("Sales", "sum"), 利润=("Profit", "sum")).sort_index()
    g.index = g.index.astype(str)
    g["累计利润"] = g["利润"].cumsum()
    return g.round(2)


def _short(s, n=50):
    return f"{s[:n]}..." if len(s) > n else s


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(OUT / path)
    plt.close(fig)


def _label_barh(ax, fmt="${:,.0f}", offset=2000, fontsize=9):
    for bar in ax.containers[0]:
        w = bar.get_width()
        x = w + offset if w >= 0 else w - offset
        ax.text(x, bar.get_y() + bar.get_height() / 2, fmt.format(w),
                va="center", ha="left" if w >= 0 else "right", fontsize=fontsize, color=C["dark"])


def _label_barv(ax, fmt="${:,.0f}", offset=2000, fontsize=9):
    for bar in ax.containers[0]:
        h = bar.get_height()
        y = h + offset if h >= 0 else h - offset
        ax.text(bar.get_x() + bar.get_width() / 2, y, fmt.format(h),
                ha="center", va="bottom" if h >= 0 else "top", fontsize=fontsize, color=C["dark"])


# ---- 图表 ----

def chart_category(data):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    vals = data["总利润"]
    colors = [C["pos"] if v >= 0 else C["neg"] for v in vals.values]
    ax.barh(list(vals.index), list(vals.values), color=colors, height=0.55)
    _label_barh(ax)
    ax.axvline(0, color=C["grey"], linewidth=0.8)
    ax.set_title("各品类总利润", fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlabel("")
    _save(fig, "01_profit_by_category.png")


def chart_subcategory(data):
    top5 = data["总利润"].head(5)
    bottom5 = data["总利润"].tail(5)
    combined = pd.concat([top5, bottom5])
    fig, ax = plt.subplots(figsize=(10, 5.5))
    colors = [C["pos"] if v >= 0 else C["neg"] for v in combined.values]
    ax.barh(list(combined.index), list(combined.values), color=colors, height=0.55)
    _label_barh(ax, offset=3000)
    ax.axvline(0, color=C["grey"], linewidth=0.8)
    ax.set_title("子品类总利润 (Top 5 & Bottom 5)", fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlabel("")
    _save(fig, "02_profit_by_subcategory.png")


def chart_region(data):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    vals = data["总利润"]
    colors = [C["pos"] if v >= 0 else C["neg"] for v in vals.values]
    ax.barh(list(vals.index), list(vals.values), color=colors, height=0.5)
    _label_barh(ax)
    ax.axvline(0, color=C["grey"], linewidth=0.8)
    ax.set_title("各地区总利润", fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlabel("")
    _save(fig, "03_profit_by_region.png")


def chart_segment(data):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    seg = data["总利润"]
    colors1 = [C["pos"] if v >= 0 else C["neg"] for v in seg.values]
    ax1.bar(list(seg.index), list(seg.values), color=colors1, width=0.45)
    _label_barv(ax1)
    ax1.axhline(0, color=C["grey"], linewidth=0.8)
    ax1.set_title("客户细分总利润", fontweight="bold")
    ax1.set_ylabel("")

    margin = data["利润率%"]
    ax2.bar(list(margin.index), list(margin.values), color=C["green"], width=0.45)
    _label_barv(ax2, fmt="{:.1f}%", offset=0.3)
    ax2.set_title("客户细分利润率", fontweight="bold")
    ax2.set_ylabel("")
    _save(fig, "04_profit_by_segment.png")


def chart_discount_scatter(df):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    pal = {"Furniture": C["neg"], "Office Supplies": C["pos"], "Technology": C["green"]}
    for cat in df["Category"].unique():
        subset = df[df["Category"] == cat]
        ax.scatter(subset["Discount"], subset["Profit"], alpha=0.3, s=10,
                   c=pal.get(cat, C["grey"]), label=cat, edgecolors="none")
    ax.axhline(0, color=C["grey"], linewidth=0.8)
    ax.set_title("折扣 vs 利润 (按品类着色)", fontweight="bold")
    ax.set_xlabel("折扣")
    ax.set_ylabel("利润 (USD)")
    ax.legend(frameon=True, facecolor="white", edgecolor=C["grey"])
    _save(fig, "05_discount_vs_profit.png")


def chart_monthly(data):
    fig, ax1 = plt.subplots(figsize=(14, 5.5))
    ax1.fill_between(range(len(data)), data["销售额"], color=C["pos"], alpha=0.15)
    ax1.plot(data.index, data["销售额"], color=C["pos"], linewidth=1.8, marker="", label="销售额")
    ax1.set_ylabel("销售额 (USD)", color=C["pos"], fontweight="bold")
    ax1.tick_params(axis="y", labelcolor=C["pos"])
    step = max(1, len(data.index) // 12)
    ax1.set_xticks(range(0, len(data.index), step))
    ax1.set_xticklabels([data.index[i] for i in range(0, len(data.index), step)], rotation=45, ha="right")

    ax2 = ax1.twinx()
    ax2.plot(data.index, data["利润"], color=C["neg"], marker="o", linewidth=1.8, markersize=4, label="利润")
    ax2.set_ylabel("利润 (USD)", color=C["neg"], fontweight="bold")
    ax2.tick_params(axis="y", labelcolor=C["neg"])
    ax2.axhline(0, color=C["grey"], linewidth=0.8, linestyle="--")

    ax1.set_title("月度销售额与利润趋势", fontweight="bold")
    _save(fig, "06_monthly_trends.png")


def chart_top_products(top10, bottom10):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    labels_top = [_short(n, 38) for n in top10.index.get_level_values(0)]
    ax1.barh(labels_top, top10["总利润"].values, color=C["pos"], height=0.55)
    _label_barh(ax1, offset=1500)
    ax1.set_title("最盈利产品 Top 10", fontweight="bold")
    ax1.set_xlabel("")
    ax1.invert_yaxis()

    labels_bot = [_short(n, 38) for n in bottom10.index.get_level_values(0)]
    ax2.barh(labels_bot, bottom10["总利润"].values, color=C["neg"], height=0.55)
    _label_barh(ax2, offset=500)
    ax2.set_title("最亏损产品 Top 10", fontweight="bold")
    ax2.set_xlabel("")
    ax2.invert_yaxis()
    _save(fig, "07_top10_products.png")


def chart_heatmap(data, title, path, figsize=(9, 5), fmt=".0f"):
    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(data.values, cmap="RdYlGn", aspect="auto")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data.iloc[i, j]
            color = "white" if abs(val) > np.nanmax(data.values) * 0.5 else C["dark"]
            ax.text(j, i, f"{val:{fmt}}", ha="center", va="center", fontsize=9, color=color)
    ax.set_xticks(range(data.shape[1]))
    ax.set_xticklabels(data.columns, fontsize=10)
    ax.set_yticks(range(data.shape[0]))
    ax.set_yticklabels(data.index, fontsize=10)
    ax.set_title(title, fontweight="bold")
    fig.colorbar(im, ax=ax, label="利润 (USD)", shrink=0.85)
    _save(fig, path)


def chart_profit_margin_box(df):
    fig, ax = plt.subplots(figsize=(9, 5))
    cats = list(df["Category"].unique())
    data = [df[df["Category"] == c]["Profit Margin"].dropna() for c in cats]
    bp = ax.boxplot(data, patch_artist=True, widths=0.45,
                    medianprops={"color": C["dark"], "linewidth": 1.5},
                    whiskerprops={"color": C["grey"]},
                    capprops={"color": C["grey"]},
                    flierprops={"markerfacecolor": C["neg"], "markersize": 4, "alpha": 0.4})
    box_colors = [C["pos"], C["green"], C["neg"]]
    for patch, color in zip(bp["boxes"], box_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_xticklabels(cats, fontsize=11)
    ax.set_title("各品类单笔利润率分布", fontweight="bold")
    ax.set_ylabel("利润率")
    ax.axhline(0, color=C["grey"], linewidth=0.8, linestyle="--")
    _save(fig, "11_profit_margin_boxplot.png")


def chart_correlation(corr):
    fig, ax = plt.subplots(figsize=(7, 5.5))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    for i in range(corr.shape[0]):
        for j in range(corr.shape[1]):
            val = corr.iloc[i, j]
            color = "white" if abs(val) > 0.6 else C["dark"]
            ax.text(j, i, f"{val:.3f}", ha="center", va="center", fontsize=11,
                    fontweight="bold" if abs(val) > 0.5 else "normal", color=color)
    ax.set_xticks(range(corr.shape[1]))
    ax.set_xticklabels(corr.columns, fontsize=11)
    ax.set_yticks(range(corr.shape[0]))
    ax.set_yticklabels(corr.index, fontsize=11)
    ax.set_title("Sales / Profit / Discount / Quantity 相关性", fontweight="bold")
    fig.colorbar(im, ax=ax, label="Pearson r", shrink=0.85).ax.yaxis.label.set_size(10)
    _save(fig, "12_correlation_heatmap.png")


def make_recommendations(subcat, region, seg, discount, monthly, top10_prod, bottom10_prod):
    focus, avoid = [], []

    for name, profit in subcat["总利润"].head(3).items():
        focus.append(f"子品类【{name}】总利润 ${profit:,.0f}，核心盈利来源")
    for name, profit in subcat["总利润"].tail(3).items():
        avoid.append(f"子品类【{name}】总利润 ${profit:,.0f}，持续亏损需复盘")

    best_region = region["总利润"].idxmax()
    focus.append(f"地区【{best_region}】利润最高 (${region.loc[best_region, '总利润']:,.0f})，加大投入")

    best_seg = seg["利润率%"].idxmax()
    focus.append(f"客户群体【{best_seg}】利润率最高 ({seg.loc[best_seg, '利润率%']:.1f}%)，精准营销")

    high_disc_loss = discount.loc["高折扣 (>40%)", "亏损率%"] if "高折扣 (>40%)" in discount.index else 0
    avoid.append(f"高折扣(>40%)订单亏损率 {high_disc_loss:.1f}%，严控高折产品审批")

    for (name, sc), profit in zip(top10_prod.index, top10_prod["总利润"].values):
        focus.append(f"产品【{_short(name)}】({sc})利润 ${profit:,.0f}，明星单品")
    for (name, sc), profit in zip(bottom10_prod.index, bottom10_prod["总利润"].values):
        avoid.append(f"产品【{_short(name)}】({sc})亏损 ${-profit:,.0f}，考虑下架或改定价")

    if monthly.tail(3)["利润"].mean() < 0:
        avoid.append("近期月度利润持续为负，需关注季节性或成本变化")

    return focus, avoid


def main():
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 60)
    print("  Superstore 超市销售数据分析")
    print("=" * 60)

    print("\n[1/4] 加载数据...")
    df = load_data(CSV)
    print(f"  加载完成: {len(df)} 行, {len(df.columns)} 列")
    dups = df["Row ID"].duplicated().sum()
    print(f"  重复 Row ID: {dups}")

    print("\n[2/4] 分析计算...")
    cat = _analyze(df, "Category")
    subcat = _analyze(df, "Sub-Category")
    region = _analyze(df, "Region")
    seg = _analyze(df, "Segment", 客单价=("Sales", "mean"))
    discount = analyze_discount(df)
    top10_prod, bottom10_prod = analyze_top_products(df)
    monthly = analyze_monthly(df)
    cat_seg = df.pivot_table(values="Profit", index="Category", columns="Segment", aggfunc="sum", observed=False).round(2)
    reg_cat = df.pivot_table(values="Profit", index="Region", columns="Category", aggfunc="sum", observed=False).round(2)
    corr = df[["Sales", "Profit", "Discount", "Quantity"]].corr().round(4)

    print("\n[3/4] 生成图表...")
    chart_category(cat)
    chart_subcategory(subcat)
    chart_region(region)
    chart_segment(seg)
    chart_discount_scatter(df)
    chart_monthly(monthly)
    chart_top_products(top10_prod, bottom10_prod)
    chart_heatmap(cat_seg, "Category × Segment 利润交叉", "09_category_segment_heatmap.png")
    chart_heatmap(reg_cat, "Region × Category 利润交叉", "10_region_category_heatmap.png")
    chart_profit_margin_box(df)
    chart_correlation(corr)
    print(f"  11 张图表已保存至 {OUT}")

    print("\n[4/4] 生成报告...\n")
    focus, avoid = make_recommendations(subcat, region, seg, discount, monthly, top10_prod, bottom10_prod)

    # ---- 打印报告 ----
    total_sales = df["Sales"].sum()
    total_profit = df["Profit"].sum()

    print("=" * 60)
    print("  [核心结论]")
    print("=" * 60)
    print(f"\n  【整体数据】")
    print(f"  总销售额: ${total_sales:,.0f}")
    print(f"  总利润:   ${total_profit:,.0f}")
    print(f"  整体利润率: {total_profit/total_sales*100:.1f}%")
    print(f"  亏损订单占比: {(df['Profit']<0).sum()/len(df)*100:.1f}%")

    print(f"\n  【品类利润排名】")
    for idx, row in cat.iterrows():
        print(f"  {idx:18s} | 利润 ${row['总利润']:>12,.0f} | 利润率 {row['利润率%']:>6.1f}% | 订单 {row['订单数']:>5,}")

    print(f"\n  【子品类 Top 5】")
    for idx, row in subcat.head(5).iterrows():
        print(f"  {idx:18s} | 利润 ${row['总利润']:>12,.0f} | 利润率 {row['利润率%']:>6.1f}%")

    print(f"\n  【子品类 Bottom 5（亏损）】")
    for idx, row in subcat.tail(5).iterrows():
        print(f"  {idx:18s} | 利润 ${row['总利润']:>12,.0f} | 利润率 {row['利润率%']:>6.1f}%")

    print(f"\n  【地区利润排名】")
    for idx, row in region.iterrows():
        print(f"  {idx:12s} | 利润 ${row['总利润']:>12,.0f} | 利润率 {row['利润率%']:>6.1f}% | 订单 {row['订单数']:>5,}")

    print(f"\n  【客户细分】")
    for idx, row in seg.iterrows():
        print(f"  {idx:14s} | 利润 ${row['总利润']:>10,.0f} | 利润率 {row['利润率%']:>5.1f}% | 客单价 ${row['客单价']:>8,.0f}")

    print(f"\n  【折扣影响】")
    for idx, row in discount.iterrows():
        print(f"  {idx:18s} | 利润 ${row['总利润']:>10,.0f} | 亏损率 {row['亏损率%']:>5.1f}% | 订单 {row['订单数']:>5,}")

    print(f"\n  【Top 10 最盈利产品】")
    for i, ((name, sc), row) in enumerate(zip(top10_prod.index, top10_prod.itertuples()), 1):
        print(f"  {i:2}. [{sc}] {_short(name, 60)}")
        print(f"      利润 ${row.总利润:,.0f} | 销售额 ${row.总销售额:,.0f} | 订单 {row.订单数:,}")

    print(f"\n  【Top 10 最亏损产品】")
    for i, ((name, sc), row) in enumerate(zip(bottom10_prod.index, bottom10_prod.itertuples()), 1):
        print(f"  {i:2}. [{sc}] {_short(name, 60)}")
        print(f"      利润 ${row.总利润:,.0f} | 销售额 ${row.总销售额:,.0f} | 订单 {row.订单数:,}")

    print(f"\n  【数值相关性】")
    for i in range(len(corr.columns)):
        row_str = "  ".join(f"{corr.columns[j]}: {corr.iloc[i, j]:+.3f}" for j in range(i+1, len(corr.columns)))
        print(f"  {corr.columns[i]} → {row_str}")

    print(f"\n{'='*60}")
    print("  >> 建议关注")
    print("=" * 60)
    for item in focus:
        print(f"  + {item}")

    print(f"\n{'='*60}")
    print("  !! 建议避免 / 重点关注风险")
    print("=" * 60)
    for item in avoid:
        print(f"  - {item}")

    results = {
        "整体": {
            "总销售额": round(total_sales, 2),
            "总利润": round(total_profit, 2),
            "整体利润率%": round(total_profit/total_sales*100, 2),
            "亏损订单占比%": round((df["Profit"]<0).sum()/len(df)*100, 2),
        },
        "品类利润排名": cat["总利润"].to_dict(),
        "子品类Top5": {k: round(v, 2) for k, v in subcat["总利润"].head(5).to_dict().items()},
        "子品类Bottom5": {k: round(v, 2) for k, v in subcat["总利润"].tail(5).to_dict().items()},
        "地区利润排名": region["总利润"].to_dict(),
        "客户细分利润率%": seg["利润率%"].to_dict(),
        "折扣档位亏损率%": discount["亏损率%"].to_dict(),
        "关注建议": focus,
        "风险提示": avoid,
    }
    with open(OUT / "analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n结构化结果已保存至 {OUT / 'analysis_results.json'}")
    print("\n分析完成。")


if __name__ == "__main__":
    main()
