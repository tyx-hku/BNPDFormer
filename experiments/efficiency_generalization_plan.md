# PHAST-DP：效率与泛化补充实验执行方案

更新：2026-10-10。对应论文第 5 章。模型：PHAST-DP、XGBoost、LSTM、BTGCN、BSTAN。

本文件规定待执行实验；空表和输出字段不代表已有测量结果。代码依据 `isaac_factory` 的 `origin/dev_tyx@29655baee57b9095119589a211ae1e2113b84078` 核对，baseline 实现沿用 `dev_xwt` 的已跑通版本。执行时另外记录实际使用的两个完整提交号。

## 1. 先统一主结果的评估样本

论文使用主模型的 `dense_i1` 协议：204 个 episode，train/val/test 为 140/28/36 个 episode，对应 20,826/4,331/5,354 个窗口。输入为 30 个一分钟历史窗口、38 个资源、27 个通道；输出评估 15 个目标资源及 20 个未来窗口。Start cap 分别为 5、10、15 分钟，Min8 标签规则沿用主实验。

当前主模型归档为 5,354 个测试窗口，baseline 公共指标 CSV 为 6,886 个测试窗口；原因评估支持分别为 579 和 4,237。这是需要重评的差异，不能通过改 CSV 中的样本数解决。论文已统一写主模型协议，并标明 baseline 数值暂为归档结果。

请先完成：

1. 从主实验实际数据加载器导出三份 manifest。每行至少包含 `episode_id, forecast_origin, resource_order, target_valid_mask`，记录数据版本、标签版本及文件 SHA-256；以实际导出清单为准。
2. 核对主模型历史预训练、课程训练、微调各阶段的 episode 使用范围，以及 baseline checkpoint 的训练/验证 episode。目标测试 episode 必须从未用于任何训练、预处理拟合或选模。
3. 如果 baseline 旧训练集与统一测试 episode 有交集，按统一 train/val/test 重新训练；没有交集且训练协议一致时，可保留 checkpoint，在统一验证集重新选阈值后重评测试集。仅删掉一部分测试窗口不构成对齐。
4. 每个模型分别保留特征转换和结构差异，统一窗口清单、标签、目标资源顺序、Min8、预测范围、评估掩码及单位。归一化、图统计、模式库和工况聚类均只在训练集拟合。
5. 输出同一 manifest 上五个模型 × 三个 cap 的完整指标，以及逐窗口预测。更新论文之前确认 `manifest_hash` 相同；原因指标还须确认有效标签掩码、四类映射和支持数相同。

### 指标字段

|论文指标|统一定义/导出要求|
|---|---|
|Will15 P/R/F1|15 个目标资源的事件工位命中，保存 TP/FP/FN|
|Report F1|工位命中并满足三窗口起点容差，保存独立的 TP/FP/FN|
|Upcoming R|最后历史窗口为非瓶颈、未来标签存在事件的窗口—资源对上的工位召回；主模型字段 `who_recall_upcoming`，baseline 字段 `upcoming_who_recall`|
|Ongoing R|最后历史窗口已为瓶颈的对应标签阳性对上的工位召回|
|按距离 Report recall|另存带起点容差的 `upcoming_report_recall` 及距离分箱；不要填进 Upcoming R|
|State F1|1-step 与 20-step；统一目标掩码与微平均方式|
|Start/Duration MAE|同一个事件解码结果，在工位匹配 TP 上计算；明确是否使用原始回归值或解码后的时间，两个版本可以同时导出|
|Union duration MAE/RMSE|统一纳入误报与漏报的 union 掩码，保存分子、分母|
|Remain MAE|全局订单剩余时间，报告分钟；与只看 primary/selected 的指标分开|
|Cause accuracy/macro recall|共同有效标签窗口、四类映射；输出支持数和混淆矩阵|

这些窗口—资源对包含滑动窗口重复观察，不能称为独立物理事件。除明确按事件去重的分析外，统计区间以完整 episode 为重采样单位。

## 2. 效率实验：五种模型均测

借鉴 PDFormer 的 Model Efficiency Study：同一硬件上比较平均每 epoch 训练和推理耗时。我们增加单样本报告延迟、完整训练成本和内存，以对应产线预警用途。PDFormer 未被用作本文件跨工况泛化方案的出处。

### 统一环境

- 固定同一台机器，记录 GPU/显存、CPU、RAM、系统、CUDA、框架版本、线程数。计时期间不并行运行其他训练任务。
- 神经模型统一 batch=16、FP32、相同 DataLoader worker/pin-memory 设置；如果实际实现必须使用不同精度，分别成表，不能混在同一速度排名中。
- XGBoost 记录真实后端、线程数和树参数；优先沿用已验证实现，不为对齐 GPU 标记而改变模型。CPU 后端的 GPU 显存记 n/a。
- 一次样本指一份完整历史窗口，输出全部目标资源；不得将某模型按单资源计时、另一模型按整张图计时。
- 三个 cap 分别使用其最终 checkpoint。先完成 cap=5 的全流程，再复制到 10/15。

### 测量项目

|项目|执行方式|汇报字段|
|---|---|---|
|参数与大小|神经模型总参数/可训练参数分开；XGBoost 记树数与叶数。统计实际推理所需模型、图、scaler、pattern 等资产大小|`params_total, params_trainable, trees, leaves, artifact_mb`|
|每 epoch 训练时间|计时第三至第七轮，分别记录纯训练与验证时间；PHAST-DP 各训练阶段分开。运行不足七轮时报告实际可测轮次|`train_epoch_s_mean, train_epoch_s_sd, val_epoch_s_mean, timed_epochs`|
|完整拟合成本|记录实际完成的全部训练、验证、选模耗时；PHAST-DP 包括早期预训练/初始化训练、三个课程阶段、remain 微调，画出共享前序关系避免重复计费|`fit_total_s, stage_times, shared_pretrain_s, actual_epochs`|
|完整测试集推理|预热 50 batch，再重复完整测试集五次；神经模型 batch=16，XGBoost 处理相同样本分块，保存每次总耗时|`test_pass_s[5], throughput_windows_per_s`|
|单样本报告延迟|batch=1，预热 50 次；按固定 manifest 顺序取前 1,000 个有效窗口，五轮重复，每次记录耗时|`report_latency_ms_raw, median, p95`|
|纯前向延迟|单独记录，保持 batch/精度相同|`forward_latency_ms_raw, median, p95`|
|内存|训练、完整测试、单样本推理分别 reset/测峰值；保存 GPU allocated/reserved 峰值及进程 CPU RSS 峰值|`gpu_peak_alloc_mib, gpu_peak_reserved_mib, cpu_peak_rss_mib`|
|离线准备|图/模式/聚类拟合、数据构建、checkpoint 加载分别计时|`preprocess_fit_s, data_build_s, model_load_s`|

计时采用单调高精度墙钟；GPU 在区间前后同步。报告延迟从已在内存中的历史窗口开始，包含输入特征转换、必要的 CPU→GPU 传输、前向、解码以及结果回到 CPU；纯前向计时使用已在设备上的输入。测试集单次耗时使用同一“报告延迟”边界，不含磁盘读取和绘图。保存原始耗时，不只保存均值。

XGBoost 没有与神经网络相同的 epoch，表中每 epoch 写 n/a，报告总拟合时间与实际 boosting rounds。对旧 checkpoint 的训练耗时，若没有可靠日志，需补跑实际训练；短跑第三至七轮只能提供每 epoch 时间，不能作为完整拟合时间。

PHAST-DP 的 Start≤10/15 依赖前一 cap，分别报告当前阶段增量成本、累计可复现成本；三个 cap 合计成本中每个共享阶段只计算一次。预训练成本拿不到时明确标记缺失，不能填零。

结果表：五个模型 × 三个 cap。配图：Report F1—batch1 延迟散点图，横轴 median 延迟、纵轴统一样本上的 Report F1，点大小可表示模型资产大小。p95 另表保留。没有同一 manifest 上的准确率时先只画耗时图。

## 3. 泛化实验：按完整工况组留出

目标是测试“训练未见的扰动类型”，保持产线拓扑和资源定义不变。代码的扰动类型包括 `none/machine/human/material/logistics`，并支持混合类型；先从每个 episode 的 metadata 核对实际分布，不能只凭文件名猜类别。

### 分组方法

四折分别留出 machine、human、material、logistics。每折：

1. 将包含被留出类型的 episode 全部排除出训练和验证，包含该类型的混合扰动也排除。主要 OOD 测试使用该类型的单一扰动 episode，混合扰动可以单独作为扩展测试。
2. 对其余类型（包括 none）按完整 episode 固定 train/val/ID-test，建议源条件按 70/15/15 划分，并保存明确 manifest；不能让相邻窗口跨集合。保持产品、订单规模和强度分布尽可能相近，记录无法控制的差异。
3. OOD-test 仅含未参与训练/验证的留出条件。先统计每组的 episode、窗口、正例支持；如果某类缺少足够独立 episode，先补数据，建议每个留出类型至少 20 个 episode。这个数是采集起点，最终区间宽度和支持数仍需报告。
4. 每折五个模型重新训练。PHAST-DP 的预训练、课程、fine-tuning，以及图/模式/工况簇都只接触该折源条件训练集；不能直接使用已见过该类扰动的主实验 checkpoint。
5. 用源条件验证集选 checkpoint/阈值，然后对源条件 ID-test 和 OOD-test 都保持固定。保留主实验的每模型训练流程/上限；不根据 OOD 结果额外调参。

第一批做 **4 折 × 5 模型 × Start≤5 × seed42 = 20 个训练配置**，确认流程与数据支持后再补 cap10/15。多 seed 可在此后作为扩展，先不要求所有消融跟跑。

### 指标与统计

- 主指标：Report F1、工位级 Upcoming R；补充 Will15 F1、1-step/20-step State F1、union duration MAE。全部沿用第 1 节定义。
- 同时列 ID 和 OOD 值；`ΔF1 = F1_OOD − F1_ID`，负值表示下降；误差用 `MAE_OOD − MAE_ID`，正值表示恶化。不要对接近零的指标计算相对百分比降幅。
- 每个域内部，以完整 episode 做 1,000 次 bootstrap。比较两个模型时使用相同重采样 episode 清单，重新汇总 TP/FP/FN 后计算 F1，并给模型差值的区间。ID/OOD 为不同 episode 集时，各自独立重采样后计算域差值，不能把两域强行配对。
- 没有 Upcoming 正例的组标 n/a，附支持数；不要以 0 代替无法定义的召回率。单 seed 的区间只描述测试样本不确定性。
- 图：按四种留出条件分别画各模型 ID→OOD 的 Report F1 及 Upcoming R，带 episode-bootstrap 区间，保持颜色与主结果图一致。

## 4. 交付文件和运行前检查

建议统一输出到新实验目录，保留旧归档：

```text
paper_supplement_2026_10/
  run_manifest.json                 # 代码/数据/权重哈希、环境、配置、时间边界
  manifests/{main,fold_*}/          # train/val/ID-test/OOD-test 清单
  common_metrics.csv               # 对齐后的五模型×三 cap
  efficiency.csv                   # 每模型/每 cap/每重复一行
  timing_raw/                      # 逐次耗时与分阶段记录
  generalization.csv               # fold/model/cap/domain/metric/support/CI
  predictions/                     # episode/origin/resource/true/pred/mask
  figures/                         # PDF + PNG，字体、单位、颜色统一
```

逐窗口导出至少包含事件概率与判定、真实/预测起点和持续时间、state 序列、cause 标签/预测/有效掩码、remain 真值/预测。没有这些信息，无法可靠重算指标、bootstrap 或补轨迹图。

启动完整训练前做一次小规模 smoke run：检查集合无交集、模型输出资源顺序一致、指标分子分母可重算、计时同步有效、内存统计已 reset。该检查通过后先完成样本重评和效率，再启动四折泛化。

## 5. 本次核对的 NoCluster / Cause×State 结果

最新 `dev_tyx` 的 `瓶颈真值有效性实验.plan.md` E.1 已列出同预算、seed42、Start≤5 的 Cause×State 结果：Backbone 的训练日志 `who_f1/cause_acc` 为 .735/.195，+Cause 为 .733/.895，+State 为 .732/.185，Full 为 .726/.895。该表的 `will_f1=0` 与 precision gate 未打开有关，因此这里使用 `who_f1` 诊断，不把它直接并入主结果的 decoded Will15 表。

+Lift 与 Full 摘要完全相同，需核查开关是否实际生效。此次本地能核对到版本化摘要和运行脚本，原始训练日志不在当前 checkout；最终定稿时请补回原始配置、日志和机器可读结果。旧 NoCluster 同时关闭多个组件且训练条件不同，不能单独用其差值证明工况聚类改善了事件真值或瓶颈识别。
