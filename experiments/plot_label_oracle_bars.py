#!/usr/bin/env python3
"""Horizontal grouped bars for the label-oracle sensitivity pilot."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
PLOT_DATA = ROOT / "experiments/data/plot_data"

STEEL, LIGHT, YELLOW, CORAL, OLIVE = "#46788E", "#78B7C9", "#F6E093", "#E58B7B", "#97B319"
INK = "#243028"

# Table order retained; Ops first as the strongest pilot method.
METHODS = ["Ops", "TPM", "Active Period", "Utilization", "Queue-Wait"]
METRICS = [
    ("NDCG@3", "ndcg3", STEEL),
    ("Positive R@2", "pos_r2", LIGHT),
    ("Positive R@3", "pos_r3", YELLOW),
    ("Weighted R@3", "w_r3", CORAL),
    ("Coverage@3 (0.9)", "cov39", OLIVE),
]
VALUES = {
    "Ops": dict(ndcg3=0.531, pos_r2=0.556, pos_r3=0.685, w_r3=0.716, cov39=0.722),
    "TPM": dict(ndcg3=0.372, pos_r2=0.278, pos_r3=0.389, w_r3=0.421, cov39=0.444),
    "Active Period": dict(ndcg3=0.382, pos_r2=0.278, pos_r3=0.315, w_r3=0.377, cov39=0.389),
    "Utilization": dict(ndcg3=0.183, pos_r2=0.222, pos_r3=0.204, w_r3=0.230, cov39=0.222),
    "Queue-Wait": dict(ndcg3=0.495, pos_r2=0.444, pos_r3=0.556, w_r3=0.585, cov39=0.611),
}


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif", "serif"],
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 9,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "text.color": INK,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
        }
    )

    n_methods = len(METHODS)
    n_metrics = len(METRICS)
    y = np.arange(n_methods)
    height = 0.14
    offsets = (np.arange(n_metrics) - (n_metrics - 1) / 2.0) * height

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    rows_out: list[dict] = []
    for offset, (label, key, color) in zip(offsets, METRICS):
        vals = [VALUES[m][key] for m in METHODS]
        ax.barh(
            y + offset,
            vals,
            height=height * 0.92,
            color=color,
            edgecolor=INK,
            linewidth=0.45,
            label=label,
            zorder=3,
        )
        for method, val in zip(METHODS, vals):
            rows_out.append({"method": method, "metric": key, "value": f"{val:.3f}"})

    ax.set_yticks(y)
    ax.set_yticklabels(METHODS)
    ax.set_xlabel("Score (higher is better)")
    ax.set_xlim(0.0, 0.85)
    ax.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8])
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.28, lw=0.6, zorder=0)
    ax.legend(
        loc="lower right",
        fontsize=7.5,
        frameon=False,
        ncol=1,
        borderaxespad=0.2,
    )
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    PLOT_DATA.mkdir(parents=True, exist_ok=True)
    for suffix in ("pdf", "png", "svg"):
        fig.savefig(FIG / f"fig_label_oracle_bars.{suffix}", dpi=600 if suffix == "png" else None)
    with (PLOT_DATA / "label_oracle_bars.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["method", "metric", "value"])
        writer.writeheader()
        writer.writerows(rows_out)
    plt.close(fig)
    print("[plot] fig_label_oracle_bars")


if __name__ == "__main__":
    main()
