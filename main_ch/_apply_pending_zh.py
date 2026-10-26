#!/usr/bin/env python3
"""Replace 【待译】 placeholders in main_ch/main.tex with Chinese translations."""
from __future__ import annotations

import re
from pathlib import Path

TEX = Path(__file__).with_name("main.tex")

TRANSLATIONS = [
    # 1 abstract
    r"""及时的动态瓶颈预测对于在吞吐约束影响生产之前发出预警、并指导资源调整具有迫切需求。
现有研究主要依赖机器或工位传感器返回的单一实体数据，对人员、物料、缓冲区和物流及其相互关系的表征有限。
这一狭窄观测范围导致工厂图建模不完整、预测精度下降，也难以刻画扰动经一定时延后在不同资源之间传播的过程。
第二项局限在于可靠瓶颈监督难以构造：正事件稀缺，而孤立的阈值穿越可能将瞬时波动与持续性约束混为一谈，并掩盖其过程原因。
针对上述局限，本文提出\textbf{面向延迟传播的过程启发式异构图时空 Transformer（PHGST-DP）}。
针对第一项局限，PHGST-DP 将异构工艺—物流图与原型条件化的延迟感知传播相结合，把较早资源状态与经运输、缓冲或服务时延后在其他位置显现的约束联系起来。
针对第二项局限，可控扰动的数字化生产线提供可追溯轨迹；过程启发式规则、持续性过滤以及仅在训练集上的聚类，共同构造持续性事件与原因目标以及重复运行模式原型。
此外，模型将瓶颈工位、开始时间、持续时间、过程原因和订单剩余时间联合输出为面向决策的事件报告。
留出数字孪生实验表明瓶颈预测精度高、报告生成及时，消融结果亦支持各组件的有效性。
上述结果支持 PHGST-DP 在所研究数字孪生条件下的适用性，并显示其在早期预警与资源协调方面的潜力。""",
    # 2 intro PHGST-DP para
    r"""为解决上述不足，本文提出 \textbf{PHGST-DP}。数字孪生已用于制造全生命周期中的产品与过程监测、仿真、优化与预测~\cite{lo2021digitaltwin}；产线研究亦已整合在线过程仿真、设备级模拟与柔性运行~\cite{leng2022digitaltwins}。可控扰动的数字孪生生产线在不干扰实体生产的条件下，提供机器、人员、物料供给、缓冲区、龙门和运输机器人的可追溯轨迹~\cite{lu2020digital,isaacsim2026,xue2026safe}。这些观测被组织为异构工艺—物流图：机器与搬运资源作为相互作用实体，物料短缺、缓冲区占用、人员可用性和运输延迟则提供与资源类型相关的运营上下文。本文的过程启发式规则与聚类时间模式构造方法，将队列、阻塞、饥饿、可用性、缺料与物流证据与持续性要求相结合，构造持续性瓶颈事件与可观测过程原因目标，并将仅来自训练集的短时间片段归纳为重复运行模式原型。确定性生成的原因对齐工况标识提供额外运营上下文，但不定义真值。随后，在由 PDFormer~\cite{jiang2023pdformer} 改造的时空 Transformer 中，原型条件化的延迟感知传播模块将近期片段与固定原型匹配，并据此调节跨资源注意力，使较早资源状态能够参与预测经一定时滞后在其他位置显现的约束。最终模型生成分钟级报告，包含瓶颈工位、开始时间、持续时间、可观测过程原因和订单剩余时间。""",
    # 3 contributions
    r"""本文的主要贡献总结如下。（1）将动态瓶颈预测从以机器为中心的观测扩展到异构多实体工厂数据。机器、人员、物料供给状态、缓冲区、龙门和运输机器人及其工艺与物流关系被联合表示，使模型能够捕捉由生产、人员、物料和搬运交互形成的瓶颈，而不再仅依赖机器状态。（2）针对正事件稀缺、且与正常波动可分性不足的瓶颈数据，提出\emph{过程启发式规则与聚类时间模式构造}。资源类型相关规则与持续性约束构造具有运营含义的事件与过程原因目标；确定性原因对齐工况标识提供结构化上下文；仅在训练集上的聚类将短时间片段归纳为重复运行模式原型。该设计在事件监督、可观测生产证据与提供给预测器的模式上下文之间保持可追溯联系，且不以簇索引作为瓶颈真值。（3）提出\emph{原型条件化的延迟感知传播模块}。该模块将近期资源轨迹与固定时间模式原型匹配，并将所得模式上下文注入跨资源地理注意力，使模型能够将上游前驱与经运输、缓冲或服务时延后出现的下游约束联系起来。""",
    # 4 method overview organization
    r"""PHGST-DP 围绕第~\ref{sec:intro}节确立的三项贡献组织。第一，可控仿真、异构工厂图与分组嵌入整合机器、人员、物料流、缓冲区、龙门与运输证据。第二，过程启发式规则与聚类时间模式构造产生可追溯的事件与原因监督、确定性工况上下文以及重复运行模式原型。第三，原型条件化的延迟感知传播模块利用这些原型组织滞后的跨资源交互。完整信息流为
\begin{equation}
\begin{aligned}
\text{simulation}&\rightarrow\text{window/event construction}\\
&\rightarrow\text{factory graph}\rightarrow\text{joint prediction}.
\end{aligned}
\end{equation}
前两阶段形成可复现的观测与目标；后两阶段参数化第~\ref{sec:problem}节定义的映射 $f_\theta$。""",
    # 5 architecture figure para
    r"""图~\ref{fig:model-architecture} 给出 PHGST-DP 的模型结构。多实体历史被划分为六个语义特征组，并与时间、图拉普拉斯与节点身份嵌入相结合。聚类时间模式构造提供固定原型库；原型条件化的延迟感知传播模块利用该库调节地理键，使重复出现的前驱模式能在延迟后影响跨资源交互。随后，工位级与图级输出头解码发生与否、开始时间、持续时间、未来占用、过程原因以及订单剩余时间。""",
    # 6 data generation isaac
    r"""数据生成环境在 NVIDIA Isaac Sim 中重建水管产线、资源布局、仓储位置与搬运活动。采集器在每个逻辑秒记录 episode 配置、活动扰动、资源状态转移、作业轨迹、缓冲事件、运输任务与物料库存。这些数据流按 episode 与逻辑时间对齐，从而使下游事件能够回溯到其前序状态。已知的仿真器实现缺陷可能触发并非预期生产过程、也不代表实体生产条件的死锁复位；受该缺陷影响的 episode 被视为无效仿真记录并剔除，有效 episode 在十件产品全部完成后导出。""",
    # 7 three clustering objects
    r"""与聚类相关的三类对象在概念上严格区分。第一，离线聚合工具可生成工位级与窗口级 $K=8$ 的 k-means 描述子，用于探索性工况分析。第二，训练数据由确定性规则得到原因对齐工况标识，可用于表示条件化与对比正则。第三，聚类时间模式构造组件对短时间片段拟合，形成重复原型库。只有第三类对象才是第二项贡献中所称的主动聚类操作；第三项贡献则始于原型条件化延迟感知传播模块将近期片段与该库匹配、并将所得上下文注入地理注意力之时。离线簇预测损失权重为零，且任何簇索引都不定义瓶颈真值；事件标签仅由上述过程规则与持续性过滤生成。""",
    # 8 encoder short
    r"""编码器首先通过分组嵌入保留异构观测的不同语义，再建模时间演化、图传播与行为相似性。原型条件化的延迟感知传播模块进一步将当前资源状态与其效应在后续生产过程中显现的重复前驱模式联系起来。""",
    # 9 comparison overview
    r"""该比较从生产预测的两项互补能力展开。瓶颈事件与时间预测识别受影响资源，并描述约束何时开始、持续与结束（表~\ref{tab:comparison-main}）；过程原因预测则为该约束提供运营解释（表~\ref{tab:comparison-state}）。二者共同构成带有过程上下文的资源级预警。本节报告的全部基线比较均在同一批 5{,}354 个共享测试窗口（及对应窗口—资源对）上统一重评，PHGST-DP 与四个基线使用相同的样本身份、目标资源、未来网格与标签定义。因此，表中分数并非沿用更早样本集的结果。""",
    # 10 cause prediction numbers
    r"""PHGST-DP 在事件与时间预测之外同时给出过程解释：三个 cap 下原因准确率为 $0.965/0.962/0.974$，宏平均召回率为 $0.967/0.965/0.978$（表~\ref{tab:comparison-state}）。XGBoost 取得最高值，各 cap 下准确率均为 $0.990$、宏平均召回率均为 $0.988$。PHGST-DP 位列第二，准确率仅落后 XGBoost $1.6$--$2.8$ 个百分点，宏平均召回率落后 $1.0$--$2.3$ 个百分点，并在每个 cap 的两项指标上均优于三个神经基线。其具有竞争力的原因识别与事件覆盖相互补充，可将所预测的资源与时间区间关联到运输延迟、物料短缺、上游饥饿或队列积压。""",
    # 11 ablation intro
    r"""消融实验将预测性能与三项设计选择联系起来：异构工艺—物流信息、过程启发式规则与聚类时间模式构造，以及原型条件化的延迟感知传播模块。另有九种配置考察支撑提前预警的解码器与训练选择（表~\ref{tab:ablation-arms}）。每一项消融比较（含 Full 对照）均从相同参数初始化出发，采用 50 个 epoch 预算、相同的 Start$\leq5\rightarrow$Start$\leq10\rightarrow$Start$\leq15$ 课程，以及相同的验证控制检查点与阈值选择规则。数据集、目标资源、标签规则与候选阈值亦遵循同一协议。该共用选择流程对多数分支给出阈值 $0.94$，对 NoFarBoost 给出 $0.90/0.88/0.94$。匹配预算的原因监督实验单独隔离原因头的解释作用。剩余时间比较使用阶段 1 参考结果，即在头级微调之前。""",
    # 12 supervision components paragraph
    r"""\textbf{（1）监督组件的影响。} NoCluster 旨在移除贡献 2——\emph{过程启发式规则与聚类时间模式构造}——中的聚类时间模式构造组件，以评估聚类在构造重复时间模式原型中的作用。NoPattern 则单独关闭原型条件化延迟感知传播模块中的原型匹配。""",
    # 13 decoder training
    r"""解码器与训练比较考察提前预警的两项要求：区分新事件与持续事件，以及保持对较远开始时刻的敏感性。NoSplit 用单一共享头替换继续头与开始头；NoFarBoost 去除远开始加权及相关的强化误报惩罚。两个分支均保留共用初始化、50 个 epoch 课程以及验证控制的检查点与阈值选择规则。表~\ref{tab:decoder-ablation} 报告相应工作点。""",
    # 14 key device figure
    r"""图~\ref{fig:key-device-baselines} 在同一设备与同一 episode 上将 PHGST-DP 与 XGBoost、LSTM、BTGCN、BSTAN 叠加对比：左侧为下一窗口状态，右侧为持续时间。黑色实线为目标；各方法预测以虚线并用不同颜色区分。窗口索引从 30 窗口历史之后开始计数。PHGST-DP 在两段瓶颈区间上保持连续状态覆盖，并跟随持续时间向恢复下降；基线在同一轨迹上则出现缺口或更弱的持续时间跟踪。总体事件与时间结果见表~\ref{tab:comparison-main}。""",
    # 15 mixed disturbance map
    r"""\textbf{混合扰动概率图。} 图~\ref{fig:attn-prediction} 将单资源轨迹扩展到补充性混合扰动 episode \texttt{n10\_mix\_all1.0\_\_episode\_03}。该 episode 因高瓶颈活动被自动选出，并显示来自 Start$\leq5$ 混合扰动检查点的相对测试窗口索引 $0$--$200$。三列对齐面板分别保留未来事件标签、模型概率与绝对概率误差。可见失配包括：无对应正标签资源上的非零概率，以及对已标注区间的覆盖不全。概率图不同于经阈值后的运营报告。所显示的 20 行包含 15 个评估目标与五个人员上下文节点；为便于阅读省略 18 个缓冲区行。因此，该图说明这一补充模型与标签在何处一致或分歧，并非保留模型 \texttt{dense\_i1} 的总体性能结果。""",
    # 16 process informed discussion
    r"""过程启发式规则使报告与生产条件之间保持可解释联系。原因头对若干受支持症状给出较高类别召回；匹配预算的组件研究表明，原因监督在几乎不影响工位识别的同时显著提升原因准确率。基于规则的事件构造提供目标，确定性原因对齐工况标识为事件头提供互补上下文。在保留的标签有效性分析中，探索性回放使 PHGST 在全部报告的软服务敏感性对齐指标上居首。该证据支持标签应与资源运行条件保持清晰关系，但其试点规模尚不足以主张在各类运行条件下的普遍优势。原因类别表达由规则得到的过程关联；回放则另行评估模拟干预敏感性。""",
    # 17 digital twin discussion limits
    r"""数字孪生评估仅在所研究的资源布局、产品组合、有效仿真运行、种子 42 以及 20 分钟预测时域下确立了这一报告能力。跨布局、跨产品与实体生产迁移尚未评估；过程规则与图编码的是应用相关的工程知识，而非可移植的制造本体。部署可沿同一接口，将 MES、WMS 与运输调度观测映射到资源图，并随新窗口到达更新报告。面向可重构制造系统的集成数字孪生监测与仿真平台，为连接 CPS/MES 数据与实时监督及离线仿真提供了相关先例~\cite{leng2023monitoring}。第~\ref{sec:efficiency}节的测量表明，在所测硬件上模型侧报告生成可舒适地落入一分钟更新周期。进一步验证可扩展到端到端数据与决策时延、缺失或延迟观测、更多种子与布局，以及对预测采取行动后的调度或吞吐结果。这些方向将已验证的预测能力与生产控制中的实际应用衔接起来。""",
    # 18 appendix intro
    r"""本附录汇集补充数值表以及支撑正文插图的完整注意力可视化。材料用于交叉核对，而非替代第~\ref{sec:exp}节的主要比较。""",
    # 19 shared protocol
    r"""\textbf{共用训练与评估协议。} 表~\ref{tab:shared-training-protocol} 记录在所报告 Full 模型与各消融分支之间保持固定的控制项。表~\ref{tab:ablation-arms} 所列架构开关是分支间的预期差异；除此之外，初始化、优化预算、课程、基于验证的模型选择以及留出评估均遵循下列共用协议。""",
    # 20 grouped ablation
    r"""\textbf{分组消融总览。} 表~\ref{tab:ablation-grouped} 给出共享 5{,}354 窗口测试划分上各消融分支的绝对 F1-score、Upcoming 召回率与并集持续时间 MAE。正文按设计问题讨论这些分支；此处保留紧凑分数以便跨分支查阅。所有分支从相同参数出发，共享 50 个 epoch 预算、课程与模型选择规则。NoInfo 与 MachineOnly 因部分资源类型不在其预测范围内而观测到更小的事件池，解读其行结果时仍需考虑这一范围差异。""",
    # 21 complete attention
    r"""\textbf{完整注意力矩阵。} 图~\ref{fig:attn-states} 与图~\ref{fig:attn-layers-all} 保留支撑图~\ref{fig:attn-change} 与图~\ref{fig:attn-layers} 的绝对资源注意力均值及完整编码器层视图。为便于阅读，资源级矩阵显示相同的 20 个非缓冲资源，并省略 18 个缓冲区行与列，且不对保留权重重新归一化。稳定的地理条带与稀疏语义块主导绝对尺度，而条件相关变化在减去正常状态均值后更易观察。图~\ref{fig:attn-layers-all} 中全部五层在各分支内使用统一色标。这些注意力值描述学习到的关联，并不确立因果效应或逐层精度贡献。""",
]


def extract_brace_arg(text: str, start: int) -> tuple[str, int]:
    assert text[start] == "{"
    depth = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            nxt = text[i + 1]
            if nxt in "{}%\\":
                i += 2
                continue
            j = i + 1
            if j < len(text) and text[j].isalpha():
                while j < len(text) and text[j].isalpha():
                    j += 1
                i = j
                continue
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
        i += 1
    raise ValueError("unbalanced")


def main() -> None:
    tex = TEX.read_text(encoding="utf-8")
    pending_spans: list[tuple[int, int]] = []
    pos = 0
    while True:
        m = re.search(r"\\zhpara\{", tex[pos:])
        if not m:
            break
        brace_at = pos + m.end() - 1
        zh, end = extract_brace_arg(tex, brace_at)
        if "【待译】" in zh:
            pending_spans.append((brace_at, end))
        pos = end

    if len(pending_spans) != len(TRANSLATIONS):
        raise SystemExit(
            f"pending={len(pending_spans)} translations={len(TRANSLATIONS)}"
        )

    # replace from the end so offsets stay valid
    for (brace_at, end), zh in zip(reversed(pending_spans), reversed(TRANSLATIONS)):
        tex = tex[: brace_at + 1] + zh.strip() + tex[end - 1 :]

    TEX.write_text(tex, encoding="utf-8")
    left = tex.count("【待译】")
    print(f"replaced {len(TRANSLATIONS)} placeholders; remaining 【待译】={left}")


if __name__ == "__main__":
    main()
