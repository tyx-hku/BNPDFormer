"""Render the English key-device figure from its existing exported series.

Keep device/episode context in the manuscript caption, not above the panels.
The CSV is read unchanged; archived raster traces are not digitized again.
"""

from pathlib import Path
import csv

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patheffects as pe

from paper_plot_style import LEGEND_SIZE, TITLE_SIZE, apply


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/data/key_device_entity_series.csv"
OUTPUT = ROOT / "main_en/figures/key_device_entity"


def main() -> None:
    apply()
    with SOURCE.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    series = {
        key: np.array([float(row[key]) if row[key] else np.nan for row in rows])
        for key in rows[0]
    }
    colors = ["#5BA7D9", "#F26121", "#00A651", "#9B2DCF"]
    styles = [(0, (4, 1.6)), (0, (1.2, 1.1)),
              (0, (1, 1.3)), (0, (3, 1.2, 1, 1.2))]
    panels = [
        ("(a) Multi-entity ablations", [
            ("PHGST-DP", "PHGST-DM"),
            ("MachineOnly", "WorkstationOnly"),
            ("NoCross", "NoCross"),
            ("NoInfo", "NoInfo"),
        ]),
        ("(b) Effect of onset limit", [
            ("Start_le5", "Onset limit ≤ 5 min"),
            ("Start_le10", "Onset limit ≤ 10 min"),
            ("Start_le15", "Onset limit ≤ 15 min"),
        ]),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.85), sharey=True)
    for ax, (title, curves) in zip(axes, panels):
        (reference,) = ax.plot(
            series["window"], series["true_dur"], color="black", lw=1.35,
            label="True", zorder=5,
            solid_capstyle="round", solid_joinstyle="round",
        )
        reference.set_path_effects([
            pe.Stroke(linewidth=2.3, foreground="white"), pe.Normal(),
        ])
        for i, (key, label) in enumerate(curves):
            ax.plot(series["window"], series[key], color=colors[i],
                    lw=1.45 if i == 0 else 1.2, ls=styles[i], label=label)
        ax.set(xlim=(0, 150), ylim=(-0.8, 21), yticks=[0, 5, 10, 15, 20],
               xlabel="Window index (60 s)")
        ax.spines[["top", "right"]].set_visible(False)
        for side in ("bottom", "left"):
            ax.spines[side].set_color("#9AA3A8")
        ax.tick_params(colors="#333333")
        ax.set_axisbelow(True)
        ax.grid(alpha=0.3, lw=0.6)
        ax.set_title(title, loc="left", fontsize=TITLE_SIZE, pad=5)
        ax.legend(loc="upper left", fontsize=LEGEND_SIZE, frameon=False,
                  ncol=1, handlelength=2.2, handletextpad=0.7)
    axes[0].set_ylabel("Bottleneck duration (min)")
    axes[1].tick_params(labelleft=False)
    fig.tight_layout(pad=0.4, w_pad=0.6)
    fig.savefig(OUTPUT.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.03)
    fig.savefig(OUTPUT.with_suffix(".png"), dpi=220,
                bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print(f"Rendered {OUTPUT.with_suffix('.pdf')}")


if __name__ == "__main__":
    main()
