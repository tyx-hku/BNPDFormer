#!/usr/bin/env python3
"""Chapter 5 figures that can be drawn from the local exports.

Does not impute missing results. Skipped, because the inputs are not in the
local files: the fair five-model slope chart (common-manifest reevaluation is
still pending), the onset-distance decay curves, an Oracle confusion matrix,
and a disturbance/cause band on the case timeline.
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
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(__file__).resolve().parent / "data"
FIG = ROOT / "figures"
PLOT_DATA = DATA / "plot_data"
EVENTS = DATA / "main_event_metrics_dev_tyx_29655ba.csv"
SUMMARY = DATA / "bottleneck_eval_summary.csv"
LABELS = DATA / "label_validity_dev_tyx_8767583.json"
TRACE = DATA / "key_device_main_aligned.csv"
PER_DEVICE = (
    ROOT
    / "_isaac_factory/source/isaaclab_tasks/isaaclab_tasks/direct/hc_factory"
    / "PDFormer/libcity/cache/bottleneck_eval/bestmodel_start5_seed42/per_device.csv"
)

STEEL, LIGHT, YELLOW, CORAL, OLIVE = "#46788E", "#7BB7C9", "#F6E093", "#E5887B", "#97B319"
INK = "#243028"
DIV = LinearSegmentedColormap.from_list("delta", [CORAL, "#F7F4EF", YELLOW, "#E4EEF2", STEEL])
SEQ = LinearSegmentedColormap.from_list("seq", ["#F7F4EF", YELLOW, LIGHT, STEEL])

STARTS = (5, 10, 15)
GROUPS = (
    ("Graph", ("NoGraph", "NoGroup", "NoCross", "NoInfo", "MachineOnly")),
    ("Supervision", ("NoCluster",)),
    ("Delay", ("NoPattern",)),
    ("Decoder", ("NoSplit", "NoFarBoost")),
)
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
ARMS = [arm for _, names in GROUPS for arm in names]


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
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
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
    for table in (events, summary):
        for arm, pattern in RUNS.items():
            for start in STARTS:
                run = pattern.format(s=start)
                if run not in table:
                    raise KeyError(f"{arm} start {start} missing: {run}")
    for row in events.values():
        if int(row["n_test_windows"]) != 5354:
            raise ValueError(f"{row['run']} has {row['n_test_windows']} windows, expected 5354")
    # Anchors transcribed in the chapter, so a wrong column fails before drawing.
    full5 = events[RUNS["Full"].format(s=5)]
    assert abs(_f(full5, "report_f1") - 0.8041144901610018) < 1e-12
    assert abs(_f(full5, "who_recall_upcoming") - 0.5416666666666666) < 1e-12
    assert abs(_f(summary[RUNS["Full"].format(s=5)], "dur_mae_union") - 4.166337889200913) < 1e-9
    graph5 = events[RUNS["NoGraph"].format(s=5)]
    assert abs(_f(graph5, "who_recall_upcoming") - 0.10416666666666667) < 1e-12
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    return events, summary, labels


def plot_ablation_delta(events: dict, summary: dict) -> None:
    metrics = (
        ("report_f1", "Report F1", "ablation - Full", events),
        ("who_recall_upcoming", "Upcoming recall", "ablation - Full", events),
        ("dur_mae_union", "Union dur. MAE", "Full - ablation", summary),
    )
    columns = [(start, key, title, sign) for start in STARTS for key, title, sign, _ in metrics]
    matrix = np.empty((len(ARMS), len(columns)))
    rows_out = []
    for i, arm in enumerate(ARMS):
        for j, (start, key, title, sign) in enumerate(columns):
            source = events if key != "dur_mae_union" else summary
            full = _f(source[RUNS["Full"].format(s=start)], key)
            arm_value = _f(source[RUNS[arm].format(s=start)], key)
            delta = (arm_value - full) if sign == "ablation - Full" else (full - arm_value)
            matrix[i, j] = delta
            rows_out.append({
                "arm": arm, "start_cap": start, "metric": key, "sign": sign,
                "full": full, "arm_value": arm_value, "delta_positive_means_ablation_better": delta,
                "n_test_windows": 5354,
            })
    _write_csv(PLOT_DATA / "ablation_delta.csv", rows_out)
    limit = float(np.max(np.abs(matrix)))
    norm = TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit)
    short = {"Report F1": "F1", "Upcoming recall": "Up. R", "Union dur. MAE": "MAE"}
    fig, ax = plt.subplots(figsize=(7.35, 3.85))
    ax.imshow(matrix, cmap=DIV, norm=norm, aspect="auto", interpolation="nearest")
    ax.set_xticks(range(len(columns)))
    ax.set_xticklabels([f"≤{start}\n{short[title]}" for start, _, title, _ in columns])
    ax.set_yticks(range(len(ARMS)))
    ax.set_yticklabels(ARMS)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("#D9D4CC")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            rgba = DIV(norm(matrix[i, j]))
            luminance = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
            ax.text(j, i, f"{matrix[i, j]:+.3f}", ha="center", va="center", fontsize=7.5,
                    color="white" if luminance < 0.45 else INK)
    boundaries = np.cumsum([len(names) for _, names in GROUPS[:-1]]) - 0.5
    for y in boundaries:
        ax.axhline(y, color=INK, lw=1.15)
    ax.set_xlim(-0.5, len(columns) - 0.5)
    cbar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=DIV), ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("positive: ablation better", fontsize=8)
    cbar.outline.set_linewidth(0.4)
    fig.subplots_adjust(left=0.02, right=0.92, top=0.96, bottom=0.16)
    _save(fig, "fig_ablation_delta")


def plot_remain_dumbbell(summary: dict) -> None:
    rows_out = []
    stage1, stage2 = [], []
    for start in STARTS:
        a = _f(summary[RUNS["Stage1"].format(s=start)], "remain_mae")
        b = _f(summary[RUNS["Full"].format(s=start)], "remain_mae")
        stage1.append(a)
        stage2.append(b)
        rows_out.append({
            "arm": "Full", "start_cap": start, "stage1_mae": a, "stage2_mae": b,
            "absolute_drop": a - b, "percent_drop": 100.0 * (a - b) / a,
            "source_stage1": RUNS["Stage1"].format(s=start),
            "source_stage2": RUNS["Full"].format(s=start),
        })
    published = {5: (10.925976792778325, 9.601598876066781), 10: (11.213109243704304, 9.268456968835453),
                 15: (9.716936303467548, 8.90945713298286)}
    for start, (a, b) in zip(STARTS, zip(stage1, stage2)):
        assert abs(a - published[start][0]) < 1e-9 and abs(b - published[start][1]) < 1e-9
    _write_csv(PLOT_DATA / "remain_dumbbell_full.csv", rows_out)
    fig, ax = plt.subplots(figsize=(6.4, 2.35))
    y = np.arange(len(STARTS))[::-1]
    for yi, a, b in zip(y, stage1, stage2):
        ax.plot([a, b], [yi, yi], color="#8AA0A8", lw=1.1, zorder=1)
        ax.scatter([a], [yi], s=42, color=LIGHT, marker="s", zorder=3, label="Stage 1" if yi == y[0] else None)
        ax.scatter([b], [yi], s=48, color=STEEL, marker="o", zorder=3, label="Stage 2" if yi == y[0] else None)
        drop = a - b
        ax.text((a + b) / 2, yi + 0.18, f"−{drop:.2f} ({100 * drop / a:.0f}%)", ha="center", va="bottom", fontsize=8)
    ax.set_yticks(y)
    ax.set_yticklabels([f"Start ≤{s}" for s in STARTS])
    ax.set_xlabel("Remaining-time MAE (min); lower is better")
    ax.set_xlim(8.4, 11.7)
    ax.grid(axis="x", color="#E6E1D8", lw=0.6)
    ax.legend(frameon=False, loc="lower right", fontsize=8)
    fig.tight_layout()
    _save(fig, "fig_remain_dumbbell")


def _panel_heatmap(ax, values: np.ndarray, row_labels, col_labels, higher_better, title: str) -> None:
    colored = np.zeros_like(values, dtype=float)
    for j in range(values.shape[1]):
        column = values[:, j]
        span = float(column.max() - column.min()) or 1.0
        scaled = (column - column.min()) / span
        colored[:, j] = scaled if higher_better[j] else 1.0 - scaled
    ax.imshow(colored, cmap=SEQ, vmin=0, vmax=1, aspect="auto", interpolation="nearest")
    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=35, ha="right")
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels)
    ax.tick_params(length=0)
    ax.set_title(title, loc="left", fontsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            rgba = SEQ(colored[i, j])
            luminance = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
            ax.text(j, i, f"{values[i, j]:.3f}", ha="center", va="center", fontsize=7.5,
                    color="white" if luminance < 0.42 else INK)


def _edge(ax, row: int, ncol: int, color: str) -> None:
    ax.add_patch(Rectangle((-0.5, row - 0.5), ncol, 1, fill=False, ec=color, lw=1.6, zorder=4))


def plot_label_validity(labels: dict) -> None:
    methods = ["Ops", "Active Period", "Queue-Wait", "Utilization", "TPM"]
    oracle = {row["method"]: row for row in labels["oracle_pilot"]["metrics"]}
    separability = {row["method"]: row for row in labels["separability"]["metrics"]}
    cause = {row["method"]: row for row in labels["cause_comparison"]["metrics"]}
    if set(oracle) != set(methods) or set(separability) != set(methods) or set(cause) != set(methods):
        raise ValueError("label methods do not match the expected five")
    support = labels["cause_comparison"]["class_support"]
    if sum(support.values()) != labels["cause_comparison"]["n_test"]:
        raise ValueError("cause class support does not sum to n_test")
    oracle_cols = ["ndcg3", "positive_recall2", "positive_recall3", "weighted_recall3", "coverage3_rho90"]
    sep_cols = ["macro_f1", "balanced_accuracy", "auroc", "station_macro_f1", "silhouette", "davies_bouldin", "fisher_ratio"]
    cause_cols = ["transport_delay", "material_shortage", "starved_upstream", "queue_buildup"]
    oracle_m = np.array([[oracle[m][c] for c in oracle_cols] for m in methods])
    sep_m = np.array([[separability[m][c] for c in sep_cols] for m in methods])
    cause_m = np.array([[cause[m][c] for c in cause_cols] for m in methods])
    macro = np.array([cause[m]["macro_f1"] for m in methods])
    rows_out = []
    for m in methods:
        rows_out.append({"method": m, **{f"oracle_{c}": oracle[m][c] for c in oracle_cols},
                         **{f"sep_{c}": separability[m][c] for c in sep_cols},
                         **{f"cause_{c}": cause[m][c] for c in cause_cols},
                         "cause_macro_f1": cause[m]["macro_f1"]})
    _write_csv(PLOT_DATA / "label_validity.csv", rows_out)
    fig = plt.figure(figsize=(7.45, 5.55))
    grid = fig.add_gridspec(2, 2, height_ratios=[1.05, 1], hspace=0.55, wspace=0.42)
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1])
    inner = grid[1, :].subgridspec(1, 2, width_ratios=[1.55, 0.72], wspace=0.08)
    ax_c = fig.add_subplot(inner[0, 0])
    ax_d = fig.add_subplot(inner[0, 1])
    _panel_heatmap(ax_a, oracle_m, methods, ["NDCG@3", "Pos. R@2", "Pos. R@3", "W. R@3", "Cov@3"],
                   [True] * 5, "(a) Development-pilot alignment")
    _panel_heatmap(
        ax_b, sep_m, methods,
        ["Macro-F1", "Bal. acc.", "AUROC", "Station F1", "Silhouette", "DB ↓", "Fisher"],
        [True, True, True, True, True, False, True],
        "(b) Representation separability",
    )
    _panel_heatmap(
        ax_c, cause_m, methods,
        ["Transport", "Shortage", "Starvation", "Queue"],
        [True] * 4, "(c) Cause-class recall",
    )
    for ax, ncol in ((ax_b, sep_m.shape[1]), (ax_c, cause_m.shape[1])):
        _edge(ax, methods.index("Active Period"), ncol, STEEL)
        _edge(ax, methods.index("Queue-Wait"), ncol, OLIVE)
    y = np.arange(len(methods))
    colors = [STEEL if m == "Active Period" else OLIVE if m == "Queue-Wait" else LIGHT for m in methods]
    ax_d.hlines(y, 0.75, macro, color="#D5D0C8", lw=1.0)
    ax_d.scatter(macro, y, c=colors, s=36, zorder=3)
    for yi, value in zip(y, macro):
        ax_d.text(value + 0.008, yi, f"{value:.3f}", va="center", fontsize=7.5)
    ax_d.set_ylim(len(methods) - 0.5, -0.5)
    ax_d.set_yticks([])
    ax_d.set_xlabel("Cause macro-F1")
    ax_d.set_xlim(0.75, 1.02)
    ax_d.grid(axis="x", color="#E6E1D8", lw=0.6)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.96, bottom=0.12, hspace=0.55, wspace=0.42)
    _save(fig, "fig_label_validity")


def plot_timeline() -> None:
    rows = _read_csv(TRACE)
    window = np.array([int(float(r["window"])) for r in rows])
    true_s = np.array([float(r["true_state"]) for r in rows])
    pred_s = np.array([float(r["pred_state"]) for r in rows])
    true_d = np.array([float(r["true_dur"]) for r in rows])
    pred_d = np.array([float(r["pred_dur"]) for r in rows])
    if not np.array_equal(window, np.arange(len(window))):
        raise ValueError("timeline windows are not a contiguous index")
    _write_csv(PLOT_DATA / "timeline_phgst.csv", rows)
    fig, (state, duration) = plt.subplots(2, 1, figsize=(7.3, 3.35), sharex=True, height_ratios=[1, 1.35])
    state.step(window, true_s, where="post", color="black", lw=1.15, label="True")
    state.step(window, pred_s, where="post", color=CORAL, lw=1.05, ls="--", label="Predicted")
    state.set_ylim(-0.08, 1.12)
    state.set_yticks([0, 1])
    state.set_ylabel("State")
    state.legend(frameon=False, ncol=2, loc="upper right", fontsize=8)
    duration.plot(window, true_d, color="black", lw=1.2, label="True")
    duration.plot(window, pred_d, color=CORAL, lw=1.05, ls="--", label="Predicted")
    duration.set_ylabel("Duration (min)")
    duration.set_xlabel("Window (60 s)")
    duration.set_ylim(-1, 21)
    duration.legend(frameon=False, ncol=2, loc="upper right", fontsize=8)
    for ax in (state, duration):
        ax.grid(axis="y", color="#E6E1D8", lw=0.6)
        ax.set_xlim(-2, window[-1] + 2)
    fig.tight_layout()
    _save(fig, "fig_key_device_timeline")


def plot_per_device() -> None:
    if not PER_DEVICE.is_file():
        raise FileNotFoundError(PER_DEVICE)
    raw = _read_csv(PER_DEVICE)
    order = {"machine": 0, "gantry": 1, "transport_robot": 2}
    if {row["type"] for row in raw} - set(order):
        raise ValueError("unexpected device type")
    raw.sort(key=lambda row: (order[row["type"]], row["device"]))
    short = {
        "num00_rotaryPipeAutomaticWeldingMachine_ws0": "weld ws0",
        "num00_rotaryPipeAutomaticWeldingMachine_ws1": "weld ws1",
        "num01_weldingRobot_ws0": "weld robot",
        "num02_rollerbedCNCPipeIntersectionCuttingMachine_ws0": "cutting",
        "num04_groovingMachineLarge_ws0": "groove",
        "num08_workbench_ws0": "bench ws0",
        "num08_workbench_ws1": "bench ws1",
    }
    labels, support, f1, mae, supported = [], [], [], [], []
    rows_out = []
    for row in raw:
        name = short.get(row["device"], row["device"].replace("_", " "))
        n_true = int(float(row["n_true"]))
        labels.append(name)
        support.append(n_true)
        ok = n_true > 0
        supported.append(ok)
        f1.append(float(row["f1"]) if ok else np.nan)
        mae.append(float(row["dur_mae_union"]) if ok else np.nan)
        rows_out.append({
            "device": row["device"], "type": row["type"], "support": n_true,
            "f1": row["f1"] if ok else "", "dur_mae_union": row["dur_mae_union"] if ok else "",
            "displayed": "value" if ok else "em-dash",
        })
    if rows_out[labels.index("cutting")]["support"] != 301:
        raise ValueError("cutting-machine support is not the 301 events cited in the chapter")
    _write_csv(PLOT_DATA / "per_device_start5.csv", rows_out)
    values = [np.array(support, dtype=float), np.array(f1), np.array(mae)]
    headers = ["Support", "F1", "Union dur. MAE"]
    higher = [True, True, False]
    fig, axes = plt.subplots(1, 3, figsize=(7.35, 4.55), sharey=True)
    y = np.arange(len(labels))
    group_ends = []
    last = raw[0]["type"]
    for i, row in enumerate(raw[1:], start=1):
        if row["type"] != last:
            group_ends.append(i - 0.5)
            last = row["type"]
    for ax, column, header, better in zip(axes, values, headers, higher):
        finite = column[np.isfinite(column)]
        span = float(finite.max() - finite.min()) or 1.0
        for yi, value, ok in zip(y, column, supported):
            if not ok:
                ax.add_patch(Rectangle((0, yi - 0.38), 1, 0.76, facecolor="#F3F1EC",
                                       edgecolor="none", hatch="////", transform=ax.get_yaxis_transform()))
                ax.text(0.5, yi, "—", ha="center", va="center", fontsize=8, transform=ax.get_yaxis_transform())
                continue
            if header == "Support":
                color = LIGHT
            else:
                scaled = (value - finite.min()) / span
                color = SEQ(scaled if better else 1.0 - scaled)
            ax.barh(yi, value, color=color, height=0.72)
            ax.text(value, yi, f" {value:.0f}" if header == "Support" else f" {value:.3f}",
                    va="center", ha="left", fontsize=7)
        for edge in group_ends:
            ax.axhline(edge, color="#D9D4CC", lw=0.7)
        ax.set_xlabel(header)
        ax.set_ylim(len(labels) - 0.5, -0.5)
        ax.grid(axis="x", color="#E6E1D8", lw=0.5)
        ax.set_axisbelow(True)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(labels)
    axes[0].set_xlim(0, 380)
    axes[1].set_xlim(0, 1.22)
    axes[2].set_xlim(0, 7.6)
    fig.tight_layout()
    _save(fig, "fig_per_device_start5")


def main() -> None:
    _style()
    events, summary, labels = _load()
    plot_ablation_delta(events, summary)
    plot_remain_dumbbell(summary)
    plot_label_validity(labels)
    plot_timeline()
    plot_per_device()


if __name__ == "__main__":
    main()
