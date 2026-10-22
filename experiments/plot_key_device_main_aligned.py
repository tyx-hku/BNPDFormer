#!/usr/bin/env python3
"""Redraw PHGST-DP's archived case and prepend it to the four baseline panels.

The baseline panels are reused without changing their curves. The main-model
trace is drawn from its exported per-window values, with t_index rebased by 30
to match the existing baseline figures. No inference or training is performed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "experiments/data/key_device_main_aligned.csv"
EPISODE = "n10_human1.0__episode_03"
RESOURCE = "num02_rollerbedCNCPipeIntersectionCuttingMachine_ws0"
FIELDS = ("true_state", "pred_state", "true_dur", "pred_dur")


def extract_series(path: Path) -> None:
    with np.load(path, allow_pickle=False) as archive:
        selected = np.flatnonzero(archive["episode"] == EPISODE)
        selected = selected[np.argsort(archive["t_index"][selected])]
        resource = list(archive["resource_ids"]).index(RESOURCE)
        times = archive["t_index"][selected]
        assert len(times) == 231 and np.array_equal(times, np.arange(30, 261))
        assert archive["valid_1step"][selected, resource].all()
        with DATA.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=("window", "t_index", *FIELDS), lineterminator="\n")
            writer.writeheader()
            for i, t in zip(selected, times):
                writer.writerow({
                    "window": int(t - times[0]), "t_index": int(t),
                    **{k: float(archive[k][i, resource]) for k in FIELDS},
                })
    metadata = {
        "model": "PHGST-DP", "episode": EPISODE, "resource": RESOURCE,
        "start_cap_min": 5, "horizon_min": 20, "window_seconds": 60,
        "windows": 231, "display_window": "t_index - 30",
        "source_branch": "dev_tyx", "source_commit": "8767583f3ed6392cfd8061d4a80de94fcfb9d7a0",
        "source_series": "/home/sci/work/isaac_factory/source/isaaclab_tasks/isaaclab_tasks/direct/hc_factory/PDFormer/libcity/cache/bottleneck_eval/bestmodel_start5_seed42/series.npz",
        "source_series_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "baseline_source": "figures/key_device_baselines_aligned.pdf",
        "baseline_png_sha256": hashlib.sha256((ROOT / "figures/key_device_baselines_aligned.png").read_bytes()).hexdigest(),
        "baseline_episode_group": "2026-08-23_13-58-14_seed42:env_00:episode_03",
        "baseline_sample_indices": [8669, 8899],
        "baseline_metadata_source": "/home/sci/work/BSTAN_isaac_factory/source/isaaclab_tasks/isaaclab_tasks/direct/hc_factory/output/bottleneck_dataset/experiments/factory_pdformer_134_v3/baseline_matched_v1_test_20261003_metrics_v4_summary/aligned_trace_metadata.json",
        "note": "The existing baseline panels are qualitative reevaluations on the main-model episode. Their archived aggregate test metrics use a different manifest. Baseline panels are reused unchanged; they are not reconstructed from the aggregate-test series.npz files.",
    }
    DATA.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--series", type=Path, help="Optionally refresh the local CSV from the archived main-model series.npz")
    args = parser.parse_args()
    if args.series:
        extract_series(args.series)
    with DATA.open(encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    arrays = {key: np.array([float(r[key]) for r in rows]) for key in rows[0]}
    assert np.array_equal(arrays["window"], np.arange(231))
    # NOTE: the final combined figure is redrawn by redraw_ch5_raster_times.py
    # (Times New Roman throughout, baselines recovered from these panels).
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif", "serif"],
        "font.size": 7.5,
        "axes.titlesize": 8.8, "axes.labelsize": 7.5,
        "axes.linewidth": 0.65, "xtick.labelsize": 7.2, "ytick.labelsize": 7.2,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 3, "ytick.major.size": 3,
        "pdf.fonttype": 42, "ps.fonttype": 42,
    })
    out = ROOT / "figures"
    true_color, pred_color = "#1f77b4", "#d34b51"
    zoom_start, zoom_end = 20, 115

    def draw_pair(title: str, destination: Path, *, zoom: bool = False) -> None:
        fig = plt.figure(figsize=(3.55, 2.95))
        state = fig.add_axes([0.107, 0.64, 0.85, 0.28])
        duration = fig.add_axes([0.107, 0.15, 0.85, 0.37])
        x = arrays["window"]
        for ax in (state, duration):
            if zoom:
                ax.set_xlim(zoom_start, zoom_end)
                ax.set_xticks([20, 40, 60, 80, 100, 115])
                ax.get_xticklabels()[-1].set_ha("right")
            else:
                ax.set_xlim(-11.5, 241.5)
                ax.set_xticks([0, 50, 100, 150, 200])
                ax.axvspan(zoom_start, zoom_end, facecolor="#efefef", edgecolor="none", zorder=0)
                for edge in (zoom_start, zoom_end):
                    ax.axvline(edge, color="0.68", lw=.55, ls=(0, (2, 2)), zorder=1)
            ax.grid(alpha=0.22, linewidth=0.55)
            ax.set_axisbelow(True)
            ax.tick_params(axis="y", pad=2)
        state.step(x, arrays["true_state"], where="post", color=true_color, lw=1.05)
        state.step(x, arrays["pred_state"], where="post", color=pred_color, lw=0.95, ls="--")
        state.set_ylim(-0.07, 1.07)
        state.set_yticks([0, 1])
        state.set_ylabel("State", labelpad=2)
        state.set_title(title, pad=4)
        duration.plot(x, arrays["true_dur"], color=true_color, lw=1.05)
        duration.plot(x, arrays["pred_dur"], color=pred_color, lw=0.95, ls="--")
        duration.set_ylim(-1, 21)
        duration.set_yticks([0, 5, 10, 15, 20])
        duration.set_ylabel("Duration (min)", labelpad=2)
        duration.set_xlabel("Window (60 s)", labelpad=3)
        fig.savefig(destination, facecolor="white")
        fig.savefig(destination.with_suffix(".png"), dpi=300, facecolor="white")
        plt.close(fig)

    main_pdf = out / "key_device_main_aligned.pdf"
    detail_pdf = out / "key_device_main_detail.pdf"
    draw_pair("PHGST-DP: full trajectory", main_pdf)
    draw_pair("PHGST-DP: event detail", detail_pdf, zoom=True)

    # Use the existing four-model figure as one immutable panel block. Clip
    # only its obsolete heading/legend and top whitespace; keep all four models.
    base = fitz.open(ROOT / "experiments/data/key_device_baselines_aligned_dev_xwt.pdf")
    clip = fitz.Rect(0, base[0].rect.height * 350 / 2390,
                     base[0].rect.width, base[0].rect.height)
    main_doc = fitz.open(main_pdf)
    width, legend_height, gap = 518.4, 19.0, 3.0
    main_height = main_doc[0].rect.height
    baseline_height = clip.height * width / clip.width
    height = legend_height + main_height + gap + baseline_height
    combined = fitz.open()
    page = combined.new_page(width=width, height=height)
    # Common legend is vector, and has the same meaning in every model panel.
    legend = plt.figure(figsize=(width / 72, legend_height / 72))
    legend.legend(handles=[Line2D([], [], color=true_color, lw=1.1, label="True"),
                           Line2D([], [], color="0.35", lw=1.0, ls="--", label="Predicted")],
                  loc="center", ncol=2, frameon=False, fontsize=7.5)
    import io
    buffer = io.BytesIO()
    legend.savefig(buffer, format="pdf", facecolor="white")
    plt.close(legend)
    legend_doc = fitz.open(stream=buffer.getvalue(), filetype="pdf")
    page.show_pdf_page(fitz.Rect(0, 0, width, legend_height), legend_doc, 0)
    main_width = main_doc[0].rect.width
    left = 0
    page.show_pdf_page(fitz.Rect(left, legend_height, left + main_width, legend_height + main_height), main_doc, 0)

    # The right-hand pair is a magnification of the same measurements, with
    # unchanged ordinate limits and absolute window indices.
    detail_doc = fitz.open(detail_pdf)
    detail_left = width * .52
    page.show_pdf_page(fitz.Rect(detail_left, legend_height,
                                detail_left + main_width, legend_height + main_height), detail_doc, 0)
    top = legend_height + main_height + gap
    page.show_pdf_page(fitz.Rect(0, top, width, height), base, 0, clip=clip)
    combined.set_metadata({"title": "Key-device case: PHGST-DP and four independent baseline panels",
                           "subject": f"{RESOURCE}; {EPISODE}; Start <= 5 min"})
    destination = out / "key_device_models_aligned.pdf"
    combined.save(destination, garbage=4, deflate=True)
    page.get_pixmap(matrix=fitz.Matrix(3, 3), alpha=False).save(destination.with_suffix(".png"))
    print(f"Wrote {main_pdf.name} and {destination.name}; {len(rows)} main-model windows")


if __name__ == "__main__":
    main()
