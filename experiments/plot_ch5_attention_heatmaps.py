"""Re-export Chapter 5 heatmaps without buffer rows or columns.

The stored matrices retain all 38 model nodes.  This plotting-only filter keeps
machine, gantry, human, and transport-robot nodes (20 resources) and excludes
the 18 buffer nodes.  Attention values are not renormalized after filtering.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, TwoSlopeNorm
import numpy as np


PALETTE = {
    "deep_teal": "#46788E",
    "light_blue": "#78B7C9",
    "pale_yellow": "#F6E093",
    "coral": "#E58B7B",
    "yellow_green": "#97B319",
}
# Same-hue pair transitions cleanly; yellow→blue midtones look muddy.
# Extra stops stretch mid-range contrast for nearly uniform attention matrices.
CMAP_SEQUENTIAL = LinearSegmentedColormap.from_list(
    "research_sequential",
    ["#F7FBFC", "#D6EAF1", "#9ECBDA", PALETTE["light_blue"], "#5A93A8", PALETTE["deep_teal"], "#2F5464"],
)
# Longer near-white ramp for nearly uniform absolute attention (e.g. temporal maps).
# Position stops keep most of the scale pale so mid-range structure stays readable.
CMAP_SEQUENTIAL_LIGHT = LinearSegmentedColormap.from_list(
    "research_sequential_light",
    [
        (0.00, "#FFFFFF"),
        (0.20, "#F7FBFC"),
        (0.40, "#E8F4F8"),
        (0.55, "#D0E8F0"),
        (0.70, "#A8D0DE"),
        (0.82, PALETTE["light_blue"]),
        (0.92, "#5A93A8"),
        (1.00, PALETTE["deep_teal"]),
    ],
)
CMAP_DIVERGING = LinearSegmentedColormap.from_list(
    "research_diverging",
    [
        (0.00, PALETTE["deep_teal"]),
        (0.35, PALETTE["light_blue"]),
        (0.50, "#FFFFFF"),
        (0.75, PALETTE["coral"]),
        (1.00, "#C45A4A"),
    ],
)
CMAP_ERROR = LinearSegmentedColormap.from_list(
    "research_error", ["#F4FAFC", PALETTE["light_blue"], PALETTE["deep_teal"]]
)
CMAP_BINARY = ListedColormap(["#F4FAFC", PALETTE["deep_teal"]])

TYPE_ORDER = ("machine", "gantry", "human", "transport_robot")
TYPE_TITLES = ("Machine", "Gantry", "Human", "AGV")
CONDITIONS = ("normal", "upcoming", "ongoing")
CONDITION_TITLES = {
    "normal": "Normal",
    "upcoming": "Upcoming bottleneck",
    "ongoing": "Ongoing bottleneck",
}


def style() -> None:
    from paper_plot_style import LABEL_SIZE, TICK_SIZE, TITLE_SIZE, apply as apply_paper_style
    apply_paper_style()
    matplotlib.rcParams.update(
        {
            "font.size": LABEL_SIZE,
            "axes.labelsize": LABEL_SIZE,
            "axes.titlesize": TITLE_SIZE,
            "xtick.labelsize": TICK_SIZE,
            "ytick.labelsize": TICK_SIZE,
            "axes.linewidth": 0.8,
            "figure.dpi": 150,
            "savefig.dpi": 600,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.04,
        }
    )


def save(fig: plt.Figure, out_dir: Path, stem: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for suffix in ("pdf", "png", "svg"):
        dest = out_dir / f"{stem}.{suffix}"
        tmp = out_dir / f"_{stem}_{suffix}.tmp"
        try:
            fig.savefig(tmp, dpi=600 if suffix == "png" else None, format=suffix)
            try:
                dest.unlink(missing_ok=True)
                tmp.replace(dest)
            except OSError:
                alt = out_dir / f"{stem}.{suffix}.new"
                if alt.exists():
                    alt.unlink()
                tmp.replace(alt)
                print(f"[warn] could not replace {dest.name}; wrote {alt.name}")
        except OSError as exc:
            print(f"[warn] skip {dest.name}: {exc}")
    plt.close(fig)


def boundaries(resource_types: list[str]) -> list[int]:
    return [i for i in range(1, len(resource_types)) if resource_types[i] != resource_types[i - 1]]


def heatmap(
    ax: plt.Axes,
    matrix: np.ndarray,
    labels: list[str] | None,
    title: str,
    cmap=CMAP_SEQUENTIAL,
    vmin: float | None = None,
    vmax: float | None = None,
    norm=None,
    group_boundaries: list[int] | None = None,
    annotate: bool = False,
    tick_step: int = 1,
    xlabel: str | None = "Attended resource",
    ylabel: str | None = "Query resource",
    *,
    tick_fontsize: float | None = None,
    label_fontsize: float | None = None,
    title_fontsize: float | None = None,
):
    image = ax.imshow(
        matrix,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        norm=norm,
        aspect="equal",
        interpolation="nearest",
    )
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(title, pad=4 if title_fontsize else 6, fontsize=title_fontsize)
    if labels is not None:
        ticks = np.arange(0, len(labels), max(1, tick_step))
        ax.set_xticks(ticks)
        ax.set_yticks(ticks)
        tick_kw = {"rotation": 90}
        if tick_fontsize is not None:
            tick_kw["fontsize"] = tick_fontsize
        ax.set_xticklabels([labels[i] for i in ticks], **tick_kw)
        ax.set_yticklabels(
            [labels[i] for i in ticks],
            fontsize=tick_fontsize if tick_fontsize is not None else None,
        )
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=label_fontsize)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=label_fontsize)
    for boundary in group_boundaries or []:
        ax.axhline(boundary - 0.5, color="white", lw=0.8)
        ax.axvline(boundary - 0.5, color="white", lw=0.8)
    if annotate:
        scale = max(float(np.nanmax(np.abs(matrix))), 1e-9)
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                value = matrix[i, j]
                color = "white" if abs(value) > 0.55 * scale else "black"
                from paper_plot_style import ANNOT_SIZE
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=ANNOT_SIZE, color=color)
    return image


def filter_square(matrix: np.ndarray, keep: np.ndarray) -> np.ndarray:
    return matrix[np.ix_(keep, keep)]


def type_aggregate(matrix: np.ndarray, resource_types: list[str]) -> np.ndarray:
    types = np.asarray(resource_types)
    out = np.zeros((len(TYPE_ORDER), len(TYPE_ORDER)), dtype=float)
    for i, source_type in enumerate(TYPE_ORDER):
        source = np.flatnonzero(types == source_type)
        for j, target_type in enumerate(TYPE_ORDER):
            target = np.flatnonzero(types == target_type)
            out[i, j] = float(matrix[np.ix_(source, target)].mean())
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("figures/attention_heatmaps/heatmap_matrices.npz"),
    )
    parser.add_argument("--out-dir", type=Path, default=Path("figures/attention_heatmaps"))
    args = parser.parse_args()
    style()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    with np.load(args.input, allow_pickle=False) as loaded:
        data = {key: loaded[key] for key in loaded.files}
    all_types = data["resource_types"].astype(str)
    keep = np.flatnonzero(all_types != "buffer")
    labels = data["short_labels"][keep].astype(str).tolist()
    resource_types = all_types[keep].tolist()
    group_boundaries = boundaries(resource_types)
    if len(keep) != 20 or any(label.startswith("B") for label in labels):
        raise RuntimeError("expected 20 non-buffer resources after filtering")

    # Figure 1: fixed structural priors.
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.2), constrained_layout=True)
    for ax, (key, title) in zip(
        axes,
        (
            ("adjacency", "(a) Factory adjacency"),
            ("hop_proximity", "(b) Hop proximity"),
            ("semantic_similarity", "(c) Semantic similarity"),
        ),
    ):
        image = heatmap(
            ax,
            filter_square(data[key], keep),
            labels,
            title,
            vmin=0.0,
            vmax=1.0,
            group_boundaries=group_boundaries,
        )
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.025)
    save(fig, args.out_dir, "fig01_graph_priors")

    state = {
        (kind, condition): filter_square(data[f"start5_{kind}_{condition}"], keep)
        for kind in ("geo", "sem")
        for condition in CONDITIONS
    }
    vmax_by_kind = {
        kind: max(float(state[(kind, condition)].max()) for condition in CONDITIONS)
        for kind in ("geo", "sem")
    }

    # Figure 2: absolute attention by operating condition.
    fig, axes = plt.subplots(2, 3, figsize=(7.2, 5.1), constrained_layout=True)
    fig.set_constrained_layout_pads(h_pad=0.10, w_pad=0.04, hspace=0.18, wspace=0.06)
    for row, kind in enumerate(("geo", "sem")):
        for col, condition in enumerate(CONDITIONS):
            image = heatmap(
                axes[row, col],
                state[(kind, condition)],
                labels,
                f"({chr(97 + row * 3 + col)}) {kind.capitalize()} - {CONDITION_TITLES[condition]}",
                vmin=0.0,
                vmax=vmax_by_kind[kind],
                group_boundaries=group_boundaries,
            )
        fig.colorbar(image, ax=axes[row, :], fraction=0.018, pad=0.018, label="Attention weight")
    save(fig, args.out_dir, "fig02_resource_attention_states")

    # Figure 3: signed changes relative to normal operation.
    deltas = {
        (kind, condition): state[(kind, condition)] - state[(kind, "normal")]
        for kind in ("geo", "sem")
        for condition in ("upcoming", "ongoing")
    }
    delta_max = max(float(np.abs(array).max()) for array in deltas.values())
    norm = TwoSlopeNorm(vmin=-delta_max, vcenter=0.0, vmax=delta_max)
    fig, axes = plt.subplots(2, 2, figsize=(6.8, 6.3), constrained_layout=True)
    fig.set_constrained_layout_pads(h_pad=0.10, w_pad=0.04, hspace=0.18, wspace=0.06)
    for row, kind in enumerate(("geo", "sem")):
        for col, condition in enumerate(("upcoming", "ongoing")):
            image = heatmap(
                axes[row, col],
                deltas[(kind, condition)],
                labels,
                f"({chr(97 + row * 2 + col)}) {kind.capitalize()}: {condition} - normal",
                cmap=CMAP_DIVERGING,
                norm=norm,
                group_boundaries=group_boundaries,
            )
    fig.colorbar(image, ax=axes, fraction=0.025, pad=0.02, label="Attention-weight change")
    save(fig, args.out_dir, "fig03_resource_attention_change")

    # Figure 4: temporal attention — (a) normal, (b) upcoming, (c) upcoming−normal.
    # Ongoing is omitted so the absolute maps can be larger and easier to read.
    temporal = {condition: data[f"start5_temporal_{condition}"] for condition in ("normal", "upcoming")}
    temporal_delta = data["start5_temporal_upcoming_minus_normal"]
    # Span the colormap over the displayed value range so low cells stay near white
    # instead of sitting in the dark half of a 0--vmax scale.
    abs_stack = np.stack([temporal["normal"], temporal["upcoming"]])
    vmin_temporal = float(np.percentile(abs_stack, 5))
    vmax_temporal = float(np.percentile(abs_stack, 95))
    if vmax_temporal <= vmin_temporal:
        vmin_temporal = float(abs_stack.min())
        vmax_temporal = float(abs_stack.max())
    delta_temporal_max = float(np.abs(temporal_delta).max())
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.9), constrained_layout=True)
    n_steps = temporal["normal"].shape[0]
    time_labels = [str(i + 1) for i in range(n_steps)]
    for col, condition in enumerate(("normal", "upcoming")):
        image = heatmap(
            axes[col],
            temporal[condition],
            time_labels,
            f"({chr(97 + col)}) {CONDITION_TITLES[condition]}",
            cmap=CMAP_SEQUENTIAL_LIGHT,
            vmin=vmin_temporal,
            vmax=vmax_temporal,
            xlabel="Attended history step",
            ylabel="Query history step" if col == 0 else None,
            tick_step=5,
        )
    fig.colorbar(image, ax=axes[:2], fraction=0.046, pad=0.02, label="Attention weight")
    temporal_norm = TwoSlopeNorm(vmin=-delta_temporal_max, vcenter=0.0, vmax=delta_temporal_max)
    image = heatmap(
        axes[2],
        temporal_delta,
        time_labels,
        "(c) Upcoming - normal",
        cmap=CMAP_DIVERGING,
        norm=temporal_norm,
        xlabel="Attended history step",
        ylabel=None,
        tick_step=5,
    )
    fig.colorbar(image, ax=axes[2], fraction=0.046, pad=0.02, label="Change")
    save(fig, args.out_dir, "fig04_temporal_attention_states")

    # Figure 5: layer-wise upcoming attention.
    depth = 5
    layer_geo = [filter_square(data[f"start5_geo_upcoming_layer{i}"], keep) for i in range(1, depth + 1)]
    layer_sem = [filter_square(data[f"start5_sem_upcoming_layer{i}"], keep) for i in range(1, depth + 1)]
    vmax_geo = max(float(array.max()) for array in layer_geo)
    vmax_sem = max(float(array.max()) for array in layer_sem)
    fig, axes = plt.subplots(2, depth, figsize=(7.5, 4.4), constrained_layout=True)
    fig.set_constrained_layout_pads(h_pad=0.10, w_pad=0.03, hspace=0.18, wspace=0.05)
    for layer in range(depth):
        geo_image = heatmap(
            axes[0, layer], layer_geo[layer], labels, f"Geo layer {layer + 1}",
            vmin=0.0, vmax=vmax_geo, group_boundaries=group_boundaries, tick_step=2,
        )
        sem_image = heatmap(
            axes[1, layer], layer_sem[layer], labels, f"Semantic layer {layer + 1}",
            vmin=0.0, vmax=vmax_sem, group_boundaries=group_boundaries, tick_step=2,
        )
    fig.colorbar(geo_image, ax=axes[0, :], fraction=0.012, pad=0.012, label="Attention weight")
    fig.colorbar(sem_image, ax=axes[1, :], fraction=0.012, pad=0.012, label="Attention weight")
    save(fig, args.out_dir, "fig05_layerwise_upcoming_attention")

    # Figure 6: aggregate the displayed nodes into four non-buffer entity types.
    type_arrays = {
        (kind, condition): type_aggregate(state[(kind, condition)], resource_types)
        for kind in ("geo", "sem")
        for condition in CONDITIONS
    }
    vmax_type = {
        kind: max(float(type_arrays[(kind, condition)].max()) for condition in CONDITIONS)
        for kind in ("geo", "sem")
    }
    fig, axes = plt.subplots(2, 3, figsize=(7.2, 5.1), constrained_layout=True)
    fig.set_constrained_layout_pads(h_pad=0.10, w_pad=0.04, hspace=0.18, wspace=0.06)
    for row, kind in enumerate(("geo", "sem")):
        for col, condition in enumerate(CONDITIONS):
            image = heatmap(
                axes[row, col],
                type_arrays[(kind, condition)],
                list(TYPE_TITLES),
                f"({chr(97 + row * 3 + col)}) {kind.capitalize()} - {CONDITION_TITLES[condition]}",
                vmin=0.0,
                vmax=vmax_type[kind],
                annotate=True,
            )
        fig.colorbar(image, ax=axes[row, :], fraction=0.02, pad=0.018, label="Mean attention weight")
    save(fig, args.out_dir, "fig06_entity_type_attention")

    # Figure 7: horizon-specific signed changes.
    # Same 2×3 form as fig02/fig05: geographic row (a,c,e), semantic row (b,d,f).
    horizon_keys = (("Startlt5", "Onset limit ≤ 5"), ("Startlt10", "Onset limit ≤ 10"), ("Startlt15", "Onset limit ≤ 15"))
    horizon = {
        (title, kind): filter_square(data[f"{key}_{kind}_upcoming_minus_normal"], keep)
        for key, title in horizon_keys
        for kind in ("geo", "sem")
    }
    horizon_max = max(float(np.abs(array).max()) for array in horizon.values())
    horizon_norm = TwoSlopeNorm(vmin=-horizon_max, vcenter=0.0, vmax=horizon_max)
    fig, axes = plt.subplots(2, 3, figsize=(7.2, 5.3), constrained_layout=True)
    fig.set_constrained_layout_pads(h_pad=0.10, w_pad=0.04, hspace=0.18, wspace=0.06)
    # Panel letters keep the prior a/c/e (geo) and b/d/f (sem) identities.
    panel_letters = {"geo": ("a", "c", "e"), "sem": ("b", "d", "f")}
    for row, kind in enumerate(("geo", "sem")):
        for col, (_, title) in enumerate(horizon_keys):
            letter = panel_letters[kind][col]
            image = heatmap(
                axes[row, col],
                horizon[(title, kind)],
                labels,
                f"({letter}) {title} {kind}: upcoming - normal",
                cmap=CMAP_DIVERGING,
                norm=horizon_norm,
                group_boundaries=group_boundaries,
                ylabel="Query resource" if col == 0 else None,
            )
    fig.colorbar(image, ax=axes, fraction=0.018, pad=0.018, label="Attention-weight change")
    save(fig, args.out_dir, "fig07_horizon_attention_change")

    # Figure 8: prediction maps; single-column stack with larger axis text.
    # Rebuild on relative windows 0--200 from the original t_index series
    # (absolute indices start at 30); do not zoom-crop a wider canvas.
    t_index = np.asarray(data["prediction_t_index"])
    t0 = int(t_index.min())
    t_rel_full = t_index - t0
    col_keep = np.flatnonzero((t_rel_full >= 0) & (t_rel_full <= 200))
    t_rel = t_rel_full[col_keep]
    prediction_matrices = (
        (data["prediction_truth"][keep][:, col_keep], "(a) Ground truth", CMAP_BINARY),
        (data["prediction_probability"][keep][:, col_keep], "(b) Predicted probability", CMAP_SEQUENTIAL),
        (data["prediction_absolute_error"][keep][:, col_keep], "(c) Absolute error", CMAP_ERROR),
    )
    fig, axes = plt.subplots(3, 1, figsize=(3.35, 5.9), sharex=True, constrained_layout=True)
    fig.set_constrained_layout_pads(h_pad=0.08, w_pad=0.02, hspace=0.12, wspace=0.02)
    x0, x1 = float(t_rel[0]) - 0.5, float(t_rel[-1]) + 0.5
    for ax, (matrix, title, cmap) in zip(axes, prediction_matrices):
        image = ax.imshow(
            matrix,
            aspect="auto",
            interpolation="nearest",
            cmap=cmap,
            vmin=0.0,
            vmax=1.0,
            extent=(x0, x1, len(labels) - 0.5, -0.5),
        )
        ax.set_yticks(np.arange(0, len(labels), 2))
        ax.set_yticklabels([labels[i] for i in range(0, len(labels), 2)])
        ax.tick_params(axis="y", labelsize=7, pad=1.5, length=2, width=0.6)
        from paper_plot_style import LABEL_SIZE, TITLE_SIZE
        ax.set_ylabel("Resource", fontsize=LABEL_SIZE)
        ax.set_title(title, loc="left", pad=2, fontsize=TITLE_SIZE)
        ax.set_xlim(0.0, 200.0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        for boundary in group_boundaries:
            ax.axhline(boundary - 0.5, color="white", lw=0.8)
        colorbar = fig.colorbar(image, ax=ax, fraction=0.045, pad=0.02)
        colorbar.ax.tick_params(labelsize=7, length=2, width=0.6)
        colorbar.outline.set_visible(False)
    tick_vals = [0, 50, 100, 150, 200]
    axes[2].set_xticks(tick_vals)
    axes[2].set_xticklabels([str(v) for v in tick_vals])
    axes[2].tick_params(axis="x", labelsize=7, length=2.5, width=0.6)
    from paper_plot_style import LABEL_SIZE as _LABEL_SIZE
    axes[2].set_xlabel("Test-window index (60 s)", fontsize=_LABEL_SIZE)
    save(fig, args.out_dir, "fig08_prediction_heatmaps")

    print(f"Wrote eight heatmap groups for {len(labels)} displayed non-buffer resources to {args.out_dir}")


if __name__ == "__main__":
    main()
