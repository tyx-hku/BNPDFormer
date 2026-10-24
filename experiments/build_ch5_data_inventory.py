"""Build source-linked Chapter 5 inventory, excluding section 5.2."""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'experiments/data'
parts = ['# 第五章数据清单（跳过 5.2）\n\n由 `experiments/build_ch5_data_inventory.py` 自动生成。比例显示为百分数（两位小数），时间误差保留三位小数；显示舍入不修改源文件。缺值显示“—”。宽表拆成最多六列的小表。配置短名对应的完整 run 见末尾登记。']
manifest = []

HEADERS = {
    'run':'配置 · cap', 'method':'方法', 'n_test_windows':'测试窗口数', 'epoch':'epoch', 'thr':'阈值',
    'will15_precision':'精确率', 'will15_recall':'召回率', 'will15_f1':'Will15 F1', 'report_f1':'Report F1',
    'who_recall_upcoming':'Upcoming召回', 'who_recall_ongoing':'Ongoing召回',
    'state_f1_1step':'单步状态F1', 'state_f1_horizon':'未来状态F1',
    'dur_mae_union':'Union MAE/min', 'dur_rmse_union':'Union RMSE/min',
    'dur_mae_tp':'TP MAE/min', 'dur_rmse_tp':'TP RMSE/min',
    'start_mae_tp':'起点MAE/min', 'start_rmse_tp':'起点RMSE/min',
    'remain_mae':'总体MAE/min', 'remain_mae_early':'早期MAE/min',
    'remain_mae_middle':'中期MAE/min', 'remain_mae_late':'晚期MAE/min',
    'arm':'配置', 'start_cap':'cap/min', 'max_epochs':'最大epoch',
    'log_who_f1':'日志工位F1', 'log_cause_acc':'日志原因准确率',
    'cause_selected_acc':'选定模型原因准确率', 'cause_selected_macro_recall':'选定模型宏召回',
    'macro_f1':'宏F1', 'balanced_accuracy':'平衡准确率', 'auroc':'AUROC',
    'station_macro_f1':'站点宏F1', 'test_positive_rate':'正例率',
    'silhouette':'轮廓系数', 'davies_bouldin':'DB指数↓', 'fisher_ratio':'Fisher比',
    'accuracy':'准确率', 'selected_epoch':'选定epoch', 'class':'类别', 'support':'支持量',
    'transport_delay':'运输延迟', 'material_shortage':'物料短缺',
    'starved_upstream':'上游饥饿', 'queue_buildup':'队列积压',
    'ndcg3':'NDCG@3', 'positive_recall2':'Positive R@2', 'positive_recall3':'Positive R@3',
    'weighted_recall3':'Weighted R@3', 'coverage3_rho90':'Coverage@3',
    'stage1_mae':'阶段1 MAE/min','stage2_mae':'阶段2 MAE/min','absolute_drop':'下降/min',
    'percent_drop':'下降/%','source_stage1':'阶段1来源','source_stage2':'阶段2来源',
    'onset_bin':'起点分箱/min','strict_report_recall':'严格报告召回',
    'short':'设备简称','type':'类型','device':'设备全名','f1':'F1',
    'forward_p50_ms':'Forward p50/ms','report_p50_ms':'Report p50/ms',
    'extra_p50_ms':'两中位数之差/ms','note':'说明','seed':'种子',
}
PERCENT = {'will15_precision','will15_recall','will15_f1','report_f1',
    'who_recall_upcoming','who_recall_ongoing','state_f1_1step','state_f1_horizon',
    'log_who_f1','log_cause_acc','cause_selected_acc','cause_selected_macro_recall',
    'macro_f1','balanced_accuracy','station_macro_f1','test_positive_rate','accuracy',
    'transport_delay','material_shortage','starved_upstream','queue_buildup','strict_report_recall','f1',
    'positive_recall2','positive_recall3','weighted_recall3','coverage3_rho90'}

def short_run(value):
    cap = re.search(r'start(\d+)', value)
    if not cap:
        return value
    name = value.split('_start')[0]
    names = {'bestmodel':'Full','full_farboost':'Full阶段1','full_nofarboost':'NoFarBoost',
        'ablation_nograph':'NoGraph','ablation_nogroup':'NoGroup','ablation_nocluster':'NoCluster',
        'entity_nocross':'NoCross','entity_noinfo':'NoInfo','entity_machineonly':'MachineOnly',
        'struct_nopattern':'NoPattern','struct_nosplit':'NoSplit'}
    return names.get(name,name) + ' · ' + cap.group(1)

def table(title, rows, fields=None, note=''):
    parts.append('\n## ' + title + '\n\n' + note)
    if not rows:
        parts.append('没有可读取的数据；不安排绘图。')
        return
    fields = fields or list(rows[0])
    def cell(field, v):
        if v is None or v == '':
            return '—'
        if field in {'run','source_stage1','source_stage2'}:
            v = short_run(str(v))
        else:
            try:
                num = float(v)
                if field in PERCENT:
                    v = f'{100*num:.2f}%'
                elif field == 'percent_drop':
                    v = f'{num:.2f}'
                elif num == int(num):
                    v = str(int(num))
                else:
                    v = f'{num:.3f}'
            except (ValueError, TypeError):
                pass
        return str(v).replace('|', '\\|').replace('\n', ' ')
    groups = [fields] if len(fields) <= 6 else [[fields[0]] + fields[i:i+5] for i in range(1,len(fields),5)]
    for number, group in enumerate(groups,1):
        if len(groups) > 1:
            parts.append(f'### 指标组 {number}')
        lines = ['| ' + ' | '.join(HEADERS.get(f,f) for f in group) + ' |',
                 '|' + '|'.join(['---'] * len(group)) + '|']
        lines.extend('| ' + ' | '.join(cell(f,r.get(f)) for f in group) + ' |' for r in rows)
        parts.append('\n'.join(lines))

def readcsv(rel):
    p = ROOT / rel
    manifest.append({'path':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

summary = readcsv('experiments/data/bottleneck_eval_summary.csv')
events = readcsv('experiments/data/main_event_metrics_dev_tyx_29655ba.csv')
index = {r['run']:r for r in summary}
assert len(index) == len(summary), 'duplicate run'
for r in events:
    assert r['run'] in index, r['run']
    assert r['n_test_windows'] == '5354', r['run']
merged = [{**index[r['run']], **r} for r in events]
table('A. 5.3 全部配置的事件识别、状态与时间误差', merged,
      ['run','n_test_windows','epoch','thr','will15_precision','will15_recall','will15_f1','report_f1','who_recall_upcoming','who_recall_ongoing','state_f1_1step','state_f1_horizon','dur_mae_union','dur_rmse_union','dur_mae_tp','dur_rmse_tp','start_mae_tp','start_rmse_tp'],
      '来源：bottleneck_eval_summary.csv 与 main_event_metrics_dev_tyx_29655ba.csv，严格按 run 连接。源比例为 0–1，本表转为百分数；时间误差单位 min。Report F1 和 Will15 F1 分列；union 与 tp 误差分列。所有配置都列出，包括 Full 对照。')
table('B. 各配置剩余时间及阶段误差', summary,
      ['run','remain_mae','remain_mae_early','remain_mae_middle','remain_mae_late'],
      '来源：bottleneck_eval_summary.csv；单位 min。这是 5.3 的训练配置补充；5.2 主结果表保持由组员维护。不要将不同训练阶段混合排名。')
table('C. 匹配预算 Cause×State 四组结果', readcsv('experiments/data/matched_auxiliary_summary_dev_tyx_29655ba.csv'),note='来源同名 CSV。log_cause_acc 与 cause_selected_acc 是不同导出口径，正文四组 19.5/89.5/18.5/89.5% 对应 log_cause_acc。')
labelpath = DATA / 'label_validity_dev_tyx_8767583.json'
labels = json.loads(labelpath.read_text(encoding='utf-8'))
manifest.append({'path':str(labelpath.relative_to(ROOT)),'sha256':hashlib.sha256(labelpath.read_bytes()).hexdigest()})
for key, title, note in [
    ('oracle_pilot','D. Oracle 先导结果','3 个无扰动开发 episode；完整 Oracle 未运行。未提交实际 anchor 清单，不能宣称已核实 27 个锚点。'),
    ('separability','E. 标签方法 raw-last 可分性','这是表示/标签可分性，并非 PHGST-DP 五种标签训练后的性能。源报告保留三位小数；实际采样量未提交。'),
    ('cause_comparison','F. 五种标签方法原因分类','共同 3245 个原因窗口，seed=42。四个原因列为类别 recall；macro_f1 与 balanced_accuracy 分列。')]:
    table(title,labels[key]['metrics'],note='来源：label_validity_dev_tyx_8767583.json。'+note)
table('F1. 原因类别支持量',[{'class':k,'support':v} for k,v in labels['cause_comparison']['class_support'].items()])
assert sum(labels['cause_comparison']['class_support'].values()) == labels['cause_comparison']['n_test']
for rel,title,note in [
    ('remain_dumbbell_full.csv','G. 两阶段剩余时间配对数据','由 source_stage1/source_stage2 指定 checkpoint；只用于 5.3 的训练分析。'),
    ('delay_distance.csv','H. 提前预警与距离分箱','上半为 cap 下 Upcoming recall，下半为起点分箱 strict report recall，不是同一指标；缺失分箱留空，不连线补齐。'),
    ('per_device_start5.csv','I. Start≤5 逐设备指标','这是 per-device 聚合点，不是逐样本误差分布。support=0 的设备仍列出，不能据其 F1 评价泛化。'),
    ('latency_stack.csv','J. 现有延迟绘图导出','forward/report 为分别测得的 p50。extra_p50_ms 只是两个中位数之差，不是组件耗时中位数，不再安排堆叠图。')]:
    table(title,readcsv('experiments/data/plot_data/'+rel),note='来源：experiments/data/plot_data/'+rel+'。'+note)
trace = readcsv('experiments/data/plot_data/timeline_phgst.csv')
table('K. 案例逐窗口数据登记',[{'file':'experiments/data/plot_data/timeline_phgst.csv','rows':len(trace),'fields':', '.join(trace[0]),'window_min':min(float(r['window']) for r in trace),'window_max':max(float(r['window']) for r in trace)}],note='完整时间序列保留在 CSV；不在 Markdown 中截断后冒充完整序列。true/pred state 与 true/pred duration 分列，duration 单位 min。该文件不含真实扰动事件起止时间，不支持直接画扰动 Gantt。')
tex = (ROOT/'main.tex').read_text(encoding='utf-8')
start = tex.index('\\subsection{Experimental setup}')
end = tex.index('\\section{Discussion}')
chapter = tex[start:end]
skip0 = chapter.index('\\subsection{Main and baseline performance comparison}')
skip1 = chapter.index('\\subsection{Ablation study}')
chapter = chapter[:skip0]+chapter[skip1:]
parts.append('\n## L. 正文表格原始行存档（5.1、5.3、5.4、5.5）\n\n本节保留 LaTeX 原始行，放入代码块供回查，不作为阅读版表格。前面的 A–K 是数值阅读版；本节补充正文设置与协议。正文记录不能代替独立实验测量。')
for block in re.findall(r'\\begin\{table\*?\}.*?\\end\{table\*?\}',chapter,re.S):
    label = re.search(r'\\label\{([^}]+)',block)
    rows = []
    for line in block.splitlines():
        if '&' in line and line.rstrip().endswith('\\\\'):
            rows.append({'原始表格行':line.rstrip()[:-2].strip()})
    parts.append('### ' + (label.group(1) if label else 'unnamed'))
    parts.append('```latex\n' + '\n'.join(r['原始表格行'] + r' \\' for r in rows) + '\n```')
parts.append('## 配置短名与原始 run 对照\n\n以下保留完整名称，供回查源CSV。')
table('run登记',[{'短名':short_run(r['run']),'完整run':r['run']} for r in summary])
parts.append('\n## M. 完整来源指纹\n\n以下 SHA-256 用于确认数据清单对应的文件版本。')
table('文件登记',manifest)
(ROOT/'第五章数据清单_跳过5.2.md').write_text('\n\n'.join(parts)+'\n',encoding='utf-8')
print(f'Generated inventory: {len(merged)} event runs; {len(summary)} checkpoints; {len(trace)} trace rows; {len(manifest)} sources')
from complete_ch5_tables import run as complete_tables
complete_tables()
