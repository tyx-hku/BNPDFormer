#!/usr/bin/env python3
"""Plot encoder attention for the selected manuscript layers 1, 4, and 5."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from plot_ch5_attention_heatmaps import boundaries, filter_square, heatmap, save, style


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "figures/attention_heatmaps/heatmap_matrices.npz"
OUT_DIR = ROOT / "figures/attention_heatmaps"
SELECTED_LAYERS = (1, 4, 5)


def main() -> None:
    style()
    with np.load(INPUT, allow_pickle=False) as loaded:
        data = {key: loaded[key] for key in loaded.files}

    all_types = data["resource_types"].astype(str)
    keep = np.flatnonzero(all_types != "buffer")
    labels = data["short_labels"][keep].astype(str).tolist()
    resource_types = all_types[keep].tolist()
    group_boundaries = boundaries(resource_types)
    if len(keep) != 20 or any(label.startswith("B") for label in labels):
        raise RuntimeError("expected 20 non-buffer resources after filtering")

    # Preserve the full five-layer scale so the selected and appendix figures
    # remain directly comparable.
    all_geo = [
        filter_square(data[f"start5_geo_upcoming_layer{i}"], keep)
        for i in range(1, 6)
    ]
    all_sem = [
        filter_square(data[f"start5_sem_upcoming_layer{i}"], keep)
        for i in range(1, 6)
    ]
    vmax_geo = max(float(array.max()) for array in all_geo)
    vmax_sem = max(float(array.max()) for array in all_sem)

    fig, axes = plt.subplots(2, 3, figsize=(7.2, 5.1), constrained_layout=True)
    fig.set_constrained_layout_pads(h_pad=0.10, w_pad=0.04, hspace=0.18, wspace=0.06)
    for column, layer in enumerate(SELECTED_LAYERS):
        geo_image = heatmap(
            axes[0, column],
            all_geo[layer - 1],
            labels,
            f"Geo layer {layer}",
            vmin=0.0,
            vmax=vmax_geo,
            group_boundaries=group_boundaries,
            tick_step=2,
            ylabel="Query resource" if column == 0 else None,
        )
        sem_image = heatmap(
            axes[1, column],
            all_sem[layer - 1],
            labels,
            f"Semantic layer {layer}",
            vmin=0.0,
            vmax=vmax_sem,
            group_boundaries=group_boundaries,
            tick_step=2,
            ylabel="Query resource" if column == 0 else None,
        )
    fig.colorbar(
        geo_image,
        ax=axes[0, :],
        fraction=0.018,
        pad=0.014,
        label="Attention weight",
    )
    fig.colorbar(
        sem_image,
        ax=axes[1, :],
        fraction=0.018,
        pad=0.014,
        label="Attention weight",
    )
    save(fig, OUT_DIR, "fig05_layerwise_upcoming_attention_selected")
    print("Wrote selected layer-wise attention figure for layers 1, 4, and 5")


if __name__ == "__main__":
    main()
