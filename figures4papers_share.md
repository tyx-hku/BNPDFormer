# figures4papers：让 AI 帮你画顶会级论文插图

> 组会分享 · AI 科研工具推荐
> 项目地址：[https://github.com/ChenLiu-1996/figures4papers](https://github.com/ChenLiu-1996/figures4papers)

---

## 1. 这是什么？

**figures4papers** 是耶鲁大学计算机博士生 [Chen Liu（刘晨）](https://chenliu-1996.github.io/) 开源的论文插图仓库，包含两部分：

1. **真实论文绘图脚本**：全部用 Python + matplotlib 编写，对应的图已发表在 *Nature Machine Intelligence*、ICML、NeurIPS、ECCV 等期刊和会议上。
2. **AI Skill（**`scientific-figure-making`**）**：把作者的绘图风格总结成一套 AI 编程助手（Cursor、Claude Code、Codex）能读懂的规范。安装后，只需用自然语言描述需求，AI 就会按这套统一风格生成可直接用于论文的绘图脚本。

---

## 2. 效果展示


| 类型       | 示例                                                                                                                               |
| -------- | -------------------------------------------------------------------------------------------------------------------------------- |
| 柱状对比图    | ![bars](https://raw.githubusercontent.com/ChenLiu-1996/figures4papers/main/figure_ImmunoStruct/figures/bars_comparison_IEDB.png) |
| 雷达图      | ![radar](https://raw.githubusercontent.com/ChenLiu-1996/figures4papers/main/figure_VIGIL/figures/comparison_radar.png)           |
| 折线图      | ![line](https://raw.githubusercontent.com/ChenLiu-1996/figures4papers/main/figure_VIGIL/figures/comparison_posttraining.png)     |
| 概念图      | ![concept](https://raw.githubusercontent.com/ChenLiu-1996/figures4papers/main/figure_VIGIL/figures/concept.png)                  |
| 趋势图      | ![trend](https://raw.githubusercontent.com/ChenLiu-1996/figures4papers/main/figure_ophthal_review/figures/trend_by_month.png)    |
| 3D 球体示意图 | ![sphere](https://raw.githubusercontent.com/ChenLiu-1996/figures4papers/main/figure_Dispersion/figures/illustration.png)         |


---



## 3. 仓库结构

```
figures4papers/
├── scientific-figure-making/      # ★ AI Skill 本体
│   ├── SKILL.md                   # 入口：什么时候用、什么时候不用
│   └── references/
│       ├── api.md                 # 配色 PALETTE、绘图函数签名、导出规范
│       ├── common-patterns.md     # 常用布局：多子图、图例面板、打印友好柱状图
│       ├── design-theory.md       # 设计原理：字体、线宽、配色、导出格式
│       ├── tutorials.md           # 分步教程：柱状图 / 趋势图 / 热力图
│       └── demos.md               # 各 figure_* 示例项目链接
├── figure_ImmunoStruct/           # 各论文的真实绘图脚本和输出
├── figure_VIGIL/
├── figure_Dispersion/
├── ...
└── assets/                        # 部分手工后期处理的示意图
```

---



## 4. 安装



### 4.1 前置条件

- [Git](https://git-scm.com/)
- Python 3，并安装 `matplotlib` 和 `numpy`：

```bash
pip install matplotlib numpy
```

- 一个支持 Skill 的 AI 编程助手：[Cursor](https://cursor.com)、Claude Code 或 Codex



### 4.2 下载仓库

```bash
git clone https://github.com/ChenLiu-1996/figures4papers.git
```

我的做法是放在 `~/.cursor/figures4papers`（Windows 下即 `C:\Users\<用户名>\.cursor\figures4papers`），方便统一管理。

### 4.3 安装为全局 Skill

核心思路：把仓库中的 `scientific-figure-making/` 文件夹**链接**到 AI 助手的 skills 目录。使用链接而不是复制，以后 `git pull` 更新仓库后，Skill 会自动同步。

**macOS / Linux**（在仓库根目录执行）：


| AI 助手       | 命令                                                                                                               |
| ----------- | ---------------------------------------------------------------------------------------------------------------- |
| Cursor      | `mkdir -p ~/.cursor/skills && ln -s "$(pwd)/scientific-figure-making" ~/.cursor/skills/scientific-figure-making` |
| Claude Code | `mkdir -p ~/.claude/skills && ln -s "$(pwd)/scientific-figure-making" ~/.claude/skills/scientific-figure-making` |
| Codex       | `mkdir -p ~/.codex/skills && ln -s "$(pwd)/scientific-figure-making" ~/.codex/skills/scientific-figure-making`   |


**Windows（PowerShell，以 Cursor 为例）**：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.cursor\skills"
New-Item -ItemType Junction `
  -Path   "$env:USERPROFILE\.cursor\skills\scientific-figure-making" `
  -Target "$env:USERPROFILE\.cursor\figures4papers\scientific-figure-making"
```

> Windows 使用 Junction（目录联接），不需要管理员权限，效果等同于 `ln -s`。



### 4.4 验证安装

1. 重启 Cursor，或执行 `Developer: Reload Window`。
2. 检查目录：

```powershell
Get-Item "$env:USERPROFILE\.cursor\skills\scientific-figure-making" | Select-Object LinkType, Target
# LinkType 显示 Junction，Target 指向仓库目录，即表示安装成功
```

1. 在 Cursor 设置的 Skills 列表中可以看到 `scientific-figure-making`。



### 4.5 免安装用法

如果不想安装，也可以直接用 Cursor 打开 figures4papers 仓库，在提示词中写明“遵循 `scientific-figure-making/SKILL.md`”，AI 同样会读取这套规范。

### 4.6 更新

```bash
cd ~/.cursor/figures4papers
git pull
```

因为使用的是链接，更新后 Skill 会自动生效。

---



## 5. 使用



### 5.1 基本流程

```
描述数据和需求 → AI 读取 Skill 规范 → 生成 Python 绘图脚本 → 运行 → 导出 PNG/PDF → 插入 LaTeX
```

全局安装后，在**任意项目**中与 AI 对话即可。只要提到“论文图”“publication-quality”“matplotlib”等关键词，AI 就会自动加载该 Skill；也可以直接点名使用：

```text
使用 scientific-figure-making skill，帮我画一张……
```



### 5.2 提示词模板

```text
使用 scientific-figure-making skill，在 figures/plot_xxx.py 创建一个论文级绘图脚本。

数据：<粘贴表格、数组，或给出 csv 路径>
图的类型：<分组柱状图 / 折线图 / 热力图 / 多子图 ...>
对比关系：<哪个是我们的方法，哪些是 baseline>
输出：figures/xxx.png 和 figures/xxx.pdf
尺寸：<单栏 / 双栏>
```



### 5.3 实际示例

**示例 1：模型对比柱状图**

```text
使用 scientific-figure-making skill，画一张分组柱状图，比较 BNPDFormer 与
BTGCN、BSTAN、PDFormer 在 F1、Precision、Recall 三个指标上的表现。
BNPDFormer 用主蓝色突出，baseline 用浅色。输出 PDF，用于双栏论文的单栏宽度。
```

**示例 2：训练曲线**

```text
读取 experiments/log.csv，画训练集和验证集的 loss 曲线，
用阴影表示 3 个随机种子的标准差，导出到 figures/fig_learning_curve.pdf。
```

**示例 3：消融实验热力图**

```text
把消融实验结果表画成热力图，行是模型变体，列是指标，格子内标注数值。
```



### 5.4 Skill 内置规范（AI 自动遵循）

**统一配色** `PALETTE`：


| 用途            | 颜色                          |
| ------------- | --------------------------- |
| 我们的方法（主色）     | 深蓝 `#0F4D92` / 中蓝 `#3775BA` |
| 提升效果          | 绿色系 `#DDF3DE` → `#8BCF8B`   |
| baseline / 对比 | 红色系 `#F6CFCB` → `#B64342`   |
| 背景 / 中性       | 灰色 `#CFCECE`                |
| 强调            | 金色 `#FFD700`                |


**封装好的绘图函数**：


| 函数                          | 作用                         |
| --------------------------- | -------------------------- |
| `apply_publication_style()` | 一键设置论文风格：去掉上右边框、无边框图例、统一字号 |
| `make_grouped_bar()`        | 分组柱状图                      |
| `make_trend()`              | 带不确定性阴影的折线图                |
| `make_heatmap()`            | 热力图                        |
| `make_scatter()`            | 散点图                        |
| `finalize_figure()`         | 一次导出 PNG/PDF/SVG，自动创建目录    |


**导出规范**：优先导出 PDF/SVG 矢量图，位图使用 300 DPI，便于直接插入 LaTeX。

---



## 6. 插入 LaTeX

```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=\columnwidth]{figures/fig_comparison.pdf}
  \caption{Comparison of BNPDFormer with baselines.}
  \label{fig:comparison}
\end{figure}
```

---



## 7. 适用范围

**适合**：

- 论文、报告、组会 PPT 中的定量结果图：柱状图、折线图、热力图、散点图、多子图
- 需要全文配色和字体保持统一的场景
- 需要矢量图投稿的场景

**不适合**：

- 交互式图表（Plotly、Bokeh 等）
- 只做数据探索、不打算发表的草图
- 复杂 3D 或地理信息图
- 框架图、流程图等以手工排版为主的示意图（仍然建议使用 PPT、Visio、Figma 或 draw.io）

---



## 8. 个人使用体会

1. **省时间**：不用反复调字号、配色和边框，一句话即可生成符合规范的脚本。
2. **风格统一**：全文所有图共享一套配色和字体，审稿人观感更专业。
3. **可复现**：输出的是 Python 脚本，数据更新后重新运行即可，不需要手工重画。
4. **可学习**：仓库中的 `figure_`* 都是真实顶会论文脚本，本身就是很好的 matplotlib 学习材料。
5. **注意**：AI 生成的图仍需人工检查数据是否正确，以及图例、坐标轴标签是否准确。

---



## 9. 参考链接

- GitHub 仓库：[https://github.com/ChenLiu-1996/figures4papers](https://github.com/ChenLiu-1996/figures4papers)
- 作者主页：[https://chenliu-1996.github.io/](https://chenliu-1996.github.io/)
- Cursor Skills 文档：[https://cursor.com/docs](https://cursor.com/docs)

> 引用说明：仓库作者欢迎在符合学术规范的前提下引用其相关论文，具体 BibTeX 见仓库 README 的 Related Papers 部分。

