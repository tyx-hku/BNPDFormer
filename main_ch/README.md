# 英中对照论文入口

- 源码：`main.tex`（以 `../main_en/main.tex` 为英文底稿；每段英文后接 `\zhpara{中文}`）
- 当前编译结果：`main.pdf`
- 编译：在 PowerShell 中执行 `powershell -ExecutionPolicy Bypass -File .\build.ps1`

共享图片位于上一级的 `figures`；表格在 `tables/`（与 `main_en/tables` 同步）。

重建流程（可选）：

1. `python _build_bilingual.py` — 从 `main_en` 生成对照骨架并复用根目录 `main.tex` 中已有中译
2. `python _apply_pending_zh.py` — 补全待译段落并统一 PHGST-PD 术语
