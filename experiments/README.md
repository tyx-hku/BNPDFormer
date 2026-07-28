# ICCBEI paper experiments (raw results from hc_factory)

Perception / TPA **training & logging** live in `isaac_factory_iccbei` (`batch_train.sh` jobs **30–39** / group **P**).
This folder only **imports raw JSON** and **plots / fills tables** for `main.tex`.

Paper repo symlink: `_isaac_factory` → `/home/xue/work/isaac_factory_iccbei`.

## Run (isaac_factory_iccbei)

```bash
cd /home/xue/work/isaac_factory_iccbei
./batch_train.sh P cuda:0          # full paper pipeline
# or stepwise:
./batch_train.sh 30 cuda:0         # TPA grid makespan/idle
./batch_train.sh 31 cuda:0         # collect source Nh5_O5
./batch_train.sh 32 cuda:0         # collect OOD cells
./batch_train.sh 33 34 35 36 cuda:0
./batch_train.sh 37 38 39 cuda:0
```

## Raw layout (copy or symlink here)

```text
isaac_factory_iccbei/.../hc_factory/output/paper_exp/
  tpa/Nh*_O*/episodes.jsonl
  datasets/Nh*_O*/
  perception_runs/*/history.json  best.pt
  metrics/*.json                  # eval dumps + aggregate
```

Suggested local mirror:

```bash
mkdir -p experiments/raw
ln -sfn /home/xue/work/isaac_factory_iccbei/source/isaaclab_tasks/isaaclab_tasks/direct/hc_factory/output/paper_exp \
  experiments/raw/paper_exp
```

## Plot

```bash
python experiments/plot_paper_exp.py --raw experiments/raw/paper_exp --out figures
python experiments/plot_fig_env_cameras.py
```

Outputs expected by `main.tex` placeholders:
- `figures/fig_learning_curve.pdf`
- `figures/fig_subtask_cm.pdf` (or combined diagnostics figure)
- `figures/fig_env_cameras.pdf` (environment + cameras + process/subtask exemplar)
- JSON summaries you can paste into `tab:tpa_scale` / `tab:perc_ood`
