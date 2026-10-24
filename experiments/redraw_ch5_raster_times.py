#!/usr/bin/env python3
"""Redraw the three raster Chapter 5 figures with Times New Roman text.

``key_device_entity``, ``all_devices_state_main``, and the baseline panels of
``key_device_models_aligned`` only exist as PNG renders whose text is baked
in (their ``series.npz`` sources stayed on the eval server). Following the
precedent of ``plot_key_device_struct_split.py``, the series are recovered
from the PNGs by colour, axis geometry is calibrated from the tick/grid
pixels, and the figures are redrawn as vector PDFs. PHGST-DP's own traces in
the combined figure come from the exact exported CSV, not from pixels.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib import patheffects as pe
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
TRUE_CSV = ROOT / "experiments/data/key_device_main_aligned.csv"
TRUE_COLOR = "black"
PRED_COLOR = "#E5887B"


def load_true_duration() -> tuple[np.ndarray, np.ndarray]:
    """Authoritative GT for the shared key-device episode; continuous, no pixel gaps.

    X uses ``t_index`` (30..260), matching the archived eval PNG axes and the
    pixel-recovered prediction traces. The CSV ``window`` column is
    ``t_index - 30`` and must not be mixed with those series.
    """
    with TRUE_CSV.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    window = np.array([float(r["window"]) for r in rows])
    x = np.array([float(r["t_index"]) for r in rows])
    y = np.array([float(r["true_dur"]) for r in rows])
    assert len(x) == 231 and np.array_equal(window, np.arange(231))
    assert np.array_equal(x, window + 30.0)
    return x, y

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif", "serif"],
        "font.size": 10,
        "axes.linewidth": 1.0,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.03,
    }
)


# --------------------------------------------------------------------------- #
# Pixel-calibration helpers
# --------------------------------------------------------------------------- #
def _dark(im: np.ndarray) -> np.ndarray:
    return im.max(axis=2) < 70


def _clusters(idxs: np.ndarray, gap: int = 3) -> list[float]:
    out: list[list[int]] = []
    for i in idxs:
        if out and i - out[-1][-1] <= gap:
            out[-1].append(int(i))
        else:
            out.append([int(i)])
    return [float(np.mean(c)) for c in out]


def spine_box(im: np.ndarray) -> tuple[int, int, int, int]:
    """Outer axes rectangle (left, right, top, bottom) from the spine lines."""
    dark = _dark(im)
    h, w = dark.shape
    rows = np.where(dark.sum(axis=1) > w * 0.4)[0]
    cols = np.where(dark.sum(axis=0) > h * 0.35)[0]
    return int(cols.min()), int(cols.max()), int(rows.min()), int(rows.max())


def grid_cols(im: np.ndarray, box: tuple[int, int, int, int]) -> list[float]:
    left, right, top, bottom = box
    crop = im[top:bottom, left:right].astype(int)
    gray = (np.abs(crop[:, :, 0] - crop[:, :, 1]) < 8) & (np.abs(crop[:, :, 1] - crop[:, :, 2]) < 8)
    light = gray & (crop[:, :, 0] > 185) & (crop[:, :, 0] < 248)
    cnt = light.sum(axis=0)
    cols = np.where(cnt > (bottom - top) * 0.55)[0] + left
    return _clusters(cols)


def tick_rows(im: np.ndarray, box: tuple[int, int, int, int]) -> list[float]:
    left, _, top, bottom = box
    band = _dark(im)[top:bottom, left - 8 : left - 1]
    return [r + top for r in _clusters(np.where(band.any(axis=1))[0], gap=2)]


def pack_series(
    im: np.ndarray,
    box: tuple[int, int, int, int],
    target: np.ndarray | None,
    x_map: tuple[float, float],
    y_map: tuple[float, float],
    legend: tuple[int, int, int, int] | None = None,
    max_gap: int = 12,
    min_run: int = 8,
    all_targets: list[np.ndarray] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Median y per pixel column for one colour (``None`` = black), mapped to data units."""
    left, right, top, bottom = box
    ys, xs = np.mgrid[0 : im.shape[0], 0 : im.shape[1]]
    inside = (xs >= left + 2) & (xs <= right - 2) & (ys >= top + 2) & (ys <= bottom - 2)
    if legend is not None:
        lx0, lx1, ly0, ly1 = legend
        inside &= ~((xs >= lx0) & (xs <= lx1) & (ys >= ly0) & (ys <= ly1))
    rgb = im.astype(np.int16)
    if target is None:
        mask = (rgb.max(axis=2) < 45) & inside
    else:
        chroma = rgb.max(axis=2) - rgb.min(axis=2)
        dist = np.linalg.norm(rgb.astype(float) - target.astype(float), axis=2)
        mask = (chroma > 28) & (rgb.max(axis=2) > 50) & (dist < 78) & inside
        if all_targets is not None:
            # Assign each chromatic pixel to its nearest series colour so that
            # crossing traces do not leak into each other's columns.
            all_dist = np.stack(
                [np.linalg.norm(rgb.astype(float) - t.astype(float), axis=2) for t in all_targets],
                axis=-1,
            )
            order = np.argsort(all_dist, axis=-1)
            ti = next(i for i, t in enumerate(all_targets) if np.array_equal(t, target))
            nearest = order[..., 0] == ti
            second = np.take_along_axis(all_dist, order[..., 1:2], axis=-1)[..., 0]
            best = np.take_along_axis(all_dist, order[..., 0:1], axis=-1)[..., 0]
            mask &= nearest & (second - best > 12)
    px, py = xs[mask], ys[mask]
    x_grid = np.arange(left + 2, right - 1)
    dur = np.full(x_grid.shape, np.nan)
    for i, x in enumerate(x_grid):
        col = py[px == x]
        if len(col):
            dur[i] = float(np.median(col))
    valid = np.where(np.isfinite(dur))[0]
    if len(valid) < 2:
        return np.array([]), np.array([])
    filled = dur.copy()
    for a, b in zip(valid[:-1], valid[1:]):
        if 1 < b - a <= max_gap:
            filled[a + 1 : b] = np.linspace(dur[a], dur[b], b - a + 1)[1:-1]
    finite = np.isfinite(filled)
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
    yy = filled.copy()
    yy[~(finite & ~kill)] = np.nan
    xval = _lin(x_grid, *x_map)
    yval = _lin(yy, *y_map)
    return xval, yval


def _lin(px: np.ndarray, val_at_ref: float, px_ref: float, val_per_px: float) -> np.ndarray:
    return val_at_ref + (px - px_ref) * val_per_px


def calibrate_x(im: np.ndarray, box, labels: list[float]) -> tuple[float, float, float]:
    """Return (value at first gridline, its pixel, value per pixel).

    Endpoint calibration, so minor gridlines between the labelled ones do not
    disturb the mapping.
    """
    grids = [g for g in grid_cols(im, box) if box[0] + 5 < g < box[1] - 5]
    assert len(grids) >= 2, grids
    return labels[0], grids[0], (labels[-1] - labels[0]) / (grids[-1] - grids[0])


def calibrate_y(im: np.ndarray, box, labels_top_to_bottom: list[float]) -> tuple[float, float, float]:
    """Endpoint calibration; unlabelled minor ticks may sit between the labels."""
    ticks = tick_rows(im, box)
    assert len(ticks) >= 2, ticks
    return labels_top_to_bottom[0], ticks[0], (labels_top_to_bottom[-1] - labels_top_to_bottom[0]) / (ticks[-1] - ticks[0])


# --------------------------------------------------------------------------- #
# 1. key_device_entity (duration traces) — two panels:
#    (a) multi-entity ablations at Start≤5
#    (b) Full model Start≤5/10/15 on the same device/episode
# Pixel RGB targets stay on the archived PNG colours; display hex is vivid.
# --------------------------------------------------------------------------- #
# Palette card: orange #F26121, mid-blue #5BA7D9; vivid green/purple complements.
COLOR_ORANGE = "#F26121"
COLOR_MIDBLUE = "#5BA7D9"
COLOR_GREEN = "#00A651"
COLOR_PURPLE = "#9B2DCF"

ENTITY_SERIES = {
    "PHGST-DP": (np.array([31, 119, 180]), COLOR_MIDBLUE),
    "MachineOnly": (np.array([242, 97, 33]), COLOR_ORANGE),
    "NoCross": (np.array([24, 120, 96]), COLOR_GREEN),
    "NoInfo": (np.array([120, 72, 144]), COLOR_PURPLE),
}
ENTITY_STYLES = {
    "PHGST-DP": (0, (4, 1.6)),
    "MachineOnly": (0, (1.2, 1.1)),
    "NoCross": (0, (1, 1.3)),
    "NoInfo": (0, (3, 1.2, 1, 1.2)),
}
# Source PNG series names → display labels (RGB = matplotlib C0/C1/C2).
START_SERIES = {
    "Start$\\leq5$": (np.array([31, 119, 180]), COLOR_MIDBLUE),
    "Start$\\leq10$": (np.array([255, 127, 14]), COLOR_ORANGE),
    "Start$\\leq15$": (np.array([44, 160, 44]), COLOR_GREEN),
}
START_STYLES = {
    "Start$\\leq5$": (0, (4, 1.6)),
    "Start$\\leq10$": (0, (1.2, 1.1)),
    "Start$\\leq15$": (0, (3, 1.2, 1, 1.2)),
}


def _style_trace_ax(ax, xlabel: bool = True) -> None:
    ax.set_xlim(20, 270)
    ax.set_ylim(-0.8, 21)
    ax.set_yticks([0, 5, 10, 15, 20])
    ax.set_ylabel("Bottleneck duration (min)")
    if xlabel:
        ax.set_xlabel("Window index (60 s)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color("#9AA3A8")
    ax.spines["left"].set_color("#9AA3A8")
    ax.tick_params(colors="#333333")
    ax.set_axisbelow(True)
    ax.grid(alpha=0.3, lw=0.6)


def _plot_true(ax) -> None:
    true_x, true_y = load_true_duration()
    (true_line,) = ax.plot(
        true_x, true_y, color=TRUE_COLOR, lw=2.0, label="True", zorder=5,
        solid_capstyle="round", solid_joinstyle="round",
    )
    true_line.set_path_effects([pe.Stroke(linewidth=3.4, foreground="white"), pe.Normal()])


def _extract_colored(
    im: np.ndarray,
    series: dict[str, tuple[np.ndarray, str]],
    legend: tuple[int, int, int, int],
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    box = spine_box(im)
    x_map = calibrate_x(im, box, [50, 100, 150, 200, 250])
    y_map = calibrate_y(im, box, [20, 17.5, 15, 12.5, 10, 7.5, 5, 2.5, 0])
    all_targets = [t for t, _ in series.values()]
    out: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for name, (target, _) in series.items():
        out[name] = pack_series(im, box, target, x_map, y_map, legend=legend, all_targets=all_targets)
    return out


def redraw_entity() -> None:
    # Original rasters are extraction sources; outputs overwrite figures/*.
    im_ent = np.array(Image.open(ROOT / "experiments/data/key_device_entity_source.png").convert("RGB"))
    im_start = np.array(Image.open(ROOT / "experiments/data/key_device_start_source.png").convert("RGB"))
    legend = (1250, 1970, 80, 215)
    ent = _extract_colored(im_ent, ENTITY_SERIES, legend)
    start = _extract_colored(im_start, START_SERIES, legend)

    fig, axes = plt.subplots(2, 1, figsize=(10.0, 6.2), sharex=True)
    # (a) entity ablations, Start≤5
    ax = axes[0]
    _plot_true(ax)
    for name, (_, color) in ENTITY_SERIES.items():
        x, y = ent[name]
        ax.plot(x, y, color=color, lw=1.45 if name == "PHGST-DP" else 1.2,
                ls=ENTITY_STYLES[name], label=name, zorder=2)
    _style_trace_ax(ax, xlabel=False)
    ax.set_title("(a) Multi-entity ablations (Start$\\leq5$)", loc="left", fontsize=10)
    ax.legend(loc="upper right", fontsize=8, frameon=False, ncol=2)

    # (b) Full model across Start caps, same device/episode
    ax = axes[1]
    _plot_true(ax)
    for name, (_, color) in START_SERIES.items():
        x, y = start[name]
        ax.plot(x, y, color=color, lw=1.45 if name == "Start$\\leq5$" else 1.2,
                ls=START_STYLES[name], label=name, zorder=2)
    _style_trace_ax(ax, xlabel=True)
    ax.set_title(
        "(b) PHGST-DP under Start$\\leq5/10/15$ (same device and episode)",
        loc="left",
        fontsize=10,
    )
    ax.legend(loc="upper right", fontsize=8, frameon=False, ncol=2)

    fig.suptitle(
        "num02_rollerbedCNCPipeIntersectionCuttingMachine_ws0 | "
        "n10_human1.0__episode_03",
        fontsize=9,
        y=1.01,
    )
    fig.tight_layout()
    fig.savefig(FIG / "key_device_entity.pdf")
    fig.savefig(FIG / "key_device_entity.png", dpi=200)
    plt.close(fig)
    print("[redraw] key_device_entity (entity + start panels)")


# --------------------------------------------------------------------------- #
# 2. all_devices_state_main (next-window state heatmap)
# --------------------------------------------------------------------------- #
DEVICES = [
    "num00_rotaryPipeAutomaticW_ws0",
    "num00_rotaryPipeAutomaticW_ws1",
    "num01_weldingRobot_ws0",
    "num02_rollerbedCNCPipeInte_ws0",
    "num04_groovingMachineLarge_ws0",
    "num08_workbench_ws0",
    "num08_workbench_ws1",
    "gantry_0",
    "gantry_1",
    "gantry_2",
    "gantry_3",
    "robot_0",
    "robot_1",
    "robot_2",
    "robot_3",
]
TN, TP, ORANGE = (242, 242, 242), (34, 123, 113), (242, 97, 33)


def redraw_state_map() -> None:
    im = np.array(Image.open(ROOT / "experiments/data/all_devices_state_main_source.png").convert("RGB"))
    left, right, top, bottom = spine_box(im)
    rows, cols = len(DEVICES), 231
    rh, cw = (bottom - top) / rows, (right - left) / cols
    code = np.zeros((rows, cols), dtype=int)
    for r in range(rows):
        for c in range(cols):
            px = tuple(int(v) for v in im[int(top + (r + 0.5) * rh), int(left + (c + 0.5) * cw)])
            code[r, c] = min(range(3), key=lambda k: np.linalg.norm(np.array(px) - np.array((TN, TP, ORANGE)[k])))
    n_tp, n_orange = int((code == 1).sum()), int((code == 2).sum())
    f1 = 2 * n_tp / max(2 * n_tp + n_orange, 1)
    print(f"[redraw] state map cells TP={n_tp} FP+FN={n_orange} F1={f1:.3f}")

    cmap = ListedColormap(["#f2f2f2", "#97B319", "#E5887B", "#E5887B"])
    fig, ax = plt.subplots(figsize=(11, 0.35 * rows + 1.6))
    ax.imshow(
        code, aspect="auto", cmap=cmap, vmin=0, vmax=3, interpolation="nearest",
        extent=[29.5, 260.5, rows - 0.5, -0.5],
    )
    ax.set_yticks(range(rows))
    ax.set_yticklabels(DEVICES, fontsize=7)
    ax.set_xlabel("window index (60 s)")
    ax.legend(
        handles=[Patch(color=c, label=l) for c, l in
                 zip(["#f2f2f2", "#97B319", "#E5887B", "#E5887B"], ["TN", "TP", "FP", "FN"])],
        loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=4, fontsize=8, frameon=False,
    )
    ax.set_title(
        f"12_3_start5 | n10_human1.0__episode_03 | next-window bottleneck state, F1={f1:.3f}",
        fontsize=9, pad=22,
    )
    fig.tight_layout()
    fig.savefig(FIG / "all_devices_state_main.pdf")
    fig.savefig(FIG / "all_devices_state_main.png", dpi=200)
    plt.close(fig)
    print("[redraw] all_devices_state_main")


# --------------------------------------------------------------------------- #
# 3. key_device_models_aligned (PHGST-DP from CSV, baselines recovered)
# --------------------------------------------------------------------------- #
BASELINES = {
    "XGBoost": "key_device_b2_aligned.png",
    "LSTM": "key_device_b3_aligned.png",
    "BTGCN": "key_device_b4_aligned.png",
    "BSTAN": "key_device_b5_aligned.png",
}


def _sub_boxes(im: np.ndarray) -> list[tuple[int, int, int, int]]:
    dark = _dark(im)
    h, w = dark.shape
    rows = _clusters(np.where(dark.sum(axis=1) > w * 0.4)[0], gap=2)
    cols = _clusters(np.where(dark.sum(axis=0) > h * 0.35)[0], gap=2)
    left, right = int(cols[0]), int(cols[-1])
    return [(left, right, int(rows[i]), int(rows[i + 1])) for i in range(0, len(rows) - 1, 2)]


def _extract_baseline(png: Path) -> dict[str, tuple[np.ndarray, np.ndarray, str]]:
    im = np.array(Image.open(png).convert("RGB"))
    state_box, dur_box = _sub_boxes(im)
    x_map = calibrate_x(im, state_box, [0, 50, 100, 150, 200])
    sy_map = calibrate_y(im, state_box, [1, 0])
    dy_map = calibrate_y(im, dur_box, [20, 15, 10, 5, 0])

    # Predicted colour: the dominant chromatic colour that is not the true blue.
    rgb = im.astype(int)
    chroma = rgb.max(axis=2) - rgb.min(axis=2)
    sel = rgb[(chroma > 60) & (rgb.max(axis=2) > 60)].reshape(-1, 3)
    dist_blue = np.linalg.norm(sel - np.array([31, 119, 180]), axis=1)
    pred = sel[dist_blue > 90]
    q = Counter(map(tuple, (pred // 24 * 24).tolist()))
    target = np.array(q.most_common(1)[0][0]) + 12
    color = "#%02x%02x%02x" % tuple(int(v) for v in target)

    out = {}
    for key, box, y_map in (("state", state_box, sy_map), ("dur", dur_box, dy_map)):
        lx = (box[1] - box[0])
        legend = (box[0] + int(0.5 * lx), box[1] - 2, box[2] + 4, box[2] + int(0.22 * (box[3] - box[2])))
        x, y = pack_series(im, box, target, x_map, y_map, legend=legend, max_gap=18, min_run=4)
        win = np.round(x).astype(int)
        keep = (win >= 0) & (win <= 230)
        agg: dict[int, list[float]] = {}
        for wi, yi in zip(win[keep], y[keep]):
            if np.isfinite(yi):
                agg.setdefault(int(wi), []).append(float(yi))
        xs = np.arange(231)
        ys = np.array([np.median(agg[w]) if w in agg else np.nan for w in xs])
        finite = np.isfinite(ys)
        ys = np.interp(xs, xs[finite], ys[finite])
        if key == "state":  # binary trace: remove antialiasing mid-levels
            ys = (ys > 0.5).astype(float)
        out[key] = (xs, ys, color)
    return out


def redraw_models_aligned() -> None:
    with (ROOT / "experiments/data/key_device_main_aligned.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    phgst = {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}
    baselines = {name: _extract_baseline(FIG / png) for name, png in BASELINES.items()}

    fig = plt.figure(figsize=(7.2, 9.47))
    outer = fig.add_gridspec(3, 2, hspace=0.55, wspace=0.16,
                             left=0.085, right=0.985, top=0.94, bottom=0.045)

    def draw_pair(cell, title, true_s, pred_s, true_d, pred_d, pred_color, *, zoom=False):
        sub = cell.subgridspec(2, 1, hspace=0.35, height_ratios=[1, 1.45])
        state, dur = fig.add_subplot(sub[0]), fig.add_subplot(sub[1])
        x = np.arange(len(true_s))
        for ax in (state, dur):
            if zoom:
                ax.set_xlim(20, 115)
                ax.set_xticks([20, 40, 60, 80, 100, 115])
            else:
                ax.set_xlim(-11.5, 241.5)
                ax.set_xticks([0, 50, 100, 150, 200])
                if zoom is False and title.startswith("PHGST"):
                    ax.axvspan(20, 115, facecolor="#efefef", edgecolor="none", zorder=0)
            ax.grid(alpha=0.22, linewidth=0.55)
            ax.set_axisbelow(True)
            ax.tick_params(labelsize=7.2)
        state.step(x, true_s, where="post", color=TRUE_COLOR, lw=1.05)
        state.step(x, pred_s, where="post", color=pred_color, lw=0.95, ls="--")
        state.set_ylim(-0.07, 1.07)
        state.set_yticks([0, 1])
        state.set_ylabel("State", fontsize=7.5, labelpad=2)
        state.set_title(title, fontsize=8.8, pad=4)
        dur.plot(x, true_d, color=TRUE_COLOR, lw=1.05)
        dur.plot(x, pred_d, color=pred_color, lw=0.95, ls="--")
        dur.set_ylim(-1, 21)
        dur.set_yticks([0, 5, 10, 15, 20])
        dur.set_ylabel("Duration (min)", fontsize=7.5, labelpad=2)
        dur.set_xlabel("Window (60 s)", fontsize=7.5, labelpad=3)

    w = phgst["window"]
    draw_pair(outer[0, 0], "PHGST-DP: full trajectory",
              phgst["true_state"], phgst["pred_state"], phgst["true_dur"], phgst["pred_dur"], PRED_COLOR)
    draw_pair(outer[0, 1], "PHGST-DP: event detail",
              phgst["true_state"], phgst["pred_state"], phgst["true_dur"], phgst["pred_dur"], PRED_COLOR, zoom=True)
    cells = [(outer[1, 0], "XGBoost"), (outer[1, 1], "LSTM"),
             (outer[2, 0], "BTGCN"), (outer[2, 1], "BSTAN")]
    for cell, name in cells:
        b = baselines[name]
        draw_pair(cell, name, phgst["true_state"], b["state"][1],
                  phgst["true_dur"], b["dur"][1], PRED_COLOR)
    fig.legend(
        handles=[Line2D([], [], color=TRUE_COLOR, lw=1.1, label="True"),
                 Line2D([], [], color=PRED_COLOR, lw=1.0, ls="--", label="Predicted")],
        loc="upper center", ncol=2, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, 1.0),
    )
    fig.savefig(FIG / "key_device_models_aligned.pdf", facecolor="white")
    fig.savefig(FIG / "key_device_models_aligned.png", dpi=300, facecolor="white")
    plt.close(fig)
    print("[redraw] key_device_models_aligned")


if __name__ == "__main__":
    redraw_entity()
    redraw_state_map()
    redraw_models_aligned()
