"""Plot the common-test cause recalls recorded in dev_tyx commit 8767583.

Run from any directory: python experiments/plot_label_validity.py
The source JSON records the report, commit, and numerical precision. This
script visualizes published summary values; it does not re-run evaluation.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
FONT = Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf")
if FONT.is_file():
    font_manager.fontManager.addfont(str(FONT))
    family = "Times New Roman"
else:
    family = "DejaVu Serif"

plt.rcParams.update({
    "font.family": family,
    "font.size": 9,
    "axes.labelsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

data = json.loads((ROOT / "experiments/data/label_validity_dev_tyx_8767583.json").read_text())
rows = {r["method"]: r for r in data["cause_comparison"]["metrics"]}
methods = ["Ops", "TPM", "Active Period", "Utilization", "Queue-Wait"]
classes = list(data["cause_comparison"]["class_support"])
assert sum(data["cause_comparison"]["class_support"].values()) == data["cause_comparison"]["n_test"]
values = np.array([[rows[m][c] for c in classes] for m in methods])
assert values.shape == (5, 4) and np.all((values >= 0) & (values <= 1))

fig, ax = plt.subplots(figsize=(6.9, 2.55), layout="constrained")
im = ax.imshow(values, cmap="Blues", vmin=0, vmax=1, aspect="auto")
ax.set_yticks(range(5), methods)
ax.set_xticks(range(4), ["Transport delay", "Material shortage", "Upstream starvation", "Queue buildup"])
ax.tick_params(axis="both", length=0, pad=7)
for (i, j), value in np.ndenumerate(values):
    ax.text(j, i, f"{value:.3f}", ha="center", va="center",
            color="white" if value >= .65 else "black", fontsize=10)
ax.set_xticks(np.arange(-.5, 4, 1), minor=True)
ax.set_yticks(np.arange(-.5, 5, 1), minor=True)
ax.grid(which="minor", color="white", linewidth=1)
ax.tick_params(which="minor", length=0)
for spine in ax.spines.values():
    spine.set_visible(False)
cbar = fig.colorbar(im, ax=ax, fraction=.035, pad=.025, ticks=[0, .25, .5, .75, 1])
cbar.set_label("Class recall")
cbar.outline.set_linewidth(.5)
out = ROOT / "figures/label_method_cause_recall"
fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight", pad_inches=.04)
fig.savefig(out.with_suffix(".png"), dpi=300, bbox_inches="tight", pad_inches=.04)
print(out.with_suffix(".pdf"))
