#!/usr/bin/env python3
"""Fill 【待译】 placeholders and normalize Chinese after bilingual rebuild from main_en."""
from __future__ import annotations

import re
from pathlib import Path

TEX = Path(__file__).with_name("main.tex")


def extract_brace_arg(text: str, start: int) -> tuple[str, int]:
    depth = 0
    i = start
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
        i += 1
    raise ValueError("unbalanced brace")


PENDING: list[tuple[str, str]] = [
    (
        "This appendix provides implementation settings",
        r"""本附录给出实现设置、数值标签与解码规则，以及支撑正文分析的注意力矩阵。""",
    ),
    (
        "summarizes the settings shared by the Full model and ablation arms",
        r"""表~\ref{tab:shared-training-protocol}汇总 Full 模型与各消融分支的共用设置；架构差异见表~\ref{tab:ablation-arms}。""",
    ),
    (
        "Evaluation counts refer to forecast-origin--resource pairs",
        r"""评价计数按预报起点—资源对统计，因此持续事件可在多个相继起点上贡献。重叠窗口不作独立性假设下的显著性检验观测。""",
    ),
]


TERM_REPLACEMENTS: list[tuple[str, str]] = [
    # Full formal name first (longer patterns before shorter).
    (
        r"面向传播延迟感知模块的过程知情异构图时空 Transformer（PHGST-PD）",
        r"面向延迟感知建模的过程知情异构图时空 Transformer（PHGST-DM）",
    ),
    (
        r"过程知情异构图时空 Transformer（含传播延迟感知模块，PHGST-PD）",
        r"过程知情异构图时空 Transformer（含延迟感知建模，PHGST-DM）",
    ),
    (r"PHGST-PD", r"PHGST-DM"),
    (r"传播延迟感知模块", r"延迟感知建模"),
    (r"面向传播延迟感知", r"面向延迟感知"),
    # Older bilingual phrasing for the same contribution.
    (r"延迟模式条件化", r"延迟感知建模"),
]


def replace_zh_for_en(tex: str, en_key: str, zh: str) -> tuple[str, bool]:
    pos = 0
    while True:
        m = re.search(r"\\zhpara\{", tex[pos:])
        if not m:
            return tex, False
        abs_start = pos + m.start()
        _old_zh, end = extract_brace_arg(tex, pos + m.end() - 1)
        before = tex[:abs_start].rstrip()
        chunks = re.split(r"\n\s*\n", before)
        en = "\n".join(
            ln for ln in chunks[-1].splitlines() if not ln.strip().startswith("%")
        ).strip()
        if en_key in en:
            return tex[:abs_start] + "\\zhpara{" + zh + "}" + tex[end:], True
        pos = end


def normalize_zhparas(tex: str) -> tuple[str, int]:
    """Apply terminology replacements only inside \\zhpara{...}."""
    out: list[str] = []
    pos = 0
    changed = 0
    while True:
        m = re.search(r"\\zhpara\{", tex[pos:])
        if not m:
            out.append(tex[pos:])
            break
        abs_start = pos + m.start()
        out.append(tex[pos:abs_start])
        zh, end = extract_brace_arg(tex, pos + m.end() - 1)
        new_zh = zh
        for old, new in TERM_REPLACEMENTS:
            if old in new_zh:
                cnt = new_zh.count(old)
                new_zh = new_zh.replace(old, new)
                changed += cnt
        out.append("\\zhpara{" + new_zh + "}")
        pos = end
    return "".join(out), changed


def main() -> None:
    tex = TEX.read_text(encoding="utf-8")

    missing = []
    for key, zh in PENDING:
        tex2, ok = replace_zh_for_en(tex, key, zh)
        if not ok:
            missing.append(key[:80])
        else:
            tex = tex2

    tex, term_hits = normalize_zhparas(tex)
    pending_left = tex.count("【待译】")
    TEX.write_text(tex, encoding="utf-8")
    print(f"wrote {TEX}")
    print(f"pending_left={pending_left}")
    print(f"missing_pending={len(missing)}")
    for x in missing:
        print("  ", x)
    print(f"term_replacements={term_hits}")
    print(f"PHGST-PD leftover={tex.count('PHGST-PD')}")
    print(f"传播延迟感知模块 leftover={tex.count('传播延迟感知模块')}")
    print(f"延迟模式条件化 leftover={tex.count('延迟模式条件化')}")


if __name__ == "__main__":
    main()
