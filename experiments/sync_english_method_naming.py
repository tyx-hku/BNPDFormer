"""Update English figure labels while preserving all plotted data and graphics.

The English figures have editorial differences from the root plotting exports.
Edit their vector text directly so regenerating legacy plots cannot revert those
differences. Re-running this script is safe: only old labels are replaced.
"""

from pathlib import Path
import re

import fitz


ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = Path("C:/Windows/Fonts")


def replacement(text: str) -> str:
    text = text.replace("\u00ad", "-").replace("\u00a0", " ")
    text = re.sub(r"PHGST-(?:PD|DP)", "PHGST-DM", text)
    text = text.replace(
        "Propagation-delay-aware module", "Delay-aware spatiotemporal modeling"
    )
    return text


def update_pdf(path: Path) -> int:
    doc = fitz.open(path)
    count = 0
    for page in doc:
        changes = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    original = span["text"]
                    normalized = original.replace("\u00ad", "-").replace("\u00a0", " ")
                    updated = replacement(original)
                    if updated != normalized:
                        changes.append((span, updated))
        if not changes:
            continue
        for span, _ in changes:
            rect = fitz.Rect(span["bbox"])
            # Retain neighbouring lines, backgrounds, curves and diagrams.
            rect.y0 += 0.1
            rect.y1 -= 0.1
            page.add_redact_annot(rect, fill=False, cross_out=False)
        page.apply_redactions(images=0, graphics=0)
        for span, updated in changes:
            bold = "Bold" in span["font"]
            font_path = FONT_DIR / ("timesbd.ttf" if bold else "times.ttf")
            font = fitz.Font(fontfile=str(font_path))
            font_name = "EditorialTimesBold" if bold else "EditorialTimes"
            page.insert_font(fontname=font_name, fontfile=str(font_path))
            rect = fitz.Rect(span["bbox"])
            # Keep the original label footprint and baseline to avoid collisions.
            size = min(span["size"], rect.width / font.text_length(updated, fontsize=1))
            color = fitz.sRGB_to_pdf(span["color"])
            page.insert_text(
                span["origin"], updated, fontname=font_name,
                fontsize=size, color=color,
            )
        count += len(changes)
    if count:
        temp = path.with_suffix(".renamed.pdf")
        doc.save(temp, garbage=4, deflate=True)
        doc.close()
        temp.replace(path)
    else:
        doc.close()
    return count


if __name__ == "__main__":
    for path in sorted((ROOT / "main_en/figures").rglob("*.pdf")):
        count = update_pdf(path)
        if count:
            print(f"{path.relative_to(ROOT)}: {count} labels updated")
