# 英中对照论文入口

- 源码：`main.tex`（以 `../main_en/main.tex` 为英文底稿；每段英文后接 `\zhpara{中文}`）
- 当前编译结果：`main.pdf`
- 编译：在 PowerShell 中执行 `powershell -ExecutionPolicy Bypass -File .\build.ps1`

共享图片位于上一级的 `figures`；相同的注意力与 checkpoint 表格直接引用 `../main_en/tables/`，不再保留重复副本。

重建流程（可选）：

1. `python _build_bilingual.py` — 以 `main_en/main.tex` 为英文底稿重建对照骨架，并复用现有 `main_ch/main.tex`（若无则回退根目录 `main.tex`）中已有中译
2. `python _apply_sync_zh.py` — 补全待译段落，并校正已复用中文中落后于英文的数字与表述
3. `powershell -ExecutionPolicy Bypass -File .\build.ps1` — 编译 `main.pdf`
