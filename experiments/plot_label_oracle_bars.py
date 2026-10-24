#!/usr/bin/env python3
"""Horizontal grouped bars for the label-oracle sensitivity pilot.

Y-axis: metrics. Bars within each metric: label methods.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from paper_plot_style import LABEL_SIZE, LEGEND_SIZE, TICK_SIZE, apply as apply_paper_style

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
PLOT_DATA = ROOT / "experiments/data/plot_data"

STEEL, LIGHT, YELLOW, CORAL, OLIVE = "#46788E", "#78B7C9", "#F6E093", "#E58B7B", "#97B319"
INK = "#243028"

# PHGST first as the strongest pilot labelling method.
METHODS = [
    ("PHGST", STEEL),
    ("Queue-Wait", OLIVE),
    ("TPM", CORAL),
    ("Active Period", LIGHT),
    ("Utilization", YELLOW),
]
METRICS = [
    ("NDCG@3", "ndcg3"),
    ("Positive R@2", "pos_r2"),
    ("Positive R@3", "pos_r3"),
    ("Weighted R@3", "w_r3"),
    ("Coverage@3 (0.9)", "cov39"),
]
VALUES = {
    "PHGST": dict(ndcg3=0.531, pos_r2=0.556, pos_r3=0.685, w_r3=0.716, cov39=0.722),
    "TPM": dict(ndcg3=0.372, pos_r2=0.278, pos_r3=0.389, w_r3=0.421, cov39=0.444),
    "Active Period": dict(ndcg3=0.382, pos_r2=0.278, pos_r3=0.315, w_r3=0.377, cov39=0.389),
    "Utilization": dict(ndcg3=0.183, pos_r2=0.222, pos_r3=0.204, w_r3=0.230, cov39=0.222),
    "Queue-Wait": dict(ndcg3=0.495, pos_r2=0.444, pos_r3=0.556, w_r3=0.585, cov39=0.611),
}


def main() -> None:
    apply_paper_style(INK)
    plt.rcParams.update(
        {
            "axes.linewidth": 0.0,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "axes.spines.bottom": False,
        }
    )

    n_metrics = len(METRICS)
    n_methods = len(METHODS)
    y = np.arange(n_metrics)
    height = 0.14
    offsets = (np.arange(n_methods) - (n_methods - 1) / 2.0) * height

    # Single-column width; legend above the bars.
    fig, ax = plt.subplots(figsize=(3.35, 3.55))
    rows_out: list[dict] = []
    for offset, (method, color) in zip(offsets, METHODS):
        vals = [VALUES[method][key] for _, key in METRICS]
        ax.barh(
            y + offset,
            vals,
            height=height * 0.92,
            color=color,
            edgecolor="none",
            label=method,
            zorder=3,
        )
        for (_, key), val in zip(METRICS, vals):
            rows_out.append({"method": method, "metric": key, "value": f"{val:.3f}"})

    # Column-width figure is barely scaled; use sizes that match Fig.4 on page.
    ax.set_yticks(y)
    ax.set_yticklabels([label for label, _ in METRICS], fontsize=7.0)
    ax.set_xlabel("Score ↑", fontsize=7.5)
    ax.set_xlim(0.0, 0.85)
    ax.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8])
    ax.tick_params(axis="x", labelsize=6.5)
    ax.invert_yaxis()
    ax.tick_params(axis="y", length=0, pad=3)
    ax.tick_params(axis="x", length=0)
    ax.grid(axis="x", color="#E2E4E4", lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.45, 1.14),
        fontsize=6.5,
        frameon=False,
        ncol=5,
        columnspacing=0.55,
        handlelength=0.95,
        handletextpad=0.25,
        borderaxespad=0.0,
    )
    fig.subplots_adjust(left=0.34, right=0.98, top=0.86, bottom=0.12)
    FIG.mkdir(parents=True, exist_ok=True)
    PLOT_DATA.mkdir(parents=True, exist_ok=True)
    for suffix in ("pdf", "png", "svg"):
        dest = FIG / f"fig_label_oracle_bars.{suffix}"
        tmp = FIG / f"_fig_label_oracle_bars_{suffix}.tmp"
        fig.savefig(
            tmp,
            dpi=600 if suffix == "png" else None,
            format=suffix,
            bbox_inches="tight",
            pad_inches=0.08,
            facecolor="white",
            edgecolor="none",
        )
        try:
            dest.unlink(missing_ok=True)
            tmp.replace(dest)
        except OSError:
            alt = FIG / f"fig_label_oracle_bars.{suffix}.new"
            if alt.exists():
                alt.unlink()
            tmp.replace(alt)
            print(f"[warn] could not replace {dest.name}; wrote {alt.name}")
    with (PLOT_DATA / "label_oracle_bars.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["method", "metric", "value"])
        writer.writeheader()
        writer.writerows(rows_out)
    plt.close(fig)
    print("[plot] fig_label_oracle_bars")


if __name__ == "__main__":
    main()
