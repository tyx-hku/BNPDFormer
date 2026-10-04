#!/usr/bin/env python3
"""PHAST-DP framework figure as an editable PPTX; PDF/PNG are exported from it via PowerPoint."""

from __future__ import annotations

import math
import subprocess
from collections import deque
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from lxml import etree
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "figures" / "raw"
ASSETS = RAW / "framework_assets"
OUT = ROOT / "figures" / "fig_method_framework"

SW, SH = 14.4, 9.0

RED = "CB001C"
ORANGE = "F26121"
AMBER = "FCB84D"
CREAM = "FFF2C7"
LBLUE = "A6DCED"
MBLUE = "5BA7D9"
DBLUE = "3D6EB4"
INK = "262626"
MUTED = "595959"
GRAY = "8C8C8C"
LGRAY = "BFBFBF"

FONT = "Arial"
SYMBOL_FONT = "Segoe UI Symbol"

ENTITY = {"machine": DBLUE, "gantry": MBLUE, "robot": LBLUE, "human": AMBER, "buffer": GRAY}


def rgb(hexcolor: str) -> RGBColor:
    return RGBColor.from_string(hexcolor.lstrip("#"))


def E(v: float) -> Emu:
    return Emu(int(round(v * 914400)))


# --------------------------------------------------------------------------- assets


def knock_bg(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    h, w = arr.shape[:2]
    bg = arr[0, 0, :3].astype(np.int16)
    if bg.mean() > 225 or bg.mean() < 35:
        near = np.abs(arr[..., :3].astype(np.int16) - bg).sum(axis=-1) < 36
        seen = np.zeros((h, w), dtype=bool)
        q: deque[tuple[int, int]] = deque()
        for x in range(w):
            q.extend([(0, x), (h - 1, x)])
        for y in range(h):
            q.extend([(y, 0), (y, w - 1)])
        while q:
            y, x = q.popleft()
            if seen[y, x] or not near[y, x]:
                continue
            seen[y, x] = True
            arr[y, x, 3] = 0
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx]:
                    q.append((ny, nx))
    return Image.fromarray(arr)


def build_assets() -> dict[str, Path]:
    ASSETS.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    for key, src in {
        "human": RAW / "figure1_assets" / "icon_human_onwhite.png",
        "machine": RAW / "methodology_prep" / "icon_machine.png",
        "material": RAW / "figure1_assets" / "icon_material_onwhite.png",
        "agv": RAW / "figure1_assets" / "icon_agv_onwhite.png",
    }.items():
        p = ASSETS / f"icon_{key}.png"
        knock_bg(src).save(p)
        out[key] = p

    rng = np.random.default_rng(7)
    cmaps = [
        LinearSegmentedColormap.from_list("l2", ["#FFFFFF", "#" + CREAM, "#" + AMBER]),
        LinearSegmentedColormap.from_list("l1", ["#FFFFFF", "#" + LBLUE, "#" + MBLUE]),
        LinearSegmentedColormap.from_list("l0", ["#FFFFFF", "#" + LBLUE, "#" + MBLUE, "#" + DBLUE]),
    ]
    for k, cmap in enumerate(cmaps):
        base = rng.random((38, 30)) ** 2.0
        base[7:11, 18:28] += 0.75
        base[2:4, 12:24] += 0.6
        fig = plt.figure(figsize=(3.0, 2.4), dpi=200)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.imshow(np.clip(base, 0, 1.2), cmap=cmap, vmin=0, vmax=1.2, aspect="auto", interpolation="nearest")
        ax.axis("off")
        p = ASSETS / f"tensor_{k}.png"
        fig.savefig(p)
        plt.close(fig)
        out[f"tensor_{k}"] = p
    out["factory"] = RAW / "methodology_prep" / "factory.jpg"
    return out


# --------------------------------------------------------------------------- drawing


class Canvas:
    def __init__(self, shapes):
        self.sh = shapes

    def box(self, x, y, w, h, fill=None, line=None, lw=1.0, radius=0.08, dash=None, shape=None):
        kind = shape or (MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE)
        s = self.sh.add_shape(kind, E(x), E(y), E(w), E(h))
        if radius and kind in (MSO_SHAPE.ROUNDED_RECTANGLE, MSO_SHAPE.ROUND_2_SAME_RECTANGLE):
            s.adjustments[0] = min(0.5, radius / min(w, h))
        if fill:
            s.fill.solid()
            s.fill.fore_color.rgb = rgb(fill)
        else:
            s.fill.background()
        if line:
            s.line.color.rgb = rgb(line)
            s.line.width = Pt(lw)
            if dash:
                s.line.dash_style = dash
        else:
            s.line.fill.background()
        s.shadow.inherit = False
        return s

    def circle(self, cx, cy, r, fill, line=None, lw=0.75):
        return self.box(cx - r, cy - r, 2 * r, 2 * r, fill, line, lw, radius=0, shape=MSO_SHAPE.OVAL)

    def star(self, cx, cy, r, fill, line=INK):
        return self.box(cx - r, cy - r, 2 * r, 2 * r, fill, line, 0.5, radius=0, shape=MSO_SHAPE.STAR_5_POINT)

    def text(self, x, y, w, h, paragraphs, size=10, color=INK, bold=False, italic=False,
             align="l", anchor="m", wrap=False):
        tb = self.sh.add_textbox(E(x), E(y), E(w), E(h))
        tf = tb.text_frame
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.word_wrap = wrap
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
        if isinstance(paragraphs, str):
            paragraphs = paragraphs.split("\n")
        for i, para in enumerate(paragraphs):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
            runs = [(para, {})] if isinstance(para, str) else para
            for chunk, style in runs:
                self._runs(p, chunk, dict(size=size, color=color, bold=bold, italic=italic) | style)
        return tb

    @staticmethod
    def _runs(p, chunk, st):
        pos = 0
        for token in _tokens(chunk):
            kind, body = token
            r = p.add_run()
            r.text = body
            f = r.font
            f.name = st.get("font", FONT)
            f.size = Pt(st["size"])
            f.bold = st["bold"]
            f.italic = st["italic"]
            f.color.rgb = rgb(st["color"])
            if kind != "n":
                r._r.get_or_add_rPr().set("baseline", "-25000" if kind == "sub" else "30000")
            pos += 1

    def _style_line(self, line, color, lw, dash, head, tail):
        line.color.rgb = rgb(color)
        line.width = Pt(lw)
        if dash:
            line.dash_style = dash
        ln = line._get_or_add_ln()
        for tag, on in (("a:headEnd", head), ("a:tailEnd", tail)):
            if on:
                el = etree.SubElement(ln, qn(tag))
                el.set("type", "triangle")
                el.set("w", "med")
                el.set("len", "med")

    def line(self, pts, color=MUTED, lw=1.25, dash=None, arrow=False, head=False):
        if len(pts) == 2:
            (x1, y1), (x2, y2) = pts
            c = self.sh.add_connector(MSO_CONNECTOR.STRAIGHT, E(x1), E(y1), E(x2), E(y2))
            self._style_line(c.line, color, lw, dash, head, arrow)
            return c
        b = self.sh.build_freeform(E(pts[0][0]), E(pts[0][1]), scale=1.0)
        b.add_line_segments([(E(x), E(y)) for x, y in pts[1:]], close=False)
        s = b.convert_to_shape()
        s.fill.background()
        s.shadow.inherit = False
        self._style_line(s.line, color, lw, dash, head, arrow)
        return s

    def curve(self, p0, p1, bend, **kw):
        (x0, y0), (x1, y1) = p0, p1
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy) or 1.0
        cx, cy = mx - dy / n * bend, my + dx / n * bend
        pts = [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1,
                (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1) for t in np.linspace(0, 1, 18)]
        return self.line(pts, **kw)

    def polygon(self, pts, fill, line=None):
        b = self.sh.build_freeform(E(pts[0][0]), E(pts[0][1]), scale=1.0)
        b.add_line_segments([(E(x), E(y)) for x, y in pts[1:]], close=True)
        s = b.convert_to_shape()
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
        if line:
            s.line.color.rgb = rgb(line)
            s.line.width = Pt(0.5)
        else:
            s.line.fill.background()
        s.shadow.inherit = False
        return s

    def picture(self, path, x, y, w, h):
        return self.sh.add_picture(str(path), E(x), E(y), E(w), E(h))

    def strip(self, x, y, w, h, cells, colors, edge=LGRAY):
        cw = w / len(cells)
        for i, c in enumerate(cells):
            self.box(x + i * cw, y, cw, h, colors[c], edge, 0.4, radius=0)

    def bracket(self, x0, x1, y, color, label, size=10):
        self.line([(x0, y - 0.04), (x0, y), (x1, y), (x1, y - 0.04)], color=color, lw=0.9)
        self.text(x0, y + 0.01, x1 - x0, 0.2, label, size=size, color=color, align="c", bold=True)

    def bolt(self, x, y, s):
        pts = [(0.15, 0.0), (0.75, 0.0), (0.45, 0.45), (0.8, 0.45), (0.1, 1.2), (0.35, 0.6), (0.0, 0.6)]
        return self.polygon([(x + px * s, y + py * s) for px, py in pts], RED, "FFFFFF")


def _tokens(chunk: str):
    """Split '_{...}' / '^{...}' markup into (kind, text) runs."""
    out, i, buf = [], 0, ""
    while i < len(chunk):
        if chunk[i] in "_^" and i + 1 < len(chunk) and chunk[i + 1] == "{":
            j = chunk.index("}", i)
            if buf:
                out.append(("n", buf))
                buf = ""
            out.append(("sub" if chunk[i] == "_" else "sup", chunk[i + 2 : j]))
            i = j + 1
        else:
            buf += chunk[i]
            i += 1
    if buf:
        out.append(("n", buf))
    return out


def group(slide) -> Canvas:
    return Canvas(slide.shapes.add_group_shape().shapes)


# --------------------------------------------------------------------------- contribution parts


def banner(c: Canvas, x, y, w, color, number, title, size=12):
    c.box(x, y, w, 0.4, color, None, radius=0.1, shape=MSO_SHAPE.ROUND_2_SAME_RECTANGLE)
    c.text(x, y, w, 0.4, [[(f"Contribution {number}", {"bold": True}), ("  ·  " + title, {"bold": True})]],
           size=size, color="FFFFFF", align="c")


def gap_pair(c: Canvas, x, y, w_prior, w_ours, h, color, prior_cap, ours_cap, draw_prior, draw_ours,
             ours_fill="FFFFFF"):
    c.box(x, y, w_prior, h, "F2F2F2", LGRAY, 0.75, radius=0.06)
    c.text(x + 0.08, y + 0.03, w_prior - 0.1, 0.2,
           [[("\u2715 ", {"font": SYMBOL_FONT, "color": RED, "bold": True}), ("Prior work", {"bold": True})]],
           size=10, color=MUTED)
    draw_prior(x, y + 0.24, w_prior, h - 0.46)
    c.text(x + 0.05, y + h - 0.23, w_prior - 0.1, 0.2, prior_cap, size=9.5, color=MUTED, align="c")

    ax = x + w_prior + 0.05
    c.line([(ax, y + h / 2), (ax + 0.22, y + h / 2)], color=GRAY, lw=1.5, arrow=True)

    ox = ax + 0.27
    c.box(ox, y, w_ours, h, ours_fill, color, 1.0, radius=0.06)
    c.text(ox + 0.08, y + 0.03, w_ours - 0.1, 0.2,
           [[("\u2713 ", {"font": SYMBOL_FONT, "bold": True}), ("PHAST-DP", {"bold": True})]],
           size=10, color=color)
    draw_ours(ox, y + 0.24, w_ours, h - 0.46)
    c.text(ox + 0.05, y + h - 0.23, w_ours - 0.1, 0.2, ours_cap, size=9.5, color=color, align="c", bold=True)


# --------------------------------------------------------------------------- panels


def panel_data(slide, a):
    c = group(slide)
    x0, y0, w, h = 0.15, 0.15, 3.8, 4.35
    c.box(x0, y0, w, h, "F6F6F6", "A6A6A6", 1.0)
    c.text(x0 + 0.15, y0 + 0.07, w - 0.3, 0.3, "Digital twin & multi-entity data", size=12.5, bold=True)

    iw, ih = 3.5, 3.5 * 470 / 820
    c.box(0.29, 0.57, iw + 0.02, ih + 0.02, "333333", None, radius=0)
    c.picture(a["factory"], 0.3, 0.58, iw, ih)
    c.box(2.62, 0.66, 1.1, 0.25, DBLUE, "FFFFFF", 0.75, radius=0.12)
    c.text(2.62, 0.66, 1.1, 0.25, "Contribution 1", size=9, bold=True, color="FFFFFF", align="c")
    c.text(0.3, 2.62, iw, 0.22, "Isaac Sim line  ·  single-axis disturbances", size=9.5, color=MUTED, align="c")

    for i, (key, lab) in enumerate([("human", "Human"), ("machine", "Machine"),
                                    ("material", "Material"), ("agv", "Logistics")]):
        cx, cy = 0.32 + (i % 2) * 0.82, 2.95 + (i // 2) * 0.76
        c.picture(a[key], cx + 0.15, cy, 0.5, 0.5)
        c.bolt(cx + 0.6, cy + 0.0, 0.17)
        c.text(cx, cy + 0.51, 0.8, 0.2, lab, size=9.5, color=MUTED, align="c")

    tx, ty, tw, th = 2.25, 3.0, 1.32, 1.0
    for k in (0, 1, 2):
        off = 0.08 * (2 - k)
        c.picture(a[f"tensor_{k}"], tx + off, ty - off, tw, th)
        c.box(tx + off, ty - off, tw, th, None, MUTED, 0.6, radius=0)
    seg = th / 38
    yy = ty
    for key, n in [("machine", 7), ("gantry", 4), ("robot", 4), ("human", 5), ("buffer", 18)]:
        c.box(tx - 0.12, yy, 0.08, n * seg, ENTITY[key], "FFFFFF", 0.3, radius=0)
        yy += n * seg
    c.text(1.95, 4.05, 1.95, 0.22, [[("X_{t} ", {}), ("\u2208 \u211D", {"font": "Cambria Math"}),
                                      ("^{30\u00D738\u00D727}", {})]], size=10.5, align="c")
    c.text(1.95, 4.25, 1.95, 0.2, "resources \u00D7 minutes \u00D7 features", size=8.5, color=MUTED, align="c")


def panel_graph(slide):
    c = group(slide)
    x0, y0, w, h = 4.15, 0.15, 5.0, 4.35
    c.box(x0, y0, w, h, "EEF5FB", DBLUE, 1.5)
    banner(c, x0, y0, w, DBLUE, 1, "Multi-entity heterogeneous graph", size=11.5)

    def prior(x, y, ww, hh):
        cy = y + hh / 2
        xs = [x + ww * f for f in (0.28, 0.5, 0.72)]
        c.line([(xs[0], cy), (xs[-1], cy)], color=GRAY, lw=1.25)
        for xx in xs:
            c.circle(xx, cy, 0.08, "A6A6A6", "FFFFFF")

    def ours(x, y, ww, hh):
        cy = y + hh / 2 + 0.02
        xs = [x + ww * f for f in (0.25, 0.5, 0.75)]
        top, bot = cy - 0.15, cy + 0.15
        for xx in xs:
            c.line([(xx - 0.1, bot), (xx, cy)], color=GRAY, lw=0.5)
        c.line([(xs[0], top), (xs[0], cy)], color=MBLUE, lw=0.75, dash=MSO_LINE_DASH_STYLE.DASH)
        c.line([(xs[2], bot), (xs[2], cy)], color=MBLUE, lw=0.75, dash=MSO_LINE_DASH_STYLE.DASH)
        c.line([(xs[0], cy), (xs[-1], cy)], color=DBLUE, lw=1.5)
        c.circle(xs[0], top, 0.06, MBLUE, "FFFFFF")
        c.box(xs[1] - 0.06, top - 0.06, 0.12, 0.12, AMBER, "FFFFFF", 0.5, radius=0)
        c.circle(xs[2], bot, 0.06, LBLUE, DBLUE, 0.6)
        for xx in xs:
            c.circle(xx - 0.1, bot, 0.035, GRAY)
            c.circle(xx, cy, 0.075, DBLUE, "FFFFFF")

    gap_pair(c, 4.3, 0.65, 2.15, 2.15, 0.85, DBLUE, "machine-only nodes", "5 entity types, typed edges",
             prior, ours)

    my = 2.98
    mxs = [4.6 + i * 0.7 for i in range(7)]
    gxs = [4.95 + i * 1.18 for i in range(4)]
    gy, ry, hy = 2.32, 3.62, 1.82
    hxs = [4.75 + i * 0.36 for i in range(5)]

    for i, gx in enumerate(gxs):
        for m in (min(2 * i, 6), min(2 * i + 1, 6)):
            c.line([(gx, gy), (mxs[m], my)], color=MBLUE, lw=0.75, dash=MSO_LINE_DASH_STYLE.DASH)
            c.line([(gx, ry), (mxs[m], my)], color=MBLUE, lw=0.75, dash=MSO_LINE_DASH_STYLE.DASH)
    c.line([(gxs[0], gy), (gxs[-1], gy)], color=GRAY, lw=0.75, dash=MSO_LINE_DASH_STYLE.ROUND_DOT)
    c.line([(gxs[0], ry), (gxs[-1], ry)], color=GRAY, lw=0.75, dash=MSO_LINE_DASH_STYLE.ROUND_DOT)

    bufs = []
    for mx in mxs:
        bufs += [(mx - 0.17, my + 0.3), (mx + 0.17, my + 0.3)]
    bufs += [(mxs[0] - 0.3, my - 0.2), (mxs[6] + 0.3, my - 0.2), (mxs[3] - 0.17, my - 0.3), (mxs[3] + 0.17, my - 0.3)]
    for bx, by in bufs:
        mx = min(mxs, key=lambda v: abs(v - bx))
        c.line([(bx, by), (mx, my)], color=LGRAY, lw=0.6)

    c.line([(mxs[0], my), (mxs[-1], my)], color=DBLUE, lw=2.0)
    for i, j in [(2, 3), (4, 5)]:
        c.curve((mxs[i], my - 0.15), (mxs[j], my - 0.15), 0.18, color=DBLUE, lw=0.9)

    c.text(6.55, 1.68, 2.55, 0.2, [[("M^{G}", {"bold": True}), (": < 4-hop neighbours", {})]], size=9.5, color=MUTED)
    c.text(6.55, 1.89, 2.55, 0.2, [[("M^{S}", {"bold": True}), (": top-5 trajectory correlation", {})]], size=9.5,
           color=MUTED)

    for bx, by in bufs:
        c.circle(bx, by, 0.045, GRAY)
    for gx in gxs:
        c.circle(gx, gy, 0.11, MBLUE, "FFFFFF")
        c.circle(gx, ry, 0.11, LBLUE, DBLUE, 0.75)
    for hx in hxs:
        c.box(hx - 0.085, hy - 0.085, 0.17, 0.17, AMBER, "FFFFFF", 0.5, radius=0)
    for i, mx in enumerate(mxs):
        c.circle(mx, my, 0.17, DBLUE, "FFFFFF", 1.0)
        c.text(mx - 0.17, my - 0.17, 0.34, 0.34, f"M{i + 1}", size=8.5, bold=True, color="FFFFFF", align="c")

    lx = 4.32
    for key, lab in [("machine", "machine"), ("gantry", "gantry"), ("robot", "robot"),
                     ("human", "human"), ("buffer", "buffer")]:
        if key == "human":
            c.box(lx - 0.06, 3.99, 0.12, 0.12, AMBER, None, radius=0)
        elif key == "robot":
            c.circle(lx, 4.05, 0.06, LBLUE, DBLUE, 0.6)
        else:
            c.circle(lx, 4.05, 0.06 if key != "buffer" else 0.045, ENTITY[key])
        c.text(lx + 0.1, 3.95, 0.8, 0.2, lab, size=9.5, color=MUTED)
        lx += 0.97
    lx = 4.25
    for lab, col, lw, dash in [("process", DBLUE, 2.0, None), ("handling", MBLUE, 0.9, MSO_LINE_DASH_STYLE.DASH),
                               ("weak", GRAY, 0.9, MSO_LINE_DASH_STYLE.ROUND_DOT), ("buffer link", LGRAY, 0.9, None)]:
        c.line([(lx, 4.3), (lx + 0.28, 4.3)], color=col, lw=lw, dash=dash)
        c.text(lx + 0.34, 4.2, 0.9, 0.2, lab, size=9.5, color=MUTED)
        lx += 1.18


def panel_labels(slide):
    c = group(slide)
    x0, y0, w, h = 9.35, 0.15, 4.9, 4.35
    c.box(x0, y0, w, h, "FFF9EA", ORANGE, 1.5)
    banner(c, x0, y0, w, ORANGE, 2, "Process-informed event labels", size=11.5)

    def prior(x, y, ww, hh):
        cy = y + hh / 2 + 0.06
        xs = np.linspace(x + 0.15, x + ww - 0.15, 15)
        amp = [0.03, -0.03, 0.11, -0.03, 0.01, -0.02, 0.03, 0.12, -0.04, 0.02, -0.01, 0.03, 0.1, -0.03, 0.01]
        c.line([(x + 0.1, cy - 0.065), (x + ww - 0.1, cy - 0.065)], color=RED, lw=0.9, dash=MSO_LINE_DASH_STYLE.DASH)
        c.line([(xx, cy - a) for xx, a in zip(xs, amp)], color=GRAY, lw=1.0)
        for i in (2, 7, 12):
            c.text(xs[i] + 0.02, cy - amp[i] - 0.08, 0.16, 0.12, "\u00D7", size=9, bold=True, color=RED)

    def ours(x, y, ww, hh):
        cells = [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0]
        c.strip(x + 0.15, y + hh / 2 - 0.05, ww - 0.3, 0.14, cells, {0: "FFFFFF", 1: ORANGE})

    gap_pair(c, 9.5, 0.65, 2.15, 2.1, 0.85, ORANGE, "threshold spikes \u2260 bottleneck",
             "sustained events, 8-min rule", prior, ours)

    cbx, cby, cbw, cbh = 9.5, 1.62, 1.6, 2.38
    c.box(cbx, cby, cbw, cbh, "FFFFFF", AMBER, 1.0, radius=0.06)
    c.text(cbx, cby + 0.05, cbw, 0.4, "Short-pattern\nclustering", size=10, bold=True, align="c", anchor="t")
    rng = np.random.default_rng(3)
    for (mx, my), col in zip([(9.92, 2.42), (10.68, 2.38), (9.98, 3.08), (10.7, 3.12)], [DBLUE, MBLUE, AMBER, ORANGE]):
        for px, py in rng.normal([mx, my], 0.09, size=(10, 2)):
            c.circle(px, py, 0.025, col)
        c.star(mx, my, 0.065, col)
    c.text(cbx, 3.42, cbw, 0.22, "16 pattern keys K^{P}", size=9.5, align="c")
    c.text(cbx, 3.64, cbw, 0.22, "regimes, not labels", size=9, italic=True, color=MUTED, align="c")

    rx, rw = 11.3, 2.8
    raw = [0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0]
    sus = [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    cols = {0: "FFFFFF", 1: AMBER, 2: ORANGE, 3: "E6E6E6", 4: RED}
    c.text(rx, 1.6, rw, 0.22, [[("Type-specific rule ", {"bold": True}), ("b^{raw}", {})]], size=10)
    c.strip(rx, 1.86, rw, 0.15, raw, cols)
    c.line([(rx + 1.4, 2.04), (rx + 1.4, 2.26)], color=MUTED, lw=1.0, arrow=True)
    c.text(rx, 2.05, 1.32, 0.2, "persistence", size=9.5, color=MUTED, align="r")
    c.text(rx + 1.5, 2.05, 1.3, 0.2, "m = 8,  g = 1", size=9.5, color=MUTED)
    c.strip(rx, 2.29, rw, 0.15, [2 if v else 0 for v in sus], cols)

    c.text(rx, 2.53, rw, 0.22, [[("Event target ", {"bold": True}), ("(w, s, d)", {})]], size=10)
    cells = [3] * 6 + [0] * 4 + [4] * 9 + [0]
    c.strip(rx, 2.79, rw, 0.15, cells, cols)
    cw = rw / 20
    bx = rx + 6 * cw
    c.line([(bx, 2.73), (bx, 3.0)], color=INK, lw=1.0)
    c.text(rx, 2.98, 6 * cw, 0.18, "history", size=8.5, color=MUTED, align="c")
    c.bracket(bx, bx + 4 * cw, 3.04, RED, "s")
    c.bracket(bx + 4 * cw, bx + 13 * cw, 3.04, RED, "d")
    c.text(rx, 3.33, rw, 0.2, "ongoing: hot at history end", size=9.5, color=MUTED)
    c.text(rx, 3.53, rw, 0.2, "upcoming: s > 0,  d \u2265 8 min", size=9.5, color=MUTED)
    c.text(rx, 3.78, rw, 0.42, "+ cause: transport \u00B7 shortage \u00B7\n   starvation \u00B7 queue buildup",
           size=9.5, color=MUTED, anchor="t")


def panel_model(slide):
    c = group(slide)
    c.box(0.15, 4.9, 11.3, 3.95, "F3F8FC", MBLUE, 1.25)
    c.text(0.3, 4.96, 2.0, 0.3, "PHAST-DP", size=13, bold=True, color=DBLUE)

    # grouped embedding
    c.box(0.3, 5.35, 2.35, 3.35, "FFFFFF", MBLUE, 1.0, radius=0.06)
    c.text(0.3, 5.42, 2.35, 0.25, "Grouped embedding", size=11, bold=True, align="c")
    c.box(0.85, 5.71, 1.25, 0.23, DBLUE, None, radius=0.11)
    c.text(0.85, 5.71, 1.25, 0.23, "Contribution 1", size=9, bold=True, color="FFFFFF", align="c")
    for i, (g, d) in enumerate([("Queue", 4), ("Stall", 6), ("Logistics", 4), ("Shortage", 1),
                                ("Context", 7), ("Type", 5)]):
        gy = 6.03 + i * 0.32
        c.line([(1.75, gy + 0.125), (2.09, 6.95)], color=LBLUE, lw=0.75)
        c.box(0.45, gy, 1.3, 0.25, "E9F4FA", LBLUE, 0.75, radius=0.05)
        c.text(0.52, gy, 0.9, 0.25, g, size=9.5)
        c.text(1.3, gy, 0.38, 0.25, str(d), size=9.5, color=MUTED, align="r")
    c.circle(2.25, 6.95, 0.17, "FFFFFF", MBLUE, 1.0)
    c.text(2.08, 6.78, 0.34, 0.34, "mean", size=8, align="c")
    c.text(0.3, 8.0, 2.35, 0.22, "+ E_{time} + E_{lap} + E_{node}", size=9.5, align="c")
    c.text(0.3, 8.25, 2.35, 0.22, "\u2192 H^{(0)}", size=10, align="c")

    # encoder block
    c.box(2.95, 5.35, 5.8, 3.35, "FFFFFF", DBLUE, 1.25, radius=0.06, dash=MSO_LINE_DASH_STYLE.DASH)
    c.text(3.1, 5.4, 3.0, 0.25, "Encoder block \u00D7 5   (d = 80)", size=10.5, bold=True)

    c.box(3.1, 5.68, 5.5, 1.24, "FDECEE", RED, 1.5, radius=0.06)
    banner(c, 3.1, 5.68, 5.5, RED, 3, "Delay-propagation module", size=11)

    def prior(x, y, ww, hh):
        cy = y + hh / 2
        x1, x2 = x + 0.45, x + ww - 0.45
        c.line([(x1, cy), (x2, cy)], color=GRAY, lw=1.25)
        for xx, lab in ((x1, "i"), (x2, "j")):
            c.circle(xx, cy, 0.08, "A6A6A6", "FFFFFF")
            c.text(xx - 0.08, cy - 0.08, 0.16, 0.16, lab, size=8, bold=True, color="FFFFFF", align="c")
        c.text(x1 - 0.32, cy - 0.08, 0.22, 0.16, "t", size=8.5, color=MUTED, align="r")
        c.text(x2 + 0.1, cy - 0.08, 0.22, 0.16, "t", size=8.5, color=MUTED)

    def ours(x, y, ww, hh):
        cy = y + hh / 2 + 0.02
        x1, x2 = x + 0.48, x + ww - 0.4
        c.curve((x1 + 0.08, cy - 0.03), (x2 - 0.09, cy - 0.03), -0.1, color=RED, lw=1.25, arrow=True)
        c.circle(x1, cy, 0.08, MBLUE, "FFFFFF")
        c.circle(x2, cy, 0.08, RED, "FFFFFF")
        c.text(x1 - 0.08, cy - 0.08, 0.16, 0.16, "i", size=8, bold=True, color="FFFFFF", align="c")
        c.text(x2 - 0.08, cy - 0.08, 0.16, 0.16, "j", size=8, bold=True, color="FFFFFF", align="c")
        c.text(x1 - 0.46, cy - 0.08, 0.36, 0.16, "t\u2212\u03C4", size=8.5, color=MUTED, align="r")
        c.text(x2 + 0.1, cy - 0.08, 0.22, 0.16, "t", size=8.5, color=MUTED)

    gap_pair(c, 3.2, 6.1, 1.55, 1.6, 0.78, RED, "same-time links", "lagged precursors", prior, ours)
    mx = 6.75
    c.text(mx, 6.13, 1.85, 0.2, "Pattern attention", size=10, bold=True)
    c.text(mx, 6.33, 1.85, 0.2, "queue patch P_{t,n}", size=9.5, color=MUTED)
    c.text(mx, 6.52, 1.85, 0.2, "\u00D7 16 keys K^{P} \u2192 C^{P}", size=9.5, color=MUTED)
    c.text(mx, 6.71, 1.85, 0.2, "C^{P} added to geo. keys", size=9.5, color=RED, bold=True)

    rows = [(7.3, DBLUE, "Geographic attn \u00D72", "  mask M^{G}, keys + C^{P}"),
            (7.74, MBLUE, "Temporal attn \u00D74", "  per resource, 30 windows"),
            (8.18, LBLUE, "Semantic attn \u00D72", "  mask M^{S}, similar resources")]
    c.line([(3.18, 7.3), (3.18, 8.18)], color=MUTED, lw=1.0)
    c.line([(7.08, 7.3), (7.08, 8.18)], color=MUTED, lw=1.0)
    for yc, col, title, body in rows:
        c.box(3.3, yc - 0.18, 3.7, 0.36, "FFFFFF", col, 1.25, radius=0.05)
        c.box(3.3, yc - 0.18, 0.07, 0.36, col, None, radius=0)
        c.text(3.45, yc - 0.18, 3.5, 0.36, [[(title, {"bold": True}), (body, {"color": MUTED})]], size=9.5)
        c.line([(3.18, yc), (3.3, yc)], color=MUTED, lw=1.0, arrow=True)
        c.line([(7.0, yc), (7.08, yc)], color=MUTED, lw=1.0)
    c.line([(5.9, 6.92), (5.9, 7.12)], color=RED, lw=1.5, arrow=True)

    c.box(7.2, 7.12, 1.4, 0.5, "FFFFFF", DBLUE, 1.0, radius=0.06)
    c.text(7.2, 7.12, 1.4, 0.5, "Concat +\nproject", size=9.5, bold=True, align="c")
    c.box(7.2, 7.86, 1.4, 0.5, "FFFFFF", DBLUE, 1.0, radius=0.06)
    c.text(7.2, 7.86, 1.4, 0.5, "Add & Norm\n+ FFN", size=9.5, bold=True, align="c")
    c.line([(7.08, 7.37), (7.2, 7.37)], color=MUTED, lw=1.0, arrow=True)
    c.line([(7.9, 7.62), (7.9, 7.86)], color=MUTED, lw=1.0, arrow=True)
    c.line([(2.65, 7.74), (3.18, 7.74)], color=MUTED, lw=1.25, arrow=True)

    # heads
    c.box(8.95, 5.35, 2.35, 3.35, "FFFFFF", MBLUE, 1.0, radius=0.06)
    c.text(8.95, 5.42, 2.35, 0.25, "Multi-task heads", size=11, bold=True, align="c")
    heads = [("Occurrence p^{cont} / p^{onset}", "station event"),
             ("Start \u03C0^{s}  \u00B7  duration d\u0302", "when and how long"),
             ("Prefix p\u0302  \u00B7  occupancy \u00D4", "dense future grid"),
             ("Cause \u0109  \u00B7  remaining \u2113\u0302", "graph-level pooling")]
    for i, (a, b) in enumerate(heads):
        hy = 5.72 + i * 0.62
        c.box(9.08, hy, 2.09, 0.54, "E9F4FA", LBLUE, 0.75, radius=0.05)
        c.text(9.16, hy + 0.04, 2.0, 0.24, a, size=9.5, bold=True)
        c.text(9.16, hy + 0.27, 2.0, 0.22, b, size=9, color=MUTED)
    c.box(9.08, 8.2, 2.09, 0.36, "F6F6F6", GRAY, 0.75, radius=0.05, dash=MSO_LINE_DASH_STYLE.DASH)
    c.text(9.08, 8.2, 2.09, 0.36, "validation-controlled decoding", size=9, color=MUTED, align="c")
    c.line([(8.6, 8.11), (8.95, 8.11)], color=MUTED, lw=1.25, arrow=True)


def panel_report(slide):
    c = group(slide)
    x0, y0, w, h = 11.65, 4.9, 2.6, 3.95
    c.box(x0, y0, w, h, "F6F6F6", "A6A6A6", 1.0)
    c.text(x0 + 0.15, y0 + 0.06, w - 0.3, 0.3, "Bottleneck report", size=12.5, bold=True)

    gx0, gx1, t0, t1 = 12.55, 14.1, -4.0, 20.0

    def tx(t):
        return gx0 + (t - t0) / (t1 - t0) * (gx1 - gx0)

    c.box(tx(t0), 5.4, tx(0) - tx(t0), 1.02, "E6E6E6", None, radius=0)
    rows = [("Weld-2", 5.52, (0, 6), RED, RED), ("Gantry-1", 5.82, (7, 15), AMBER, ORANGE), ("AGV-3", 6.3, None, None, None)]
    for name, yv, span, fc, ec in rows:
        c.text(11.8, yv - 0.1, 0.75, 0.2, name, size=9.5)
        c.line([(gx0, yv), (gx1, yv)], color=LGRAY, lw=0.5)
        if span:
            c.box(tx(span[0]), yv - 0.08, tx(span[1]) - tx(span[0]), 0.16, fc, ec, 0.75, radius=0)
    c.line([(tx(0), 5.4), (tx(0), 6.42)], color=INK, lw=1.25)
    c.text(tx(0) - 0.25, 5.25, 0.5, 0.15, "now", size=8.5, align="c")
    c.bracket(tx(0), tx(7), 6.02, RED, "s\u0302", size=9.5)
    c.bracket(tx(7), tx(15), 6.02, RED, "d\u0302", size=9.5)
    c.text(11.8, 6.45, 2.3, 0.18, "future minutes (cap 5/10/15)", size=8.5, color=MUTED, align="c")

    c.text(11.8, 6.7, 2.3, 0.22, "Process cause \u0109", size=10, bold=True)
    causes = [("Transport", 0.12), ("Shortage", 0.07), ("Starvation", 0.09), ("Queue", 0.72)]
    for i, (name, p) in enumerate(causes):
        cy = 7.03 + i * 0.25
        c.text(11.8, cy - 0.1, 0.85, 0.2, name, size=9, color=MUTED)
        c.box(12.65, cy - 0.08, 1.45, 0.16, "FFFFFF", LGRAY, 0.5, radius=0)
        c.box(12.65, cy - 0.08, 1.45 * p, 0.16, DBLUE if p == 0.72 else LBLUE, None, radius=0)

    c.text(11.8, 8.06, 2.3, 0.22, "Remaining order time \u2113\u0302", size=10, bold=True)
    c.box(11.8, 8.35, 2.3, 0.18, "FFFFFF", LGRAY, 0.5, radius=0)
    c.box(11.8, 8.35, 2.3 * 0.6, 0.18, MBLUE, None, radius=0)
    c.text(11.8 + 2.3 * 0.6 + 0.05, 8.34, 0.9, 0.2, "12 min left", size=9)


def connectors(slide):
    c = Canvas(slide.shapes)
    c.line([(3.95, 2.4), (4.15, 2.4)], color=MUTED, lw=1.5, arrow=True)
    c.line([(2.2, 4.5), (2.2, 5.35)], color=MUTED, lw=1.5, arrow=True)
    c.text(2.28, 4.97, 0.6, 0.22, "X_{t}", size=10, bold=True)
    c.line([(5.4, 4.5), (5.4, 5.35)], color=DBLUE, lw=1.5, arrow=True)
    c.text(5.48, 4.97, 1.6, 0.22, "G,  M^{G},  M^{S}", size=10, bold=True, color=DBLUE)
    c.line([(10.3, 4.0), (10.3, 4.62), (7.6, 4.62), (7.6, 5.68)], color=ORANGE, lw=1.5, arrow=True)
    c.text(7.7, 4.64, 2.4, 0.22, "pattern keys K^{P}", size=9.5, bold=True, color=ORANGE)
    c.line([(12.4, 4.5), (12.4, 4.72), (10.6, 4.72), (10.6, 5.35)], color=ORANGE, lw=1.5,
           dash=MSO_LINE_DASH_STYLE.DASH, arrow=True)
    c.text(10.7, 4.74, 1.0, 0.2, "training targets", size=9, italic=True, color=ORANGE)
    c.line([(11.3, 7.0), (11.65, 7.0)], color=MUTED, lw=1.5, arrow=True)


def build_pptx(path: Path) -> None:
    assets = build_assets()
    prs = Presentation()
    prs.slide_width, prs.slide_height = E(SW), E(SH)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    panel_data(slide, assets)
    panel_graph(slide)
    panel_labels(slide)
    panel_model(slide)
    panel_report(slide)
    connectors(slide)
    prs.save(path)


def export(pptx: Path) -> None:
    ps = f"""
$ErrorActionPreference = 'Stop'
$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open('{pptx}', $true, $false, $false)
$pres.SaveAs('{pptx.with_suffix(".pdf")}', 32)
$pres.Slides.Item(1).Export('{pptx.with_suffix(".png")}', 'PNG', 2880, 1800)
$pres.Close()
$app.Quit()
"""
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)


def main() -> None:
    pptx = OUT.with_suffix(".pptx")
    build_pptx(pptx)
    export(pptx)
    print(f"wrote {pptx} (+ .pdf, .png)")


if __name__ == "__main__":
    main()
