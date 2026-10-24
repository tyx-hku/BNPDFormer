#!/usr/bin/env python3
"""Chapter 5 experiment figures per 第五章实验图表重构方案.md (v2).

Uses only exported metrics under experiments/data and bottleneck_eval caches.
Does not invent missing distance bins, disturbance intervals, or baseline
efficiency numbers. Palette: #46788E / #78B7C9 / #F6E093 / #E58B7B / #97B319.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(__file__).resolve().parent / "data"
FIG = ROOT / "figures"
PLOT_DATA = DATA / "plot_data"
EVENTS = DATA / "main_event_metrics_dev_tyx_29655ba.csv"
SUMMARY = DATA / "bottleneck_eval_summary.csv"
BASELINE = DATA / "baseline_metrics_common_archived.csv"
LABELS = DATA / "label_validity_dev_tyx_8767583.json"
PER_DEVICE = (
    ROOT
    / "_isaac_factory/source/isaaclab_tasks/isaaclab_tasks/direct/hc_factory"
    / "PDFormer/libcity/cache/bottleneck_eval/bestmodel_start5_seed42/per_device.csv"
)

STEEL, LIGHT, YELLOW, CORAL, OLIVE = "#46788E", "#78B7C9", "#F6E093", "#E58B7B", "#97B319"
INK = "#243028"
BEST_BG = "#D9E7F4"
ALT_BG = "#DDEBCF"

STARTS = (5, 10, 15)
RUNS = {
    "Full": "bestmodel_start{s}_seed42",
    "NoGraph": "ablation_nograph_start{s}_seed42",
    "NoGroup": "ablation_nogroup_start{s}_seed42",
    "NoCross": "entity_nocross_start{s}_min8_cold_ep50_seed42",
    "NoInfo": "entity_noinfo_start{s}_min8_cold_ep50_seed42",
    "MachineOnly": "entity_machineonly_start{s}_min8_cold_ep50_seed42",
    "NoCluster": "ablation_nocluster_start{s}_seed42",
    "NoPattern": "struct_nopattern_start{s}_min8_cold_ep50_seed42",
    "NoSplit": "struct_nosplit_start{s}_min8_cold_ep50_seed42",
    "NoFarBoost": "full_nofarboost_start{s}_seed42",
    "Stage1": "full_farboost_start{s}_seed42",
}
BASELINE_MAP = {"B2": "XGBoost", "B3": "LSTM", "B4": "BTGCN", "B5": "BSTAN"}
MODEL_STYLE = {
    "PHGST-DP": dict(color=STEEL, marker="o", lw=2.0, ms=6.5),
    "XGBoost": dict(color=OLIVE, marker="s", lw=1.2, ms=5.5),
    "LSTM": dict(color=CORAL, marker="^", lw=1.2, ms=5.5),
    "BTGCN": dict(color=LIGHT, marker="D", lw=1.2, ms=5.0),
    "BSTAN": dict(color="#C4A35A", marker="v", lw=1.2, ms=5.5),
}

# Reported manuscript values; archived baseline sample alignment is pending.
# The 2026-10-24 comparison protocol targets the main 5,354-window manifest.
# Duration MAE = detected-event duration MAE (min); Remain MAE from regression table.
MAIN = {
    "PHGST-DP": {
        5: dict(report_f1=0.804, upcoming=0.542, dur_mae=1.863, state20=0.525, cause_r=0.967, remain=9.600),
        10: dict(report_f1=0.778, upcoming=0.535, dur_mae=1.788, state20=0.589, cause_r=0.965, remain=9.270),
        15: dict(report_f1=0.768, upcoming=0.537, dur_mae=1.716, state20=0.610, cause_r=0.978, remain=8.910),
    },
    "XGBoost": {
        5: dict(report_f1=0.702, upcoming=0.060, dur_mae=3.264, state20=0.373, cause_r=0.988, remain=5.231),
        10: dict(report_f1=0.611, upcoming=0.041, dur_mae=3.210, state20=0.337, cause_r=0.988, remain=5.231),
        15: dict(report_f1=0.577, upcoming=0.039, dur_mae=3.170, state20=0.322, cause_r=0.988, remain=5.231),
    },
    "LSTM": {
        5: dict(report_f1=0.583, upcoming=0.099, dur_mae=3.855, state20=0.295, cause_r=0.920, remain=10.593),
        10: dict(report_f1=0.477, upcoming=0.112, dur_mae=3.768, state20=0.262, cause_r=0.930, remain=10.607),
        15: dict(report_f1=0.461, upcoming=0.102, dur_mae=3.615, state20=0.260, cause_r=0.922, remain=9.009),
    },
    "BTGCN": {
        5: dict(report_f1=0.669, upcoming=0.046, dur_mae=3.322, state20=0.372, cause_r=0.882, remain=19.343),
        10: dict(report_f1=0.579, upcoming=0.045, dur_mae=3.238, state20=0.359, cause_r=0.900, remain=18.102),
        15: dict(report_f1=0.518, upcoming=0.054, dur_mae=3.121, state20=0.323, cause_r=0.900, remain=12.829),
    },
    "BSTAN": {
        5: dict(report_f1=0.687, upcoming=0.095, dur_mae=3.565, state20=0.379, cause_r=0.952, remain=14.704),
        10: dict(report_f1=0.609, upcoming=0.057, dur_mae=3.533, state20=0.365, cause_r=0.951, remain=13.850),
        15: dict(report_f1=0.534, upcoming=0.044, dur_mae=3.422, state20=0.335, cause_r=0.935, remain=13.557),
    },
}

# Strict report recall by onset distance (Start≤15). Only published values.
# Full: text §comparison; NoFarBoost >10: decoder table; NoPattern bins: delay table.
DIST_BINS = {
    "Full": {"≤5": 0.574, "6–10": 0.522, ">10": 0.433},
    "NoFarBoost": {">10": 0.240},
    "NoPattern": {"6–10": 0.396, ">10": 0.163},
}

# Efficiency p50 (ms) from tab:efficiency.
LATENCY = {
    5: dict(forward=3.52, report=4.75),
    10: dict(forward=3.53, report=4.77),
    15: dict(forward=3.49, report=4.72),
}

# True-event composition recovered from who_recall × n_true_who integers.
EVENT_COMPOSITION = {
    5: dict(upcoming=336, ongoing=766, n_true=1102),
    10: dict(upcoming=604, ongoing=768, n_true=1372),
    15: dict(upcoming=708, ongoing=770, n_true=1478),
}
N_WINDOWS = {"train": 20826, "val": 4331, "test": 5354}
N_EPISODES = {"train": 140, "val": 28, "test": 36}
N_STATIONS = 15


def _style() -> None:
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif", "serif"],
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
    })


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _save(fig: plt.Figure, stem: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    base = FIG / stem
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.03)
    fig.savefig(base.with_suffix(".svg"), bbox_inches="tight", pad_inches=0.03)
    fig.savefig(base.with_suffix(".png"), dpi=600, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print(f"[plot] wrote {base.with_suffix('.pdf')}")


def _f(row: dict[str, str], key: str) -> float:
    value = float(row[key])
    if not np.isfinite(value):
        raise ValueError(f"non-finite {key} in {row.get('run')}")
    return value


def _index(rows: list[dict[str, str]], key: str = "run") -> dict[str, dict[str, str]]:
    out = {row[key]: row for row in rows}
    if len(out) != len(rows):
        raise ValueError(f"duplicate {key}")
    return out


def _load() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict]:
    events = _index(_read_csv(EVENTS))
    summary = _index(_read_csv(SUMMARY))
    for arm, pattern in RUNS.items():
        for start in STARTS:
            run = pattern.format(s=start)
            if run not in events or run not in summary:
                raise KeyError(f"missing {arm} start {start}: {run}")
    full5 = events[RUNS["Full"].format(s=5)]
    assert abs(_f(full5, "report_f1") - 0.8041144901610018) < 1e-12
    assert int(full5["n_test_windows"]) == 5354
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    return events, summary, labels


def plot_dataset_composition() -> None:
    """Fig 5-2: split sizes + Upcoming/Ongoing/No-event composition."""
    rows = []
    for split in ("train", "val", "test"):
        rows.append({
            "split": split,
            "episodes": N_EPISODES[split],
            "windows": N_WINDOWS[split],
        })
    total_pairs = N_WINDOWS["test"] * N_STATIONS
    for start, comp in EVENT_COMPOSITION.items():
        no_event = total_pairs - comp["n_true"]
        rows.append({
            "split": f"test_start{start}",
            "upcoming": comp["upcoming"],
            "ongoing": comp["ongoing"],
            "no_event": no_event,
            "n_true_who": comp["n_true"],
            "n_window_resource_pairs": total_pairs,
        })
    _write_csv(PLOT_DATA / "dataset_composition.csv", rows)

    fig = plt.figure(figsize=(7.4, 3.15))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 1.35], wspace=0.38)

    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[0, 1])
    ax2 = fig.add_subplot(gs[0, 2])

    splits = ["train", "val", "test"]
    x = np.arange(3)
    ep = [N_EPISODES[s] for s in splits]
    win = [N_WINDOWS[s] for s in splits]
    ax0.bar(x, ep, color=[STEEL, LIGHT, OLIVE], width=0.62, edgecolor="none")
    for xi, v in zip(x, ep):
        ax0.text(xi, v + 2, str(v), ha="center", va="bottom", fontsize=8)
    ax0.set_xticks(x)
    ax0.set_xticklabels(["Train", "Val", "Test"])
    ax0.set_ylabel("Episodes")
    ax0.set_title("(a) Episodes", loc="left")
    ax0.set_ylim(0, max(ep) * 1.18)

    ax1.bar(x, win, color=[STEEL, LIGHT, OLIVE], width=0.62, edgecolor="none")
    for xi, v in zip(x, win):
        ax1.text(xi, v + 400, f"{v:,}", ha="center", va="bottom", fontsize=7.5)
    ax1.set_xticks(x)
    ax1.set_xticklabels(["Train", "Val", "Test"])
    ax1.set_ylabel("Windows")
    ax1.set_title("(a′) Windows", loc="left")
    ax1.set_ylim(0, max(win) * 1.18)

    # 100% stacked horizontal bars of window–resource pairs.
    y = np.arange(3)
    labels_y = [f"Start ≤{s}" for s in STARTS]
    up = np.array([EVENT_COMPOSITION[s]["upcoming"] for s in STARTS], dtype=float)
    on = np.array([EVENT_COMPOSITION[s]["ongoing"] for s in STARTS], dtype=float)
    none = np.array([total_pairs - EVENT_COMPOSITION[s]["n_true"] for s in STARTS], dtype=float)
    tot = up + on + none
    up_p, on_p, none_p = 100 * up / tot, 100 * on / tot, 100 * none / tot
    ax2.barh(y, none_p, color="#E8E4DC", height=0.55, label="No-event", edgecolor="none")
    ax2.barh(y, on_p, left=none_p, color=LIGHT, height=0.55, label="Ongoing", edgecolor="none")
    ax2.barh(y, up_p, left=none_p + on_p, color=STEEL, height=0.55, label="Upcoming", edgecolor="none")
    for yi, u, o, n in zip(y, up, on, none):
        ax2.text(100.2, yi, f"Up {int(u)} / On {int(o)} / None {int(n)}",
                 va="center", ha="left", fontsize=6.5, color=INK)
    ax2.set_yticks(y)
    ax2.set_yticklabels(labels_y)
    ax2.set_xlim(0, 118)
    ax2.set_xlabel("Share of window–resource pairs (%)")
    ax2.set_title("(b) Label composition (test)", loc="left")
    ax2.legend(frameon=False, fontsize=7, loc="lower right")
    ax2.invert_yaxis()

    for ax in (ax0, ax1, ax2):
        ax.grid(axis="x" if ax is ax2 else "y", color="#E6E1D8", lw=0.5)
        ax.set_axisbelow(True)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.88, bottom=0.16)
    _save(fig, "fig_dataset_composition")


def plot_range_response() -> None:
    """Grouped horizontal bars for three discrete onset-cap settings."""
    from matplotlib.patches import Patch
    from matplotlib.ticker import PercentFormatter
    from matplotlib import font_manager
    for path in Path("/System/Library/Fonts/Supplemental").glob("Times New Roman*.ttf"):
        font_manager.fontManager.addfont(str(path))
    _style()
    rows = _read_csv(DATA / "comparison_by_output_2026-10-24.csv")
    values = {(r["model"], int(r["start_cap"])): r for r in rows}
    _write_csv(PLOT_DATA / "range_response.csv", rows)
    models = ("PHGST-DP", "XGBoost", "LSTM", "BTGCN", "BSTAN")
    metrics = (
        ("report_f1", "(a) F1-score", "Higher is better", (0.0, 0.90)),
        ("upcoming", "(b) Upcoming recall", "Higher is better", (0.0, 0.65)),
        ("dur_mae", "(c) Duration MAE", "Minutes · lower is better", (0.0, 4.4)),
    )
    # Palette light blue / coral / yellow for Start ≤5 / 10 / 15.
    colors = (LIGHT, CORAL, YELLOW)
    bar_h = 0.22
    offsets = (-bar_h, 0.0, bar_h)
    fig, axes = plt.subplots(1, 3, figsize=(7.5, 3.35), sharey=True)
    y = np.arange(len(models))
    for ax, (key, title, xlabel, limits) in zip(axes, metrics):
        ax.axhspan(-0.48, 0.48, color="#EEF5F7", zorder=0)
        for j, cap in enumerate(STARTS):
            xs = [float(values[(m, cap)][key]) for m in models]
            ax.barh(
                y + offsets[j], xs, height=bar_h * 0.92, color=colors[j],
                edgecolor="none", zorder=3, label=f"Start ≤ {cap} min",
            )
        ax.set_xlim(limits)
        ax.set_ylim(len(models) - 0.55, -0.55)
        ax.set_yticks(y)
        ax.set_yticklabels(models, fontsize=10)
        ax.tick_params(axis="y", length=0, pad=6)
        ax.set_title(title, loc="left", fontsize=11, pad=9)
        ax.set_xlabel(xlabel, fontsize=9, labelpad=8)
        ax.spines["left"].set_visible(False)
        if key != "dur_mae":
            ax.xaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        ax.grid(axis="x", color="#E3E5E5", lw=0.5)
        ax.set_axisbelow(True)
    axes[0].get_yticklabels()[0].set_fontweight("bold")
    handles = [Patch(facecolor=c, edgecolor="none", label=f"Start ≤ {cap} min")
               for cap, c in zip(STARTS, colors)]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.55, 1.0),
               ncol=3, frameon=False, fontsize=10, handletextpad=0.4)
    fig.subplots_adjust(left=0.13, right=0.99, bottom=0.19, top=0.79, wspace=0.20)
    _save(fig, "fig_range_response")
    svg = FIG / "fig_range_response.svg"
    if svg.is_file():
        svg.write_text(
            "\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
            encoding="utf-8",
        )


def plot_delay_distance(events: dict) -> None:
    """Fig 5-5: delay-arm Upcoming recall curves + available onset-distance bins."""
    arms = ("Full", "NoPattern", "NoSplit", "NoFarBoost")
    colors = {"Full": STEEL, "NoPattern": CORAL, "NoSplit": LIGHT, "NoFarBoost": OLIVE}
    markers = {"Full": "o", "NoPattern": "s", "NoSplit": "^", "NoFarBoost": "D"}
    rows = []
    for arm in arms:
        for start in STARTS:
            val = _f(events[RUNS[arm].format(s=start)], "who_recall_upcoming")
            rows.append({"arm": arm, "start_cap": start, "who_recall_upcoming": val})
    for arm, bins in DIST_BINS.items():
        for bin_name, val in bins.items():
            rows.append({"arm": arm, "onset_bin": bin_name, "strict_report_recall": val})
    _write_csv(PLOT_DATA / "delay_distance.csv", rows)

    fig, (ax0, ax1) = plt.subplots(
        2, 1, figsize=(6.6, 4.35), height_ratios=[1.35, 1.0],
        gridspec_kw={"hspace": 0.42},
    )
    xs = np.array(STARTS, dtype=float)
    for arm in arms:
        ys = [_f(events[RUNS[arm].format(s=start)], "who_recall_upcoming") for start in STARTS]
        ax0.plot(xs, ys, color=colors[arm], marker=markers[arm],
                 lw=2.0 if arm == "Full" else 1.25, ms=6 if arm == "Full" else 5,
                 label=arm)
        for x, y in zip(xs, ys):
            ax0.text(x, y + 0.018, f"{y:.3f}", ha="center", fontsize=6.5, color=colors[arm])
    ax0.set_xticks(STARTS)
    ax0.set_xticklabels(["≤5", "≤10", "≤15"])
    ax0.set_xlabel("Start cap (min)")
    ax0.set_ylabel("Upcoming recall")
    ax0.set_ylim(0.05, 0.72)
    ax0.set_title("(a) Delay / decoder arms", loc="left")
    ax0.legend(frameon=False, ncol=4, fontsize=7.5, loc="upper right")
    ax0.grid(color="#E6E1D8", lw=0.5)

    # Lower: only published bins; do not invent missing NoFarBoost ≤5 / 6–10.
    bin_order = ["≤5", "6–10", ">10"]
    xpos = np.arange(len(bin_order), dtype=float)
    width = 0.28
    series = [("Full", STEEL, -width), ("NoFarBoost", OLIVE, 0.0), ("NoPattern", CORAL, width)]
    for name, color, offset in series:
        vals = [DIST_BINS.get(name, {}).get(b, np.nan) for b in bin_order]
        finite = [(x + offset, v) for x, v in zip(xpos, vals) if np.isfinite(v)]
        if not finite:
            continue
        ax1.bar([p[0] for p in finite], [p[1] for p in finite], width=width * 0.95,
                color=color, edgecolor="none", label=name)
        for px, pv in finite:
            ax1.text(px, pv + 0.015, f"{pv:.3f}", ha="center", fontsize=6.5, color=color)
    ax1.set_xticks(xpos)
    ax1.set_xticklabels(bin_order)
    ax1.set_xlabel("True onset distance (min), Start ≤15")
    ax1.set_ylabel("Strict report recall")
    ax1.set_ylim(0, 0.72)
    ax1.set_title("(b) Distance bins (published values only)", loc="left")
    ax1.legend(frameon=False, fontsize=7.5, loc="upper right")
    ax1.grid(axis="y", color="#E6E1D8", lw=0.5)
    fig.subplots_adjust(left=0.11, right=0.98, top=0.94, bottom=0.10)
    _save(fig, "fig_delay_distance")


def plot_remain_finetuning_matrix(summary: dict) -> None:
    """Stage-1 → stage-2 remaining-time MAE by production phase."""
    metrics = (
        ("Overall", "remain_mae"),
        ("Early", "remain_mae_early"),
        ("Middle", "remain_mae_middle"),
        ("Late", "remain_mae_late"),
    )
    stage1 = np.zeros((len(STARTS), len(metrics)))
    stage2 = np.zeros_like(stage1)
    rows_out = []
    for i, start in enumerate(STARTS):
        source_stage1 = RUNS["Stage1"].format(s=start)
        source_stage2 = RUNS["Full"].format(s=start)
        for j, (phase, key) in enumerate(metrics):
            before = _f(summary[source_stage1], key)
            after = _f(summary[source_stage2], key)
            stage1[i, j] = before
            stage2[i, j] = after
            rows_out.append({
                "arm": "Full",
                "start_cap": start,
                "phase": phase,
                "stage1_mae": before,
                "stage2_mae": after,
                "absolute_drop": before - after,
                "percent_drop": 100.0 * (before - after) / before,
                "source_stage1": source_stage1,
                "source_stage2": source_stage2,
            })

    published = {
        5: (10.925976792778325, 9.601598876066781),
        10: (11.213109243704304, 9.268456968835453),
        15: (9.716936303467548, 8.90945713298286),
    }
    for i, start in enumerate(STARTS):
        assert abs(stage1[i, 0] - published[start][0]) < 1e-9
        assert abs(stage2[i, 0] - published[start][1]) < 1e-9
    _write_csv(PLOT_DATA / "remain_dumbbell_full.csv", rows_out)

    reduction = stage1 - stage2
    cmap = LinearSegmentedColormap.from_list(
        "remain_gain",
        [(0.0, CORAL), (0.5, "#FAF8F3"), (0.70, "#D9E7F4"), (1.0, STEEL)],
    )
    norm = TwoSlopeNorm(vmin=-0.25, vcenter=0.0, vmax=3.6)
    fig, ax = plt.subplots(figsize=(6.6, 2.75))
    image = ax.imshow(reduction, cmap=cmap, norm=norm, aspect="auto")

    for i in range(len(STARTS)):
        for j in range(len(metrics)):
            before = stage1[i, j]
            after = stage2[i, j]
            drop = reduction[i, j]
            pct = 100.0 * abs(drop) / before
            arrow = "↓" if drop >= 0 else "↑"
            pct_text = f"{pct:.1f}%" if pct < 1.0 else f"{pct:.0f}%"
            text_color = "white" if drop >= 2.35 else INK
            ax.text(
                j, i - 0.10, f"{before:.2f} → {after:.2f}",
                ha="center", va="center", fontsize=8.2, color=text_color,
            )
            ax.text(
                j, i + 0.19, f"{arrow}{abs(drop):.2f} min ({pct_text})",
                ha="center", va="center", fontsize=7.5, fontweight="bold",
                color=text_color,
            )

    ax.set_xticks(np.arange(len(metrics)))
    ax.set_xticklabels([name for name, _ in metrics])
    ax.xaxis.tick_top()
    ax.set_yticks(np.arange(len(STARTS)))
    ax.set_yticklabels([f"Start ≤{start}" for start in STARTS])
    ax.tick_params(which="both", length=0, pad=5)
    ax.set_xticks(np.arange(-0.5, len(metrics), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(STARTS), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(
        "Stage 1 → Stage 2 remaining-time MAE (min; lower is better)",
        loc="left", pad=10, fontsize=9,
    )

    colorbar = fig.colorbar(image, ax=ax, fraction=0.032, pad=0.035)
    colorbar.set_label("MAE reduction (min)", fontsize=8)
    colorbar.set_ticks([-0.2, 0.0, 1.0, 2.0, 3.0])
    colorbar.ax.tick_params(labelsize=7, length=2)
    colorbar.outline.set_linewidth(0.5)
    fig.subplots_adjust(left=0.13, right=0.91, top=0.76, bottom=0.08)
    _save(fig, "fig_remain_dumbbell")


def plot_label_dots(labels: dict) -> None:
    """Fig 5-8: Cleveland dot plot for five label methods."""
    methods = ["Active Period", "Utilization", "Ops", "Queue-Wait", "TPM"]
    sep = {row["method"]: row for row in labels["separability"]["metrics"]}
    panels = [
        ("macro_f1", "Macro-F1 ↑", True),
        ("balanced_accuracy", "Balanced accuracy ↑", True),
        ("auroc", "AUROC ↑", True),
        ("silhouette", "Silhouette ↑", True),
        ("davies_bouldin", "Davies–Bouldin ↓", False),
        ("fisher_ratio", "Fisher ratio ↑", True),
    ]
    rows = []
    for m in methods:
        rows.append({"method": m, **{k: sep[m][k] for k, _, _ in panels},
                     "station_macro_f1": sep[m]["station_macro_f1"]})
    _write_csv(PLOT_DATA / "label_dots.csv", rows)

    fig, axes = plt.subplots(2, 3, figsize=(7.45, 4.55), sharey=True)
    y = np.arange(len(methods))
    for ax, (key, title, higher) in zip(axes.ravel(), panels):
        vals = np.array([sep[m][key] for m in methods], dtype=float)
        best = int(np.argmin(vals) if not higher else np.argmax(vals))
        for yi, v in enumerate(vals):
            ax.hlines(yi, min(vals.min() * 0.92, 0), v, color="#D8D3CB", lw=0.9)
            if yi == best:
                ax.scatter([v], [yi], s=42, color=STEEL, zorder=3)
            else:
                ax.scatter([v], [yi], s=38, facecolors="none", edgecolors=LIGHT,
                           linewidths=1.2, zorder=3)
            ax.text(v, yi + 0.28, f"{v:.3f}", ha="center", va="bottom", fontsize=6.5)
        ax.set_yticks(y)
        ax.set_yticklabels(methods)
        ax.set_title(title, loc="left", fontsize=8.5)
        ax.invert_yaxis()
        ax.grid(axis="x", color="#E6E1D8", lw=0.5)
        ax.set_axisbelow(True)
        pad = 0.08 * (vals.max() - vals.min() or 1.0)
        ax.set_xlim(vals.min() - pad, vals.max() + pad * 1.8)
    fig.tight_layout()
    _save(fig, "fig_label_dots")


def plot_cause_recall(labels: dict) -> None:
    """Fig 5-9: per-class cause recall + macro-F1 ranking."""
    methods = ["Active Period", "Utilization", "Ops", "Queue-Wait", "TPM"]
    cause = {row["method"]: row for row in labels["cause_comparison"]["metrics"]}
    classes = [
        ("transport_delay", "Transport delay"),
        ("material_shortage", "Material shortage"),
        ("starved_upstream", "Starved upstream"),
        ("queue_buildup", "Queue buildup"),
    ]
    style = {
        "Active Period": dict(color=STEEL, marker="o", filled=True),
        "Queue-Wait": dict(color=OLIVE, marker="s", filled=True),
        "Utilization": dict(color=LIGHT, marker="^", filled=False),
        "Ops": dict(color=CORAL, marker="D", filled=False),
        "TPM": dict(color="#C4A35A", marker="v", filled=False),
    }
    rows = []
    for m in methods:
        rows.append({
            "method": m,
            **{c: cause[m][c] for c, _ in classes},
            "macro_f1": cause[m]["macro_f1"],
        })
    _write_csv(PLOT_DATA / "cause_recall_dots.csv", rows)

    fig = plt.figure(figsize=(7.45, 3.35))
    gs = fig.add_gridspec(1, 5, width_ratios=[1, 1, 1, 1, 0.85], wspace=0.28)
    axes = [fig.add_subplot(gs[0, i]) for i in range(4)]
    ax_r = fig.add_subplot(gs[0, 4])
    y = np.arange(len(methods))
    for ax, (key, title) in zip(axes, classes):
        for yi, m in enumerate(methods):
            v = cause[m][key]
            st = style[m]
            ax.hlines(yi, 0.55, v, color="#D8D3CB", lw=0.9)
            if st["filled"]:
                ax.scatter([v], [yi], s=40, color=st["color"], marker=st["marker"], zorder=3)
            else:
                ax.scatter([v], [yi], s=38, facecolors="none", edgecolors=st["color"],
                           marker=st["marker"], linewidths=1.2, zorder=3)
            ax.text(v + 0.012, yi, f"{v:.3f}", va="center", fontsize=6.5)
        ax.set_yticks(y)
        ax.set_yticklabels(methods if ax is axes[0] else [])
        ax.set_xlim(0.55, 1.12)
        ax.set_title(title, loc="left", fontsize=8)
        ax.invert_yaxis()
        ax.grid(axis="x", color="#E6E1D8", lw=0.5)

    order = sorted(methods, key=lambda m: cause[m]["macro_f1"], reverse=True)
    y2 = np.arange(len(order))
    macros = [cause[m]["macro_f1"] for m in order]
    colors = [style[m]["color"] for m in order]
    ax_r.hlines(y2, 0.75, macros, color="#D8D3CB", lw=0.9)
    ax_r.scatter(macros, y2, c=colors, s=40, zorder=3)
    for yi, m, v in zip(y2, order, macros):
        ax_r.text(v + 0.008, yi, f"{v:.3f}", va="center", fontsize=6.5)
    ax_r.set_yticks(y2)
    ax_r.set_yticklabels(order, fontsize=7.5)
    ax_r.set_xlim(0.75, 1.02)
    ax_r.set_xlabel("Macro-F1")
    ax_r.set_title("Rank", loc="left", fontsize=8)
    ax_r.invert_yaxis()
    ax_r.grid(axis="x", color="#E6E1D8", lw=0.5)
    fig.subplots_adjust(left=0.12, right=0.98, top=0.88, bottom=0.14)
    _save(fig, "fig_cause_recall")


def plot_per_device_box() -> None:
    """Fig 5-10: per-device F1-score and Duration MAE by resource type."""
    raw = _read_csv(PER_DEVICE)
    short = {
        "num00_rotaryPipeAutomaticWeldingMachine_ws0": "weld0",
        "num00_rotaryPipeAutomaticWeldingMachine_ws1": "weld1",
        "num01_weldingRobot_ws0": "wRobot",
        "num02_rollerbedCNCPipeIntersectionCuttingMachine_ws0": "cut",
        "num04_groovingMachineLarge_ws0": "groove",
        "num08_workbench_ws0": "bench0",
        "num08_workbench_ws1": "bench1",
        "gantry_0": "g0", "gantry_1": "g1", "gantry_2": "g2", "gantry_3": "g3",
        "robot_0": "r0", "robot_1": "r1", "robot_2": "r2", "robot_3": "r3",
    }
    type_map = {"machine": "Machine", "gantry": "Gantry", "transport_robot": "AGV"}
    groups = ["Machine", "Gantry", "AGV"]
    rows_out = []
    by_group: dict[str, list[dict]] = {g: [] for g in groups}
    no_support = []
    for row in raw:
        n_true = int(float(row["n_true"]))
        g = type_map[row["type"]]
        name = short.get(row["device"], row["device"])
        entry = {
            "device": row["device"], "short": name, "type": g, "support": n_true,
            "f1": float(row["f1"]) if n_true > 0 else "",
            "dur_mae_union": float(row["dur_mae_union"]) if n_true > 0 else "",
        }
        rows_out.append(entry)
        if n_true > 0:
            by_group[g].append({
                "short": name,
                "f1": float(row["f1"]),
                "mae": float(row["dur_mae_union"]),
            })
        else:
            no_support.append(name)
    if any(r["support"] == 301 for r in rows_out if "cutting" in r["device"] or "Cutting" in r["device"]):
        pass
    else:
        cut = [r for r in rows_out if "Cutting" in r["device"]]
        if not cut or cut[0]["support"] != 301:
            raise ValueError("cutting-machine support is not 301")
    _write_csv(PLOT_DATA / "per_device_start5.csv", [
        {k: ("" if v == "" else v) for k, v in r.items()} for r in rows_out
    ])

    fig, axes = plt.subplots(1, 2, figsize=(7.35, 3.55))
    fill = {"Machine": STEEL, "Gantry": LIGHT, "AGV": OLIVE}
    for ax, metric, ylabel, lower in (
        (axes[0], "f1", "F1-score", False),
        (axes[1], "mae", "Union duration MAE (min)\nlower is better", True),
    ):
        data = [[d[metric] for d in by_group[g]] for g in groups]
        bp = ax.boxplot(
            data, positions=np.arange(len(groups)), widths=0.45, patch_artist=True,
            showfliers=False, medianprops=dict(color=INK, lw=1.1),
            whiskerprops=dict(color="#8A9296"), capprops=dict(color="#8A9296"),
            boxprops=dict(linewidth=0.8, edgecolor="#8A9296"),
        )
        for patch, g in zip(bp["boxes"], groups):
            patch.set_facecolor(fill[g])
            patch.set_alpha(0.28)
        rng = np.random.default_rng(42)
        for gi, g in enumerate(groups):
            pts = by_group[g]
            xs = gi + rng.uniform(-0.12, 0.12, size=len(pts))
            ys = [p[metric] for p in pts]
            ax.scatter(xs, ys, s=28, color=fill[g], zorder=3, edgecolors="none")
            for x, y, p in zip(xs, ys, pts):
                ax.text(x + 0.06, y, p["short"], fontsize=6, va="center", color=INK)
        ax.set_xticks(range(len(groups)))
        ax.set_xticklabels(groups)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", color="#E6E1D8", lw=0.5)
        ax.set_axisbelow(True)
    axes[0].set_title("(a)", loc="left")
    axes[1].set_title("(b)", loc="left")
    note = "No support (excluded from boxes): " + ", ".join(no_support) if no_support else ""
    fig.text(0.5, 0.01, note, ha="center", fontsize=7.5, color=INK)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, "fig_per_device_box")


def plot_latency_stack() -> None:
    """Fig 5-13: forward vs report−forward stacked bars."""
    rows = []
    for start, lat in LATENCY.items():
        extra = lat["report"] - lat["forward"]
        rows.append({
            "start_cap": start,
            "forward_p50_ms": lat["forward"],
            "report_p50_ms": lat["report"],
            "extra_p50_ms": extra,
            "note": "extra = report − forward (transfer + decode + materialize)",
        })
    _write_csv(PLOT_DATA / "latency_stack.csv", rows)

    fig, ax = plt.subplots(figsize=(6.2, 2.55))
    y = np.arange(len(STARTS))[::-1]
    fwd = [LATENCY[s]["forward"] for s in STARTS]
    rep = [LATENCY[s]["report"] for s in STARTS]
    extra = [r - f for r, f in zip(rep, fwd)]
    ax.barh(y, fwd, color=STEEL, height=0.48, label="Forward p50", edgecolor="none")
    ax.barh(y, extra, left=fwd, color=LIGHT, height=0.48,
            label="Report − forward p50", edgecolor="none")
    for yi, f, e, r in zip(y, fwd, extra, rep):
        ax.text(f / 2, yi, f"{f:.2f}", ha="center", va="center", fontsize=7.5, color="white")
        ax.text(f + e / 2, yi, f"{e:.2f}", ha="center", va="center", fontsize=7.5, color=INK)
        ax.text(r + 0.08, yi, f"total {r:.2f} ms", va="center", fontsize=7.5, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([f"Start ≤{s}" for s in STARTS])
    ax.set_xlabel("Batch-1 latency (ms)")
    ax.set_xlim(0, max(rep) + 1.4)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.grid(axis="x", color="#E6E1D8", lw=0.5)
    fig.tight_layout()
    _save(fig, "fig_latency_stack")


def write_ablation_table_csv(events: dict, summary: dict) -> None:
    """Export absolute ablation metrics for Table 5-4 (not a delta heatmap)."""
    arms = (
        "Full", "NoGraph", "NoGroup", "NoCross", "NoInfo", "MachineOnly",
        "NoCluster", "NoPattern", "NoSplit", "NoFarBoost",
    )
    groups = {
        "Full": "reference",
        "NoGraph": "graph", "NoGroup": "graph", "NoCross": "graph",
        "NoInfo": "graph", "MachineOnly": "graph",
        "NoCluster": "supervision",
        "NoPattern": "delay", "NoSplit": "decoder", "NoFarBoost": "decoder",
    }
    rows = []
    for arm in arms:
        for start in STARTS:
            er = events[RUNS[arm].format(s=start)]
            sr = summary[RUNS[arm].format(s=start)]
            rows.append({
                "group": groups[arm],
                "arm": arm,
                "start_cap": start,
                "report_f1": _f(er, "report_f1"),
                "who_recall_upcoming": _f(er, "who_recall_upcoming"),
                "dur_mae_union": _f(sr, "dur_mae_union"),
                "n_test_windows": 5354,
            })
    _write_csv(PLOT_DATA / "ablation_absolute.csv", rows)


def main() -> None:
    _style()
    events, summary, labels = _load()
    plot_dataset_composition()
    plot_range_response()
    plot_delay_distance(events)
    plot_remain_finetuning_matrix(summary)
    plot_label_dots(labels)
    plot_cause_recall(labels)
    plot_per_device_box()
    plot_latency_stack()
    write_ablation_table_csv(events, summary)
    print("[plot] Ch5 v2 figures complete")


if __name__ == "__main__":
    main()
