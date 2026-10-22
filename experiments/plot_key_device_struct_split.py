"""Split the structural key-device trace into two figures.

The source PNG is the original matplotlib export. Series are recovered from
their tab10 colours, then redrawn so red and orange are not on the same axes.
NoGraph and NoGroup are the heterogeneous-graph arms. NoCluster, NoPattern,
and NoSplit are the cause, delay-pattern, and decoder arms.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(
    r"D:\Capstone\isaac_factory\source\isaaclab_tasks\isaaclab_tasks"
    r"\direct\hc_factory\PDFormer\libcity\cache\bottleneck_eval\figures\key_device_struct.png"
)
OUT = ROOT / "figures"

# Spines and major ticks measured on the 2000x760 export.
X_TICK_PX, X_TICK_VAL, X_TICK_STEP = 377.5, 50.0, 359.0
Y_TICK_PX, Y_TICK_VAL, Y_TICK_STEP = 94.5, 20.0, 65.25
AX = (151, 1969, 69, 642)  # left, right, top, bottom
LEGEND = (1280, 1965, 75, 270)  # left, right, top, bottom

SERIES = {
    "PHGST-DP": np.array([31, 119, 180]),
    "NoCluster": np.array([255, 127, 14]),
    "NoGraph": np.array([44, 160, 44]),
    "NoGroup": np.array([214, 39, 40]),
    "NoPattern": np.array([148, 103, 189]),
    "NoSplit": np.array([140, 86, 75]),
}

GRAPH = ("PHGST-DP", "NoGraph", "NoGroup")
MECH = ("PHGST-DP", "NoCluster", "NoPattern", "NoSplit")
COLORS = {
    "PHGST-DP": "#5BA7D9",
    "NoGraph": "#2F9E5A",
    "NoGroup": "#7A5898",
    "NoCluster": "#7A5898",
    "NoPattern": "#2F9E5A",
    "NoSplit": "#FCB84D",
}
STYLES = {
    "PHGST-DP": (0, (4, 1.6)),
    "NoGraph": (0, (1.2, 1.1)),
    "NoGroup": (0, (3, 1.2, 1, 1.2)),
    "NoCluster": (0, (1.2, 1.1)),
    "NoPattern": (0, (3, 1.2, 1, 1.2)),
    "NoSplit": (0, (5, 1.4)),
}


def _window(x: np.ndarray) -> np.ndarray:
    return X_TICK_VAL + (x - X_TICK_PX) / X_TICK_STEP * 50.0


def _duration(y: np.ndarray) -> np.ndarray:
    return Y_TICK_VAL - (y - Y_TICK_PX) / Y_TICK_STEP * 2.5


def _extract(im: np.ndarray) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    h, w = im.shape[:2]
    left, right, top, bottom = AX
    ys, xs = np.mgrid[0:h, 0:w]
    inside = (xs >= left + 2) & (xs <= right - 2) & (ys >= top + 2) & (ys <= bottom - 2)
    legend = (xs >= LEGEND[0]) & (xs <= LEGEND[1]) & (ys >= LEGEND[2]) & (ys <= LEGEND[3])
    rgb = im.astype(np.int16)
    chroma = rgb.max(axis=2) - rgb.min(axis=2)
    dark = (rgb.max(axis=2) < 45) & inside & ~legend
    colored = (chroma > 28) & (rgb.max(axis=2) > 50) & inside & ~legend

    names = list(SERIES)
    targets = np.stack([SERIES[n] for n in names])
    pts = rgb[colored]
    dist = np.linalg.norm(pts[:, None, :] - targets[None, :, :], axis=2)
    order = np.argsort(dist, axis=1)
    best = order[:, 0]
    keep = (dist[np.arange(len(pts)), best] < 78) & (
        dist[np.arange(len(pts)), order[:, 1]] - dist[np.arange(len(pts)), best] > 12
    )
    px = xs[colored][keep]
    py = ys[colored][keep]
    lab = best[keep]

    out: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    x_grid = np.arange(left + 2, right - 1)

    def pack(mask: np.ndarray, max_gap: int = 12, min_run: int = 8) -> tuple[np.ndarray, np.ndarray]:
        sel_x, sel_y = px[mask], py[mask]
        dur = np.full(x_grid.shape, np.nan)
        for i, x in enumerate(x_grid):
            col = sel_y[sel_x == x]
            if len(col):
                dur[i] = float(np.median(col))
        valid = np.where(np.isfinite(dur))[0]
        if len(valid) < 2:
            return _window(x_grid), np.array([])
        filled = dur.copy()
        # Only close the short gaps left by the original dashed stroke.
        # Longer gaps are real breaks; bridging them draws a false diagonal.
        for a, b in zip(valid[:-1], valid[1:]):
            if 1 < b - a <= max_gap:
                filled[a + 1 : b] = np.linspace(dur[a], dur[b], b - a + 1)[1:-1]
        finite = np.isfinite(filled)
        # Drop isolated specks left by legend strokes and antialiased crossings.
        kill = np.zeros(len(filled), dtype=bool)
        i = 0
        while i < len(filled):
            if not finite[i]:
                i += 1
                continue
            j = i
            while j < len(filled) and finite[j]:
                j += 1
            if j - i < min_run:
                kill[i:j] = True
            i = j
        finite &= ~kill
        yy = filled.copy()
        yy[~finite] = np.nan
        return _window(x_grid), _duration(yy)

    true_x, true_y = xs[dark], ys[dark]
    px, py = true_x, true_y
    out["True"] = pack(np.ones(len(px), dtype=bool), max_gap=36, min_run=4)
    px_c, py_c, lab_c = xs[colored][keep], ys[colored][keep], best[keep]
    for i, name in enumerate(names):
        px, py = px_c, py_c
        out[name] = pack(lab_c == i)
    return out


def _draw(series: dict[str, tuple[np.ndarray, np.ndarray]], names: tuple[str, ...], out: Path) -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif", "serif"],
            "font.size": 10,
            "axes.linewidth": 1.0,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.03,
        }
    )
    fig, ax = plt.subplots(figsize=(7.2, 3.05))
    x, y = series["True"]
    ax.plot(x, y, color="black", lw=1.8, label="True", zorder=3)
    for name in names:
        xx, yy = series[name]
        ax.plot(xx, yy, color=COLORS[name], lw=1.45, ls=STYLES[name], label=name, zorder=2)
    ax.set_xlim(20, 270)
    ax.set_ylim(-1, 21)
    ax.set_xlabel("Window index (60 s)")
    ax.set_ylabel("Bottleneck duration (min)")
    ax.set_yticks([0, 5, 10, 15, 20])
    ax.grid(alpha=0.3, lw=0.6)
    ax.legend(loc="upper right", fontsize=8, frameon=False, ncol=1)
    fig.tight_layout()
    fig.savefig(out)
    fig.savefig(out.with_suffix(".png"), dpi=200)
    plt.close(fig)
    print(f"[plot] wrote {out}")


def main() -> None:
    im = np.array(Image.open(SRC).convert("RGB"))
    series = _extract(im)
    _draw(series, GRAPH, OUT / "key_device_struct_graph.pdf")
    _draw(series, MECH, OUT / "key_device_struct_mech.pdf")


if __name__ == "__main__":
    main()
