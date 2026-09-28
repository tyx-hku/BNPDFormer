#!/usr/bin/env python3
"""Build figures/fig_env_cameras.{pdf,png} from camera_views assets.

Layout:
  (a) factory overview
  (b) multi-camera views (2 x 4)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from PIL import Image


# ---------- style knobs (edit here) ----------
FIG_W_IN = 11.0
DPI = 220

FS_PANEL = 13.0
FS_CAM_CAP = 9.5

PANEL_FACE = "#F5F7FA"
PANEL_EDGE = "#285AA0"
BORDER = "#3C3C3C"

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


def build_figure(cam_dir: Path, out_pdf: Path, out_png: Path) -> None:
    env_path = cam_dir / "env_screen_shot.png"
    if not env_path.exists():
        raise FileNotFoundError(env_path)

    content_w_in = FIG_W_IN * 0.95
    env = Image.open(env_path)
    env_h_in = content_w_in * (env.height / env.width)
    cam_cell_w_in = content_w_in / 4.0
    cam_cell_h_in = cam_cell_w_in * (720.0 / 1080.0)
    cam_h_in = 2.0 * cam_cell_h_in
    title_h_in = 0.32
    gap_h_in = 0.06
    fig_h_in = 2 * title_h_in + env_h_in + cam_h_in + 2 * gap_h_in

    fig = plt.figure(figsize=(FIG_W_IN, fig_h_in), dpi=DPI)
    outer = GridSpec(
        4,
        1,
        figure=fig,
        height_ratios=[title_h_in, env_h_in, title_h_in, cam_h_in],
        hspace=gap_h_in / max(env_h_in, 1e-6),
        left=0.025,
        right=0.975,
        top=0.992,
        bottom=0.01,
    )

    _panel_title(fig.add_subplot(outer[0, 0]), "(a) Factory overview")
    ax_env = fig.add_subplot(outer[1, 0])
    _show_image(ax_env, env_path)

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
