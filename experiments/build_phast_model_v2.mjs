import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const runtime=process.env.RUNTIME_NODE_MODULES;
const req=createRequire(runtime?path.join(runtime,'package.json'):import.meta.url);
const {Presentation,PresentationFile}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')).href);
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const BUILD=path.join(ROOT,'build/phast_model_v2');
const OUT=path.join(ROOT,'figures/drafts/phast_model_v2');
await fs.mkdir(BUILD,{recursive:true});await fs.mkdir(OUT,{recursive:true});
const W=1800,H=1100;
const p=Presentation.create({slideSize:{width:W,height:H}}),s=p.slides.add();s.background.fill='#FFFFFF';
const C={ink:'#202A39',text:'#242424',grey:'#6B7079',line:'#657386',blue:'#EAF1F8',green:'#EBF3E6',yellow:'#FBF3D8',purple:'#F1EAF5',rose:'#F8EBDD',detail:'#FDFDFC',teal:'#527C64'};
let seq=0;
function box(x,y,w,h,fill='none',stroke=C.ink,sw=1.5,name='',dash=false,round=false){return s.shapes.add({geometry:round?'roundRect':'rect',name:name||`shape-${++seq}`,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:sw,style:dash?'dashed':'solid'},...(round?{borderRadius:26}:{})});}
function tx(t,x,y,w,h=28,size=22,opt={}){const q=s.shapes.add({geometry:'textbox',name:t,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});q.text=t;q.text.style={typeface:'Times New Roman',fontSize:size,color:opt.color||C.text,bold:!!opt.bold,italic:!!opt.italic,alignment:opt.align||'center',verticalAlignment:'middle',autoFit:'none',wrap:'none',insets:0};return q;}
function ln(x1,y1,x2,y2,color=C.ink,sw=1.6,dash=false){
 // Native freeform lines use their true bounds, including vertical segments.
 const left=Math.min(x1,x2),top=Math.min(y1,y2),w=Math.max(.01,Math.abs(x2-x1)),h=Math.max(.01,Math.abs(y2-y1));
 return s.shapes.add({geometry:'custom',name:`line-${++seq}`,position:{left,top,width:w,height:h},fill:'none',line:{fill:color,width:sw,style:dash?'dashed':'solid'},customPaths:[{width:w,height:h,commands:[{moveTo:{x:x1-left,y:y1-top}},{lineTo:{x:x2-left,y:y2-top}}]}]});
}
function route(pts,color=C.ink,sw=1.6,dash=false,head=true){for(let i=1;i<pts.length;i++)ln(...pts[i-1],...pts[i],color,sw,dash);if(head){const[a,b]=pts.slice(-2),a0=Math.atan2(b[1]-a[1],b[0]-a[0]),k=7;ln(b[0],b[1],b[0]-k*Math.cos(a0-.48),b[1]-k*Math.sin(a0-.48),color,sw);ln(b[0],b[1],b[0]-k*Math.cos(a0+.48),b[1]-k*Math.sin(a0+.48),color,sw);}}
function mod(t,x,y,w,h=38,fill=C.blue,size=21,stroke=C.ink){box(x,y,w,h,fill,stroke,1.3,t);tx(t,x+4,y+2,w-8,h-4,size);}
function op(t,x,y,r=12){const q=s.shapes.add({geometry:'ellipse',name:`operator-${t}`,position:{left:x-r,top:y-r,width:2*r,height:2*r},fill:'#FFFFFF',line:{fill:C.ink,width:1.4}});tx(t,x-r,y-r,2*r,2*r,22);return q;}

// Central complete network. Only repeated computation and magnified modules
// have enclosing boundaries. The computation flows from bottom to top.
tx('PHAST-DP',729,10,346,38,30,{bold:true});
tx('Resource, onset, duration, cause and remaining order time',586,52,627,32,21);
mod('Event decoding and report assembly',713,108,374,46,C.green,23);
route([[900,108],[900,88]]);
const headCenters=[708,921,1120];
ln(708,181,1120,181);route([[900,181],[900,154]]);
headCenters.forEach(x=>route([[x,224],[x,181]]));
mod('Event heads (a)',620,224,176,59,C.rose,22);
mod('State and remaining\ntime decoders',822,224,198,59,C.yellow,21);
mod('Cause\nclassifier',1045,224,151,59,C.purple,21);
mod('Regime + precursor\nfusion',620,298,176,44,C.rose,18);
mod('Skip + order-progress\nfusion',822,298,198,44,C.yellow,18);
mod('Graph pooling\n+ node evidence',1045,298,151,44,C.purple,18);
headCenters.forEach(x=>route([[x,298],[x,283]]));
ln(708,360,1120,360);headCenters.forEach(x=>route([[x,360],[x,342]]));
route([[900,416],[900,360]]);tx('H(t)',914,369,79,29,22,{italic:true});

box(594,402,612,503,'none',C.ink,1.7,'Repeated encoder block',true);
tx('Spatiotemporal block × 5',603,371,289,29,23,{bold:true});
// Pre-normalized attention and feed-forward residuals.
op('+',900,430);route([[900,470],[900,443]]);
mod('Feed-forward network',787,470,226,42,C.blue,21);
route([[900,533],[900,512]]);mod('LayerNorm',802,533,196,35,C.blue,21);
route([[900,586],[900,568]]);op('+',900,600);
route([[900,631],[900,613]]);mod('Concat + Linear',802,631,196,43,C.purple,22);
route([[900,695],[900,674]]);ln(713,695,1087,695);
const atts=[[625,'Temporal attention\n4 heads',C.blue],[812,'Geographic (b)\n2 heads, hop mask',C.green],[999,'Semantic attention\n2 heads, corr. mask',C.yellow]];
for(const[x,t,fill]of atts){mod(t,x,724,176,65,fill,18);route([[x+88,724],[x+88,695]]);route([[x+88,814],[x+88,789]]);}
ln(713,814,1087,814);route([[900,835],[900,814]]);mod('LayerNorm',802,835,196,36,C.blue,21);
route([[900,891],[900,871]]);
route([[900,886],[1189,886],[1189,600],[913,600]],C.ink,1.6);
route([[900,577],[614,577],[614,430],[887,430]],C.ink,1.6);
tx('residual',1034,858,115,23,17,{italic:true,color:C.grey});
tx('residual',650,550,111,23,17,{italic:true,color:C.grey});

// Embedding and typed graph priors.
route([[900,920],[900,905]]);op('+',900,935);
route([[900,967],[900,948]]);
mod('Grouped Linear + GELU\nMean aggregation',710,967,380,56,C.blue,22);
route([[900,1046],[900,1023]]);
tx('Historical features X (30 × 38 × 27)',632,1049,544,34,23);
tx('Time + Laplacian\n+ node embeddings',998,916,238,42,20);
route([[997,936],[913,936]],C.grey,1.3);
tx('6 feature groups',465,981,204,29,21,{italic:true});route([[675,995],[710,995]],C.grey,1.2);

// Detail leaders are dashed and have no arrowheads.
route([[620,254],[540,254]],C.line,1.3,true,false);
route([[900,724],[900,708],[1230,708],[1250,708]],C.line,1.2,true,false);

// (a) Expanded event head: two additive conditioning stages, five prediction
// heads, and hot/cold selection for event occurrence.
box(35,176,505,572,C.detail,C.ink,1.5,'Event-head detail',true,true);
tx('(a) Process-informed event head',52,188,470,32,25,{bold:true});
mod('Occurrence, onset, duration and prefix',74,242,425,43,C.rose,21);
mod('Hot / cold selection',63,309,181,43,C.rose,20);
route([[153,309],[153,292],[286,292],[286,285]]);
tx('History-end state',54,362,193,27,19,{italic:true});route([[154,362],[154,352]],C.grey,1.3);
const ep=[
 [60,'Continue\nhead'],[156,'Onset\nhead'],[252,'Start\nhead'],[348,'Duration\nhead'],[444,'Prefix\nhead']
];
for(const[x,t]of ep){mod(t,x,405,86,57,C.rose,18);route([[x+43,488],[x+43,462]]);}
route([[103,405],[103,395],[77,395],[77,352]]);
route([[199,405],[199,395],[230,395],[230,352]]);
for(const x of[295,391,487])route([[x,405],[x,300],[x,285]]);
ln(103,488,487,488);route([[206,503],[206,488]]);
op('+',206,516);route([[206,557],[206,529]]);op('+',206,570);
tx('h(event)',229,489,103,24,18,{italic:true});
mod('H(t)',69,659,115,41,C.blue,22);
route([[127,659],[127,570],[193,570]]);
mod('History regime',205,659,144,41,C.rose,19);
mod('Embedding',205,600,144,38,C.rose,20);route([[277,659],[277,638]]);
route([[277,600],[277,570],[219,570]]);
mod('Precursor cues',369,659,149,41,C.rose,19);
mod('Local + neighbour\nMLP',369,589,149,50,C.rose,18);route([[444,659],[444,639]]);
route([[444,589],[444,516],[219,516]]);
tx('Conditioned node representation',66,714,446,23,18,{italic:true,color:C.grey});

// (b) Enlarged delay-conditioned geographic attention. Qp/Kp/Vp are learned
// pattern projections. Context is added only to geographic K.
box(1250,398,515,611,C.detail,C.ink,1.5,'Geographic-attention detail',true,true);
tx('(b) Delay-conditioned geographic attention',1268,412,480,34,24,{bold:true});
mod('History patch',1281,477,170,43,C.blue,21);
mod('Pattern bank (16)',1555,477,180,43,C.green,21);
mod('Linear: Qp',1281,558,117,40,C.blue,21);
mod('Linear: Kp',1455,558,117,40,C.green,21);
mod('Linear: Vp',1629,558,117,40,C.green,21);
route([[1366,520],[1366,540],[1340,540],[1340,558]]);
route([[1645,520],[1645,540],[1514,540],[1514,558]]);
route([[1645,540],[1688,540],[1688,558]]);
mod('softmax(Qp Kpᵀ / √d)',1308,635,286,44,C.green,24);
route([[1340,598],[1340,635]]);route([[1514,598],[1514,635]]);
op('×',1621,657);route([[1594,657],[1608,657]]);route([[1688,598],[1688,657],[1634,657]]);
route([[1621,670],[1621,709],[1518,709],[1518,738]],C.teal,1.8);
tx('C(pattern)',1625,690,123,26,19,{italic:true,color:C.teal});
mod('Qg',1297,732,79,40,C.blue,23);
mod('Kg',1406,732,79,40,C.blue,23);
mod('Vg',1654,732,79,40,C.blue,23);
op('+',1518,751);route([[1485,752],[1505,752]]);
tx('K̃g',1540,737,87,27,22,{italic:true});
mod('softmax(Qg K̃gᵀ / √d + Mg) Vg',1312,827,420,53,C.green,24);
route([[1337,772],[1337,809],[1376,809],[1376,827]]);
route([[1518,764],[1518,827]]);route([[1694,772],[1694,827]]);
tx('Geographic mask Mg',1273,896,258,27,19,{italic:true});
route([[1320,896],[1288,896],[1288,853],[1312,853]],C.grey,1.3);
route([[1571,880],[1571,923]]);tx('Geographic output',1475,929,260,30,23);
tx('Qg, Kg, Vg = Linear(LN(H))',1288,966,445,27,21,{italic:true});

// The two spatial masks are identified within their attention modules.
s.speakerNotes.text=`模型架构图修订 v2。中央从下到上完整展示输入、分组嵌入、位置/节点编码、五层pre-norm时空编码器、三条预测分支及报告输出。左侧(a)展开事件头：H_last依次加上历史regime embedding、包含邻域统计的precursor MLP，然后预测continue/onset、start、duration、prefix；history-end hot/cold选择发生概率。右侧(b)展开延迟条件地理注意力：历史patch与训练pattern bank分别投影为Qp/Kp/Vp，模式注意力生成C_pattern，仅加到地理K。当前图省略dropout和训练专用辅助损失。\n图中的主模型为PHAST-DP；代码类名仍BNPDFormer。依据论文dev_xwt ffcfbb7及isaac_factory origin/dev_tyx 29655baee57b9095119589a211ae1e2113b84078。主要代码factory_bn/backbone.py与model.py；_cluster_fused、_fuse_precursor、_combine_will_logit、_remain_decode、STSelfAttention.forward。\n颜色区分运算模块；虚线边界标识重复编码器或局部展开，虚线引出线表示对应关系。Times New Roman为用户指定。参考用户提供论文Fig.3的中央主干和局部展开层级，内容依据当前PHAST-DP实现。`;
await (await PresentationFile.exportPptx(p)).save(path.join(BUILD,'candidate.pptx'));
const png=await p.export({slide:s,format:'png',scale:1.3});await fs.writeFile(path.join(OUT,'PHAST_DP_model_v2.png'),new Uint8Array(await png.arrayBuffer()));
const layout=await s.export({format:'layout'});await fs.writeFile(path.join(BUILD,'layout.json'),await layout.text());
console.log('Created model revision:',OUT);
