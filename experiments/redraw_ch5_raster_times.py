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

from paper_plot_style import LABEL_SIZE, LEGEND_SIZE, TICK_SIZE, TITLE_SIZE, apply as apply_paper_style

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
TRUE_CSV = ROOT / "experiments/data/key_device_main_aligned.csv"
TRUE_COLOR = "black"
# Research palette card: steel / light blue / yellow / coral / olive.
METHOD_PRED = {
    "PHGST-DP": "#46788E",
    "XGBoost": "#78B7C9",
    "LSTM": "#F6E093",
    "BTGCN": "#E58B7B",
    "BSTAN": "#97B319",
}


def load_true_duration() -> tuple[np.ndarray, np.ndarray]:
    """Authoritative GT on absolute ``t_index`` (30..260) for PNG-aligned redraws."""
    window, _t_index, true_dur, _pred = load_main_aligned()
    return window + 30.0, true_dur


def load_main_aligned() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Per-window CSV for the shared key-device episode.

    ``window`` is the paper display index (``t_index - 30``, range 0..230).
    """
    with TRUE_CSV.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    window = np.array([float(r["window"]) for r in rows])
    t_index = np.array([float(r["t_index"]) for r in rows])
    true_dur = np.array([float(r["true_dur"]) for r in rows])
    pred_dur = np.array([float(r["pred_dur"]) for r in rows])
    assert len(window) == 231 and np.array_equal(window, np.arange(231))
    assert np.array_equal(t_index, window + 30.0)
    return window, t_index, true_dur, pred_dur


def tindex_to_window_series(
    x_tindex: np.ndarray, y: np.ndarray, n_windows: int = 231
) -> tuple[np.ndarray, np.ndarray]:
    """Map PNG-calibrated ``t_index`` traces onto integer display windows."""
    windows = np.arange(n_windows, dtype=float)
    x_w = np.asarray(x_tindex, dtype=float) - 30.0
    y = np.asarray(y, dtype=float)
    out = np.full(n_windows, np.nan)
    for i, w in enumerate(windows):
        m = np.isfinite(y) & (x_w >= w - 0.5) & (x_w < w + 0.5)
        if m.any():
            out[i] = float(np.nanmedian(y[m]))
    return windows, out

apply_paper_style()
plt.rcParams.update(
    {
        "axes.linewidth": 1.0,
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


def _style_trace_ax(
    ax,
    *,
    xlabel: bool = True,
    ylabel: bool = True,
    xlim: tuple[float, float] = (0, 150),
) -> None:
    ax.set_xlim(*xlim)
    ax.set_ylim(-0.8, 21)
    ax.set_yticks([0, 5, 10, 15, 20])
    if ylabel:
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


def _plot_true_window(ax, window: np.ndarray, true_dur: np.ndarray) -> None:
    (true_line,) = ax.plot(
        window, true_dur, color=TRUE_COLOR, lw=1.35, label="True", zorder=5,
        solid_capstyle="round", solid_joinstyle="round",
    )
    true_line.set_path_effects([pe.Stroke(linewidth=2.3, foreground="white"), pe.Normal()])


def _extract_colored(
    im: np.ndarray,
    series: dict[str, tuple[np.ndarray, str]],
    legend: tuple[int, int, int, int],
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Recover series on the archived PNG ``t_index`` axis (labels 50..250)."""
    box = spine_box(im)
    x_map = calibrate_x(im, box, [50, 100, 150, 200, 250])
    y_map = calibrate_y(im, box, [20, 17.5, 15, 12.5, 10, 7.5, 5, 2.5, 0])
    all_targets = [t for t, _ in series.values()]
    out: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for name, (target, _) in series.items():
        out[name] = pack_series(im, box, target, x_map, y_map, legend=legend, all_targets=all_targets)
    return out


def redraw_entity() -> None:
    """Side-by-side entity/start traces on relative window index 0..150.

    True and PHGST-DP (Start≤5) come from ``key_device_main_aligned.csv``.
    Other arms are recovered from the archived eval PNGs (``t_index`` axis),
    then remapped to ``window = t_index - 30`` and drawn from that series.
    """
    window, _t_index, true_dur, pred_dur = load_main_aligned()

    im_ent = np.array(Image.open(ROOT / "experiments/data/key_device_entity_source.png").convert("RGB"))
    im_start = np.array(Image.open(ROOT / "experiments/data/key_device_start_source.png").convert("RGB"))
    legend = (1250, 1970, 80, 215)
    ent_t = _extract_colored(im_ent, ENTITY_SERIES, legend)
    start_t = _extract_colored(im_start, START_SERIES, legend)

    # Remap ablation / start-cap PNG traces onto the CSV window grid.
    ent_w: dict[str, tuple[np.ndarray, np.ndarray]] = {
        "PHGST-DP": (window, pred_dur),
    }
    for name in ("MachineOnly", "NoCross", "NoInfo"):
        ent_w[name] = tindex_to_window_series(*ent_t[name])

    start_w: dict[str, tuple[np.ndarray, np.ndarray]] = {
        "Start$\\leq5$": (window, pred_dur),
    }
    for name in ("Start$\\leq10$", "Start$\\leq15$"):
        start_w[name] = tindex_to_window_series(*start_t[name])

    # Persist the window-indexed series used for the figure.
    series_csv = ROOT / "experiments/data/key_device_entity_series.csv"
    with series_csv.open("w", encoding="utf-8", newline="") as fh:
        fields = [
            "window", "true_dur", "PHGST-DP", "MachineOnly", "NoCross", "NoInfo",
            "Start_le5", "Start_le10", "Start_le15",
        ]
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        def _cell(v: float) -> str:
            return "" if not np.isfinite(v) else f"{float(v):.6g}"

        for i, w in enumerate(window):
            writer.writerow(
                {
                    "window": int(w),
                    "true_dur": _cell(true_dur[i]),
                    "PHGST-DP": _cell(pred_dur[i]),
                    "MachineOnly": _cell(ent_w["MachineOnly"][1][i]),
                    "NoCross": _cell(ent_w["NoCross"][1][i]),
                    "NoInfo": _cell(ent_w["NoInfo"][1][i]),
                    "Start_le5": _cell(pred_dur[i]),
                    "Start_le10": _cell(start_w["Start$\\leq10$"][1][i]),
                    "Start_le15": _cell(start_w["Start$\\leq15$"][1][i]),
                }
            )

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.15), sharey=True)
    ax = axes[0]
    _plot_true_window(ax, window, true_dur)
    for name, (_, color) in ENTITY_SERIES.items():
        x, y = ent_w[name]
        ax.plot(x, y, color=color, lw=1.45 if name == "PHGST-DP" else 1.2,
                ls=ENTITY_STYLES[name], label=name, zorder=2)
    _style_trace_ax(ax, xlabel=True, ylabel=True, xlim=(0, 150))
    ax.set_title("(a) Multi-entity ablations (Start$\\leq5$)", loc="left", fontsize=TITLE_SIZE)
    ax.legend(loc="upper left", fontsize=LEGEND_SIZE, frameon=False, ncol=1)

    ax = axes[1]
    _plot_true_window(ax, window, true_dur)
    for name, (_, color) in START_SERIES.items():
        x, y = start_w[name]
        ax.plot(x, y, color=color, lw=1.45 if name == "Start$\\leq5$" else 1.2,
                ls=START_STYLES[name], label=name, zorder=2)
    _style_trace_ax(ax, xlabel=True, ylabel=False, xlim=(0, 150))
    ax.set_title("(b) PHGST-DP under Start$\\leq5/10/15$", loc="left", fontsize=TITLE_SIZE)
    ax.legend(loc="upper left", fontsize=LEGEND_SIZE, frameon=False, ncol=1)
    ax.tick_params(labelleft=False)

    fig.suptitle(
        "num02_rollerbedCNCPipeIntersectionCuttingMachine_ws0 | "
        "n10_human1.0__episode_03",
        fontsize=TITLE_SIZE,
        y=1.02,
    )
    fig.tight_layout(w_pad=0.6)
    fig.savefig(FIG / "key_device_entity.pdf")
    fig.savefig(FIG / "key_device_entity.png", dpi=200)
    plt.close(fig)
    print(f"[redraw] key_device_entity (window 0..150; series -> {series_csv.name})")


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
    # Gantry and transport-robot rows are blank in this episode and are omitted.
    kept = [i for i, name in enumerate(DEVICES) if not name.startswith(("gantry", "robot"))]
    labels = [DEVICES[i] for i in kept]
    rows_src, cols = len(DEVICES), 231
    rh, cw = (bottom - top) / rows_src, (right - left) / cols
    code = np.zeros((len(kept), cols), dtype=int)
    for row, r in enumerate(kept):
        for c in range(cols):
            px = tuple(int(v) for v in im[int(top + (r + 0.5) * rh), int(left + (c + 0.5) * cw)])
            code[row, c] = min(range(3), key=lambda k: np.linalg.norm(np.array(px) - np.array((TN, TP, ORANGE)[k])))
    n_tp, n_orange = int((code == 1).sum()), int((code == 2).sum())
    f1 = 2 * n_tp / max(2 * n_tp + n_orange, 1)
    print(f"[redraw] state map rows={len(kept)} TP={n_tp} FP+FN={n_orange} F1={f1:.3f}")

    # Palette: TN gray; TP light blue; FP/FN red. The source stores FP and FN
    # as one colour, so green is not assigned to a separate class.
    tn_c, tp_c, err_c = "#D0D0D0", "#78B7C9", "#E58B7B"
    cmap = ListedColormap([tn_c, tp_c, err_c])
    # Relative window index (t_index - 30); single-column layout.
    short = [
        name.replace("num00_rotaryPipeAutomaticW_", "weld_")
        .replace("num01_weldingRobot_", "weldRobot_")
        .replace("num02_rollerbedCNCPipeInte_", "cutting_")
        .replace("num04_groovingMachineLarge_", "groove_")
        .replace("num08_workbench_", "bench_")
        for name in labels
    ]
    fig, ax = plt.subplots(figsize=(3.35, 3.05))
    ax.imshow(
        code, aspect="auto", cmap=cmap, vmin=0, vmax=2, interpolation="nearest",
        extent=[-0.5, 230.5, len(kept) - 0.5, -0.5],
    )
    ax.set_xlim(0, 150)
    ax.set_yticks(range(len(kept)))
    ax.set_yticklabels(short, fontsize=TICK_SIZE)
    ax.set_xlabel("Window index (60 s)", fontsize=LABEL_SIZE)
    ax.tick_params(axis="x", labelsize=TICK_SIZE)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(f"n10_human1.0__episode_03 | F1={f1:.3f} ↑", loc="left", fontsize=TITLE_SIZE)
    fig.legend(
        handles=[Patch(color=c, label=l) for c, l in
                 zip([tn_c, tp_c, err_c], ["TN", "TP", "FP/FN"])],
        loc="upper center", bbox_to_anchor=(0.58, 1.02), ncol=3,
        fontsize=LEGEND_SIZE, frameon=False, handlelength=1.1, columnspacing=0.9,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    for stem, dpi in (("all_devices_state_main.pdf", None), ("all_devices_state_main.png", 200)):
        dest = FIG / stem
        tmp = FIG / f"_{stem}.new"
        fig.savefig(tmp, dpi=dpi, format=stem.split(".")[-1])
        try:
            dest.unlink(missing_ok=True)
            tmp.replace(dest)
        except OSError:
            # Fall back if the destination is locked by a PDF viewer.
            alt = FIG / f"{stem}.new"
            if alt.exists():
                alt.unlink()
            tmp.replace(alt)
            print(f"[warn] could not replace {dest.name}; wrote {alt.name}")
    plt.close(fig)
    print("[redraw] all_devices_state_main (single-column, window 0..150)")


# --------------------------------------------------------------------------- #
# 3. key_device_models_aligned (PHGST-DP from CSV, baselines recovered)
# --------------------------------------------------------------------------- #
BASELINES = {
    "XGBoost": "key_device_b2_aligned.png",
    "LSTM": "key_device_b3_aligned.png",
    "BTGCN": "key_device_b4_aligned.png",
    "BSTAN": "key_device_b5_aligned.png",
}
# Crops recovered from the archived multi-panel PDF when the per-model PNGs are absent.
BASELINE_CROPS = {
    "XGBoost": "experiments/data/key_device_b_XGBoost.png",
    "LSTM": "experiments/data/key_device_b_LSTM.png",
    "BTGCN": "experiments/data/key_device_b_BTGCN.png",
    "BSTAN": "experiments/data/key_device_b_BSTAN.png",
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
    """Single-column overlay: (a) state and (b) duration for five methods."""
    with (ROOT / "experiments/data/key_device_main_aligned.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    phgst = {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}
    baselines = {}
    for name, png in BASELINES.items():
        path = FIG / png
        if not path.exists():
            path = ROOT / BASELINE_CROPS[name]
        baselines[name] = _extract_baseline(path)
    x = phgst["window"]
    methods = ("PHGST-DP", "XGBoost", "LSTM", "BTGCN", "BSTAN")
    state_pred = {
        "PHGST-DP": phgst["pred_state"],
        **{name: baselines[name]["state"][1] for name in BASELINES},
    }
    dur_pred = {
        "PHGST-DP": phgst["pred_dur"],
        **{name: baselines[name]["dur"][1] for name in BASELINES},
    }

    # Match Figure 6 (key_device_entity): same canvas and open-frame style.
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.15), sharex=False)

    def _open_frame(ax: plt.Axes) -> None:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color("#9AA3A8")
        ax.spines["left"].set_color("#9AA3A8")
        ax.tick_params(colors="#333333", labelsize=TICK_SIZE)
        ax.grid(alpha=0.3, lw=0.6)
        ax.set_axisbelow(True)

    ax = axes[0]
    ax.step(x, phgst["true_state"], where="post", color=TRUE_COLOR, lw=1.35, label="True", zorder=5)
    for name in methods:
        ax.step(
            x, state_pred[name], where="post",
            color=METHOD_PRED[name], lw=1.45 if name == "PHGST-DP" else 1.2,
            ls="--", label=name, zorder=2,
        )
    ax.set_xlim(0, 150)
    ax.set_ylim(-0.08, 1.08)
    ax.set_yticks([0, 1])
    ax.set_ylabel("State", fontsize=LABEL_SIZE)
    ax.set_xlabel("Window index (60 s)", fontsize=LABEL_SIZE)
    ax.set_title("(a) Next-window state", loc="left", fontsize=TITLE_SIZE)
    _open_frame(ax)

    ax = axes[1]
    (true_line,) = ax.plot(
        x, phgst["true_dur"], color=TRUE_COLOR, lw=1.35, label="True", zorder=5,
        solid_capstyle="round", solid_joinstyle="round",
    )
    true_line.set_path_effects([pe.Stroke(linewidth=2.3, foreground="white"), pe.Normal()])
    for name in methods:
        ax.plot(
            x, dur_pred[name],
            color=METHOD_PRED[name], lw=1.45 if name == "PHGST-DP" else 1.2,
            ls="--", label=name, zorder=2,
        )
    ax.set_xlim(0, 150)
    ax.set_ylim(-0.8, 21)
    ax.set_yticks([0, 5, 10, 15, 20])
    ax.set_ylabel("Duration (min)", fontsize=LABEL_SIZE)
    ax.set_xlabel("Window index (60 s)", fontsize=LABEL_SIZE)
    ax.set_title("(b) Duration", loc="left", fontsize=TITLE_SIZE)
    _open_frame(ax)

    axes[1].legend(
        handles=[Line2D([], [], color=TRUE_COLOR, lw=1.4, label="True")]
        + [Line2D([], [], color=METHOD_PRED[name], lw=1.25, ls="--", label=name) for name in methods],
        loc="upper right",
        ncol=1,
        frameon=False,
        fontsize=LEGEND_SIZE,
        handlelength=1.5,
        labelspacing=0.2,
        borderaxespad=0.25,
        handletextpad=0.35,
    )
    fig.tight_layout(w_pad=0.6)
    for stem, dpi in (("key_device_models_aligned.pdf", None), ("key_device_models_aligned.png", 300)):
        dest = FIG / stem
        tmp = FIG / f"_{stem}.new"
        fig.savefig(tmp, dpi=dpi, format=stem.split(".")[-1], facecolor="white")
        try:
            dest.unlink(missing_ok=True)
            tmp.replace(dest)
        except OSError:
            alt = FIG / f"{stem}.new"
            if alt.exists():
                alt.unlink()
            tmp.replace(alt)
            print(f"[warn] could not replace {dest.name}; wrote {alt.name}")
    plt.close(fig)
    print("[redraw] key_device_models_aligned (overlay, full-width, research palette)")


if __name__ == "__main__":
    redraw_entity()
    redraw_state_map()
    redraw_models_aligned()
