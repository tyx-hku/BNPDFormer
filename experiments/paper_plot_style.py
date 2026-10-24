"""Shared Matplotlib style for manuscript figures after Figure 4.

In-figure text uses Times New Roman. Sizes match Figure 4
(``fig_range_response``): axis/title 8 pt, tick/legend 7 pt in the PDF asset.
Figure 4 itself keeps its existing Arial asset and is not regenerated from here.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
from matplotlib import font_manager


# Match Figure 4 hard-coded sizes (pt in the figure PDF).
LABEL_SIZE = 8.0
TITLE_SIZE = 8.0
TICK_SIZE = 7.0
LEGEND_SIZE = 7.0
ANNOT_SIZE = 7.5


def apply(ink: str = "#243028") -> None:
    windows_fonts = Path("C:/Windows/Fonts")
    # Times New Roman (Windows); fall back to Liberation Serif / DejaVu Serif.
    for filename in (
        "times.ttf",
        "timesbd.ttf",
        "timesi.ttf",
        "timesbi.ttf",
        "LiberationSerif-Regular.ttf",
        "LiberationSerif-Bold.ttf",
    ):
        path = windows_fonts / filename
        if path.exists():
            font_manager.fontManager.addfont(str(path))
    matplotlib.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": [
                "Times New Roman",
                "Times",
                "Liberation Serif",
                "DejaVu Serif",
                "serif",
            ],
            "mathtext.fontset": "stix",
            "font.size": LABEL_SIZE,
            "axes.labelsize": LABEL_SIZE,
            "axes.titlesize": TITLE_SIZE,
            "xtick.labelsize": TICK_SIZE,
            "ytick.labelsize": TICK_SIZE,
            "legend.fontsize": LEGEND_SIZE,
            "axes.linewidth": 0.75,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "text.color": ink,
            "axes.labelcolor": ink,
            "xtick.color": ink,
            "ytick.color": ink,
        }
    )
