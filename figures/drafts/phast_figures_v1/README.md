# PHAST-DP figure draft v1

Three editable scientific figures, one figure per PowerPoint slide. The figure text uses Times New Roman. Chinese explanations and source references are in the slide notes.

1. **Overall methodology**: factory observations, historical resource representation, prediction, reporting, and training supervision.
2. **PHAST-DP architecture**: grouped embedding, five spatiotemporal encoder blocks, delay-pattern conditioning, and prediction heads.
3. **Heterogeneous resource representation**: five resource types, a representative resource subgraph, feature tensor, and attention masks.

## Files

- `PHAST_DP_figures_v1_editable.pptx`: editable labels, modules, graphs, and lines. The production-line screenshot is an embedded raster image.
- `PHAST_DP_figures_v1_editable.pdf`: three-page vector export with embedded Times New Roman fonts.
- `01_methodology.png`, `02_model_architecture.png`, and `03_heterogeneous_resources.png`: previews rendered from the PDF.

The source is `experiments/build_phast_figures_v1.mjs`. It uses `@oai/artifact-tool` and writes a candidate deck to `build/phast_figures_v1/`. Set `RUNTIME_NODE_MODULES` to the installed runtime package directory when running the builder. Final PDF export requires Times New Roman to be visible to the PDF renderer.

## Evidence and scope

- Manuscript: `dev_xwt`, commit `ffcfbb7`.
- Experimental code: `isaac_factory`, `origin/dev_tyx`, commit `29655baee57b9095119589a211ae1e2113b84078`.
- Main code files: `graph.py`, `dataset.py`, `backbone.py`, `model.py`, `train.py`, and `PDFormer.py` under `source/isaaclab_tasks/isaaclab_tasks/direct/hc_factory/PDFormer/`.
- Factory screenshot: `figures/camera_views/env_screen_shot.png`.
- Input: 30 history windows, 38 resource nodes, 27 feature channels. Future grid: 20 windows.
- Resource counts: 7 machines/workbenches, 4 gantries, 4 transport robots, 5 workers, and 18 buffers; 15 prediction targets.
- Graph views, feature-cell colours, history strips, and pattern thumbnails are schematic. The resource graph shows a representative subset of nodes and edges.

This is a review draft. The manuscript source and its existing figures are unchanged.
