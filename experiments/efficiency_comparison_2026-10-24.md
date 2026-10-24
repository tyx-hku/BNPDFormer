# Efficiency comparison: RTX 5090 update and provenance

## Current sources

- Repository: `jintaoXue/isaac_factory`, branch `dev_xwt`, commit `a5b6c929331a7531218372af9a7f111b6c27c35a`.
- Source directory: `doc/experiments/efficiency_5090_20261024/`.
- Six source files are archived byte-for-byte in `data/efficiency_5090_20261024/`: the combined MD/CSV, baseline MD/CSV/JSON, and `main_efficiency_source_snapshot.json`. `source_manifest.json` records the commit and SHA-256 of each file. The code checkout was read through `git show` without modifying its working files or active branch.
- `data/efficiency_comparison_5090_2026-10-24.csv` is the current normalized 15-row input. Timing precision, source test counts, and both memory fields are retained. Model names map B2 = XGBoost, B3 = LSTM, B4 = BTGCN, and B5 = BSTAN.
- All 15 combined timing rows were checked against the baseline CSV or original main-model report snapshots. The 12 baseline Report F1 values agree with the manuscript at its displayed precision.
- B2 uses the new 2026-10-24 CUDA measurement. B3–B5 retain the 2026-10-23 GPU measurements; PHGST-DP retains the 2026-10-17 measurements, now verified against source JSON rather than rounded author-supplied values.
- Historical CPU-B2 data under `data/efficiency_20261023/` and `data/efficiency_comparison_2026-10-24.csv` remain archival records. They are not read by the current plot or used in the current efficiency table.

## Measurement protocol

- All five models execute prediction on RTX 5090 CUDA. Environment: Python 3.11.15, PyTorch 2.11.0+cu128, CUDA 12.8; B2 uses XGBoost 3.2.0 with CuPy 14.2.0.
- Throughput: batch 16, five complete test passes after 50 warm-up batches. Batch-one forward/report latency: 5,000 calls, five repetitions of 1,000 over a fixed 256-sample pool, with CUDA synchronization around each timed call.
- Forward: neural input or XGBoost prepared features already reside on the GPU. All seven XGBoost prediction heads execute CUDA `inplace_predict`, with CPU fallback prohibited.
- Report: includes transfer, model-specific feature processing, prediction, decoding, and event materialization. XGBoost includes CPU history-feature construction, H2D features, all seven CUDA heads, and D2H outputs. Batch test passes additionally include DataLoader iteration. File writing, loss, and evaluation-metric computation are excluded.
- Throughput and batch-one latency use different batching settings and are not reciprocals.
- Neural GPU memory is the PyTorch allocator peak, including the model and resident inference sample pool. XGBoost's native CUDA allocations are not captured by that allocator: its corresponding table entry is unavailable, and its 662–670 MiB NVML process peak is separately described. NVML samples include CUDA context, libraries, and caches; these two metrics are not ranked together.
- Checkpoint sizes describe saved artifacts, which may contain training metadata; they do not measure equivalent pure-parameter serialization. Training time was not measured by this experiment.
- The source validates B2 CPU/GPU output agreement over all 6,886 baseline samples: cause/onset/threshold decisions agree, with maximum regression-output absolute difference 0.00061035. No new training or threshold selection was performed.

## Presentation and reproduction

- Section 5.5 in both manuscript editions uses the new CUDA results and a five-model table. Table ranges are minima/maxima across the three onset caps, not confidence intervals.
- XGBoost: throughput 236–323 samples/s; report p50 39.29–58.55 ms, p95 41.73–60.86 ms, p99 52.81–72.66 ms. PHGST-DP: throughput 1,946–1,987 samples/s; report p50 4.72–4.77 ms and p99 5.51–5.60 ms.
- `plot_efficiency_comparison.py` reads the current normalized GPU CSV, joins Report F1 from `main.tex` (`tab:comparison-main`) by model/onset cap, and exports `data/plot_data/quality_cost_comparison.csv` and `figures/fig_quality_cost.pdf/.svg/.png`.
- The three quality–cost panels use a shared, explicitly labelled logarithmic latency axis to accommodate the new XGBoost measurements. Fonts, colors, and model markers retain the existing figure style.
- The section emphasizes reported event-identification quality, millisecond-scale report generation, and stable PHGST-DP resource requirements. It does not infer architecture-only speedup ratios from these deployment measurements.

```sh
python experiments/plot_efficiency_comparison.py
latexmk -xelatex main.tex
```

## Source scope and raw records

- Baseline timing uses 6,886 windows / 40 episodes; the main-model snapshot uses 5,354 windows / 36 episodes. The section's existing table note points to the draft evaluation note distinguishing the specified common 5,354-window protocol from archived workloads. Updating B2's inference device does not establish that the sample manifests were aligned. Source counts are unchanged.
- Measurements were collected on different dates on a shared GPU server. The baseline JSON records GPU load before/after each run, including another user's Isaac Sim workload. They characterize measured implementations and workloads; no exclusive-device benchmark is claimed.
- The quality/cost chart pairs existing reported quality with measured runtime. It does not establish matched-sample Pareto optimality, statistical significance, energy efficiency, or performance on other hardware.
- B2 raw records: `/home/sci/work/BSTAN_isaac_factory/output/baseline_efficiency/formal_5090_20261024/B2_cap{5,10,15}/`.
- B3–B5 raw records: `/home/sci/work/BSTAN_isaac_factory/output/baseline_efficiency/formal_20261023/B{3,4,5}_cap{5,10,15}/`.
- Each directory contains `baseline_efficiency.json`, `forward_latency_raw.csv`, and `report_latency_raw.csv`. Main-model report paths and original report SHA-256 values are preserved in `main_efficiency_source_snapshot.json`.
