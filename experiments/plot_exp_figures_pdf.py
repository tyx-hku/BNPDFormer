#!/usr/bin/env python3
"""Export the Chapter 5 experiment figures as PDF.

Vector redraws: baseline comparison (values of tab:comparison-event /
tab:comparison-regression), ablation overview and remaining-time bars
(``data/bottleneck_eval_summary.csv`` from ``eval_bottleneck summarize``).

Trace and state-map figures need per-window ``series.npz`` from the server
eval; those are wrapped losslessly from their PNG renders instead.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SUMMARY = Path(__file__).resolve().parent / "data" / "bottleneck_eval_summary.csv"
MAIN_EVENTS = SUMMARY.parent / "main_event_metrics_dev_tyx_29655ba.csv"
BASELINE_EVENTS = SUMMARY.parent / "baseline_metrics_common_archived.csv"

PALETTE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "green_3": "#8BCF8B",
    "red_strong": "#B64342",
    "teal": "#42949E",
    "violet": "#9A4D8E",
    "neutral": "#CFCECE",
}

STARTS = (5, 10, 15)
ARMS = {
    "PHAST-DP": "bestmodel_start{s}_seed42",
    "NoFarBoost": "full_nofarboost_start{s}_seed42",
    "NoCluster": "ablation_nocluster_start{s}_seed42",
    "NoGraph": "ablation_nograph_start{s}_seed42",
    "NoGroup": "ablation_nogroup_start{s}_seed42",
    "NoPattern": "struct_nopattern_start{s}_min8_cold_ep50_seed42",
    "NoSplit": "struct_nosplit_start{s}_min8_cold_ep50_seed42",
    "NoCross": "entity_nocross_start{s}_min8_cold_ep50_seed42",
    "NoInfo": "entity_noinfo_start{s}_min8_cold_ep50_seed42",
    "MachineOnly": "entity_machineonly_start{s}_min8_cold_ep50_seed42",
}

BASELINE_COLORS = {
    "PHAST-DP": PALETTE["blue_main"],
    "XGBoost": PALETTE["red_strong"],
    "LSTM": PALETTE["green_3"],
    "BTGCN": PALETTE["violet"],
    "BSTAN": PALETTE["teal"],
}
BASELINE_MARKERS = {"PHAST-DP": "o", "XGBoost": "s", "LSTM": "^", "BTGCN": "D", "BSTAN": "v"}

RASTER_FIGURES = (
    "key_device_main",
    "key_device_struct",
    "key_device_entity",
    "key_device_baselines_aligned",
    "all_devices_state_main",
)
RASTER_DPI = 200


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans", "Helvetica", "sans-serif"],
            "font.size": 10,
            "axes.linewidth": 1.0,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.03,
        }
    )


def _to_float(v: str | None) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _read_summary(path: Path) -> dict[str, dict[str, float | None]]:
    with path.open(encoding="utf-8") as fh:
        return {row["run"]: {k: _to_float(v) for k, v in row.items() if k != "run"} for row in csv.DictReader(fh)}


def plot_baseline_comparison(out: Path) -> None:
    main = _read_summary(MAIN_EVENTS)
    with BASELINE_EVENTS.open(encoding="utf-8") as fh:
        baseline = {(r["model"], int(r["start_cap"])): r for r in csv.DictReader(fh)}
    values = {"PHAST-DP": {
        key: [main[f"bestmodel_start{s}_seed42"][field] for s in STARTS]
        for key, field in (("report_f1", "report_f1"), ("upcoming_r", "who_recall_upcoming"), ("dur_mae", "dur_mae_tp"))
    }}
    for model, code in (("XGBoost", "B2"), ("LSTM", "B3"), ("BTGCN", "B4"), ("BSTAN", "B5")):
        values[model] = {
            key: [float(baseline[(code, s)][field]) for s in STARTS]
            for key, field in (("report_f1", "report_f1"), ("upcoming_r", "upcoming_who_recall"), ("dur_mae", "duration_mae"))
        }
    panels = (
        ("report_f1", "Report F1", (0.4, 0.85)),
        ("upcoming_r", "Upcoming station recall", (0.0, 0.6)),
        ("dur_mae", "Duration MAE (min)", (1.5, 4.0)),
    )
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5))
    for ax, (key, title, ylim) in zip(axes, panels):
        for model, vals in values.items():
            ax.plot(
                STARTS,
                vals[key],
                marker=BASELINE_MARKERS[model],
                color=BASELINE_COLORS[model],
                lw=2.0 if model == "PHAST-DP" else 1.3,
                ms=5,
                label=model,
                zorder=3 if model == "PHAST-DP" else 2,
            )
        ax.set_title(title, fontsize=10)
        ax.set_xticks(STARTS)
        ax.set_xticklabels([f"≤{s}" for s in STARTS])
        ax.set_xlabel("Onset cap (min)")
        ax.set_ylim(*ylim)
        ax.grid(axis="y", alpha=0.3, lw=0.6)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.04), fontsize=9)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(out)
    fig.savefig(out.with_suffix(".png"), dpi=250)
    plt.close(fig)
    print(f"[plot] wrote {out}")


def _bars(summary: dict, panels: tuple[tuple[str, str], ...], out: Path, f1_axis: bool, arm_patterns: dict | None = None) -> None:
    arms = {a: p for a, p in (ARMS if arm_patterns is None else arm_patterns).items() if any(p.format(s=s) in summary for s in STARTS)}
    x = np.arange(len(arms))
    w = 0.26
    colors = (PALETTE["blue_main"], PALETTE["teal"], PALETTE["neutral"])
    fig, axes = plt.subplots(1, len(panels), figsize=(7.2, 2.7))
    for ax, (key, ylab) in zip(axes, panels):
        for i, s in enumerate(STARTS):
            vals = [summary.get(p.format(s=s), {}).get(key) for p in arms.values()]
            ax.bar(
                x + (i - 1) * w,
                [np.nan if v is None else v for v in vals],
                w,
                color=colors[i],
                edgecolor="black",
                linewidth=0.3,
                label=f"Start≤{s}",
            )
        ax.set_xticks(x)
        ax.set_xticklabels(list(arms), fontsize=7, rotation=45, ha="right", rotation_mode="anchor")
        ax.set_ylabel(ylab, fontsize=9)
        ax.tick_params(axis="y", labelsize=8)
        ax.grid(axis="y", alpha=0.3, lw=0.6)
        ax.set_axisbelow(True)
    if f1_axis:
        axes[0].set_ylim(0, 1)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.04), fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out)
    fig.savefig(out.with_suffix(".png"), dpi=250)
    plt.close(fig)
    print(f"[plot] wrote {out}")


def wrap_png(png: Path, out: Path, dpi: int = RASTER_DPI) -> None:
    import fitz

    with fitz.open(png) as img:
        w_px, h_px = img[0].rect.width, img[0].rect.height
    w_pt, h_pt = w_px / dpi * 72.0, h_px / dpi * 72.0
    doc = fitz.open()
    page = doc.new_page(width=w_pt, height=h_pt)
    page.insert_image(page.rect, filename=str(png))
    doc.save(out, deflate=True, garbage=3)
    doc.close()
    print(f"[wrap] wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "figures")
    ap.add_argument("--summary", type=Path, default=SUMMARY)
    ap.add_argument("--charts-only", action="store_true", help="Redraw metric charts without rewrapping the existing trace PNGs")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    apply_style()

    plot_baseline_comparison(args.out / "fig_baseline_comparison.pdf")
    summary = _read_summary(args.summary)
    _bars(
        summary,
        (("will15_f1", "Will15 F1"), ("dur_mae_union", "Union duration MAE (min)"), ("dur_rmse_union", "Union duration RMSE (min)")),
        args.out / "overview_bars.pdf",
        True,
    )
    _bars(
        summary,
        (("remain_mae", "Remaining-time MAE (min)"), ("remain_mae_early", "Early-phase MAE (min)"), ("remain_mae_late", "Late-phase MAE (min)")),
        args.out / "remain_bars.pdf",
        False,
        {"PHAST-DP (stage 1)": "full_farboost_start{s}_seed42", **{a: p for a, p in ARMS.items() if a != "PHAST-DP"}},
    )
    for name in (() if args.charts_only else RASTER_FIGURES):
        png = args.out / f"{name}.png"
        if png.is_file():
            wrap_png(png, args.out / f"{name}.pdf")


if __name__ == "__main__":
    main()
