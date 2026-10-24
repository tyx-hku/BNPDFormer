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
# Same-hue pair (#78B7C9 → #46788E) transitions cleanly; yellow→blue midtones look muddy.
# Near-white low end keeps zero cells readable without leaving the blue family.
CMAP_SEQUENTIAL = LinearSegmentedColormap.from_list(
    "research_sequential",
    ["#F4FAFC", PALETTE["light_blue"], PALETTE["deep_teal"]],
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
    matplotlib.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "axes.linewidth": 0.8,
            "figure.dpi": 150,
            "savefig.dpi": 600,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.04,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def save(fig: plt.Figure, out_dir: Path, stem: str) -> None:
    for suffix in ("pdf", "png", "svg"):
        fig.savefig(out_dir / f"{stem}.{suffix}", dpi=600 if suffix == "png" else None)
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
    ax.set_title(title, pad=5)
    if labels is not None:
        ticks = np.arange(0, len(labels), max(1, tick_step))
        ax.set_xticks(ticks)
        ax.set_yticks(ticks)
        ax.set_xticklabels([labels[i] for i in ticks], rotation=90)
        ax.set_yticklabels([labels[i] for i in ticks])
        ax.set_xlabel("Attended resource")
        ax.set_ylabel("Query resource")
    for boundary in group_boundaries or []:
        ax.axhline(boundary - 0.5, color="white", lw=0.8)
        ax.axvline(boundary - 0.5, color="white", lw=0.8)
    if annotate:
        scale = max(float(np.nanmax(np.abs(matrix))), 1e-9)
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                value = matrix[i, j]
                color = "white" if abs(value) > 0.55 * scale else "black"
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=7, color=color)
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
    fig, axes = plt.subplots(2, 3, figsize=(12.6, 8.0), constrained_layout=True)
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
    fig, axes = plt.subplots(2, 2, figsize=(8.7, 7.6), constrained_layout=True)
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

    # Figure 4: temporal attention has no resource-labelled axis and is unchanged.
    temporal = {condition: data[f"start5_temporal_{condition}"] for condition in CONDITIONS}
    temporal_delta = data["start5_temporal_upcoming_minus_normal"]
    vmax_temporal = max(float(array.max()) for array in temporal.values())
    delta_temporal_max = float(np.abs(temporal_delta).max())
    fig, axes = plt.subplots(1, 4, figsize=(14.2, 3.5), constrained_layout=True)
    time_labels = [str(i + 1) if i % 3 == 0 else "" for i in range(temporal["normal"].shape[0])]
    for col, condition in enumerate(CONDITIONS):
        image = heatmap(
            axes[col],
            temporal[condition],
            time_labels,
            f"({chr(97 + col)}) {CONDITION_TITLES[condition]}",
            vmin=0.0,
            vmax=vmax_temporal,
        )
        axes[col].set_xlabel("Attended history step")
        axes[col].set_ylabel("Query history step")
    fig.colorbar(image, ax=axes[:3], fraction=0.022, pad=0.018, label="Attention weight")
    temporal_norm = TwoSlopeNorm(vmin=-delta_temporal_max, vcenter=0.0, vmax=delta_temporal_max)
    image = heatmap(
        axes[3], temporal_delta, time_labels, "(d) Upcoming - normal", cmap=CMAP_DIVERGING, norm=temporal_norm
    )
    axes[3].set_xlabel("Attended history step")
    axes[3].set_ylabel("Query history step")
    fig.colorbar(image, ax=axes[3], fraction=0.046, pad=0.025, label="Change")
    save(fig, args.out_dir, "fig04_temporal_attention_states")

    # Figure 5: layer-wise upcoming attention.
    depth = 5
    layer_geo = [filter_square(data[f"start5_geo_upcoming_layer{i}"], keep) for i in range(1, depth + 1)]
    layer_sem = [filter_square(data[f"start5_sem_upcoming_layer{i}"], keep) for i in range(1, depth + 1)]
    vmax_geo = max(float(array.max()) for array in layer_geo)
    vmax_sem = max(float(array.max()) for array in layer_sem)
    fig, axes = plt.subplots(2, depth, figsize=(15.2, 6.1), constrained_layout=True)
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
    fig, axes = plt.subplots(2, 3, figsize=(10.4, 6.5), constrained_layout=True)
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
    horizon_keys = (("Startlt5", "Start<=5"), ("Startlt10", "Start<=10"), ("Startlt15", "Start<=15"))
    horizon = {
        (title, kind): filter_square(data[f"{key}_{kind}_upcoming_minus_normal"], keep)
        for key, title in horizon_keys
        for kind in ("geo", "sem")
    }
    horizon_max = max(float(np.abs(array).max()) for array in horizon.values())
    horizon_norm = TwoSlopeNorm(vmin=-horizon_max, vcenter=0.0, vmax=horizon_max)
    fig, axes = plt.subplots(3, 2, figsize=(8.7, 10.8), constrained_layout=True)
    for row, (_, title) in enumerate(horizon_keys):
        for col, kind in enumerate(("geo", "sem")):
            image = heatmap(
                axes[row, col],
                horizon[(title, kind)],
                labels,
                f"({chr(97 + row * 2 + col)}) {title} {kind}: upcoming - normal",
                cmap=CMAP_DIVERGING,
                norm=horizon_norm,
                group_boundaries=group_boundaries,
            )
    fig.colorbar(image, ax=axes, fraction=0.018, pad=0.018, label="Attention-weight change")
    save(fig, args.out_dir, "fig07_horizon_attention_change")

    # Figure 8: prediction maps for the displayed non-buffer resources.
    t_index = data["prediction_t_index"]
    prediction_matrices = (
        (data["prediction_truth"][keep], "(a) Future bottleneck ground truth", CMAP_BINARY),
        (data["prediction_probability"][keep], "(b) Predicted bottleneck probability", CMAP_SEQUENTIAL),
        (data["prediction_absolute_error"][keep], "(c) Absolute probability error", CMAP_ERROR),
    )
    fig, axes = plt.subplots(3, 1, figsize=(12.0, 6.4), sharex=True, constrained_layout=True)
    for ax, (matrix, title, cmap) in zip(axes, prediction_matrices):
        image = ax.imshow(matrix, aspect="auto", interpolation="nearest", cmap=cmap, vmin=0.0, vmax=1.0)
        ax.set_yticks(np.arange(len(labels)))
        ax.set_yticklabels(labels)
        ax.set_ylabel("Resource")
        ax.set_title(title, loc="left")
        for boundary in group_boundaries:
            ax.axhline(boundary - 0.5, color="white", lw=0.7)
        fig.colorbar(image, ax=ax, fraction=0.018, pad=0.012)
    tick_pos = np.linspace(0, len(t_index) - 1, min(10, len(t_index)), dtype=int)
    axes[2].set_xticks(tick_pos)
    axes[2].set_xticklabels([str(t_index[i]) for i in tick_pos])
    axes[2].set_xlabel("Test-window index (60 s)")
    save(fig, args.out_dir, "fig08_prediction_heatmaps")

    print(f"Wrote eight heatmap groups for {len(labels)} displayed non-buffer resources to {args.out_dir}")


if __name__ == "__main__":
    main()
