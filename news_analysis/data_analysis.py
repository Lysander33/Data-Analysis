# -*- coding: utf-8 -*-
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ── 编码配置 ──
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "news.csv"
OUT = SCRIPT_DIR / "outputs" / "charts"

matplotlib.use("Agg")
plt.style.use("seaborn-v0_8-whitegrid")

C = {
    "fake": "#E05561", "real": "#4A90D9", "green": "#3CB878",
    "amber": "#F5A623", "purple": "#9B7ED8", "dark": "#434A54", "grey": "#AAB2BD",
}

STOPWORDS = {
    "the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or", "but",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "shall", "should", "may", "might",
    "must", "can", "could", "it", "its", "he", "she", "they", "them", "their",
    "his", "her", "we", "us", "our", "you", "your", "i", "me", "my", "mine",
    "not", "no", "nor", "so", "as", "if", "than", "then", "also", "very",
    "too", "just", "now", "here", "there", "when", "where", "why", "how",
    "all", "each", "every", "both", "few", "more", "most", "other", "some",
    "such", "only", "own", "same", "into", "up", "out", "about", "over",
    "under", "again", "further", "once", "during", "before", "after", "above",
    "below", "between", "through", "because", "until", "while", "with", "from",
    "this", "that", "these", "those", "which", "who", "whom", "whose", "what",
    "by", "been", "hadn", "hasn", "haven", "isn", "mightn", "mustn", "needn",
    "shan", "shouldn", "wasn", "weren", "won", "wouldn", "don", "didn", "doesn",
    "aren", "couldn", "ain", "ll", "ve", "re", "m", "s", "t", "d",
}

EMOTIONAL_WORDS = {
    "breaking", "shocking", "shock", "scandal", "scandalous", "exposed",
    "truth", "conspiracy", "secret", "leaked", "bombshell", "hoax",
    "unbelievable", "incredible", "outrageous", "outrage", "horrifying",
    "terrifying", "disgusting", "sickening", "explosive", "devastating",
    "catastrophic", "tragic", "amazing", "mind-blowing", "stunning",
    "sensational", "horrific", "disgraceful", "disgusted", "furious",
    "enraged", "panic", "chaos", "crisis", "emergency", "urgent",
    "warning", "alert", "dangerous", "deadly", "killer", "massacre",
    "slaughter", "atrocity", "monstrous", "evil", "vile", "appalling",
    "outcry", "uproar", "fury", "rage",
}


def detect_chinese_font():
    candidates = [
        "Microsoft YaHei", "SimHei", "Noto Sans CJK SC",
        "WenQuanYi Micro Hei", "Noto Sans SC", "sans-serif",
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    for font_name in candidates:
        try:
            plt.rcParams["font.family"] = font_name
            fig = plt.figure(figsize=(1, 1), dpi=10)
            fig.text(0.5, 0.5, "中文", fontsize=8)
            test_path = OUT / "_font_test.png"
            fig.savefig(str(test_path), dpi=10)
            plt.close(fig)
            if test_path.exists():
                test_path.unlink()
            return font_name
        except Exception:
            continue
    return "sans-serif"


def welch_ttest(a, b):
    n1, n2 = len(a), len(b)
    m1, m2 = sum(a) / n1, sum(b) / n2
    v1 = sum((x - m1) ** 2 for x in a) / (n1 - 1)
    v2 = sum((x - m2) ** 2 for x in b) / (n2 - 1)
    se = math.sqrt(v1 / n1 + v2 / n2)
    if se == 0:
        return {"t_stat": 0, "p_value": 1.0, "df": float("inf"), "mean0": m1, "mean1": m2}
    t_stat = (m1 - m2) / se
    df_num = (v1 / n1 + v2 / n2) ** 2
    df_den = (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    df = df_num / df_den
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))
    return {"t_stat": t_stat, "p_value": p_value, "df": df, "mean0": m1, "mean1": m2}


def cohens_d(a, b):
    n1, n2 = len(a), len(b)
    m1, m2 = sum(a) / n1, sum(b) / n2
    v1 = sum((x - m1) ** 2 for x in a) / (n1 - 1)
    v2 = sum((x - m2) ** 2 for x in b) / (n2 - 1)
    pooled = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    return (m1 - m2) / pooled if pooled > 0 else 0.0


def chi_square(a, b, c, d):
    """2x2 contingency table: [[a,b],[c,d]] — a=fake+has, b=fake+!has, c=real+has, d=real+!has"""
    n = a + b + c + d
    if n == 0:
        return {"chi2": 0, "p_value": 1.0}
    denom = (a + b) * (c + d) * (a + c) * (b + d)
    if denom == 0:
        return {"chi2": 0, "p_value": 1.0}
    chi2 = float(n) * (float(a) * float(d) - float(b) * float(c)) ** 2 / float(denom)
    p_value = 1 - (1 + math.erf(math.sqrt(chi2 / 2))) / 2 if chi2 > 0 else 1.0
    return {"chi2": chi2, "p_value": p_value, "a": a, "b": b, "c": c, "d": d, "n": n}


def _save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _sig(p):
    if p < 0.001: return "***"
    if p < 0.01: return "**"
    if p < 0.05: return "*"
    return "n.s."


def extract_word_features(text):
    words = [w for w in text.split() if w.strip()]
    n = len(words)
    if n == 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    sw_cnt = sum(1 for w in words if w.lower() in STOPWORDS)
    em_cnt = sum(1 for w in words if w.lower() in EMOTIONAL_WORDS)
    unique = len(set(w.lower() for w in words))
    avg_len = sum(len(w) for w in words) / n
    caps = sum(1 for w in words if w and w[0].isupper())
    return (
        sw_cnt / n * 100, em_cnt / n * 100, unique / n * 100,
        avg_len, caps / n * 100,
    )


# ══════════════════════════════════════════════════════════════════
# ── 主程序 ──
# ══════════════════════════════════════════════════════════════════

def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # ── 1. 数据加载 ──
    print("=" * 60)
    print("  假新闻 vs 真新闻 文本特征分析")
    print("=" * 60)
    print("\n[1/5] 加载数据...")
    df = pd.read_csv(CSV)
    print(f"  加载完成: {len(df):,} 行, {len(df.columns)} 列")
    print(f"  假新闻 (label=0): {(df['label']==0).sum():,}")
    print(f"  真新闻 (label=1): {(df['label']==1).sum():,}")

    # ── 2. 特征提取 ──
    print("\n[2/5] 提取文本特征...")

    df["text_len"] = df["text"].str.len()
    df["word_count"] = df["text"].str.split(r"\s+").str.len()
    df["sentence_count"] = df["text"].str.split(r"[.!?]+").str.len()
    df["words_per_sentence"] = df["word_count"] / df["sentence_count"].replace(0, 1)
    df["exclamation_ratio"] = df["text"].str.count("!") / df["word_count"] * 100
    df["question_ratio"] = df["text"].str.count(r"\?") / df["word_count"] * 100
    df["quote_ratio"] = (df["text"].str.count('"') + df["text"].str.count("'")) / df["word_count"] * 100
    df["allcaps_ratio"] = df["text"].str.findall(r"\b[A-Z]{3,}\b").str.len() / df["word_count"] * 100
    df["number_ratio"] = df["text"].str.count(r"\d") / df["text_len"] * 100

    df["has_reuters"] = df["text"].str.contains(r"\bReuters\b", case=False, na=False)
    df["has_ap"] = df["text"].str.contains(r"\bAP\b", case=False, na=False)
    df["has_video_ref"] = df["text"].str.contains(
        r"\b(?:VIDEO|WATCH|PHOTO|IMAGE)\b", case=False, na=False
    )
    df["has_url"] = df["text"].str.contains(r"https?://", case=False, na=False)
    df["has_breaking"] = df["text"].str.lower().str.contains(r"\bbreaking\b", na=False)

    print("  提取词级特征...")
    word_features = df["text"].apply(lambda t: pd.Series(extract_word_features(t)))
    word_features.columns = ["stopword_ratio", "emotional_ratio", "unique_ratio", "avg_word_len", "capitalized_ratio"]
    df = pd.concat([df, word_features], axis=1)

    print(f"  共提取 {len([c for c in df.columns if c not in ('text','label')])} 个特征")

    # ── 3. 统计分析 ──
    print("\n[3/5] 统计检验...")

    fake = df[df["label"] == 0]
    real = df[df["label"] == 1]

    continuous_features = [
        ("text_len", "文本长度(字符)"),
        ("word_count", "词数"),
        ("sentence_count", "句数"),
        ("words_per_sentence", "每句词数"),
        ("exclamation_ratio", "感叹号密度(%)"),
        ("question_ratio", "问号密度(%)"),
        ("quote_ratio", "引号密度(%)"),
        ("allcaps_ratio", "全大写词比例(%)"),
        ("number_ratio", "数字占比(%)"),
        ("stopword_ratio", "停用词比例(%)"),
        ("emotional_ratio", "情感词比例(%)"),
        ("unique_ratio", "独特词比例(%)"),
        ("avg_word_len", "平均词长"),
        ("capitalized_ratio", "首字母大写比例(%)"),
    ]

    bool_features = [
        ("has_reuters", "含Reuters引用"),
        ("has_ap", '含"AP"'),
        ("has_video_ref", "含视频/图片引用"),
        ("has_url", "含URL链接"),
        ("has_breaking", '含"breaking"'),
    ]

    t_results = []
    for col, name in continuous_features:
        r = welch_ttest(fake[col].tolist(), real[col].tolist())
        d = cohens_d(fake[col].tolist(), real[col].tolist())
        t_results.append({
            "feature": name, "col": col,
            "fake_mean": r["mean0"], "real_mean": r["mean1"],
            "t_stat": r["t_stat"], "p_value": r["p_value"],
            "cohens_d": d, "sig": _sig(r["p_value"]),
        })

    chi_results = []
    for col, name in bool_features:
        a = (fake[col] == True).sum()
        b = (fake[col] == False).sum()
        c2 = (real[col] == True).sum()
        d2 = (real[col] == False).sum()
        r = chi_square(a, b, c2, d2)
        chi_results.append({
            "feature": name, "col": col,
            "fake_pct": a / len(fake) * 100,
            "real_pct": c2 / len(real) * 100,
            "chi2": r["chi2"], "p_value": r["p_value"],
        })

    # 相关系数矩阵
    corr_cols = [c for c, _ in continuous_features]
    corr_matrix = df[corr_cols].corr().round(3)

    # Bigrams
    print("  提取Top Bigrams...")
    f_bigrams = Counter()
    r_bigrams = Counter()
    for _, row in fake["text"].sample(min(10000, len(fake)), random_state=42).items():
        words = [w.lower() for w in row.split() if len(w) > 1]
        for i in range(len(words) - 1):
            bg = f"{words[i]} {words[i+1]}"
            if not any(c in bg for c in ".,!?;:\"'()[]{}"):
                f_bigrams[bg] += 1
    for _, row in real["text"].sample(min(10000, len(real)), random_state=42).items():
        words = [w.lower() for w in row.split() if len(w) > 1]
        for i in range(len(words) - 1):
            bg = f"{words[i]} {words[i+1]}"
            if not any(c in bg for c in ".,!?;:\"'()[]{}"):
                r_bigrams[bg] += 1

    # ── 4. 终端报告 ──
    print("\n" + "=" * 60)
    print("  [分析报告]")
    print("=" * 60)

    print(f"\n  【数据概况】")
    print(f"  总样本数: {len(df):,}")
    print(f"  假新闻 (label=0): {len(fake):,} ({len(fake)/len(df)*100:.1f}%)")
    print(f"  真新闻 (label=1): {len(real):,} ({len(real)/len(df)*100:.1f}%)")
    print(f"  文本长度: 均值 {df['text_len'].mean():.0f}, 中位数 {df['text_len'].median():.0f}, "
          f"范围 [{df['text_len'].min()}, {df['text_len'].max()}]")

    print(f"\n  【文本长度与结构】")
    for r in t_results:
        if r["col"] in ("text_len", "word_count", "sentence_count", "words_per_sentence"):
            direction = "假 > 真" if r["fake_mean"] > r["real_mean"] else "真 > 假"
            print(f"  {r['feature']:14s}  假={r['fake_mean']:>8.1f}  真={r['real_mean']:>8.1f}  "
                  f"d={r['cohens_d']:+.2f}  {r['sig']:4s}  ({direction})")

    print(f"\n  【标点与强调特征】")
    for r in t_results:
        if r["col"] in ("exclamation_ratio", "question_ratio", "quote_ratio",
                         "allcaps_ratio", "number_ratio"):
            direction = "假 > 真" if r["fake_mean"] > r["real_mean"] else "真 > 假"
            print(f"  {r['feature']:14s}  假={r['fake_mean']:>8.2f}  真={r['real_mean']:>8.2f}  "
                  f"d={r['cohens_d']:+.2f}  {r['sig']:4s}  ({direction})")

    print(f"\n  【词汇特征】")
    for r in t_results:
        if r["col"] in ("stopword_ratio", "emotional_ratio", "unique_ratio",
                         "avg_word_len", "capitalized_ratio"):
            direction = "假 > 真" if r["fake_mean"] > r["real_mean"] else "真 > 假"
            print(f"  {r['feature']:14s}  假={r['fake_mean']:>8.2f}  真={r['real_mean']:>8.2f}  "
                  f"d={r['cohens_d']:+.2f}  {r['sig']:4s}  ({direction})")

    print(f"\n  【来源引用特征 (卡方检验)】")
    for r in chi_results:
        dir_str = "假 > 真" if r["fake_pct"] > r["real_pct"] else "真 > 假"
        p = r["p_value"]
        sig = _sig(p)
        print(f"  {r['feature']:16s}  假={r['fake_pct']:>6.2f}%  真={r['real_pct']:>6.2f}%  "
              f"χ²={r['chi2']:>10.1f}  {sig:4s}  ({dir_str})")

    print(f"\n  【效应量排名 (|Cohen's d|)】")
    t_results_sorted = sorted(t_results, key=lambda x: abs(x["cohens_d"]), reverse=True)
    for i, r in enumerate(t_results_sorted, 1):
        direction = "假 > 真" if r["fake_mean"] > r["real_mean"] else "真 > 假"
        bar = "█" * min(30, int(abs(r["cohens_d"]) * 20))
        print(f"  {i:2}. d={r['cohens_d']:+.3f}  {r['feature']:14s}  {bar}  ({direction})")

    print(f"\n  【最具区分力 Bigrams】")
    # 计算 fake/real 频率比
    bg_ratio = {}
    for bg in set(f_bigrams) | set(r_bigrams):
        fc = f_bigrams.get(bg, 1)  # +1 平滑
        rc = r_bigrams.get(bg, 1)
        if fc + rc > 20:  # 过滤低频
            bg_ratio[bg] = fc / rc
    top_fake_bg = sorted(bg_ratio.items(), key=lambda x: x[1], reverse=True)[:10]
    top_real_bg = sorted(bg_ratio.items(), key=lambda x: x[1])[:10]
    print("  假新闻高频 (Fake/Real > 5):")
    for bg, ratio in top_fake_bg:
        print(f"    {bg:35s}  比={ratio:.1f}  (假{f_bigrams.get(bg,0):,} / 真{r_bigrams.get(bg,0):,})")
    print("  真新闻高频 (Real/Fake > 5):")
    for bg, ratio in top_real_bg:
        if ratio < 0.2:
            inv = 1/ratio if ratio > 0 else 999
            print(f"    {bg:35s}  比=1:{inv:.0f}  (假{f_bigrams.get(bg,0):,} / 真{r_bigrams.get(bg,0):,})")

    # ── 5. JSON 持久化 ──
    print(f"\n[4/5] 保存分析结果...")
    results = {
        "样本概况": {"总数": len(df), "假新闻": int(len(fake)), "真新闻": int(len(real))},
        "t检验结果": [{k: float(v) if isinstance(v, (np.floating, float, np.integer)) and k != 'feature' and k != 'col' and k != 'sig' else v
                    for k, v in r.items()} for r in t_results],
        "卡方检验结果": [{k: float(v) if isinstance(v, (np.floating, float, np.integer)) and k != 'feature' and k != 'col' else v
                       for k, v in r.items()} for r in chi_results],
    }
    with open(OUT / "analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"  已保存至 {OUT / 'analysis_results.json'}")

    # ══════════════════════════════════════════════════════════════
    # ── 6. 图表生成 ──
    # ══════════════════════════════════════════════════════════════
    print(f"\n[5/5] 生成图表...")

    font = detect_chinese_font()
    print(f"  字体: {font}")
    plt.rcParams.update({
        "font.family": font, "font.size": 10, "axes.titlesize": 14,
        "axes.labelsize": 11, "figure.dpi": 150, "axes.unicode_minus": False,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.4, "grid.linestyle": "--", "grid.linewidth": 0.5,
        "xtick.bottom": False, "ytick.left": False,
    })

    fake_vals = fake["text_len"].values
    real_vals = real["text_len"].values

    # ── 01 文本长度分布 ──
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(fake_vals, bins=50, alpha=0.6, color=C["fake"], label=f"假新闻 (n={len(fake):,})", edgecolor="white")
    ax.hist(real_vals, bins=50, alpha=0.6, color=C["real"], label=f"真新闻 (n={len(real):,})", edgecolor="white")
    ax.set_xlabel("文本长度 (字符)")
    ax.set_ylabel("数量")
    ax.set_title("文本长度分布对比")
    ax.legend()
    _save(fig, "01_text_length_hist.png")
    print("  [1/10] 文本长度分布图")

    # ── 02 词数/句数/每句词数/平均词长 2x2 箱线图 ──
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    box_opts = {"patch_artist": True, "widths": 0.5, "medianprops": {"color": C["dark"], "linewidth": 1.5}}
    box_data = [
        (axes[0, 0], "word_count", "词数"),
        (axes[0, 1], "sentence_count", "句数"),
        (axes[1, 0], "words_per_sentence", "每句词数"),
        (axes[1, 1], "avg_word_len", "平均词长"),
    ]
    for ax, col, title in box_data:
        data = [fake[col].values, real[col].values]
        bp = ax.boxplot(data, **box_opts)
        for patch, color in zip(bp["boxes"], [C["fake"], C["real"]]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax.set_xticklabels(["假新闻", "真新闻"])
        ax.set_title(title)
        # 计算均值标注
        m0, m1 = fake[col].mean(), real[col].mean()
        ax.annotate(f"{m0:.1f}", xy=(1, m0), fontsize=8, ha="center", color=C["fake"],
                     xytext=(1.35, m0), arrowprops=dict(arrowstyle="->", color=C["fake"], lw=0.5))
        ax.annotate(f"{m1:.1f}", xy=(2, m1), fontsize=8, ha="center", color=C["real"],
                     xytext=(2.35, m1), arrowprops=dict(arrowstyle="->", color=C["real"], lw=0.5))
    _save(fig, "02_word_sentence_boxplot.png")
    print("  [2/10] 词句结构箱线图")

    # ── 03 标点符号密度分组柱状图 ──
    fig, ax = plt.subplots(figsize=(10, 5))
    punct_features = ["exclamation_ratio", "question_ratio", "quote_ratio", "number_ratio", "allcaps_ratio"]
    punct_labels = ["感叹号", "问号", "引号", "数字", "全大写词"]
    x = np.arange(len(punct_labels))
    w = 0.35
    f_means = [fake[c].mean() for c in punct_features]
    r_means = [real[c].mean() for c in punct_features]
    bars1 = ax.bar(x - w/2, f_means, w, label="假新闻", color=C["fake"], edgecolor="white")
    bars2 = ax.bar(x + w/2, r_means, w, label="真新闻", color=C["real"], edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels(punct_labels)
    ax.set_ylabel("密度 (%)")
    ax.set_title("标点符号与强调特征对比")
    ax.legend()
    for bar, val in zip(bars1, f_means):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, f"{val:.2f}%",
                ha="center", fontsize=8, color=C["fake"])
    for bar, val in zip(bars2, r_means):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, f"{val:.2f}%",
                ha="center", fontsize=8, color=C["real"])
    _save(fig, "03_punctuation_bar.png")
    print("  [3/10] 标点符号密度图")

    # ── 04 全大写词比例箱线图 ──
    fig, ax = plt.subplots(figsize=(7, 6))
    bp = ax.boxplot([fake["allcaps_ratio"].values, real["allcaps_ratio"].values],
                     patch_artist=True, widths=0.5, medianprops={"color": C["dark"], "linewidth": 1.5})
    for patch, color in zip(bp["boxes"], [C["fake"], C["real"]]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_xticklabels(["假新闻", "真新闻"])
    ax.set_ylabel("全大写词比例 (%)")
    ax.set_title("全大写词比例 (标题党特征)")
    _save(fig, "04_allcaps_boxplot.png")
    print("  [4/10] 全大写词箱线图")

    # ── 05 来源引用占比 ──
    fig, ax = plt.subplots(figsize=(9, 5))
    source_features = ["has_reuters", "has_ap", "has_video_ref", "has_url", "has_breaking"]
    source_labels = ["Reuters引用", '含"AP"', "视频/图片引用", "URL链接", '含"breaking"']
    x = np.arange(len(source_labels))
    w = 0.35
    f_pcts = [fake[c].mean() * 100 for c in source_features]
    r_pcts = [real[c].mean() * 100 for c in source_features]
    ax.bar(x - w/2, f_pcts, w, label="假新闻", color=C["fake"], edgecolor="white")
    ax.bar(x + w/2, r_pcts, w, label="真新闻", color=C["real"], edgecolor="white")
    for i, (fp, rp) in enumerate(zip(f_pcts, r_pcts)):
        ax.text(i - w/2, fp + 0.5, f"{fp:.1f}%", ha="center", fontsize=8, color=C["fake"])
        ax.text(i + w/2, rp + 0.5, f"{rp:.1f}%", ha="center", fontsize=8, color=C["real"])
    ax.set_xticks(x)
    ax.set_xticklabels(source_labels)
    ax.set_ylabel("占比 (%)")
    ax.set_title("来源引用特征对比")
    ax.legend()
    _save(fig, "05_source_attribution.png")
    print("  [5/10] 来源引用占比图")

    # ── 06 情感词频率对比 ──
    em_counts_fake = Counter()
    em_counts_real = Counter()
    for _, row in fake["text"].sample(min(15000, len(fake)), random_state=42).items():
        for w in row.split():
            wl = w.lower().strip(".,!?;:\"'()[]{}")
            if wl in EMOTIONAL_WORDS:
                em_counts_fake[wl] += 1
    for _, row in real["text"].sample(min(15000, len(real)), random_state=42).items():
        for w in row.split():
            wl = w.lower().strip(".,!?;:\"'()[]{}")
            if wl in EMOTIONAL_WORDS:
                em_counts_real[wl] += 1

    total_words = sum(em_counts_fake.values()) + sum(em_counts_real.values())
    if total_words > 0:
        all_em_words = set(em_counts_fake) | set(em_counts_real)
        em_ratios = []
        for w in all_em_words:
            fc = em_counts_fake.get(w, 0) / max(1, len(fake)) * 10000
            rc = em_counts_real.get(w, 0) / max(1, len(real)) * 10000
            if fc + rc > 2:
                em_ratios.append((w, fc, rc, fc - rc))
        em_ratios.sort(key=lambda x: abs(x[3]), reverse=True)
        top_em = em_ratios[:15]
        fig, ax = plt.subplots(figsize=(10, 6))
        y_pos = np.arange(len(top_em))
        f_vals = [x[1] for x in top_em]
        r_vals = [x[2] for x in top_em]
        h = 0.35
        ax.barh(y_pos + h/2, f_vals, h, label="假新闻", color=C["fake"], edgecolor="white")
        ax.barh(y_pos - h/2, r_vals, h, label="真新闻", color=C["real"], edgecolor="white")
        ax.set_yticks(y_pos)
        ax.set_yticklabels([x[0] for x in top_em])
        ax.set_xlabel("每万词出现频率")
        ax.set_title("情感词使用频率对比 (Top 15)")
        ax.legend()
        ax.invert_yaxis()
        _save(fig, "06_emotional_words_bar.png")
    print("  [6/10] 情感词频率对比图")

    # ── 07 特征相关性热力图 ──
    fig, ax = plt.subplots(figsize=(11, 9))
    labels = [name for _, name in continuous_features]
    vals = corr_matrix.values
    im = ax.imshow(vals, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    for i in range(len(labels)):
        for j in range(len(labels)):
            color = "white" if abs(vals[i, j]) > 0.6 else C["dark"]
            ax.text(j, i, f"{vals[i, j]:.2f}", ha="center", va="center",
                    fontsize=8, fontweight="bold" if abs(vals[i, j]) > 0.5 else "normal", color=color)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_title("特征相关性矩阵 (Pearson r)", fontweight="bold")
    fig.colorbar(im, ax=ax, label="相关系数", shrink=0.8)
    _save(fig, "07_feature_correlation_heatmap.png")
    print("  [7/10] 特征相关性热力图")

    # ── 08 效应量棒棒糖图 ──
    fig, ax = plt.subplots(figsize=(10, 7))
    d_vals = [abs(r["cohens_d"]) for r in t_results_sorted]
    d_labels = [r["feature"] for r in t_results_sorted]
    d_dirs = ["假 > 真" if r["fake_mean"] > r["real_mean"] else "真 > 假" for r in t_results_sorted]
    colors_d = [C["fake"] if d == "假 > 真" else C["real"] for d in d_dirs]
    y_pos = range(len(d_labels))
    ax.barh([len(d_labels) - 1 - i for i in y_pos], d_vals, color=colors_d, height=0.5, edgecolor="white")
    for i, (v, d) in enumerate(zip(d_vals, d_dirs)):
        lbl = f"d={v:.3f} ({d})"
        ax.text(v + 0.01, len(d_labels) - 1 - i, lbl, va="center", fontsize=9, color=C["dark"])
    ax.set_yticks([len(d_labels) - 1 - i for i in y_pos])
    ax.set_yticklabels(d_labels)
    ax.set_xlabel("|Cohen's d|")
    ax.set_title("特征效应量排名 (Cohen's d)")
    ax.axvline(0.2, color=C["grey"], linestyle="--", alpha=0.5, label="小效应(0.2)")
    ax.axvline(0.5, color=C["grey"], linestyle="--", alpha=0.7, label="中效应(0.5)")
    ax.axvline(0.8, color=C["grey"], linestyle="--", alpha=0.9, label="大效应(0.8)")
    ax.legend(fontsize=8)
    _save(fig, "08_effect_size_lollipop.png")
    print("  [8/10] 效应量棒棒糖图")

    # ── 09 最具区分力 Bigrams ──
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    ax = axes[0]
    top10_fake = top_fake_bg[:10]
    ax.barh([x[0] for x in top10_fake][::-1], [x[1] for x in top10_fake][::-1],
            color=C["fake"], edgecolor="white", height=0.5)
    ax.set_title("假新闻高频 Bigrams\n(Fake/Real 比值)")
    ax.set_xlabel("频率比 (假/真)")
    ax = axes[1]
    top10_real = top_real_bg[:10]
    real_bg_vals = [1/x[1] if x[1] > 0 else 999 for x in top10_real]
    ax.barh([x[0] for x in top10_real][::-1], real_bg_vals[::-1],
            color=C["real"], edgecolor="white", height=0.5)
    ax.set_title("真新闻高频 Bigrams\n(Real/Fake 比值)")
    ax.set_xlabel("频率比 (真/假)")
    _save(fig, "09_top_ngrams_bar.png")
    print("  [9/10] Bigrams 对比图")

    # ── 10 雷达图 ──
    radar_features = [
        ("exclamation_ratio", "感叹号密度"),
        ("question_ratio", "问号密度"),
        ("allcaps_ratio", "全大写词"),
        ("emotional_ratio", "情感词"),
        ("words_per_sentence", "每句词数"),
        ("unique_ratio", "词汇多样性"),
        ("stopword_ratio", "停用词"),
        ("avg_word_len", "平均词长"),
    ]
    angles = np.linspace(0, 2 * np.pi, len(radar_features), endpoint=False).tolist()
    angles += angles[:1]

    f_z = []
    r_z = []
    for col, _ in radar_features:
        all_vals = df[col].values
        m, s = all_vals.mean(), all_vals.std()
        if s > 0:
            f_z.append((fake[col].mean() - m) / s)
            r_z.append((real[col].mean() - m) / s)
        else:
            f_z.append(0)
            r_z.append(0)
    f_z += f_z[:1]
    r_z += r_z[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})
    ax.fill(angles, f_z, alpha=0.3, color=C["fake"], label="假新闻")
    ax.plot(angles, f_z, color=C["fake"], linewidth=2)
    ax.fill(angles, r_z, alpha=0.3, color=C["real"], label="真新闻")
    ax.plot(angles, r_z, color=C["real"], linewidth=2)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([name for _, name in radar_features], fontsize=9)
    ax.set_title("真假新闻特征雷达图 (Z-score 标准化)", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    _save(fig, "10_combined_radar.png")
    print("  [10/10] 综合雷达图")

    # ── 完成 ──
    print(f"\n{'='*60}")
    print(f"  全部图表已保存至: {OUT.resolve()}/")
    for fname in sorted(OUT.glob("*.png")):
        if not fname.name.startswith("_"):
            print(f"    {fname.name}")
    print(f"  分析结果 JSON: {OUT.resolve() / 'analysis_results.json'}")
    print(f"{'='*60}")
    print("  分析完成。")


if __name__ == "__main__":
    main()
