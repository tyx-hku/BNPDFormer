#!/usr/bin/env python3
"""Plot reported predictive quality against measured report latency.

Efficiency values: all-RTX-5090 export at isaac_factory@a5b6c92,
including PHGST-DP source snapshots and the 2026-10-24 XGBoost CUDA run.
F1-score: parsed from the current manuscript's tab:comparison-main.
See efficiency_comparison_2026-10-24.md for provenance and open checks.
This script never reruns or changes model experiments.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FuncFormatter, MultipleLocator, NullLocator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "experiments/data/efficiency_comparison_5090_2026-10-24.csv"
MODELS = ("PHGST-DP", "XGBoost", "LSTM", "BTGCN", "BSTAN")
STYLES = {
    "PHGST-DP": ("#46788E", "o"),
    "XGBoost": ("#97B319", "s"),
    "LSTM": ("#E58B7B", "^"),
    "BTGCN": ("#78B7C9", "D"),
    "BSTAN": ("#C4A35A", "v"),
}


def read_manuscript_f1() -> dict[tuple[int, str], float]:
    text = (ROOT / "main.tex").read_text(encoding="utf-8")
    start = text.index(r"\label{tab:comparison-main}")
    end = text.index(r"\end{table*}", start)
    cap = None
    values = {}
    for line in text[start:end].splitlines():
        match = re.search(r"Start\s*\$\\leq(5|10|15)\$", line)
        if match:
            cap = int(match.group(1))
        fields = line.split("&")
        if len(fields) < 5 or fields[0].strip() not in MODELS:
            continue
        match = re.search(r"(\d+(?:\.\d+)?)\\%", fields[1])
        if cap is None or not match:
            raise ValueError(f"Cannot parse F1-score: {line}")
        values[(cap, fields[0].strip())] = float(match.group(1)) / 100
    expected = {(cap, model) for cap in (5, 10, 15) for model in MODELS}
    if set(values) != expected:
        raise ValueError("Expected exactly five F1-score values per onset cap")
    return values


def main() -> None:
    font_dir = Path("/System/Library/Fonts/Supplemental")
    for path in font_dir.glob("Times New Roman*.ttf"):
        font_manager.fontManager.addfont(str(path))
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
        "font.size": 10,
        "axes.labelsize": 10,
        "axes.titlesize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.7,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "text.color": "#243028",
        "axes.labelcolor": "#243028",
    })
    with DATA.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    expected = {(cap, model) for cap in (5, 10, 15) for model in MODELS}
    keys = {(int(row["start_cap_min"]), row["model"]) for row in rows}
    if len(rows) != 15 or keys != expected:
        raise ValueError("Efficiency table must contain 15 unique model/cap pairs")
    f1 = read_manuscript_f1()
    for row in rows:
        row["report_f1"] = f1[(int(row["start_cap_min"]), row["model"])]
    joined = ROOT / "experiments/data/plot_data/quality_cost_comparison.csv"
    joined.parent.mkdir(parents=True, exist_ok=True)
    with joined.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    fig, axes = plt.subplots(1, 3, figsize=(7.5, 2.85), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.23, top=0.77, wspace=0.17)
    for i, (ax, cap) in enumerate(zip(axes, (5, 10, 15))):
        subset = [row for row in rows if int(row["start_cap_min"]) == cap]
        for row in subset:
            name = row["model"]
            color, marker = STYLES[name]
            x, y = float(row["report_p50_ms"]), row["report_f1"]
            ax.scatter(x, y, s=55 if name == "PHGST-DP" else 39,
                       c=color, marker=marker, edgecolors="white", linewidths=0.6,
                       zorder=4)
            if name == "PHGST-DP":
                ax.annotate(f"{y:.3f}", (x, y), xytext=(-8, 7),
                            textcoords="offset points", ha="right", va="bottom",
                            color=color, fontsize=10, fontweight="bold")
        ax.set_title(f"({chr(97 + i)}) Start $\\leq$ {cap} min", pad=9)
        ax.set_xscale("log")
        ax.set_xlim(0.4, 100)
        ax.set_ylim(0.40, 0.90)
        ax.xaxis.set_major_locator(FixedLocator([0.5, 1, 5, 10, 50]))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.yaxis.set_major_locator(MultipleLocator(0.1))
        ax.grid(color="#E2E4E4", lw=0.55, zorder=0)
        ax.tick_params(length=3, width=0.6)
    axes[0].set_ylabel("F1-score")
    fig.supxlabel("Report latency p50 (ms, log scale)", y=0.06, fontsize=10)
    handles = [Line2D([], [], color=STYLES[name][0], marker=STYLES[name][1],
                      ls="none", markersize=6,
                      label=name)
               for name in MODELS]
    fig.legend(handles=handles, loc="upper center", ncol=5, frameon=False,
               bbox_to_anchor=(0.51, 1.01), handletextpad=0.35,
               columnspacing=1.2, fontsize=10)
    out = ROOT / "figures/fig_quality_cost"
    for ext in ("pdf", "svg", "png"):
        fig.savefig(out.with_suffix(f".{ext}"), dpi=300, facecolor="white")
    svg = out.with_suffix(".svg")
    svg.write_text(
        "\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
        encoding="utf-8",
    )
    plt.close(fig)
    print(f"Wrote {out}.pdf/.svg/.png and {joined}")


if __name__ == "__main__":
    main()
