# 实验产线、工序与多实体关系图

产物：`fig_factory_process_entities.pdf`（论文）、`.svg`（文字与形状可编辑）、`.png`（300 dpi 预览）。截图作为栅格图嵌入，其余元素为矢量。原截图未修改；通过绘图视口显示左侧 47.5% 的区域。

复现：在仓库根目录运行 `python experiments/plot_factory_process_entities.py`。

LaTeX 插入片段：`figures/fig_factory_process_entities.tex`。建议在实验设置开头用 `\input{figures/fig_factory_process_entities.tex}` 引入，使用双栏跨栏尺寸。此次未修改已有正文。

## 内容核对依据

代码根目录：`_isaac_factory/source/isaaclab_tasks/isaaclab_tasks/direct/hc_factory/`。

- `env_asset_cfg/cfg_process_task_gallery.py`：六道工序为切割、开槽、组装点焊、氩弧根焊、MIG 面焊和防锈涂装；点焊输入为管材、法兰和弯头；点焊和防锈涂装使用同一工作台资源族。
- `env_asset_cfg/cfg_process_subtask_gallery.py`：同区龙门搬运；跨区源龙门装载、运输机器人搬运、目标龙门卸载，并包含人工协作。
- `PDFormer/factory_bn/graph.py`：七节点 PROCESS_CHAIN、无向连接、按名称匹配的缓冲区关联、全部人员/龙门/运输机器人到全部机器节点的连接，以及龙门和运输机器人各自的同类型连接。
- `_isaac_factory/10.实验说明.md` 第 20 行：38 节点构成为 7 工位、4 龙门、5 人员、4 运输机器人、18 缓冲区。
- `figures/camera_views/env_screen_shot.png` 与已有分设备相机图：环境与设备位置。

## 解释边界

工艺图箭头表示六道真实工序的先后。关系图表示模型构图规则，不表示物理搬运方向、因果关系或具体时刻的人员分配。尤其不能把 graph.py 中相邻的两个工作台和两个旋转焊接工位解释成必须顺序访问的加工步骤。

关系图合并显示人员和物流节点，缓冲区按三类名称关联规则归组；不暗示每一类缓冲区数量相同。缓冲区到机器组的线为关联束，具体目的工位写在每组标签中。自环与龙门/运输机器人同类边省略。物料为工序输入而不是额外资源节点。

颜色来自用户给定方案：#3D6EB4、#5BA7D9、#A6DCED、#FFF2C7、#FCB84D、#F26121；未为凑齐色板强行使用红色。
