#!/usr/bin/env python3
"""Plot ICCBEI paper figures from hc_factory paper_exp raw JSON.

Does not re-train; only reads metrics/ and run histories.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def plot_learning_curve(raw: Path, out: Path) -> None:
    metrics = raw / "metrics"
    xs, id_acc, sub_acc, done_acc = [], [], [], []
    for frac in (25, 50, 75, 100):
        p_id = metrics / f"curve_id_f{frac:03d}_test.json"
        p_sub = metrics / f"curve_subtask_f{frac:03d}_test.json"
        if not p_id.exists() or not p_sub.exists():
            continue
        xs.append(frac)
        id_acc.append(_load(p_id).get("elem_acc"))
        sub_acc.append(_load(p_sub).get("subtask_acc"))
        done_acc.append(_load(p_sub).get("done_acc"))
    if not xs:
        print("[plot] no learning-curve metrics yet")
        return
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.plot(xs, id_acc, "o-", label="Task A elem_acc")
    ax.plot(xs, sub_acc, "s-", label="Task B subtask_acc")
    ax.plot(xs, done_acc, "^-", label="Task B done_acc")
    ax.set_xlabel("Training data fraction (%)")
    ax.set_ylabel("In-distribution test accuracy")
    ax.set_xticks(xs)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    print(f"[plot] wrote {out}")


def plot_confusion(raw: Path, out: Path) -> None:
    p = raw / "metrics" / "subtask_source_test_detailed.json"
    if not p.exists():
        print("[plot] missing detailed subtask metrics")
        return
    m = _load(p)
    cm = np.asarray(m["confusion_matrix"], dtype=float)
    names = m.get("class_names") or [str(i) for i in range(cm.shape[0])]
    row_sum = cm.sum(axis=1, keepdims=True)
    cm_n = np.divide(cm, np.maximum(row_sum, 1.0))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    im = axes[0].imshow(cm_n, cmap="Blues", vmin=0, vmax=1)
    axes[0].set_title("Subtask confusion (row-norm)")
    axes[0].set_xticks(range(len(names)))
    axes[0].set_yticks(range(len(names)))
    axes[0].set_xticklabels(names, rotation=90, fontsize=6)
    axes[0].set_yticklabels(names, fontsize=6)
    fig.colorbar(im, ax=axes[0], fraction=0.046)
    done = m.get("done_acc_by_subtask") or {}
    axes[1].bar(range(len(names)), [done.get(n, 0.0) for n in names], color="#2F855A")
    axes[1].set_ylim(0, 1)
    axes[1].set_xticks(range(len(names)))
    axes[1].set_xticklabels(names, rotation=90, fontsize=6)
    axes[1].set_title("Done acc by GT subtask")
    axes[1].grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    print(f"[plot] wrote {out}")


def summarize_tpa(raw: Path, out: Path) -> None:
    p = raw / "metrics" / "tpa_grid.json"
    if not p.exists():
        print("[plot] missing tpa_grid.json (run job 39)")
        return
    grid = _load(p).get("grid", {})
    lines = ["setting,success_n,makespan_mean,idle_h_mean,idle_m_mean"]
    for k in sorted(grid.keys()):
        g = grid[k]
        lines.append(
            f"{k},{g.get('success_n')},{g.get('makespan_mean')},{g.get('idle_h_mean')},{g.get('idle_m_mean')}"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[plot] wrote {out}")


def summarize_ood(raw: Path, out: Path) -> None:
    metrics = raw / "metrics"
    rows = ["setting,acc_a,acc_b,done"]
    for p in sorted(metrics.glob("ood_id_Nh*_O*.json")):
        m = re.match(r"ood_id_(Nh\d+_O\d+)\.json", p.name)
        if not m:
            continue
        cell = m.group(1)
        idm = _load(p)
        subp = metrics / f"ood_subtask_{cell}.json"
        if not subp.exists():
            continue
        sub = _load(subp)
        rows.append(
            f"{cell},{idm.get('elem_acc')},{sub.get('subtask_acc')},{sub.get('done_acc')}"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"[plot] wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, required=True, help="Path to paper_exp root")
    ap.add_argument("--out", type=Path, default=Path("figures"))
    args = ap.parse_args()
    plot_learning_curve(args.raw, args.out / "fig_learning_curve.pdf")
    plot_confusion(args.raw, args.out / "fig_subtask_cm.pdf")
    summarize_tpa(args.raw, args.out / "tpa_grid_summary.csv")
    summarize_ood(args.raw, args.out / "ood_grid_summary.csv")


if __name__ == "__main__":
    main()
