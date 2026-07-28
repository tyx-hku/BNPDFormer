#!/usr/bin/env python3
"""Build figures/fig_env_cameras.{pdf,png} from camera_views assets.

Layout (kept fixed):
  (a) factory overview
  (b) multi-camera views (2 x 4)
  (c) process-task chain + exemplar subtask tables
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.table import Table
from PIL import Image


# ---------- style knobs (edit here) ----------
FIG_W_IN = 11.0
DPI = 220

FS_PANEL = 13.0          # (a)/(b)/(c) titles
FS_CAM_CAP = 9.5         # camera captions (overlaid on image)
FS_TASK = 9.5            # process-task box text
FS_TASK_TAG = 8.0        # L1/P1 tags
FS_LEGEND = 9.5
FS_TABLE_TITLE = 10.0
FS_TABLE = 8.5
FS_NOTE = 8.5

PANEL_FACE = "#F5F7FA"
PANEL_EDGE = "#285AA0"
BORDER = "#3C3C3C"
LOGISTIC_FACE = "#E8F1FB"
PROCESS_FACE = "#FDEBD0"
TABLE_HEAD = "#E6EBF2"
TABLE_ALT = "#F8F9FB"

CAMERA_VIEWS = [
    ("camera_num00_storage_area.jpg", "Storage"),
    ("camera_num02_rollerbedCNCPipeIntersectionCuttingMachine_part01_station.jpg", "Cutting"),
    ("camera_num04_groovingMachineLarge_part01_large_fixed_base.jpg", "Grooving"),
    ("camera_num08_workbench.jpg", "Workbench"),
    ("camera_num01_weldingRobot_part02_robot_arm_and_base.jpg", "Welding robot"),
    ("camera_num00_rotaryPipeAutomaticWeldingMachine_part_01_station.jpg", "Rotary welding A"),
    ("camera_num00_rotaryPipeAutomaticWeldingMachine_part_02_station.jpg", "Rotary welding B"),
    ("camera_num00_highrise_for_env.jpg", "Highrise cam"),
]

PROCESS_ROW1 = [
    ("L1", "Logistic\n→ cutting", LOGISTIC_FACE),
    ("P1", "Pipe\ncutting", PROCESS_FACE),
    ("L2", "Logistic\n→ grooving", LOGISTIC_FACE),
    ("P2", "Pipe\ngrooving", PROCESS_FACE),
    ("L3", "Logistic\n→ spot", LOGISTIC_FACE),
    ("P3", "Batch spot\nwelding", PROCESS_FACE),
]
PROCESS_ROW2 = [
    ("L4", "Logistic\n→ arc", LOGISTIC_FACE),
    ("P4", "Arc welding\nroot", PROCESS_FACE),
    ("L5", "Logistic\n→ MIG", LOGISTIC_FACE),
    ("P5", "MIG welding\nsurface", PROCESS_FACE),
    ("L6", "Logistic\n→ paint", LOGISTIC_FACE),
    ("P6", "Paint &\nrust-proof", PROCESS_FACE),
]

TABLE_L = {
    "title": "Exemplar: logistic_for_pipe_cutting",
    "headers": ["Row", "Human", "Gantry", "Machine", "Robot"],
    "rows": [
        ["1", "go_to_material", "go_to_material", "wait", "go_to_material"],
        ["2", "material_on_gantry", "wait", "wait", "wait"],
        ["3", "control_gantry", "carry_to_robot", "wait", "wait"],
        ["4", "material_on_robot", "wait", "wait", "wait"],
        ["5", "go_to_goal_area", "move_to_goal", "wait", "carry_to_goal"],
    ],
}
TABLE_P = {
    "title": "Exemplar: pipe_cutting (processing)",
    "headers": ["Row", "Human", "Gantry", "Machine"],
    "rows": [
        ["1", "go_to_machine", "none", "wait"],
        ["2", "control_machine", "none", "process"],
        ["3", "wait", "find_gantry", "wait"],
        ["4", "control_gantry", "go_to_machine", "wait"],
        ["5", "material_on_gantry", "wait", "wait"],
    ],
}


def _panel_title(ax, text: str) -> None:
    ax.set_axis_off()
    ax.text(
        0.0,
        0.5,
        text,
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=FS_PANEL,
        fontweight="bold",
        color=PANEL_EDGE,
        bbox=dict(
            boxstyle="round,pad=0.28",
            facecolor=PANEL_FACE,
            edgecolor=PANEL_EDGE,
            linewidth=1.4,
        ),
    )


def _show_image(
    ax,
    path: Path,
    *,
    border: bool = True,
    caption: str | None = None,
) -> None:
    """Fill axes completely (no letterbox whitespace)."""
    img = Image.open(path).convert("RGB")
    ax.imshow(img, aspect="auto", interpolation="bilinear")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(-0.5, img.width - 0.5)
    ax.set_ylim(img.height - 0.5, -0.5)
    for spine in ax.spines.values():
        spine.set_visible(border)
        spine.set_color(BORDER)
        spine.set_linewidth(0.8)
    if caption:
        # Caption bar overlaid at bottom (no extra gap between tiles).
        ax.add_patch(
            mpatches.Rectangle(
                (0.0, 0.0),
                1.0,
                0.13,
                transform=ax.transAxes,
                facecolor=PANEL_FACE,
                edgecolor=BORDER,
                linewidth=0.6,
                zorder=3,
                clip_on=False,
            )
        )
        ax.text(
            0.5,
            0.065,
            caption,
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=FS_CAM_CAP,
            color="#141414",
            zorder=4,
            clip_on=False,
        )


def _draw_process_row(ax, steps) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()

    n = len(steps)
    gap = 0.012
    arrow = 0.018
    usable = 1.0 - (n - 1) * (gap + arrow)
    box_w = usable / n
    box_h = 0.78
    y0 = 0.11

    for i, (tag, label, face) in enumerate(steps):
        x0 = i * (box_w + gap + arrow)
        rect = mpatches.FancyBboxPatch(
            (x0, y0),
            box_w,
            box_h,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            linewidth=0.9,
            edgecolor=BORDER,
            facecolor=face,
            transform=ax.transAxes,
            clip_on=False,
        )
        ax.add_patch(rect)
        ax.text(
            x0 + 0.01,
            y0 + box_h - 0.08,
            tag,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=FS_TASK_TAG,
            color=PANEL_EDGE,
            fontweight="bold",
        )
        ax.text(
            x0 + box_w / 2,
            y0 + box_h / 2 - 0.02,
            label,
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=FS_TASK,
            color="#191919",
            linespacing=1.15,
        )
        if i < n - 1:
            ax_x0 = x0 + box_w + 0.004
            ax_x1 = x0 + box_w + arrow
            mid = y0 + box_h / 2
            ax.annotate(
                "",
                xy=(ax_x1, mid),
                xytext=(ax_x0, mid),
                xycoords=ax.transAxes,
                textcoords=ax.transAxes,
                arrowprops=dict(arrowstyle="-|>", color=BORDER, lw=1.2),
            )


def _draw_table(ax, spec: dict) -> None:
    ax.set_axis_off()
    ax.text(
        0.0,
        1.02,
        spec["title"],
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=FS_TABLE_TITLE,
        color=PANEL_EDGE,
        fontweight="bold",
        clip_on=False,
    )

    headers = spec["headers"]
    rows = spec["rows"]
    n_cols = len(headers)
    n_rows = len(rows)

    table = Table(ax, bbox=[0.0, 0.0, 1.0, 0.96])
    col_w = 1.0 / n_cols
    row_h = 1.0 / (n_rows + 1)

    for j, h in enumerate(headers):
        cell = table.add_cell(
            0,
            j,
            width=col_w,
            height=row_h,
            text=h,
            loc="center",
            facecolor=TABLE_HEAD,
            edgecolor=BORDER,
        )
        cell.get_text().set_fontsize(FS_TABLE)
        cell.get_text().set_fontweight("bold")

    for i, row in enumerate(rows, start=1):
        face = "#FFFFFF" if i % 2 == 1 else TABLE_ALT
        for j, val in enumerate(row):
            cell = table.add_cell(
                i,
                j,
                width=col_w,
                height=row_h,
                text=val,
                loc="center",
                facecolor=face,
                edgecolor=BORDER,
            )
            cell.get_text().set_fontsize(FS_TABLE)

    ax.add_table(table)


def build_figure(cam_dir: Path, out_pdf: Path, out_png: Path) -> None:
    env_path = cam_dir / "env_screen_shot.png"
    if not env_path.exists():
        raise FileNotFoundError(env_path)

    # Size panels from image aspects so (a)/(b) fill width with minimal whitespace.
    content_w_in = FIG_W_IN * 0.95
    env = Image.open(env_path)
    env_h_in = content_w_in * (env.height / env.width)
    # 4 columns, 2 rows, 3:2 camera frames, zero gaps
    cam_cell_w_in = content_w_in / 4.0
    cam_cell_h_in = cam_cell_w_in * (720.0 / 1080.0)
    cam_h_in = 2.0 * cam_cell_h_in
    title_h_in = 0.32
    panel_c_h_in = 3.55
    gap_h_in = 0.06
    note_h_in = 0.22
    fig_h_in = (
        3 * title_h_in
        + env_h_in
        + cam_h_in
        + panel_c_h_in
        + 4 * gap_h_in
        + note_h_in
    )

    fig = plt.figure(figsize=(FIG_W_IN, fig_h_in), dpi=DPI)
    outer = GridSpec(
        6,
        1,
        figure=fig,
        height_ratios=[title_h_in, env_h_in, title_h_in, cam_h_in, title_h_in, panel_c_h_in],
        hspace=gap_h_in / max(env_h_in, 1e-6),
        left=0.025,
        right=0.975,
        top=0.992,
        bottom=note_h_in / fig_h_in,
    )

    # (a)
    _panel_title(fig.add_subplot(outer[0, 0]), "(a) Factory overview")
    ax_env = fig.add_subplot(outer[1, 0])
    _show_image(ax_env, env_path)

    # (b)
    _panel_title(fig.add_subplot(outer[2, 0]), "(b) Multi-camera views")
    cam_gs = GridSpecFromSubplotSpec(
        2,
        4,
        subplot_spec=outer[3, 0],
        wspace=0.0,
        hspace=0.0,
    )
    for i, (fname, caption) in enumerate(CAMERA_VIEWS):
        r, c = divmod(i, 4)
        ax = fig.add_subplot(cam_gs[r, c])
        _show_image(ax, cam_dir / fname, caption=caption)

    # (c)
    _panel_title(
        fig.add_subplot(outer[4, 0]),
        "(c) Process tasks and exemplar subtask rows",
    )
    c_gs = GridSpecFromSubplotSpec(
        4,
        2,
        subplot_spec=outer[5, 0],
        height_ratios=[0.28, 0.28, 0.10, 0.55],
        hspace=0.18,
        wspace=0.06,
    )

    ax_r1 = fig.add_subplot(c_gs[0, :])
    _draw_process_row(ax_r1, PROCESS_ROW1)
    ax_r2 = fig.add_subplot(c_gs[1, :])
    _draw_process_row(ax_r2, PROCESS_ROW2)

    ax_leg = fig.add_subplot(c_gs[2, :])
    ax_leg.set_axis_off()
    ax_leg.set_xlim(0, 1)
    ax_leg.set_ylim(0, 1)
    ax_leg.add_patch(
        mpatches.FancyBboxPatch(
            (0.005, 0.25),
            0.025,
            0.45,
            boxstyle="round,pad=0.004",
            facecolor=LOGISTIC_FACE,
            edgecolor=BORDER,
            transform=ax_leg.transAxes,
        )
    )
    ax_leg.text(0.04, 0.45, "Logistic task", transform=ax_leg.transAxes, va="center", fontsize=FS_LEGEND)
    ax_leg.add_patch(
        mpatches.FancyBboxPatch(
            (0.22, 0.25),
            0.025,
            0.45,
            boxstyle="round,pad=0.004",
            facecolor=PROCESS_FACE,
            edgecolor=BORDER,
            transform=ax_leg.transAxes,
        )
    )
    ax_leg.text(0.255, 0.45, "Processing task", transform=ax_leg.transAxes, va="center", fontsize=FS_LEGEND)

    ax_tl = fig.add_subplot(c_gs[3, 0])
    _draw_table(ax_tl, TABLE_L)
    ax_tr = fig.add_subplot(c_gs[3, 1])
    _draw_table(ax_tr, TABLE_P)

    # # bottom note under tables
    # fig.text(
    #     0.035,
    #     0.008,
    #     "Full process-task gallery (12 tasks) and complete subtask tables are listed in the manuscript table.",
    #     fontsize=FS_NOTE,
    #     color="#505050",
    #     ha="left",
    #     va="bottom",
    # )

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf)
    fig.savefig(out_png)
    plt.close(fig)
    print(f"[plot] wrote {out_pdf}")
    print(f"[plot] wrote {out_png}")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cam-dir",
        type=Path,
        default=root / "figures" / "camera_views",
        help="Directory with env_screen_shot.png and camera_*.jpg",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=root / "figures",
        help="Output directory for fig_env_cameras.{pdf,png}",
    )
    args = parser.parse_args()
    build_figure(
        cam_dir=args.cam_dir,
        out_pdf=args.out_dir / "fig_env_cameras.pdf",
        out_png=args.out_dir / "fig_env_cameras.png",
    )


if __name__ == "__main__":
    main()
