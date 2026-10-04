#!/usr/bin/env python3
"""PHAST-DP framework figure (v2): data construction on top, model and report below."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plot_fig_method_flow import flatten, knock_bg  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "figures" / "raw"
OUT = ROOT / "figures" / "fig_method_framework_v2"

W, H = 100.0, 56.0
FIG_W = 7.16

PALETTE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "green_1": "#DDF3DE",
    "green_2": "#AADCA9",
    "green_3": "#8BCF8B",
    "red_1": "#F6CFCB",
    "red_2": "#E9A6A1",
    "red_strong": "#B64342",
    "neutral": "#CFCECE",
    "highlight": "#FFD700",
    "teal": "#42949E",
    "violet": "#9A4D8E",
}
INK = "#272727"
MUTED = "#4D4D4D"
GRAY = "#767676"

STAGE = {
    "env": ("#F4F4F4", GRAY),
    "data": ("#F1F9F1", "#6FB86F"),
    "model": ("#EEF3FA", PALETTE["blue_secondary"]),
    "report": ("#FDF1F0", PALETTE["red_strong"]),
}
ENTITY = {
    "machine": PALETTE["blue_main"],
    "gantry": PALETTE["teal"],
    "robot": PALETTE["violet"],
    "human": "#C98B2B",
    "buffer": "#9E9E9E",
}
GOLD_BG, GOLD_E = "#FFF6CC", "#C9A400"


def rbox(ax, x, y, w, h, fc, ec, lw=1.0, rad=0.5, z=2, ls="-"):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad=0,rounding_size={rad}",
            facecolor=fc, edgecolor=ec, linewidth=lw, linestyle=ls, zorder=z,
        )
    )


def arrow(ax, p0, p1, color=MUTED, lw=1.1, ls="-", ms=9, rad=0.0, z=7):
    ax.add_patch(
        FancyArrowPatch(
            p0, p1, arrowstyle="-|>", mutation_scale=ms, linewidth=lw, linestyle=ls,
            color=color, zorder=z, shrinkA=0, shrinkB=0,
            connectionstyle=f"arc3,rad={rad}",
        )
    )


def txt(ax, x, y, s, size=5.2, weight="normal", color=INK, ha="left", va="center", z=8, **kw):
    ax.text(x, y, s, fontsize=size, fontweight=weight, color=color, ha=ha, va=va,
            zorder=z, linespacing=1.15, **kw)


def stage_title(ax, x, y, n, title, ec):
    ax.add_patch(Circle((x, y), 0.95, fc="white", ec=ec, lw=0.9, zorder=8))
    txt(ax, x, y - 0.05, str(n), size=5.8, weight="bold", ha="center", color=ec)
    txt(ax, x + 1.6, y, title, size=6.8, weight="bold")


def ctag(ax, x, y, label):
    """Contribution tag (C1/C2/C3), anchored at its right edge."""
    w, h = 3.4, 1.7
    rbox(ax, x - w, y - h / 2, w, h, PALETTE["blue_main"], PALETTE["blue_main"], lw=0.6, rad=0.5, z=9)
    txt(ax, x - w / 2, y - 0.05, label, size=5.0, weight="bold", ha="center", color="white", z=10)


def bolt(ax, x, y, s=1.0, color=PALETTE["red_strong"]):
    pts = np.array([[0.15, 1.0], [0.75, 1.0], [0.45, 0.55], [0.8, 0.55], [0.1, -0.2], [0.35, 0.4], [0.0, 0.4]])
    ax.add_patch(Polygon(pts * s + [x, y], closed=True, fc=color, ec="white", lw=0.3, zorder=9))


def put_img(ax, im, x, y, w, h, z=4):
    ax.imshow(im, extent=(x, x + w, y, y + h), zorder=z, interpolation="lanczos")


def strip(ax, x, y, w, h, cells, colors, edge="#BDBDBD"):
    n = len(cells)
    cw = w / n
    for i, c in enumerate(cells):
        ax.add_patch(Rectangle((x + i * cw, y), cw, h, fc=colors[c], ec=edge, lw=0.25, zorder=4))


# --------------------------------------------------------------------------- panels


def panel_environment(ax, icons):
    x0, x1, y0, y1 = 1.0, 20.0, 30.0, 55.0
    rbox(ax, x0, y0, x1 - x0, y1 - y0, *STAGE["env"])
    stage_title(ax, x0 + 1.5, y1 - 1.7, 1, "Digital-twin line", STAGE["env"][1])

    env = Image.open(RAW / "methodology_prep" / "factory.jpg").convert("RGB")
    iw = 17.0
    ih = iw * env.height / env.width
    rbox(ax, 2.0 - 0.15, 41.3 - 0.15, iw + 0.3, ih + 0.3, "#222222", "#222222", lw=0.5, rad=0.2, z=3)
    put_img(ax, env, 2.0, 41.3, iw, ih)
    txt(ax, 10.5, 40.0, "Isaac Sim water-pipe line", size=5.0, ha="center", color=MUTED)

    items = [("human", "Human"), ("machine", "Machine"), ("material", "Material"), ("agv", "Logistics")]
    for i, (key, lab) in enumerate(items):
        x = 2.3 + i * 4.3
        put_img(ax, flatten(icons[key], STAGE["env"][0]), x, 34.6, 3.6, 3.6)
        bolt(ax, x + 2.7, 37.0, s=1.25)
        txt(ax, x + 1.8, 33.6, lab, size=4.8, ha="center", color=MUTED)
    txt(ax, 10.5, 31.6, "one disturbance axis per episode", size=4.9, ha="center", color=PALETTE["red_strong"])


def panel_state(ax, rng):
    x0, x1, y0, y1 = 22.0, 42.0, 30.0, 55.0
    rbox(ax, x0, y0, x1 - x0, y1 - y0, *STAGE["data"])
    stage_title(ax, x0 + 1.5, y1 - 1.7, 2, "Multi-entity state", STAGE["data"][1])
    ctag(ax, x1 - 0.6, y1 - 1.7, "C1")

    counts = [("machine", 7), ("gantry", 4), ("robot", 4), ("human", 5), ("buffer", 18)]
    tx, ty, tw, th = 25.6, 35.0, 10.0, 12.6
    for k, off in enumerate([2.0, 1.0, 0.0]):
        base = rng.random((38, 30)) ** 2.2
        base[7:11, 18:28] += 0.7
        base[2:4, 12:24] += 0.6
        ax.imshow(
            np.clip(base, 0, 1), extent=(tx + off, tx + off + tw, ty + off, ty + off + th),
            cmap="Greens" if k < 2 else "Blues", vmin=0, vmax=1.3, zorder=3 + k,
            interpolation="nearest", aspect="auto",
        )
        ax.add_patch(Rectangle((tx + off, ty + off), tw, th, fc="none", ec=MUTED, lw=0.5, zorder=3.5 + k))

    yy = ty + th
    seg_h = th / 38
    for key, n in counts:
        ax.add_patch(Rectangle((tx - 1.0, yy - n * seg_h), 0.75, n * seg_h, fc=ENTITY[key], ec="white", lw=0.3, zorder=6))
        yy -= n * seg_h
    txt(ax, tx - 1.9, ty + th / 2, "38 resources", size=4.8, ha="center", color=MUTED, rotation=90)
    txt(ax, tx + tw / 2, ty - 1.0, "30 one-minute windows", size=4.8, ha="center", color=MUTED)
    txt(ax, tx + tw + 1.3, ty + th + 2.3, "27 ch.", size=4.8, ha="left", color=MUTED)

    ly = 46.6
    for key, lab in [("machine", "mach."), ("gantry", "gantry"), ("robot", "robot"), ("human", "human"), ("buffer", "buffer")]:
        ax.add_patch(Circle((38.6, ly), 0.45, fc=ENTITY[key], ec="none", zorder=6))
        txt(ax, 39.25, ly, lab, size=4.6, color=MUTED)
        ly -= 1.7
    txt(ax, 32.0, 31.6, r"$X_t\in\mathbb{R}^{30\times 38\times 27}$", size=5.6, ha="center")


def panel_labels(ax, rng):
    x0, x1, y0, y1 = 44.0, 71.0, 30.0, 55.0
    rbox(ax, x0, y0, x1 - x0, y1 - y0, *STAGE["data"])
    stage_title(ax, x0 + 1.5, y1 - 1.7, 3, "Process labels + clustering", STAGE["data"][1])
    ctag(ax, x1 - 0.6, y1 - 1.7, "C2")

    sx, sw, sh = 45.2, 13.6, 1.35
    cmap = {0: "white", 1: PALETTE["red_2"], 2: PALETTE["red_strong"], 3: "#EDEDED"}
    raw = [0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0]
    sus = [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    txt(ax, sx, 49.6, r"type rule $b^{\mathrm{raw}}$", size=5.0, weight="bold")
    strip(ax, sx, 47.6, sw, sh, raw, cmap)
    arrow(ax, (sx + sw / 2, 47.3), (sx + sw / 2, 45.9), lw=0.8, ms=6)
    txt(ax, sx + sw / 2 - 0.6, 46.6, "persistence", size=4.7, ha="right", color=MUTED)
    txt(ax, sx + sw / 2 + 0.6, 46.6, r"$m{=}8,\ g{=}1$", size=4.7, color=MUTED)
    strip(ax, sx, 44.2, sw, sh, [2 if c else 0 for c in sus], cmap)

    txt(ax, sx, 41.9, r"event target $(w,s,d)$", size=5.0, weight="bold")
    hist = [3] * 6
    fut = [0] * 4 + [2] * 9 + [0]
    cw = sw / 20
    strip(ax, sx, 39.6, sw, sh, hist + fut, cmap)
    bx = sx + 6 * cw
    ax.plot([bx, bx], [38.9, 41.3], color=INK, lw=0.8, zorder=6)
    txt(ax, sx + 3 * cw, 38.5, "history", size=4.6, ha="center", color=MUTED)
    s0, s1 = bx, bx + 4 * cw
    d1 = s1 + 9 * cw
    for a, b, lab in [(s0, s1, r"$s$"), (s1, d1, r"$d$")]:
        ax.plot([a, a, b, b], [38.9, 38.5, 38.5, 38.9], color=PALETTE["red_strong"], lw=0.6, zorder=6)
        txt(ax, (a + b) / 2, 37.7, lab, size=5.2, ha="center", color=PALETTE["red_strong"])
    txt(ax, sx, 35.6, "ongoing: hot at history end", size=4.7, color=MUTED)
    txt(ax, sx, 34.2, r"upcoming: $s>0$, $d\geq 8$ min", size=4.7, color=MUTED)

    cx, cy, cwid, chei = 60.4, 35.0, 9.8, 13.0
    rbox(ax, cx, cy, cwid, chei, "white", "#BFDDBF", lw=0.6, rad=0.3, z=3)
    txt(ax, cx + cwid / 2, 49.6, "short-pattern k-means", size=5.0, weight="bold", ha="center")
    centres = [(62.6, 45.0), (67.6, 45.6), (63.4, 38.6), (68.0, 39.4)]
    ccols = [PALETTE["blue_secondary"], PALETTE["teal"], PALETTE["violet"], "#9E9E9E"]
    for (mx, my), c in zip(centres, ccols):
        pts = rng.normal([mx, my], 0.85, size=(14, 2))
        ax.scatter(pts[:, 0], pts[:, 1], s=2.2, color=c, alpha=0.75, lw=0, zorder=5)
        ax.scatter([mx], [my], s=16, marker="*", color=c, edgecolor=INK, lw=0.35, zorder=6)
    txt(ax, cx + cwid / 2, 36.0, r"16 keys $K^P$ (length-3)", size=4.7, ha="center", color=MUTED)
    txt(ax, cx + cwid / 2, 33.6, "regimes, not labels", size=4.7, ha="center", color=MUTED, style="italic")


def panel_graph(ax):
    x0, x1, y0, y1 = 73.0, 99.0, 30.0, 55.0
    rbox(ax, x0, y0, x1 - x0, y1 - y0, *STAGE["data"])
    stage_title(ax, x0 + 1.5, y1 - 1.7, 4, "Heterogeneous graph", STAGE["data"][1])
    ctag(ax, x1 - 0.6, y1 - 1.7, "C1")

    my = 43.2
    mxs = [76.0 + i * 3.45 for i in range(7)]
    gys, rys, hys = 47.6, 38.6, 51.0
    gxs = [77.7 + i * 5.2 for i in range(4)]
    rxs = [77.7 + i * 5.2 for i in range(4)]
    hxs = [76.6 + i * 2.2 for i in range(5)]

    for a, b in zip(mxs, mxs[1:]):
        ax.plot([a, b], [my, my], color=INK, lw=1.0, zorder=4)
    for i, j in [(2, 3), (4, 5)]:
        ax.add_patch(FancyArrowPatch((mxs[i], my + 0.9), (mxs[j], my + 0.9), arrowstyle="-",
                                     connectionstyle="arc3,rad=-0.6", color=INK, lw=0.6, zorder=4))
    for i, gx in enumerate(gxs):
        for m in (min(2 * i, 6), min(2 * i + 1, 6)):
            ax.plot([gx, mxs[m]], [gys, my], color=ENTITY["gantry"], lw=0.55, ls=(0, (2.2, 1.2)), zorder=3)
    for i, rx in enumerate(rxs):
        for m in (min(2 * i, 6), min(2 * i + 1, 6)):
            ax.plot([rx, mxs[m]], [rys, my], color=ENTITY["robot"], lw=0.55, ls=(0, (2.2, 1.2)), zorder=3)
    for xs, yv, key in [(gxs, gys, "gantry"), (rxs, rys, "robot")]:
        ax.plot(xs, [yv] * len(xs), color=ENTITY[key], lw=0.5, ls=(0, (0.6, 1.0)), zorder=3)

    buf = []
    for i, mx in enumerate(mxs):
        buf.append((mx - 0.95, my - 1.75))
        buf.append((mx + 0.95, my - 1.75))
    buf += [(mxs[0] - 1.6, my + 1.5), (mxs[6] + 1.6, my + 1.5), (mxs[3] - 0.9, my + 1.9), (mxs[3] + 0.9, my + 1.9)]
    for bx, by in buf:
        mx = min(mxs, key=lambda v: abs(v - bx))
        ax.plot([bx, mx], [by, my], color="#B0B0B0", lw=0.45, zorder=3)
        ax.add_patch(Circle((bx, by), 0.38, fc=ENTITY["buffer"], ec="white", lw=0.2, zorder=5))

    for gx in gxs:
        ax.add_patch(Circle((gx, gys), 0.7, fc=ENTITY["gantry"], ec="white", lw=0.4, zorder=5))
    for rx in rxs:
        ax.add_patch(Circle((rx, rys), 0.7, fc=ENTITY["robot"], ec="white", lw=0.4, zorder=5))
    for hx in hxs:
        ax.add_patch(Rectangle((hx - 0.55, hys - 0.55), 1.1, 1.1, fc=ENTITY["human"], ec="white", lw=0.3, zorder=5))
    for i, mx in enumerate(mxs):
        ax.add_patch(Circle((mx, my), 1.05, fc=ENTITY["machine"], ec="white", lw=0.5, zorder=6))
        txt(ax, mx, my - 0.05, f"M{i + 1}", size=4.0, weight="bold", ha="center", color="white", z=7)

    ax.add_patch(FancyArrowPatch((hxs[4] + 0.6, hys), (mxs[5], my + 1.1), arrowstyle="-",
                                 connectionstyle="arc3,rad=-0.35", color=PALETTE["violet"], lw=0.7,
                                 ls=(0, (1.2, 0.9)), zorder=4))
    txt(ax, 88.4, 51.0, "semantic top-5", size=4.6, color=PALETTE["violet"])

    legend = [
        ("process", dict(color=INK, lw=1.0)),
        ("buffer", dict(color="#B0B0B0", lw=0.8)),
        ("handling", dict(color=MUTED, lw=0.7, ls=(0, (2.2, 1.2)))),
        ("weak", dict(color=MUTED, lw=0.7, ls=(0, (0.6, 1.0)))),
    ]
    for i, (lab, kw) in enumerate(legend):
        lx = 74.4 + i * 6.2
        ax.plot([lx, lx + 1.6], [35.0, 35.0], zorder=5, **kw)
        txt(ax, lx + 2.0, 35.0, lab, size=4.6, color=MUTED)
    txt(ax, 86.0, 32.7, r"geographic mask $M^G$: $<4$ hops", size=4.8, ha="center", color=MUTED)
    txt(ax, 86.0, 31.2, r"semantic mask $M^S$: top-5 trajectory corr.", size=4.8, ha="center", color=MUTED)


def panel_model(ax):
    x0, x1, y0, y1 = 22.0, 99.0, 1.0, 28.0
    rbox(ax, x0, y0, x1 - x0, y1 - y0, *STAGE["model"])
    stage_title(ax, x0 + 1.5, y1 - 1.7, 5, "PHAST-DP", STAGE["model"][1])
    txt(ax, 41.5, y1 - 1.75, "process-informed heterogeneous-graph Transformer", size=5.2, color=MUTED, style="italic")

    # grouped embedding
    ex, ew = 84.0, 14.0
    rbox(ax, ex, 3.0, ew, 21.0, "white", PALETTE["blue_secondary"], lw=0.8, rad=0.4, z=3)
    txt(ax, ex + ew / 2, 22.4, "Grouped embedding", size=5.6, weight="bold", ha="center")
    ctag(ax, ex + ew - 0.5, 24.0, "C1")
    groups = [("Queue", 4), ("Stall", 6), ("Logistics", 4), ("Shortage", 1), ("Context", 7), ("Type", 5)]
    for i, (g, d) in enumerate(groups):
        gy = 19.8 - i * 2.15
        rbox(ax, ex + 0.8, gy - 0.8, 7.0, 1.6, "#E4EDF8", "#9CB9DD", lw=0.5, rad=0.3, z=4)
        txt(ax, ex + 1.3, gy, g, size=4.8, color=INK)
        txt(ax, ex + 7.3, gy, str(d), size=4.8, ha="right", color=MUTED)
        ax.plot([ex + 7.8, ex + 10.0], [gy, 14.4], color="#9CB9DD", lw=0.45, zorder=3)
    ax.add_patch(Circle((ex + 11.0, 14.4), 1.1, fc="white", ec=PALETTE["blue_secondary"], lw=0.7, zorder=5))
    txt(ax, ex + 11.0, 14.35, "mean", size=4.3, ha="center", color=INK)
    txt(ax, ex + ew / 2, 5.9, r"$+\,E_{\mathrm{time}}+E_{\mathrm{lap}}+E_{\mathrm{node}}$", size=5.0, ha="center")
    txt(ax, ex + ew / 2, 4.2, r"$\rightarrow\ H^{(0)}$", size=5.2, ha="center")

    # encoder block
    bx0, bx1 = 41.0, 81.5
    rbox(ax, bx0, 3.0, bx1 - bx0, 21.0, "none", PALETTE["blue_secondary"], lw=0.8, rad=0.4, z=3,
         ls=(0, (3, 1.6)))
    txt(ax, bx0 + 1.0, 22.7, r"Encoder block $\times 5$  ($d=80$)", size=5.6, weight="bold")
    arrow(ax, (ex, 14.4), (bx1 + 0.1, 14.4))

    rx0, rx1 = 55.0, 80.0
    rows = [
        (20.0, GOLD_BG, GOLD_E, "Pattern attention",
         r"queue patch $P_{t,n}$ $\times$ activity keys $K^P$ $\rightarrow$ $C^P$"),
        (15.2, "white", PALETTE["teal"], "Geographic attention  (2 heads)",
         r"mask $M^G$;  keys $+\,C^P$  (delayed propagation)"),
        (10.4, "white", PALETTE["blue_secondary"], "Temporal attention  (4 heads)",
         "each resource across 30 windows"),
        (5.6, "white", PALETTE["violet"], "Semantic attention  (2 heads)",
         r"mask $M^S$;  similar but non-adjacent resources"),
    ]
    for yc, fc, ec, title, body in rows:
        rbox(ax, rx0, yc - 1.85, rx1 - rx0, 3.7, fc, ec, lw=0.9, rad=0.35, z=4)
        ax.add_patch(Rectangle((rx0 + 0.05, yc - 1.8), 0.7, 3.6, fc=ec, ec="none", zorder=5))
        txt(ax, rx0 + 1.4, yc + 0.75, title, size=5.2, weight="bold")
        txt(ax, rx0 + 1.4, yc - 0.85, body, size=4.7, color=MUTED)
    ctag(ax, rx1 - 0.3, 20.0 + 0.95, "C3")
    arrow(ax, (67.5, 18.1), (67.5, 17.1), color=GOLD_E, lw=1.0, ms=7)

    ax.plot([bx1 + 0.1, rx1 + 0.6], [14.4, 14.4], color=MUTED, lw=0.9, zorder=3)
    ax.plot([rx1 + 0.6, rx1 + 0.6], [5.6, 15.2], color=MUTED, lw=0.9, zorder=3)
    for yc in (15.2, 10.4, 5.6):
        arrow(ax, (rx1 + 0.6, yc), (rx1 + 0.05, yc), lw=0.8, ms=6)

    rbox(ax, 42.2, 11.6, 10.6, 5.2, "white", PALETTE["blue_secondary"], lw=0.7, rad=0.35, z=4)
    txt(ax, 47.5, 15.0, "Concat + project", size=5.0, weight="bold", ha="center")
    txt(ax, 47.5, 13.1, r"$[H_T\,\|\,H_G\,\|\,H_S]$", size=5.0, ha="center")
    rbox(ax, 42.2, 4.4, 10.6, 5.2, "white", PALETTE["blue_secondary"], lw=0.7, rad=0.35, z=4)
    txt(ax, 47.5, 7.8, "Add & Norm", size=5.0, weight="bold", ha="center")
    txt(ax, 47.5, 5.9, "+ feed-forward", size=5.0, ha="center")
    bus = 54.0
    ax.plot([bus, bus], [5.6, 15.2], color=MUTED, lw=0.9, zorder=3)
    for yc in (15.2, 10.4, 5.6):
        ax.plot([bus, rx0], [yc, yc], color=MUTED, lw=0.9, zorder=3)
    arrow(ax, (bus, 14.2), (52.85, 14.2), lw=0.8, ms=6)
    arrow(ax, (47.5, 11.6), (47.5, 9.65), lw=0.8, ms=6)

    # heads
    hx, hw = 23.0, 16.6
    rbox(ax, hx, 3.0, hw, 21.0, "white", PALETTE["blue_secondary"], lw=0.8, rad=0.4, z=3)
    txt(ax, hx + hw / 2, 22.6, "Multi-task heads", size=5.6, weight="bold", ha="center")
    arrow(ax, (42.2, 7.0), (hx + hw + 0.05, 7.0))
    heads = [
        (r"occurrence $p^{\mathrm{cont}}$ / $p^{\mathrm{onset}}$", "station event"),
        (r"start $\pi^{s}$,  duration $\hat d$", "when and how long"),
        (r"prefix $\hat p$,  occupancy $\hat O$", "dense future grid"),
        (r"cause $\hat c$,  remain $\hat\ell$", "graph-level pooling"),
    ]
    for i, (a, b) in enumerate(heads):
        hy = 19.6 - i * 3.6
        rbox(ax, hx + 0.8, hy - 1.5, hw - 1.6, 3.0, "#E4EDF8", "#9CB9DD", lw=0.5, rad=0.3, z=4)
        txt(ax, hx + 1.4, hy + 0.55, a, size=4.9)
        txt(ax, hx + 1.4, hy - 0.75, b, size=4.5, color=MUTED)
    rbox(ax, hx + 0.8, 3.7, hw - 1.6, 2.6, "#F4F4F4", GRAY, lw=0.5, rad=0.3, z=4, ls=(0, (2, 1)))
    txt(ax, hx + hw / 2, 5.0, "validation-controlled decoding", size=4.7, ha="center", color=MUTED)


def panel_report(ax):
    x0, x1, y0, y1 = 1.0, 20.0, 1.0, 28.0
    rbox(ax, x0, y0, x1 - x0, y1 - y0, *STAGE["report"])
    stage_title(ax, x0 + 1.5, y1 - 1.7, 6, "Bottleneck report", STAGE["report"][1])

    gx0, gx1 = 6.6, 18.8
    t0, t1 = -4.0, 20.0

    def tx(t):
        return gx0 + (t - t0) / (t1 - t0) * (gx1 - gx0)

    rows = [("Weld-2", 21.6, (0, 6), "ongoing"), ("Gantry-1", 19.4, (7, 15), "upcoming"), ("AGV-3", 17.2, None, "")]
    ax.add_patch(Rectangle((tx(t0), 15.9), tx(0) - tx(t0), 6.9, fc="#EDEDED", ec="none", zorder=3))
    for name, yv, span, kind in rows:
        txt(ax, 2.0, yv, name, size=4.8, color=INK)
        ax.plot([gx0, gx1], [yv, yv], color="#C8C8C8", lw=0.4, zorder=3)
        if span:
            fc = PALETTE["red_strong"] if kind == "ongoing" else PALETTE["red_2"]
            ax.add_patch(Rectangle((tx(span[0]), yv - 0.6), tx(span[1]) - tx(span[0]), 1.2, fc=fc,
                                   ec=PALETTE["red_strong"], lw=0.5, zorder=5))
    ax.plot([tx(0), tx(0)], [15.9, 22.8], color=INK, lw=0.8, zorder=6)
    txt(ax, tx(0), 23.4, "now", size=4.6, ha="center", color=INK)
    yb = 18.0
    for a, b, lab in [(0, 7, r"$\hat s$"), (7, 15, r"$\hat d$")]:
        ax.plot([tx(a), tx(a), tx(b), tx(b)], [yb + 0.35, yb, yb, yb + 0.35], color=PALETTE["red_strong"],
                lw=0.55, zorder=6)
        txt(ax, (tx(a) + tx(b)) / 2, yb - 0.75, lab, size=5.0, ha="center", color=PALETTE["red_strong"])
    txt(ax, (gx0 + gx1) / 2, 15.2, "future minutes (onset cap 5/10/15)", size=4.5, ha="center", color=MUTED)

    txt(ax, 2.0, 13.4, r"process cause $\hat c$", size=5.0, weight="bold")
    causes = [("Transport", 0.12), ("Shortage", 0.07), ("Starvation", 0.09), ("Queue", 0.72)]
    for i, (name, p) in enumerate(causes):
        cy = 11.6 - i * 1.55
        txt(ax, 2.0, cy, name, size=4.6, color=MUTED)
        ax.add_patch(Rectangle((8.2, cy - 0.5), 10.4, 1.0, fc="white", ec="#D0D0D0", lw=0.35, zorder=4))
        fc = PALETTE["red_strong"] if p == max(c[1] for c in causes) else PALETTE["red_1"]
        ax.add_patch(Rectangle((8.2, cy - 0.5), 10.4 * p, 1.0, fc=fc, ec="none", zorder=5))

    txt(ax, 2.0, 4.6, r"remaining order time $\hat\ell$", size=5.0, weight="bold")
    ax.add_patch(Rectangle((2.0, 2.4), 16.6, 1.1, fc="white", ec="#D0D0D0", lw=0.35, zorder=4))
    ax.add_patch(Rectangle((2.0, 2.4), 16.6 * 0.62, 1.1, fc=PALETTE["red_2"], ec="none", zorder=5))
    txt(ax, 2.0 + 16.6 * 0.62 + 0.4, 2.95, "12 min left", size=4.5, color=INK)


def build_figure():
    plt.rcParams.update(
        {
            "font.family": ["Arial", "DejaVu Sans", "sans-serif"],
            "mathtext.fontset": "custom",
            "mathtext.rm": "Arial",
            "mathtext.it": "Arial:italic",
            "mathtext.bf": "Arial:bold",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    rng = np.random.default_rng(7)
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_W * H / W))
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.set_aspect("equal")
    ax.axis("off")

    icons = {
        "human": knock_bg(RAW / "figure1_assets" / "icon_human_onwhite.png"),
        "machine": knock_bg(RAW / "methodology_prep" / "icon_machine.png"),
        "material": knock_bg(RAW / "figure1_assets" / "icon_material_onwhite.png"),
        "agv": knock_bg(RAW / "figure1_assets" / "icon_agv_onwhite.png"),
    }

    panel_environment(ax, icons)
    panel_state(ax, rng)
    panel_labels(ax, rng)
    panel_graph(ax)
    panel_model(ax)
    panel_report(ax)

    for xa, xb in [(20.05, 21.95), (42.05, 43.95), (71.05, 72.95)]:
        arrow(ax, (xa, 42.5), (xb, 42.5))
    arrow(ax, (91.0, 30.0), (91.0, 28.05))
    txt(ax, 91.8, 29.05, r"$X_t,\ G,\ M^G,\ M^S$", size=4.8, color=MUTED)
    arrow(ax, (65.3, 34.95), (65.3, 22.0), color=GOLD_E, lw=1.0)
    txt(ax, 64.8, 29.05, r"$K^P$", size=5.2, ha="right", color=GOLD_E, weight="bold")
    arrow(ax, (49.0, 33.3), (36.5, 24.1), color=PALETTE["red_strong"], lw=0.8, ls=(0, (3, 1.6)), ms=7, rad=0.08)
    txt(ax, 45.2, 29.05, "training targets", size=4.7, ha="left", color=PALETTE["red_strong"], style="italic")
    arrow(ax, (23.0, 14.0), (20.05, 14.0))

    fig.subplots_adjust(0, 0, 1, 1)
    return fig


def main() -> None:
    fig = build_figure()
    for ext in ("pdf", "png", "svg"):
        fig.savefig(OUT.with_suffix(f".{ext}"), dpi=300, facecolor="white")
    plt.close(fig)
    print(f"wrote {OUT}.pdf/.png")


if __name__ == "__main__":
    main()
