#!/usr/bin/env python3
"""Four-module method figure: environment, labelling, PHAST-DP, report."""

from __future__ import annotations

from collections import deque
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "figures" / "raw"
OUT_PNG = ROOT / "figures" / "fig_method_flow.png"
OUT_PDF = ROOT / "figures" / "fig_method_flow.pdf"

W, H = 100.0, 46.0
FIG_W = 7.15

C_EDGE = "#2C2C2C"
C_BLUE = "#E7F1FB"
C_BLUE_E = "#7FA6D4"
C_YEL = "#FFF4D4"
C_YEL_E = "#D4B45A"
C_PNK = "#FDECEA"
C_PNK_E = "#E07A6A"
C_GRN = "#E7F6EA"
C_GRN_E = "#7FBF86"
C_MUTED = "#333333"
C_RED = "#C0392B"


def knock_bg(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    h, w = arr.shape[:2]
    bg = arr[0, 0, :3].astype(np.int16)
    if bg.mean() > 225 or bg.mean() < 35:
        diff = np.abs(arr[..., :3].astype(np.int16) - bg).sum(axis=-1)
        near = diff < 36
        seen = np.zeros((h, w), dtype=bool)
        q: deque[tuple[int, int]] = deque()
        for x in range(w):
            q.append((0, x))
            q.append((h - 1, x))
        for y in range(h):
            q.append((y, 0))
            q.append((y, w - 1))
        while q:
            y, x = q.popleft()
            if seen[y, x] or not near[y, x]:
                continue
            seen[y, x] = True
            arr[y, x, 3] = 0
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx]:
                    q.append((ny, nx))
    return Image.fromarray(arr)


def flatten(im: Image.Image, hexcolor: str) -> Image.Image:
    h = hexcolor.lstrip("#")
    rgb = tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
    bg = Image.new("RGBA", im.size, rgb + (255,))
    return Image.alpha_composite(bg, im.convert("RGBA"))


def rbox(ax, x, y, w, h, fc, ec, lw=1.15, rad=0.45, z=2, ls="-"):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle=f"round,pad=0,rounding_size={rad}",
            facecolor=fc,
            edgecolor=ec,
            linewidth=lw,
            linestyle=ls,
            zorder=z,
        )
    )


def arrow(ax, p0, p1):
    ax.add_patch(
        FancyArrowPatch(
            p0,
            p1,
            arrowstyle="-|>",
            mutation_scale=11,
            linewidth=1.25,
            color="#444444",
            zorder=5,
            shrinkA=0,
            shrinkB=0,
        )
    )


def put_img(ax, im, x, y, w, h):
    ax.imshow(im, extent=(x, x + w, y, y + h), zorder=4, interpolation="lanczos")


def txt(ax, x, y, s, size=6.2, weight="normal", color=C_MUTED, ha="left", va="center"):
    ax.text(x, y, s, fontsize=size, fontweight=weight, color=color, ha=ha, va=va, zorder=6, linespacing=1.2)


def badge(ax, x, y, n, ec):
    ax.add_patch(Circle((x, y), 1.15, fc="white", ec=ec, lw=1.0, zorder=6))
    txt(ax, x, y, str(n), size=7.2, weight="bold", ha="center")


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "mathtext.fontset": "stix",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_W * H / W), dpi=220)
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")

    env = Image.open(RAW / "methodology_prep" / "factory.jpg").convert("RGB")
    icons = {
        "human": knock_bg(RAW / "figure1_assets" / "icon_human_onwhite.png"),
        "machine": knock_bg(RAW / "methodology_prep" / "icon_machine.png"),
        "material": knock_bg(RAW / "figure1_assets" / "icon_material_onwhite.png"),
        "agv": knock_bg(RAW / "figure1_assets" / "icon_agv_onwhite.png"),
    }

    for i, (x, w, fc, ec, title) in enumerate(
        [
            (1.2, 23.8, C_BLUE, C_BLUE_E, "Environment"),
            (27.2, 23.2, C_YEL, C_YEL_E, "Data processing"),
            (52.6, 23.2, C_PNK, C_PNK_E, "PHAST-DP"),
            (78.0, 20.8, C_GRN, C_GRN_E, "Prediction report"),
        ]
    ):
        rbox(ax, x, 1.4, w, 43.2, fc, ec)
        badge(ax, x + 1.7, 42.2, i + 1, ec)
        txt(ax, x + 3.3, 42.2, title, size=7.6, weight="bold")

    arrow(ax, (25.1, 23.0), (27.0, 23.0))
    arrow(ax, (50.5, 23.0), (52.4, 23.0))
    arrow(ax, (75.9, 23.0), (77.8, 23.0))

    # ----- 1 Environment -----
    rbox(ax, 2.0, 24.6, 22.2, 15.2, "#111111", C_EDGE, lw=0.7, rad=0.25)
    put_img(ax, env, 2.15, 24.75, 21.9, 14.7)
    txt(ax, 13.1, 22.9, "Water-pipe digital twin", size=6.0, ha="center")
    txt(ax, 13.1, 21.0, "Controlled disturbances", size=6.0, weight="bold", ha="center")
    labels = [("human", "Human"), ("machine", "Machine"), ("material", "Material"), ("agv", "Logistics")]
    for i, (key, lab) in enumerate(labels):
        x = 2.5 + i * 5.5
        put_img(ax, flatten(icons[key], C_BLUE), x, 14.6, 4.6, 4.6)
        txt(ax, x + 2.3, 13.6, lab, size=5.4, ha="center")
    txt(ax, 13.1, 11.2, "Machines, workers, buffers,", size=5.6, ha="center", color="#555555")
    txt(ax, 13.1, 9.4, "gantries, and transport robots", size=5.6, ha="center", color="#555555")
    txt(ax, 13.1, 6.6, "One disturbance axis at a time", size=5.5, ha="center", color="#555555")
    txt(ax, 13.1, 4.6, "so bottleneck traces stay attributable", size=5.5, ha="center", color="#555555")

    # ----- 2 Data processing -----
    cards = [
        (33.2, "Minute windows", "Raw logs become a\nresource--time grid"),
        (24.6, "Process-informed labels", "Type-specific rules plus\npersistence filtering"),
        (16.0, "Short-pattern clustering", "Recurrent precursors,\nnot the bottleneck label"),
    ]
    for y, title, body in cards:
        rbox(ax, 28.2, y, 21.2, 7.4, "white", C_YEL_E, lw=0.8, rad=0.3)
        txt(ax, 29.1, y + 5.6, title, size=6.2, weight="bold")
        txt(ax, 29.1, y + 2.7, body, size=5.6, color="#444444", va="center")
    xs = [32.2, 35.4, 38.6, 41.8, 45.0]
    for a, b in zip(xs, xs[1:]):
        ax.plot([a, b], [6.4, 6.4], color="#8A8A8A", lw=0.9, zorder=3)
    cols = ["#5B8DEF", "#5B8DEF", "#E0C44A", "#E39B4A", "#E07A5F"]
    for x, c in zip(xs, cols):
        ax.add_patch(Circle((x, 6.4), 0.85, fc=c, ec="white", lw=0.4, zorder=4))
    txt(ax, 38.8, 4.2, "process · buffer · logistics", size=5.3, ha="center", color="#666666")

    # ----- 3 PHAST-DP -----
    rbox(ax, 53.5, 35.2, 21.4, 5.4, "white", C_PNK_E, lw=0.8, rad=0.3)
    txt(ax, 64.2, 37.9, "Grouped resource embedding", size=6.1, weight="bold", ha="center")
    txt(ax, 64.2, 36.2, "queue · stall · logistics · type", size=5.3, ha="center", color="#555555")

    branches = [
        (53.6, "#5B8DEF", "Temporal", "one resource\nover time"),
        (60.6, "#E39B4A", "Graph", "neighbours\n+ patterns"),
        (67.6, "#7B6BB5", "Semantic", "similar, not\nonly adjacent"),
    ]
    for x, c, title, body in branches:
        rbox(ax, x, 22.2, 6.6, 11.6, "white", c, lw=0.9, rad=0.28)
        ax.add_patch(Rectangle((x, 31.2), 6.6, 2.6, fc=c, ec=c, zorder=3))
        txt(ax, x + 3.3, 32.5, title, size=5.5, weight="bold", ha="center", color="white")
        txt(ax, x + 3.3, 26.4, body, size=5.1, ha="center", color="#444444")
    txt(ax, 64.2, 20.2, "Pattern keys condition geographic attention", size=5.4, ha="center", color="#7A4038")
    txt(ax, 64.2, 18.4, "so delayed propagation can be learned", size=5.4, ha="center", color="#7A4038")
    rbox(ax, 53.5, 8.6, 21.4, 8.0, "white", C_PNK_E, lw=0.8, rad=0.3)
    txt(ax, 64.2, 14.6, "Prediction heads", size=6.1, weight="bold", ha="center")
    txt(ax, 64.2, 12.4, "Station event  ·  process cause", size=5.5, ha="center")
    txt(ax, 64.2, 10.6, "Remaining order time", size=5.5, ha="center")

    # ----- 4 Output -----
    outs = [
        (31.6, "Station", "Which resource constrains\nthroughput"),
        (23.2, "Onset and duration", "When it starts and\nhow long it persists"),
        (14.8, "Process cause", "Shortage, transport delay,\nstarvation, or queue buildup"),
        (6.4, "Remaining order time", "Line-level consequence\nof the current state"),
    ]
    for y, title, body in outs:
        rbox(ax, 79.0, y, 18.8, 7.6, "white", C_GRN_E, lw=0.8, rad=0.28)
        txt(ax, 80.0, y + 5.7, title, size=6.2, weight="bold", color=C_RED)
        txt(ax, 80.0, y + 2.8, body, size=5.4, color="#444444")

    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(OUT_PDF, dpi=300)
    fig.savefig(OUT_PNG, dpi=220)
    plt.close(fig)
    print(f"wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
