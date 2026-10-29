#!/usr/bin/env python3
"""Plot compact evidence for cross-resource advance warning and type balance."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator

from paper_plot_style import ANNOT_SIZE, LABEL_SIZE, LEGEND_SIZE, TICK_SIZE, TITLE_SIZE, apply as apply_paper_style


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures/fig_cross_resource_evidence"
DATA = ROOT / "experiments/data/plot_data/cross_resource_evidence.csv"
ARMS = ("Full", "NoGroup", "NoCross", "NoGraph")
# Palette card: light blue, yellow, red, green.
COLORS = {
    "Full": "#78B7C9",
    "NoGroup": "#F6E093",
    "NoCross": "#E58B7B",
    "NoGraph": "#97B319",
}

FAR_RECALL = {"Full": 43.3, "NoGroup": 19.2, "NoCross": 6.7, "NoGraph": 0.0}
TYPE_HMEAN = {
    "Full": {5: 50.5, 10: 53.0, 15: 53.6},
    "NoGroup": {5: 43.2, 10: 45.2, 15: 46.9},
    "NoCross": {5: 39.6, 10: 37.1, 15: 36.5},
    "NoGraph": {5: 38.4, 10: 37.6, 15: 36.0},
}


def configure_style() -> None:
    apply_paper_style()
    plt.rcParams["legend.frameon"] = False


def write_data() -> None:
    DATA.parent.mkdir(parents=True, exist_ok=True)
    with DATA.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("arm", "start_cap_min", "far_recall_pct", "type_hmean_pct"),
            lineterminator="\n",
        )
        writer.writeheader()
        for arm in ARMS:
            for cap in (5, 10, 15):
                writer.writerow(
                    {
                        "arm": arm,
                        "start_cap_min": cap,
                        "far_recall_pct": FAR_RECALL[arm] if cap == 15 else "",
                        "type_hmean_pct": TYPE_HMEAN[arm][cap],
                    }
                )


def main() -> None:
    configure_style()
    write_data()

    # Side-by-side panels sized for a single journal column.
    fig, axes = plt.subplots(1, 2, figsize=(3.40, 2.55))
    fig.subplots_adjust(left=0.14, right=0.99, bottom=0.22, top=0.88, wspace=0.55)

    # (a) Vertical bars: far-ahead recall by arm
    ax = axes[0]
    x = np.arange(len(ARMS))
    values = [FAR_RECALL[arm] for arm in ARMS]
    bars = ax.bar(
        x,
        values,
        width=0.68,
        color=[COLORS[arm] for arm in ARMS],
        edgecolor="none",
        linewidth=0,
        zorder=3,
    )
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            value + 1.2,
            f"{value:.1f}",
            ha="center",
            va="bottom",
            fontsize=ANNOT_SIZE,
        )
    ax.set_xticks(x)
    ax.set_xticklabels(ARMS, fontsize=TICK_SIZE, rotation=25, ha="right")
    ax.set_ylim(0, 52)
    ax.yaxis.set_major_locator(MultipleLocator(10))
    ax.tick_params(axis="y", labelsize=TICK_SIZE)
    ax.grid(axis="y", color="#E2E4E4", linewidth=0.5, zorder=0)
    ax.set_ylabel(r"$>10$-min upcoming recall (%)", fontsize=LABEL_SIZE)
    ax.set_title("(a) Far-ahead recall\nOnset limit $\\leq15$ min", fontsize=TITLE_SIZE, pad=4)

    # (b) Grouped vertical bars: type hmean by Start cap
    ax = axes[1]
    caps = (5, 10, 15)
    n_arms = len(ARMS)
    group_x = np.arange(len(caps))
    width = 0.18
    offsets = (np.arange(n_arms) - (n_arms - 1) / 2.0) * width
    for offset, arm in zip(offsets, ARMS):
        vals = [TYPE_HMEAN[arm][cap] for cap in caps]
        ax.bar(
            group_x + offset,
            vals,
            width=width * 0.92,
            color=COLORS[arm],
            edgecolor="none",
            linewidth=0,
            label=arm,
            zorder=3,
        )
    ax.set_xticks(group_x, [str(cap) for cap in caps], fontsize=TICK_SIZE)
    ax.set_ylim(0, 60)
    ax.yaxis.set_major_locator(MultipleLocator(10))
    ax.tick_params(axis="y", labelsize=TICK_SIZE)
    ax.grid(axis="y", color="#E2E4E4", linewidth=0.5, zorder=0)
    ax.set_xlabel("Onset limit (min)", fontsize=LABEL_SIZE)
    ax.set_ylabel("Resource-type hmean (%)", fontsize=LABEL_SIZE)
    ax.set_title("(b) Type-balanced hmean", fontsize=TITLE_SIZE, pad=4)

    handles = [Patch(facecolor=COLORS[arm], edgecolor="none", linewidth=0, label=arm) for arm in ARMS]
    axes[0].legend(
        handles=handles,
        loc="upper right",
        ncol=1,
        fontsize=LEGEND_SIZE,
        frameon=False,
        handlelength=0.95,
        labelspacing=0.2,
        borderaxespad=0.2,
        handletextpad=0.25,
    )

    for extension in ("pdf", "svg", "png"):
        fig.savefig(OUT.with_suffix(f".{extension}"), dpi=300, facecolor="white")
    svg = OUT.with_suffix(".svg")
    svg.write_text(
        "\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
        encoding="utf-8",
    )
    plt.close(fig)
    print(f"Wrote {OUT}.pdf/.svg/.png and {DATA}")


if __name__ == "__main__":
    main()
