#!/usr/bin/env python3
"""Clean, publication-ready PHAST-DP model architecture diagram."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "fig_model_architecture"

# Restrained academic palette. Red is reserved for the delay-pattern pathway.
INK = "#20262D"
MUTED = "#65717A"
EDGE = "#3B4650"
LIGHT_EDGE = "#B8C1C8"
PANEL = "#F3F4F5"
WHITE = "#FFFFFF"
NAVY = "#315A86"
BLUE = "#6E9CC5"
BLUE_BG = "#E7F0F8"
TEAL = "#5D9B94"
TEAL_BG = "#E4F1EF"
VIOLET = "#8A78B4"
VIOLET_BG = "#EEEAF6"
GOLD = "#C88A32"
GOLD_BG = "#FAEFCF"
RED = "#C74E4E"
RED_BG = "#F8E4E1"
GREEN = "#7D9F6B"
GREEN_BG = "#EAF1E5"


def rbox(ax, x, y, w, h, fc=WHITE, ec=EDGE, lw=0.9, radius=0.75,
         ls="-", z=2):
    p = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.02,rounding_size={radius}",
        facecolor=fc, edgecolor=ec, linewidth=lw, linestyle=ls, zorder=z,
    )
    ax.add_patch(p)
    return p


def text(ax, x, y, s, size=11, color=INK, weight="normal", ha="center",
         va="center", style="normal", z=8, linespacing=1.05):
    return ax.text(
        x, y, s, fontsize=size, color=color, fontweight=weight,
        ha=ha, va=va, fontstyle=style, zorder=z, linespacing=linespacing,
    )


def arrow(ax, p0, p1, color=EDGE, lw=1.2, ls="-", rad=0.0,
          ms=10, z=6, style="-|>"):
    p = FancyArrowPatch(
        p0, p1, arrowstyle=style, mutation_scale=ms,
        color=color, linewidth=lw, linestyle=ls,
        connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0, zorder=z,
    )
    ax.add_patch(p)
    return p


def path(ax, pts, color=EDGE, lw=1.0, ls="-", z=4):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, linewidth=lw, linestyle=ls, zorder=z)


def heading(ax, x, y, index, title, subtitle=None):
    ax.add_patch(Circle((x, y), 0.78, fc=NAVY, ec="none", zorder=5))
    text(ax, x, y, index, size=11, color=WHITE, weight="bold")
    text(ax, x + 1.35, y, title, size=14.5, weight="bold", ha="left")
    if subtitle:
        text(ax, x + 1.38, y - 1.7, subtitle, size=8.8,
             color=MUTED, ha="left")


def draw_tensor(ax, x, y):
    rng = np.random.default_rng(12)
    cols = ["#ECF3F8", "#D5E4EF", "#A9C7DC", "#6E9CC5"]
    for layer in range(3):
        ox, oy = 0.34 * layer, 0.32 * layer
        ax.add_patch(Rectangle((x + ox, y + oy), 5.3, 4.2,
                               fc=WHITE, ec=BLUE, lw=0.55,
                               zorder=3 + layer))
        a = rng.integers(0, 4, size=(5, 7))
        for i in range(5):
            for j in range(7):
                ax.add_patch(Rectangle(
                    (x + ox + j * 5.3 / 7, y + oy + i * 4.2 / 5),
                    5.3 / 7, 4.2 / 5, fc=cols[a[i, j]], ec=WHITE,
                    lw=0.18, zorder=4 + layer,
                ))


def draw_graph(ax, x, y):
    pts = [(x, y), (x + 2.1, y + 1.15), (x + 4.2, y),
           (x + 6.3, y + 1.15), (x + 8.4, y)]
    for a, b in zip(pts[:-1], pts[1:]):
        path(ax, [a, b], color="#76828A", lw=0.9)
    path(ax, [pts[0], pts[2], pts[4]], color=TEAL, lw=0.8,
         ls=(0, (2, 1.5)))
    for i, (xx, yy) in enumerate(pts):
        ax.add_patch(Circle((xx, yy), 0.48,
                            fc=TEAL if i % 2 else NAVY,
                            ec=WHITE, lw=0.6, zorder=5))


def draw_inputs(ax):
    heading(ax, 3.0, 43.3, "A", "Model inputs")

    rbox(ax, 1.5, 26.2, 17.2, 13.5, fc=WHITE, ec=BLUE, lw=1.0)
    text(ax, 2.5, 38.0, "Multi-entity state history", size=11.6,
         weight="bold", ha="left")
    draw_tensor(ax, 2.7, 29.1)
    text(ax, 9.5, 34.2, r"$X_t\in\mathbb{R}^{30\times38\times27}$",
         size=11.3, weight="bold", ha="left")
    text(ax, 9.5, 31.3,
         "30 one-minute windows\n38 resources · 27 features",
         size=9.2, color=MUTED, ha="left")

    rbox(ax, 1.5, 9.0, 17.2, 13.5, fc=WHITE, ec=TEAL, lw=1.0)
    text(ax, 2.5, 20.8, "Structured priors", size=11.6,
         weight="bold", ha="left")
    draw_graph(ax, 2.7, 16.4)
    text(ax, 12.3, 17.5, r"factory graph  $G$", size=9.4,
         weight="bold", ha="left")
    text(ax, 12.3, 15.7, r"masks  $M^G,\ M^S$", size=9.4,
         color=MUTED, ha="left")
    rbox(ax, 2.7, 10.6, 13.8, 2.7, fc=GOLD_BG, ec=GOLD,
         lw=0.7, radius=0.45)
    text(ax, 3.4, 11.95, "short-pattern bank", size=9.0,
         weight="bold", ha="left")
    text(ax, 15.7, 11.95, r"$K^P:16\times3$", size=9.3,
         color="#80581F", weight="bold", ha="right")


def token_bar(ax, y, label, dim, fc, ec):
    rbox(ax, 25.0, y, 13.2, 2.75, fc=fc, ec=ec, lw=0.7, radius=0.6)
    text(ax, 25.8, y + 1.38, label, size=9.7, weight="bold", ha="left")
    text(ax, 37.3, y + 1.38, str(dim), size=9.1, color=MUTED, ha="right")


def draw_embedding(ax):
    rbox(ax, 22.7, 5.2, 18.1, 38.3, fc=PANEL, ec="none", lw=0)
    heading(ax, 24.2, 41.7, "B", "Grouped token embedding")

    groups = [
        ("Queue", 4, BLUE_BG, BLUE),
        ("Stall", 6, RED_BG, "#D47A72"),
        ("Logistics", 4, TEAL_BG, TEAL),
        ("Shortage", 1, GOLD_BG, GOLD),
        ("Context", 7, VIOLET_BG, VIOLET),
        ("Type", 5, GREEN_BG, GREEN),
    ]
    for i, args in enumerate(groups):
        token_bar(ax, 34.8 - i * 4.15, *args)

    # Group projections converge through a visible collection bus.
    centres = [34.8 - i * 4.15 + 1.375 for i in range(6)]
    for yy in centres:
        path(ax, [(38.25, yy), (39.2, yy)], color="#87939B", lw=0.7)
    path(ax, [(39.2, centres[-1]), (39.2, centres[0])],
         color="#87939B", lw=0.8)
    arrow(ax, (39.2, centres[-1]), (36.7, 9.4), color=NAVY,
          lw=0.9, ms=8, rad=-0.08)

    rbox(ax, 26.6, 7.6, 10.1, 3.5, fc=WHITE, ec=NAVY,
         lw=0.8, radius=0.55)
    text(ax, 31.65, 9.85, r"$\mathrm{Linear}_q+\mathrm{GELU}$",
         size=9.7, weight="bold")
    text(ax, 31.65, 8.35, "mean aggregation", size=8.4, color=MUTED)

    ax.add_patch(Circle((31.65, 5.55), 0.82, fc=WHITE, ec=NAVY,
                        lw=0.9, zorder=5))
    text(ax, 31.65, 5.55, "+", size=15, color=NAVY, weight="bold")
    text(ax, 33.0, 5.55, r"$E_{time}+E_{lap}+E_{node}$",
         size=8.8, color=MUTED, ha="left")
    arrow(ax, (31.65, 7.55), (31.65, 6.4), color=NAVY, lw=0.9, ms=8)
    rbox(ax, 26.1, 0.9, 11.0, 2.4, fc=NAVY, ec=NAVY, lw=0.8, radius=0.6)
    text(ax, 31.6, 2.1, r"Initial tokens  $H^{(0)}$", size=10.4,
         color=WHITE, weight="bold")
    arrow(ax, (31.65, 4.7), (31.65, 3.35), color=NAVY, lw=1.0)


def attention_box(ax, y, title, detail, fc, ec):
    rbox(ax, 51.2, y, 14.1, 5.2, fc=fc, ec=ec, lw=0.9, radius=0.65)
    text(ax, 52.0, y + 3.45, title, size=10.1, weight="bold", ha="left")
    text(ax, 52.0, y + 1.4, detail, size=8.5, color=MUTED, ha="left")


def draw_encoder(ax):
    rbox(ax, 45.0, 5.2, 39.0, 38.3, fc=PANEL, ec="none", lw=0)
    heading(ax, 46.5, 41.7, "C", "Spatiotemporal encoder")
    rbox(ax, 70.8, 39.6, 11.4, 2.7, fc=NAVY, ec=NAVY, lw=0.8, radius=0.7)
    text(ax, 76.5, 40.95, r"Block $\times5$   ($d=80$)", size=10.2,
         color=WHITE, weight="bold")

    # Pattern cross-attention sits above the three dependency branches.
    rbox(ax, 51.2, 34.0, 20.0, 4.8, fc=GOLD_BG, ec=GOLD, lw=1.0, radius=0.65)
    text(ax, 52.0, 37.05, "Queue patch", size=9.0, weight="bold", ha="left")
    text(ax, 52.0, 35.55, r"$P_{t,n}$", size=9.6, color=MUTED, ha="left")
    arrow(ax, (56.3, 36.4), (59.1, 36.4), color=RED, lw=1.0, ms=8)
    rbox(ax, 59.2, 34.65, 6.2, 3.5, fc=WHITE, ec=RED, lw=0.85, radius=0.5)
    text(ax, 62.3, 36.4, "Pattern MHA", size=9.3, weight="bold")
    arrow(ax, (65.5, 36.4), (68.3, 36.4), color=RED, lw=1.0, ms=8)
    text(ax, 69.0, 36.4, r"$C^P$", size=10.2, color=RED, weight="bold")

    attention_box(ax, 26.4, "Temporal self-attention",
                  "4 heads · within-resource history", BLUE_BG, BLUE)
    attention_box(ax, 18.3, "Geographic attention",
                  r"2 heads · mask $M^G$ · keys $+C^P$", TEAL_BG, TEAL)
    attention_box(ax, 10.2, "Semantic self-attention",
                  r"2 heads · top-5 mask $M^S$", VIOLET_BG, VIOLET)

    # Input fan-out and attention collection buses.
    rbox(ax, 46.2, 1.0, 8.6, 2.5, fc=BLUE_BG, ec=NAVY, lw=0.8, radius=0.55)
    text(ax, 50.5, 2.25, r"$H^{(l-1)}$", size=11.2, color=NAVY, weight="bold")
    path(ax, [(50.5, 3.55), (49.0, 3.55), (49.0, 29.0)], color=EDGE, lw=1.0)
    for yy, col in [(29.0, BLUE), (20.9, TEAL), (12.8, VIOLET)]:
        arrow(ax, (49.0, yy), (51.1, yy), color=col, lw=0.95, ms=8)

    path(ax, [(65.4, 12.8), (67.0, 12.8), (67.0, 29.0),
              (65.4, 29.0)], color=EDGE, lw=1.0)
    path(ax, [(65.4, 20.9), (67.0, 20.9)], color=EDGE, lw=1.0)

    # Fusion and Transformer residual stack.
    rbox(ax, 69.0, 26.1, 12.1, 5.6, fc=BLUE_BG, ec=NAVY, lw=0.9, radius=0.65)
    text(ax, 75.05, 29.7, "Concat + Linear", size=9.8, weight="bold")
    text(ax, 75.05, 27.8, r"$[H_T\Vert H_G\Vert H_S]$", size=9.0, color=MUTED)
    arrow(ax, (67.0, 28.9), (68.9, 28.9), color=NAVY, lw=1.0, ms=8)

    stages = [
        (20.0, "Add & Norm", TEAL_BG, TEAL),
        (14.1, "Feed-forward network", WHITE, LIGHT_EDGE),
        (8.2, "Add & Norm", TEAL_BG, TEAL),
    ]
    for yy, label, fc, ec in stages:
        rbox(ax, 69.0, yy, 12.1, 4.1, fc=fc, ec=ec, lw=0.85, radius=0.6)
        text(ax, 75.05, yy + 2.05, label, size=9.4, weight="bold")
    arrow(ax, (75.05, 26.0), (75.05, 24.2), lw=1.0)
    arrow(ax, (75.05, 19.9), (75.05, 18.25), lw=1.0)
    arrow(ax, (75.05, 14.0), (75.05, 12.35), lw=1.0)

    # Residual connections echo the reference architecture style.
    path(ax, [(50.5, 3.55), (82.1, 3.55), (82.1, 22.0), (81.2, 22.0)],
         color=EDGE, lw=0.9)
    path(ax, [(75.05, 18.2), (83.0, 18.2), (83.0, 10.25), (81.2, 10.25)],
         color=EDGE, lw=0.9)
    text(ax, 82.0, 23.2, "residual", size=7.7, color=MUTED, style="italic")

    rbox(ax, 69.0, 1.0, 12.1, 4.0, fc=NAVY, ec=NAVY, lw=0.8, radius=0.65)
    text(ax, 75.05, 3.0, r"Encoded states  $H^{(L)}$", size=10.2,
         color=WHITE, weight="bold")
    arrow(ax, (75.05, 8.1), (75.05, 5.05), color=NAVY, lw=1.0)
    path(ax, [(69.0, 34.0), (67.2, 34.0), (67.2, 20.9), (66.0, 20.9)],
         color=RED, lw=1.05, ls=(0, (4, 2)), z=5)
    arrow(ax, (66.0, 20.9), (65.4, 20.9), color=RED, lw=1.05,
          ls=(0, (4, 2)), ms=8)


def head_box(ax, x, y, w, title, detail, fc, ec):
    rbox(ax, x, y, w, 4.3, fc=fc, ec=ec, lw=0.75, radius=0.55)
    text(ax, x + 0.65, y + 2.85, title, size=9.3, weight="bold", ha="left")
    text(ax, x + 0.65, y + 1.15, detail, size=8.3, color=MUTED, ha="left")


def draw_decoders(ax):
    rbox(ax, 87.7, 5.2, 20.0, 38.3, fc=PANEL, ec="none", lw=0)
    heading(ax, 89.2, 41.7, "D", "Multi-task heads")

    text(ax, 90.1, 37.6, "Station-level decoding", size=10.8,
         weight="bold", ha="left")
    head_box(ax, 90.0, 31.9, 15.4, "Occurrence",
             r"$p^{cont},\ p^{onset}$", BLUE_BG, BLUE)
    head_box(ax, 90.0, 26.8, 15.4, "Onset and duration",
             r"$\pi^s,\ \hat d$", GOLD_BG, GOLD)
    head_box(ax, 90.0, 21.7, 15.4, "Dense future",
             r"$\hat p,\ \hat O$", VIOLET_BG, VIOLET)

    text(ax, 90.1, 18.3, "Graph-level decoding", size=10.8,
         weight="bold", ha="left")
    rbox(ax, 90.0, 12.2, 15.4, 4.5, fc=TEAL_BG, ec=TEAL, lw=0.75, radius=0.55)
    text(ax, 97.7, 15.15, "mean + gated-max pool", size=9.2, weight="bold")
    text(ax, 97.7, 13.55, "+ order progress", size=8.4, color=MUTED)
    head_box(ax, 90.0, 6.5, 7.3, "Cause", r"$\hat c$", RED_BG, RED)
    head_box(ax, 98.1, 6.5, 7.3, "Remaining", r"$\hat\ell$", GOLD_BG, GOLD)


def draw_output(ax):
    heading(ax, 111.0, 41.7, "E", "Prediction")
    rbox(ax, 110.0, 12.2, 8.5, 25.0, fc=WHITE, ec=NAVY, lw=1.0, radius=0.8)
    text(ax, 114.25, 35.2, "Bottleneck report", size=10.0, weight="bold")
    rows = [
        ("station", r"$\hat n$", BLUE_BG, BLUE),
        ("onset", r"$\hat s$", GOLD_BG, GOLD),
        ("duration", r"$\hat d$", VIOLET_BG, VIOLET),
        ("cause", r"$\hat c$", RED_BG, RED),
        ("remaining", r"$\hat\ell$", TEAL_BG, TEAL),
    ]
    for i, (label, symbol, fc, ec) in enumerate(rows):
        yy = 30.9 - i * 4.0
        rbox(ax, 111.0, yy, 6.5, 2.8, fc=fc, ec=ec, lw=0.65, radius=0.45)
        text(ax, 111.55, yy + 1.4, label, size=8.4, weight="bold", ha="left")
        text(ax, 116.85, yy + 1.4, symbol, size=9.2, color=ec,
             weight="bold", ha="right")


def build_figure():
    plt.rcParams.update({
        "font.family": "Arial",
        "font.size": 11,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "mathtext.fontset": "stixsans",
    })
    fig, ax = plt.subplots(figsize=(17.2, 6.85))
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 48)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    draw_inputs(ax)
    draw_embedding(ax)
    draw_encoder(ax)
    draw_decoders(ax)
    draw_output(ax)

    # Primary left-to-right network path.
    arrow(ax, (18.8, 32.9), (22.55, 32.9), color=EDGE, lw=1.5, ms=11)
    arrow(ax, (37.2, 2.1), (46.1, 2.25), color=NAVY, lw=1.5, ms=11)
    arrow(ax, (81.2, 3.0), (87.55, 24.0), color=NAVY, lw=1.5,
          rad=-0.08, ms=11)
    arrow(ax, (107.75, 24.0), (109.85, 24.0), color=EDGE, lw=1.5, ms=11)

    # Cross-attention/control paths from structured priors.
    arrow(ax, (17.0, 11.95), (59.1, 36.4), color=RED, lw=1.25,
          ls=(0, (4, 2)), rad=-0.23, ms=10)
    text(ax, 42.8, 40.2, r"pattern keys $K^P$", size=9.0,
         color=RED, weight="bold")

    path(ax, [(18.7, 17.5), (43.2, 17.5), (43.2, 20.9), (51.0, 20.9)],
         color=TEAL, lw=1.0, ls=(0, (3, 2)))
    arrow(ax, (51.0, 20.9), (51.1, 20.9), color=TEAL, lw=1.0,
          ls=(0, (3, 2)), ms=8)
    text(ax, 43.6, 18.6, r"$G,\ M^G,\ M^S$", size=8.8,
         color=TEAL, weight="bold")

    fig.subplots_adjust(left=0.006, right=0.994, bottom=0.02, top=0.985)
    return fig


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig = build_figure()
    for ext in ("pdf", "svg"):
        fig.savefig(OUT.with_suffix(f".{ext}"), facecolor=WHITE,
                    bbox_inches="tight", pad_inches=0.04)
    fig.savefig(OUT.with_suffix(".png"), dpi=600, facecolor=WHITE,
                bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    print(f"wrote {OUT}.pdf/.svg/.png")


if __name__ == "__main__":
    main()
