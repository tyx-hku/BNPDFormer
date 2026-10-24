# Baseline 计算效率实验（2026-10-23）

B2–B5 × Start≤5/10/15，共 12 组。复用 frozen validation-selected 模型和阈值；未训练、未选新阈值。

## 评测口径

- 参考 dev_tyx c1404e0 的 phgst_efficiency_server_guide.md 和 benchmark_efficiency.py。
- 同一 RTX 5090 服务器；Python 3.11.15、PyTorch 2.11.0+cu128、CUDA 12.8。B3–B5 使用 CUDA；B2 使用 XGBoost 3.2.0 CPU（4 线程，沿用保存的配置）。
- 过去 30 × 60 秒窗口，未来 20 窗口。batch=16，完整 test pass 重复 5 次，取平均；吞吐量=测试样本数/平均耗时。
- batch=1 延迟：预热 50 次，256 个固定测试样本循环采样，5×1000 次，共 5000 次；CSV 保留每次 wall-clock 延迟。CUDA 计时前后同步。
- forward：神经模型为输入已驻留 GPU 的完整 forward；B2 为特征已准备好的全部 7 个 CPU 树模型预测头。
- report：神经模型包含 CPU batch 传输、完整 forward、sigmoid/argmax、事件字典实例化；B2 包含历史特征构造、7 个预测头、事件实例化。均不计文件写入、损失或评估指标计算。
- test pass 额外包含 DataLoader 迭代；B2 所有有效设备的 hot/score 头按固定 20 窗口推理，不利用未来真值裁短计算量。
- 加载时间包含数据读取/校验、task view、必要的历史特征构造和模型加载；不包含旧阶段 ZIP 解包。与主模型一样，不是纯权重读取时间。
- checkpoint 大小：神经模型 best.pt 原文件（可能包含训练元数据）；B2 是 config.json 和全部 7 个模型文件总和。不是等价的纯参数存储大小。
- 参数量按加载的神经模型统计；B2 参数量/GPU 显存记 NA。GPU allocated 是当前进程 PyTorch allocator 峰值，包含模型和预加载 256 个 batch-1 样本池，不是整卡占用。
- 未补测训练耗时，不以历史 elapsed_seconds 冒充纯训练时间。

## 比较限制

- baseline 测试为 6886 窗口、40 episodes；主模型公开效率结果为 5354 窗口、36 episodes。整套测试总耗时不能直接作为速度比；吞吐/延迟也应注明输入样本、模型任务和设备差异。
- 主模型测量日期为 2026-10-17；本次为 2026-10-23。测量时另一用户的 Isaac Sim 进程仍占用 GPU，未停止他人任务。JSON 记录每组前后 GPU 负载。结果是共享服务器实测，不能宣称独占 GPU、公平隔离下的严格速度排名。
- 模型文件按原冻结记录在测量前后校验 SHA-256，阈值与最新 baseline Test JSON 逐项核对。smoke 结果不进入本表。

## 效率结果

| model | Start≤ | device | 参数量 | 模型 MiB | 加载 s | Test s | samples/s | forward p50/p95/p99 ms | report p50/p95/p99 ms | GPU MiB |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---:|
| B2 | 5 | cpu | NA | 19.844 | 1.537 | 10.248 | 671.944 | 2.920 / 3.125 / 3.398 | 4.462 / 7.258 / 24.315 | NA |
| B3 | 5 | cuda | 752867 | 8.659 | 1.275 | 0.794 | 8669.530 | 0.364 / 0.654 / 0.905 | 0.645 / 1.150 / 1.340 | 83.787 |
| B4 | 5 | cuda | 274339 | 3.198 | 3.476 | 1.001 | 6880.989 | 0.646 / 1.085 / 1.183 | 0.953 / 1.513 / 1.663 | 240.346 |
| B5 | 5 | cuda | 287267 | 3.350 | 3.414 | 1.046 | 6584.365 | 0.743 / 1.181 / 1.254 | 1.026 / 1.581 / 1.683 | 239.712 |
| B2 | 10 | cpu | NA | 26.049 | 1.650 | 11.067 | 622.209 | 3.582 / 3.874 / 4.309 | 5.339 / 8.694 / 25.812 | NA |
| B3 | 10 | cuda | 752867 | 8.660 | 1.279 | 0.806 | 8546.927 | 0.378 / 0.845 / 0.927 | 0.650 / 1.146 / 1.351 | 83.787 |
| B4 | 10 | cuda | 274339 | 3.198 | 3.421 | 0.947 | 7274.477 | 0.630 / 1.071 / 1.160 | 0.918 / 1.479 / 1.615 | 240.346 |
| B5 | 10 | cuda | 287267 | 3.350 | 3.437 | 1.039 | 6625.873 | 0.734 / 1.171 / 1.258 | 1.022 / 1.569 / 1.650 | 239.712 |
| B2 | 15 | cpu | NA | 28.500 | 1.675 | 11.613 | 592.973 | 3.762 / 3.997 / 6.289 | 5.464 / 9.394 / 24.795 | NA |
| B3 | 15 | cuda | 752867 | 8.660 | 1.272 | 0.788 | 8740.447 | 0.356 / 0.635 / 0.906 | 0.645 / 1.140 / 1.329 | 83.787 |
| B4 | 15 | cuda | 274339 | 3.198 | 3.441 | 0.969 | 7106.329 | 0.646 / 1.048 / 1.160 | 0.938 / 1.496 / 1.618 | 240.346 |
| B5 | 15 | cuda | 287267 | 3.350 | 3.383 | 1.033 | 6667.498 | 0.719 / 1.122 / 1.235 | 0.998 / 1.541 / 1.636 | 239.712 |

## 原始文件与复现

- 正式结果根目录：`/home/sci/work/BSTAN_isaac_factory/output/baseline_efficiency/formal_20261023`
- 每个 `B*_cap*` 目录包含 `baseline_efficiency.json`、`forward_latency_raw.csv`、`report_latency_raw.csv`。
- 性能指标来源：`/home/sci/work/BSTAN_isaac_factory/source/isaaclab_tasks/isaaclab_tasks/direct/hc_factory/output/bottleneck_dataset/experiments/factory_pdformer_134_v3/baseline_matched_v1_test_20261003_metrics_v4.json`；效率表 CSV 另带 who/report F1 以确认对应模型。
- 代码：`source/isaaclab_tasks/isaaclab_tasks/direct/hc_factory/tools/benchmark_baseline_efficiency.py`。
- 运行：在 `/home/sci/work/BSTAN_isaac_factory` 的 `dev_xwt` 执行 `bash scripts/run_baseline_efficiency.sh output/baseline_efficiency/<新的目录>`。已有报告不会覆盖。
- 使用主模型现有 bn_pdformer Python 环境；B2 只加载现有 env_isaaclab 中的 XGBoost 包，没有修改任何 Conda 环境。
