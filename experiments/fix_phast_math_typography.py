"""Use native DrawingML baselines for two unsupported Unicode math glyphs."""
from copy import deepcopy
from pathlib import Path
import re
import sys
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree

target = Path(sys.argv[1])
ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
aq = "{" + ns["a"] + "}"
with ZipFile(target) as source:
    entries = [(item, source.read(item.filename)) for item in source.infolist()]
changed = 0
result = []
for item, data in entries:
    if re.fullmatch(r"ppt/slides/slide\d+\.xml", item.filename):
        root = etree.fromstring(data)
        for run in list(root.findall(".//a:r", ns)):
            element = run.find("a:t", ns)
            text = element.text or "" if element is not None else ""
            if not re.search("⁽⁰⁾|ₕ", text):
                continue
            parent, index = run.getparent(), run.getparent().index(run)
            replacements = []
            for part in re.split("(⁽⁰⁾|ₕ)", text):
                if not part:
                    continue
                new = deepcopy(run)
                new.find("a:t", ns).text = {"⁽⁰⁾": "(0)", "ₕ": "h"}.get(part, part)
                if part in ("⁽⁰⁾", "ₕ"):
                    properties = new.find("a:rPr", ns)
                    if properties is None:
                        properties = etree.Element(aq + "rPr")
                        new.insert(0, properties)
                    size = int(properties.get("sz", "1600"))
                    properties.set("sz", str(round(size * 0.70)))
                    properties.set("baseline", "30000" if part == "⁽⁰⁾" else "-25000")
                replacements.append(new)
            parent.remove(run)
            for offset, new in enumerate(replacements):
                parent.insert(index + offset, new)
            changed += 1
        data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    result.append((item, data))
temporary = target.with_suffix(".mathfix.pptx")
with ZipFile(temporary, "w", compression=ZIP_DEFLATED) as output:
    for item, data in result:
        output.writestr(item, data)
temporary.replace(target)
print(f"Native math baseline fixes: {changed}")
