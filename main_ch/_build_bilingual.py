#!/usr/bin/env python3
"""Build main_ch/main.tex: current main_en English + Chinese from prior bilingual (fuzzy reuse) + markers for new translations."""
from __future__ import annotations

import difflib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EN = (ROOT / "main_en" / "main.tex").read_text(encoding="utf-8")
OUT = ROOT / "main_ch" / "main.tex"
NEED = ROOT / "main_ch" / "_need_zh.txt"
# Prefer the existing bilingual draft; fall back to a deleted-root main.tex if present.
_ZH_CANDIDATES = [OUT, ROOT / "main.tex"]
_zh_src = next((p for p in _ZH_CANDIDATES if p.exists()), None)
if _zh_src is None:
    raise SystemExit("No Chinese source found (expected main_ch/main.tex or root main.tex)")
MAIN = _zh_src.read_text(encoding="utf-8")


def extract_brace_arg(text: str, start: int) -> tuple[str, int]:
    assert text[start] == "{"
    depth = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
        i += 1
    raise ValueError("unbalanced brace")


def extract_zh_pairs(src: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    pos = 0
    while True:
        m = re.search(r"\\zhpara\{", src[pos:])
        if not m:
            break
        abs_start = pos + m.start()
        zh, end = extract_brace_arg(src, pos + m.end() - 1)
        before = src[:abs_start].rstrip()
        chunks = re.split(r"\n\s*\n", before)
        en_para = chunks[-1].strip() if chunks else ""
        # strip trailing comments-only lines
        en_lines = [ln for ln in en_para.splitlines() if not ln.strip().startswith("%")]
        en_para = "\n".join(en_lines).strip()
        pairs.append((en_para, zh.strip()))
        pos = end
    return pairs


def normalize(s: str) -> str:
    s = re.sub(r"\s+", " ", s)
    s = s.replace("\\,", " ").replace("~", " ")
    return s.strip()


def best_zh(en_para: str, pairs: list[tuple[str, str]], cutoff: float = 0.72) -> tuple[str | None, float]:
    n = normalize(en_para)
    best_r, best_zh_text = 0.0, None
    for en0, zh0 in pairs:
        r = difflib.SequenceMatcher(None, n, normalize(en0)).ratio()
        if r > best_r:
            best_r, best_zh_text = r, zh0
    if best_r >= cutoff:
        return best_zh_text, best_r
    return None, best_r


def should_translate_block(block: str) -> bool:
    b = block.strip()
    if not b or b.startswith("%"):
        return False
    # skip pure latex structural / float / math-heavy short blocks
    skip_prefixes = (
        "\\documentclass",
        "\\usepackage",
        "\\PassOptions",
        "\\DeclareMathOperator",
        "\\DontPrint",
        "\\SetAl",
        "\\SetAlgo",
        "\\SetInd",
        "\\SetComment",
        "\\hypersetup",
        "\\captionsetup",
        "\\IfFontExistsTF",
        "\\setmainfont",
        "\\setmonofont",
        "\\setsansfont",
        "\\newfontfamily",
        "\\newcommand",
        "\\renewcommand",
        "\\RenewDocumentCommand",
        "\\AddToHook",
        "\\ExplSyntax",
        "\\cs_set",
        "\\makeatletter",
        "\\makeatother",
        "\\begin{document}",
        "\\end{document}",
        "\\nocite",
        "\\emergencystretch",
        "\\let\\WriteBookmarks",
        "\\def\\float",
        "\\def\\textpage",
        "\\shorttitle",
        "\\shortauthors",
        "\\title",
        "\\author",
        "\\cormark",
        "\\affiliation",
        "\\cortext",
        "\\begin{keywords}",
        "\\end{keywords}",
        "\\begin{NoHyper}",
        "\\end{NoHyper}",
        "\\maketitle",
        "\\section",
        "\\subsection",
        "\\subsubsection",
        "\\begin{figure}",
        "\\end{figure}",
        "\\begin{table}",
        "\\end{table}",
        "\\begin{algorithm}",
        "\\end{algorithm}",
        "\\begin{itemize}",
        "\\end{itemize}",
        "\\begin{enumerate}",
        "\\end{enumerate}",
        "\\begin{assumption}",
        "\\end{assumption}",
        "\\includegraphics",
        "\\caption",
        "\\label",
        "\\centering",
        "\\small",
        "\\footnotesize",
        "\\scriptsize",
        "\\FloatBarrier",
        "\\newpage",
        "\\clearpage",
        "\\bibliography",
        "\\bibliographystyle",
        "\\printcredits",
        "\\bio",
        "\\begin{thebibliography}",
        "\\InputIfFileExists",
        "\\input{",
        "\\vspace",
        "\\hspace",
        "\\noindent",
        "\\item",
        "\\State",
        "\\For",
        "\\If",
        "\\Else",
        "\\Return",
        "\\KwIn",
        "\\KwOut",
        "\\KwData",
        "\\KwResult",
        "\\tcp",
        "\\BlankLine",
        "\\SetAlgoLined",
        "\\LinesNumbered",
        "\\begin{equation}",
        "\\end{equation}",
        "\\begin{align}",
        "\\end{align}",
        "\\begin{equation*}",
        "\\begin{align*}",
        "\\[",
    )
    first = b.splitlines()[0].strip()
    for p in skip_prefixes:
        if first.startswith(p) or b.startswith(p):
            return False
    # whole-block environments that are tables/algorithms/equations
    if re.match(r"\\begin\{(table|figure|algorithm|equation|align|tabular)", b):
        return False
    # abstract: special handling
    if b.startswith("\\begin{abstract}"):
        return True
    letters = sum(c.isalpha() for c in b)
    cmds = len(re.findall(r"\\[a-zA-Z]+", b))
    # prose-like: enough letters, not command-dominated
    if letters < 60:
        return False
    if cmds > 25 and letters / max(cmds, 1) < 8:
        return False
    # mostly math display
    if b.count("$") > 12 and letters < 200:
        return False
    return True


def inject_cjk_preamble(tex: str) -> str:
    """Ensure xeCJK + zhpara exist; CJK fonts after Latin main font."""
    if "\\usepackage{xeCJK}" not in tex:
        needle = "\\usepackage{amsmath}"
        if needle not in tex:
            raise SystemExit("amsmath not found")
        tex = tex.replace(needle, "\\usepackage{amsmath}\n\\usepackage{xeCJK}", 1)

    if "\\newcommand{\\zhpara}" not in tex:
        # Insert CJK font setup + zhpara after Latin font block.
        marker = "\\setsansfont{lmsans10-regular.otf}}}"
        cjk = (
            marker
            + "\n% CJK must be declared after the Latin main font so Han glyphs are not dropped.\n"
            + "\\IfFontExistsTF{SimSun}\n"
            + "  {\\setCJKmainfont{SimSun}[BoldFont=SimHei,ItalicFont=KaiTi,BoldItalicFont=SimHei]\n"
            + "   \\setCJKsansfont{Microsoft YaHei}\n"
            + "   \\setCJKmonofont{SimHei}}\n"
            + "  {\\setCJKmainfont{FandolSong-Regular.otf}[BoldFont=FandolSong-Bold.otf,AutoFakeSlant=0.2]\n"
            + "   \\setCJKsansfont{FandolHei-Regular.otf}\n"
            + "   \\setCJKmonofont{FandolHei-Regular.otf}}\n"
            + "\\newcommand{\\zhpara}[1]{%\n"
            + "  \\par\\begingroup\\small\\color{black!72}\\noindent #1\\par\\endgroup}"
        )
        if marker not in tex:
            raise SystemExit("Latin font block marker not found for CJK injection")
        tex = tex.replace(marker, cjk, 1)

    tex = tex.replace(
        "%% English-only manuscript. Chinese paragraph translations are omitted.",
        "%% Bilingual manuscript: English paragraph followed by Chinese \\zhpara{...}.",
        1,
    )
    return tex


def process_abstract(block: str, pairs: list[tuple[str, str]]) -> tuple[str, list[str]]:
    notes: list[str] = []
    # Extract abstract body between begin/end
    m = re.search(r"\\begin\{abstract\}(.*)\\end\{abstract\}", block, re.S)
    if not m:
        return block, notes
    body = m.group(1).strip()
    # remove any existing zhpara in source (shouldn't be in main_en)
    body = re.sub(r"\\zhpara\{.*?\}", "", body, flags=re.S).strip()
    zh, score = best_zh(body, pairs, cutoff=0.55)
    if zh is None:
        notes.append(f"ABSTRACT need_zh score={score:.3f}")
        zh = "【待译】摘要中文翻译待补充。"
    out = "\\begin{abstract}\n" + body + "\n\n\\zhpara{" + zh + "}\n\\end{abstract}"
    return out, notes


def main() -> None:
    pairs = extract_zh_pairs(MAIN)
    print(f"loaded {len(pairs)} zh pairs from main.tex")

    tex = inject_cjk_preamble(EN)
    # Share identical English table fragments with the English manuscript.
    for name in ("ch5_attention_resources.tex", "ch5_attention_temporal.tex", "ch5_checkpoint_validation.tex"):
        tex = tex.replace("\\input{tables/" + name + "}", "\\input{../main_en/tables/" + name + "}")
    # Split into blank-line blocks while preserving separators approximately
    parts = re.split(r"(\n\s*\n)", tex)
    out_parts: list[str] = []
    need: list[str] = []
    reused = 0
    needed = 0
    skipped = 0

    i = 0
    while i < len(parts):
        part = parts[i]
        if re.fullmatch(r"\n\s*\n", part or ""):
            out_parts.append(part)
            i += 1
            continue

        block = part
        if block.strip().startswith("\\begin{abstract}"):
            # abstract may span multiple split parts until \end{abstract}
            combined = block
            j = i + 1
            while j < len(parts) and "\\end{abstract}" not in combined:
                combined += parts[j]
                j += 1
            new_block, notes = process_abstract(combined, pairs)
            need.extend(notes)
            if notes:
                needed += 1
            else:
                reused += 1
            out_parts.append(new_block)
            i = j
            continue

        if should_translate_block(block):
            zh, score = best_zh(block, pairs)
            if zh is None:
                needed += 1
                preview = normalize(block)[:180]
                need.append(f"NEED score={score:.3f}\nEN: {preview}\n---")
                # Placeholder must not contain TeX grouping braces.
                safe = re.sub(r"[{}]", "", preview[:60])
                zh = f"【待译】{safe}…"
            else:
                reused += 1
            out_parts.append(block.rstrip() + "\n\n\\zhpara{" + zh + "}")
        else:
            skipped += 1
            out_parts.append(block)
        i += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(out_parts), encoding="utf-8")
    NEED.write_text("\n".join(need), encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"reused={reused} needed={needed} skipped_blocks={skipped}")
    print(f"need list: {NEED} ({len(need)} items)")


if __name__ == "__main__":
    main()
