"""Add every metric from the archived six summary tables, without mixing definitions."""
import hashlib
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'experiments/data/all_metrics_source_20261005.tex'
TITLES = ['Event identification and onset tolerance', 'Onset and duration estimation',
          'Decoded state, occupancy and resource-type performance', 'Process-cause identification',
          'Order remaining-time estimation', 'Per-device event and duration performance']

def plain(s):
    s = re.sub(r'\\(?:textbf|mathrm|text)\{([^{}]*)\}', r'\1', s)
    s = s.replace('\\_', '_').replace('\\le', '≤').replace('\\Delta', 'Δ')
    s = s.replace('\\dagger', '†').replace('\\ast','*')
    return s.replace('$','').replace('{','').replace('}','').replace('\\','').strip()

def run():
    source = SOURCE.read_text(encoding='utf-8')
    assert source.rstrip().endswith('\\end{document}'), 'source truncated'
    blocks = re.findall(r'\\begin\{tabular\}\{[^\n]*\}\s*(.*?)\\end\{tabular\}',source,re.S)[:6]
    assert len(blocks)==6
    md = ['## N. 指标汇总 PDF 补全数据',
          '来源：`D:/Capstone/isaac_factory/bnpdformer_all_metrics.pdf`及其同名TeX，2026-10-05版本。归档副本：`experiments/data/all_metrics_source_20261005.tex`。以下保留归档精度；比例转为百分数，时间单位min。不是新增训练结果。',
          '本节完整保留汇总的六张结果表。A–K中who召回与这里的strict report召回是不同口径，均保留，不按方法分数高低替换。BestModel对应PHGST-DP，Full-S1为其微调前模型，pretrain_init仅作历史参考。']
    outputs = {key:[] for key in ['ablation','device']}
    for ti,block in enumerate(blocks):
        lines=[l.strip() for l in block.splitlines() if '&' in l and l.rstrip().endswith('\\\\')]
        cells=[[x.strip() for x in l[:-2].split('&')] for l in lines]
        header, rawrows = cells[0],cells[1:]
        expected=15 if ti==5 else 34
        assert len(rawrows)==expected,(ti,len(rawrows))
        assert all(len(r)==len(header) for r in rawrows),(ti,'columns')
        # Units are fixed from export_metrics_tex.py, not chosen by observed scores.
        percent_cols = {0:set(range(3,15)),1:{5,6,7},2:set(range(2,len(header))),
                        3:{2,3,4,5,7,8,9,10},4:set(),5:{3,4,5}}[ti]
        # Exclude delta F1: express it as percentage points.
        rows=[]; cap=''
        for raw in rawrows:
            row=[re.sub(r'\\textbf\{([^{}]+)\}',r'\1',v) for v in raw]
            if ti<5:
                if row[1]: cap=row[1]
                row[1]=cap
            row=[v.replace('BestModel','PHGST-DP') for v in row]
            for j in percent_cols:
                try:
                    number=float(row[j])
                    row[j]=f'{number*100:.1f}' + (' pp' if ti==0 and j==6 else r'\%')
                except ValueError:
                    pass
            rows.append(row)
        # Split wide metrics into at most five data columns; keep cap and method explicit.
        idcount=1 if ti==5 else 2
        for group,offset in enumerate(range(idcount,len(header),5),1):
            inds=list(range(idcount))+list(range(offset,min(offset+5,len(header))))
            heads=[header[j] for j in inds]
            md += [f'### N{ti+1}.{group} {TITLES[ti]}',
                   '| '+' | '.join(plain(h) for h in heads)+' |',
                   '|'+ '|'.join(['---']*len(inds))+'|']
            md += ['| '+' | '.join(plain(row[j]) for j in inds)+' |' for row in rows]
            md.append('')
            caption=TITLES[ti]+f' (metric group {group}).'
            note = ('Proportions are percentages; timing errors are in minutes. '
                    'PHGST-DP and Full-S1 share frozen event/cause heads. '
                    'Training schedules and event pools follow Table~\\ref{tab:ablation-arms}. '
                    'The pretraining row is a historical reference, not a matched comparator.')
            if ti==0:
                note += ' Upcoming/Ongoing and onset-bin recalls use strict report matching; tolerance is 3 min unless stated. Delta F1 is in percentage points.'
            if ti==2:
                note += ' State is decoded from event timing; Hot is the occupancy head. Type hmean is the harmonic mean of per-type Hot F1.'
            if ti==3:
                note += ' Cause labels are rule-derived associations; the unsupervised NoCluster cause head is not evaluated.'
            if ti==4:
                note += ' Only PHGST-DP receives stage-2 remaining-time fine-tuning; Full-S1 is the appropriate stage-1 reference.'
            if ti==5:
                note='Start cap 5 min. Zero-support resources are retained as coverage information, not assigned a performance score.'
            # tabularx wraps long metric headers without shrinking text below scriptsize.
            latex=['\\begin{table*}[p]','\\centering','\\scriptsize',
                   '\\setlength{\\tabcolsep}{3pt}', '\\renewcommand{\\arraystretch}{1.12}',
                   '\\caption{'+caption+' '+note+'}',
                   f'\\label{{tab:complete-{ti+1}-{group}}}',
                   '\\begin{tabularx}{\\textwidth}{@{}l'+ 'X'*(len(inds)-1)+'@{}}',
                   '\\toprule',' & '.join(heads)+r' \\', '\\midrule']
            lastcap=None
            for row in rows:
                if ti<5 and lastcap is not None and row[1]!=lastcap: latex.append('\\midrule')
                if ti<5: lastcap=row[1]
                latex.append(' & '.join(row[j] for j in inds)+r' \\')
            latex += ['\\bottomrule','\\end{tabularx}','\\end{table*}','']
            outputs['device' if ti==5 else 'ablation'].extend(latex)
    # Label-method development experiments are distinct from checkpoint ablations.
    labels=json.loads((ROOT/'experiments/data/label_validity_dev_tyx_8767583.json').read_text(encoding='utf-8'))
    for title,key,fields in [
        ('Label representation separability','separability',['test_positive_rate','macro_f1','balanced_accuracy','auroc','station_macro_f1']),
        ('Label representation geometry','separability',['silhouette','davies_bouldin','fisher_ratio']),
        ('Label-method cause classification','cause_comparison',['accuracy','macro_f1','balanced_accuracy']),
        ('Label-method cause recall','cause_comparison',['transport_delay','material_shortage','starved_upstream','queue_buildup'])]:
        lines=['\\begin{table*}[p]','\\centering\\scriptsize',
               '\\caption{'+title+'. Development comparison at seed 42, not an ablation of the retained PHGST-DP checkpoint. Proportions are percentages; geometry indices retain their original scales.}',
               '\\begin{tabularx}{\\textwidth}{l'+'X'*len(fields)+'}', '\\toprule',
               'Method & '+' & '.join(f.replace('_',r'\_') for f in fields)+r' \\', '\\midrule']
        for row in labels[key]['metrics']:
            vals=[f'{row[f]:.3f}' if f in {'silhouette','davies_bouldin','fisher_ratio'} else f'{row[f]*100:.1f}'+r'\%' for f in fields]
            lines.append(row['method']+' & '+' & '.join(vals)+r' \\')
        lines+=['\\bottomrule','\\end{tabularx}','\\end{table*}','']
        outputs['ablation'].extend(lines)
    # Keep the full validation cards available without copying their repeated test columns.
    cards=re.findall(r'\\noindent\\begin\{minipage\}.*?\\end\{minipage\}',source,re.S)
    assert len(cards)==34
    validation=[]
    for card in cards:
        runid=re.search(r'\\scriptsize\\texttt\{([^}]+)\}',card).group(1)
        cardrows=[]
        for line in card.splitlines():
            if line.strip().startswith('&') and line.rstrip().endswith('\\\\'):
                cols=[v.strip() for v in line.strip()[:-2].split('&')]
                if len(cols)==4:cardrows.append(cols)
        validation.append((runid,cardrows))
    for group,metricnames in enumerate([
        ['Precision $P$','Recall $R$','F1',r'Upcoming $R_{\mathrm{up}}$',r'Ongoing $R_{\mathrm{on}}$'],
        ['Start MAE (tp)','Duration MAE (tp)','Hot F1','Accuracy','Macro recall'],
        ['MAE']],1):
        heads=['Checkpoint']+metricnames
        md += [f'### N7.{group} 验证集指标（保留归档比例0–1及分钟单位）',
               '| '+' | '.join(plain(x) for x in heads)+' |','|'+'|'.join(['---']*len(heads))+'|']
        lines=['\\begin{table*}[p]','\\centering\\scriptsize',
               '\\caption{Validation results at the selected checkpoints. Report precision/recall and F1 are validation report metrics; remaining-time MAE is in minutes. These values document selection, not held-out superiority. Proportions retain the archived 0--1 scale.}',
               '\\begin{tabularx}{\\textwidth}{l'+'X'*len(metricnames)+'}', '\\toprule',
               ' & '.join(heads)+r' \\', '\\midrule']
        for runid,rows0 in validation:
            lookup={r[1]:r[2] for r in rows0}
            # Long exact checkpoint names remain in Markdown; compact labels in the manuscript.
            short=plain(runid).replace('_seed42','').replace('_min8_cold_ep50','')
            short=short.replace('bestmodel','PHGST-DP').replace('full_farboost','Full-S1')
            for prefix in ['ablation_','entity_','struct_']:short=short.replace(prefix,'')
            vals=[lookup.get(k,'---') for k in metricnames]
            md.append('| '+' | '.join([plain(runid)]+[plain(x) for x in vals])+' |')
            lines.append(short.replace('_',r'\_')+' & '+' & '.join(vals)+r' \\')
        md.append('')
        lines+=['\\bottomrule','\\end{tabularx}','\\end{table*}','']
        outputs['ablation'].extend(lines)
    # Export all four matched-budget arms under both logged and selected-checkpoint definitions.
    aux=list(csv.DictReader((ROOT/'experiments/data/matched_auxiliary_summary_dev_tyx_29655ba.csv').open(encoding='utf-8')))
    lines=['\\begin{table*}[p]','\\centering\\scriptsize',
           '\\caption{Matched-budget auxiliary supervision: logged and separately selected cause metrics. All arms use seed 42, Start cap 5 min and 50 epochs. Values are percentages; the two export definitions are not interchanged.}',
           '\\begin{tabularx}{\\textwidth}{lXXXXX}','\\toprule',
           'Arm & Logged station F1 & Logged cause acc. & Selected cause acc. & Selected cause macro recall & Seed'+r' \\', '\\midrule']
    for row in aux:
        vals=[f'{float(row[k])*100:.1f}'+r'\%' for k in ['log_who_f1','log_cause_acc','cause_selected_acc','cause_selected_macro_recall']]
        lines.append(row['arm']+' & '+' & '.join(vals)+' & 42'+r' \\')
    lines+=['\\bottomrule','\\end{tabularx}','\\end{table*}','']
    outputs['ablation'].extend(lines)
    outdir=ROOT/'experiments/tables';outdir.mkdir(exist_ok=True)
    for name,lines in outputs.items():
        (outdir/f'ch5_complete_{name}.tex').write_text('\n'.join(lines),encoding='utf-8')
    inventory=ROOT/'第五章数据清单_跳过5.2.md'
    old=inventory.read_text(encoding='utf-8').split('\n## N.')[0]
    inventory.write_text(old+'\n\n'+'\n'.join(md)+'\n',encoding='utf-8')
    print('Completed six source tables: 5 × 34 checkpoint rows and 15 device rows; separate label tables included.')

if __name__=='__main__':run()
