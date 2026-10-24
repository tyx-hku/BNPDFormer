# BNPDFormer explainability heatmaps

These figures distinguish fixed graph priors, learned attention, and decoded forecasts.
Attention is an associative model weight, not a causal effect.
Palette: sequential maps use the same-hue pair light blue `#78B7C9` → deep teal `#46788E` (with a near-white low end); diverging maps use that blue ramp against coral `#E58B7B`. Pale yellow `#F6E093` and yellow-green `#97B319` are reserved for categorical charts, not sequential heatmaps.

## Sampling and aggregation

- Seed/split: `42` (from checkpoint configuration)
- Target samples per condition and model: `96`
- Conditions: normal = no current/future bottleneck; upcoming = no current but at least one future bottleneck; ongoing = at least one current bottleneck.
- Resource attention: averaged over selected samples, 30 history steps, heads, and encoder layers unless the figure states otherwise.
- Temporal attention: averaged over selected samples, resources, heads, and encoder layers.
- Inference runs in evaluation mode. Forward hooks read post-softmax attention after dropout; dropout is inactive and predictions are unchanged.
- Resource-labelled panels display 20 machine, gantry, human, and AGV nodes. B1--B18 are omitted from both axes without renormalizing the retained values; the stored matrices still contain all 38 model nodes.

## Figure inventory

1. `fig01_graph_priors`: fixed adjacency, hop proximity, and semantic similarity.
2. `fig02_resource_attention_states`: spatial and semantic attention for normal, upcoming, and ongoing states.
3. `fig03_resource_attention_change`: upcoming/ongoing attention minus normal attention.
4. `fig04_temporal_attention_states`: history-step attention under the three states and upcoming-minus-normal change.
5. `fig05_layerwise_upcoming_attention`: per-layer spatial and semantic attention for upcoming bottlenecks.
6. `fig06_entity_type_attention`: displayed resource attention aggregated to four non-buffer entity types.
7. `fig07_horizon_attention_change`: Start<=5/10/15 upcoming-minus-normal comparison.
8. `fig08_prediction_heatmaps`: future bottleneck truth, predicted probability, and absolute error for the busiest test episode.

## Limitations

- Attention weights do not establish causal effects.
- The underlying 38 nodes are production resources, not the 52 event nodes used by the reference ECGBSTNN paper; figures omit the 18 buffer nodes for readability.
- Condition averages use a deterministic episode-stratified subset; counts are recorded in `metadata.json`.
- The prediction heatmap shows one automatically selected high-activity episode and is illustrative rather than a complete performance summary.

## Reproduction

The stored matrices were extracted by `factory_bn.plot_explainability_heatmaps`. The paper figures are reproduced from those matrices with:

```powershell
cd D:\Capstone\BNPDFormer
python experiments\plot_ch5_attention_heatmaps.py
```

Extraction-script SHA-256: `fb1a0ad04e011b134d6dd0a17827467b45365a425d8352c6e96574b47dd5fa0c`
Plot-script SHA-256: `32480d522c4b5ecdbca609e85b5232add68b05c5bf48ebdeb9fad3e74556e32b`
Git commit: `c1404e06befa4a1eaeaf7701cd0c9a4a52b6e5f6`

## Generated files

- `fig01_graph_priors.pdf`
- `fig01_graph_priors.png`
- `fig01_graph_priors.svg`
- `fig02_resource_attention_states.pdf`
- `fig02_resource_attention_states.png`
- `fig02_resource_attention_states.svg`
- `fig03_resource_attention_change.pdf`
- `fig03_resource_attention_change.png`
- `fig03_resource_attention_change.svg`
- `fig04_temporal_attention_states.pdf`
- `fig04_temporal_attention_states.png`
- `fig04_temporal_attention_states.svg`
- `fig05_layerwise_upcoming_attention.pdf`
- `fig05_layerwise_upcoming_attention.png`
- `fig05_layerwise_upcoming_attention.svg`
- `fig06_entity_type_attention.pdf`
- `fig06_entity_type_attention.png`
- `fig06_entity_type_attention.svg`
- `fig07_horizon_attention_change.pdf`
- `fig07_horizon_attention_change.png`
- `fig07_horizon_attention_change.svg`
- `fig08_prediction_heatmaps.pdf`
- `fig08_prediction_heatmaps.png`
- `fig08_prediction_heatmaps.svg`
- `figure_table_trace.yaml`
- `heatmap_matrices.npz`
- `metadata.json`
