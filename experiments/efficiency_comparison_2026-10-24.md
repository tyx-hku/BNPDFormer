# Efficiency comparison: data and provenance

## Verified sources

- Baseline source repository: `jintaoXue/isaac_factory`, branch `dev_xwt`, commit `2cfa56287700b08649f2b489f58a5239c426c168`.
- Committed `baseline_efficiency.md`, `baseline_efficiency.csv`, and `baseline_efficiency.json` are archived under `data/efficiency_20261023/`. They were read with `git show`; CSV line endings are normalized to LF with all field contents preserved. The code checkout and its active branch were not modified.
- All 12 baseline rows were checked against the author's supplied table. Every supplied latency, throughput, parameter count and GPU-memory value matches the formal CSV at the supplied display precision.
- The combined `data/efficiency_comparison_2026-10-24.csv` retains the full precision of baseline measurements. Main-model values come from the author's efficiency table and the existing manuscript: 713,984 parameters, 2.91 MiB checkpoint, 175.8 MiB peak allocated memory; three onset caps.
- The source JSON records unchanged checkpoint hashes, no training and no threshold selection for all 12 baseline tasks. Raw per-call latency files remain on the server under `output/baseline_efficiency/formal_20261023/`.

## Measurement protocol

- Author instruction on 2026-10-24: describe the experiments using the main model's measurement configuration. The baseline export confirms the same RTX 5090 server, Python 3.11.15, PyTorch 2.11.0+cu128, CUDA 12.8, batch 16, five complete test passes, 50 warm-up calls, and 5,000 batch-one calls per latency metric (five repetitions of 1,000 over a 256-sample pool).
- XGBoost 3.2.0 uses CPU with four threads. The benchmark's `TreeAdapter` explicitly calls `head.model.set_params(n_jobs=self.threads, device='cpu')`; this preserves the saved baseline CPU implementation. This is not a limitation of XGBoost's GPU support.
- Forward timing covers the full neural forward pass on a resident GPU input, or all seven XGBoost heads on prepared CPU features. Report timing adds transfer or history-feature construction, prediction decoding, and event materialization. Test-pass throughput includes DataLoader iteration. File writing, loss and metric computation are excluded.
- Throughput and batch-one report latency use different batching settings and are not reciprocals.
- GPU allocation is the PyTorch allocator peak for the process, including the model and prepared 256-sample pool; it is not total board memory. Model-file sizes describe saved artifacts, which may include training metadata. They do not measure identical pure-parameter serialization.

## Presentation and reproducibility

- Section 5.5 contains one compact table and three Report F1 versus report-p50 panels, one for each onset cap. The bilingual and existing English-only sections are synchronized; each uses its edition's event-results table label.
- Table ranges are the minimum and maximum across Start <= 5, 10 and 15, not confidence intervals or repeated-run uncertainty. Complete forward/report latency values and individual checkpoint sizes are retained in the combined CSV and original source files.
- `plot_efficiency_comparison.py` reads Report F1 from the current `main.tex` table `tab:comparison-main`, joins by model and onset cap, and exports `data/plot_data/quality_cost_comparison.csv`. Baseline Report F1 in the source efficiency CSV agrees with the manuscript after rounding to its three-decimal precision.
- Names are mapped as B2 = XGBoost, B3 = LSTM, B4 / GCN-GRU = BTGCN, and B5 / GAT-GRU = BSTAN. XGBoost is explicitly marked CPU.
- The old median-difference latency stack is removed from the manuscript; a difference of separately measured medians is not treated as a measured component latency.

```sh
python experiments/plot_efficiency_comparison.py
latexmk -xelatex main.tex
```

## Evaluation scope retained from the source

- The baseline timing export uses 6,886 windows / 40 episodes; the main-model reference uses 5,354 windows / 36 episodes. The table note discloses the two test-pool sizes. Total test-pass times are not used to compute speedup ratios.
- Main-model timings were collected on 2026-10-17 and baseline timings on 2026-10-23. The baseline record reports another user's Isaac Sim GPU workload during measurement and records GPU utilization before and after each run. The table note identifies the shared server; the text describes measured implementation costs without claiming an isolated architecture-only speed ranking.
- Existing `data/comparison_sources_2026-10-10.json` already records the 6,886-versus-5,354 comparison issue. The main performance table calls its results common-manifest, while baseline Report F1 in the new efficiency CSV still originates from the 6,886-window export. This efficiency revision preserves those reported F1 values and does not verify or resolve the performance-table sample-matching claim. Confirm or revise that claim before final submission.
- The quality/cost chart shows existing reported quality and measured runtime. It does not claim matched-sample Pareto optimality, statistical significance, new training-cost data, energy efficiency, or deployment performance on different hardware.
