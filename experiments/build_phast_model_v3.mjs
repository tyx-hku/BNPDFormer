import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const runtime=process.env.RUNTIME_NODE_MODULES;
const req=createRequire(runtime?path.join(runtime,'package.json'):import.meta.url);
const {Presentation,PresentationFile}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')).href);
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const BUILD=path.join(ROOT,'build/phast_model_v3');
const OUT=path.join(ROOT,'figures/drafts/phast_model_v3');
await fs.mkdir(BUILD,{recursive:true});await fs.mkdir(OUT,{recursive:true});
const W=1800,H=1240;
const p=Presentation.create({slideSize:{width:W,height:H}}),s=p.slides.add();s.background.fill='#FFFFFF';
const C={ink:'#202A39',text:'#242424',grey:'#6B7079',line:'#657386',blue:'#EAF1F8',green:'#EAF2EB',yellow:'#EAF1F8',purple:'#EAF1F8',rose:'#F7EEE4',detail:'#FFFFFF',teal:'#527C64',steel:'#55768D',orange:'#B48358'};
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

// Reusable visual vocabulary: editable matrices, vectors, nodes and short patches.
const blues=['#F1F5F8','#D7E3EB','#A7BCCD','#6D8CA2','#3D617B'];
const greens=['#F2F6F2','#DCE9DE','#ACC5B1','#799E81','#4F7658'];
const oranges=['#FCF6EF','#EDDBCA','#D8B89B','#BB8A61','#95633F'];
function matrix(x,y,rows,cols,cell=9,palette=blues,mode='features'){
 for(let r=0;r<rows;r++)for(let c=0;c<cols;c++){
  let k=(r*3+c*2+r*c)%palette.length;
  if(mode==='similarity')k=r===c?4:((r+c)%4===0?3:0);
  if(mode==='mask')k=(Math.abs(r-c)<2||r===2||c===2)?3:0;
  box(x+c*cell,y+r*cell,cell,cell,palette[k],'#FFFFFF',.65,`${mode}-${r}-${c}`);
 }
 box(x,y,cols*cell,rows*cell,'none',C.line,.6);
}
function vector(x,y,n=8,cell=10,palette=blues){matrix(x,y,1,n,cell,palette,'vector');}
function nd(x,y,r=8,fill='#D7E3EB',stroke=C.steel,label=''){
 s.shapes.add({geometry:'ellipse',name:label||'resource node',position:{left:x-r,top:y-r,width:r*2,height:r*2},fill,line:{fill:stroke,width:1.4}});
 if(label)tx(label,x-r,y-r,r*2,r*2,13,{color:fill===C.steel||fill===C.teal?'#FFFFFF':C.ink});
}
function curve(x1,y1,x2,y2,rise,color=C.line,sw=1.2){
 const x=Math.min(x1,x2),y=Math.min(y1,y2)-rise,w=Math.max(1,Math.abs(x2-x1)),h=rise+Math.abs(y2-y1);
 s.shapes.add({geometry:'custom',name:'temporal attention link',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:color,width:sw},customPaths:[{width:w,height:h,commands:[{moveTo:{x:x1-x,y:y1-y}},{cubicBezTo:{x1:x1-x,y1:0,x2:x2-x,y2:0,x:x2-x,y:y2-y}}]}]});
}
function patchTrace(x,y,w,h,vals,color=C.teal){
 ln(x,y+h,w+x,y+h,'#B8C4CD',.65);
 const pts=vals.map((v,i)=>[x+i*w/(vals.length-1),y+h-v*h]);
 for(let i=1;i<pts.length;i++)ln(...pts[i-1],...pts[i],color,1.8);
 for(const pt of pts)nd(...pt,2.3,color,color);
}
function neighbourhood(x,y,k=1,accent=C.teal){
 const pts=[[0,0],[-42,-27],[36,-31],[-46,30],[42,29]];
 for(let i=1;i<pts.length;i++)ln(x,y,x+pts[i][0]*k,y+pts[i][1]*k,'#AAB9C4',1.2);
 ln(x-42*k,y-27*k,x-46*k,y+30*k,'#C7D1D8',1);
 ln(x+36*k,y-31*k,x+42*k,y+29*k,'#C7D1D8',1);
 pts.forEach(([a,b],i)=>nd(x+a*k,y+b*k,i===0?10:7,i===0?accent:'#FFFFFF',i===0?accent:C.line));
}

// Central complete network. Only repeated computation and magnified modules
// have enclosing boundaries. The computation flows from bottom to top.
tx('PHAST-DP',729,10,346,38,30,{bold:true});
tx('Resource, onset, duration, state, cause and remaining time',578,52,643,32,21);
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

box(594,402,612,577,'none',C.ink,1.7,'Repeated encoder block',true);
tx('Spatiotemporal block × 5',603,371,289,29,23,{bold:true});
// Pre-normalized attention and feed-forward residuals.
op('+',900,430);route([[900,470],[900,443]]);
mod('Feed-forward network',787,470,226,42,C.blue,21);
route([[900,533],[900,512]]);mod('LayerNorm',802,533,196,35,C.blue,21);
route([[900,586],[900,568]]);op('+',900,600);
route([[900,631],[900,613]]);mod('Concat + Linear',802,631,196,43,C.purple,22);
route([[900,695],[900,674]]);ln(713,695,1087,695);
const atts=[[625,'Temporal attention'],[812,'Geographic (b)'],[999,'Semantic attention']];
for(const[x,t]of atts){box(x,724,176,150,'#FFFFFF',C.ink,1.1,t);tx(t,x+4,730,168,25,18,{bold:true});route([[x+88,724],[x+88,695]]);route([[x+88,895],[x+88,874]]);}
// Temporal attention: one query attends to several observed time steps.
for(const [x,rise]of [[650,40],[691,29],[732,18]])curve(x,810,774,810,rise,x===650?'#ACBBC7':C.steel,x===650?1:1.4);
ln(642,810,782,810,'#B5C2CD',.8);
for(const x of[650,691,732,774])nd(x,810,6.7,x===774?C.steel:'#FFFFFF',C.steel);
tx('time steps',640,824,145,20,16,{italic:true,color:C.grey});tx('4 heads',640,848,145,22,17);
// Geographic attention: a selected node and its resource neighbours.
neighbourhood(900,803,.96,C.teal);tx('2 heads, hop mask',818,848,164,22,17);
// Semantic attention: correlation structure and selected similar resources.
matrix(1017,772,6,6,9,blues,'similarity');
route([[1077,801],[1094,801]],C.grey,1.1);
for(const [x,y]of [[1118,777],[1150,797],[1128,825]])ln(1114,807,x,y,'#B0BECB',1);
nd(1114,807,8,C.steel,C.steel);nd(1118,777,5,'#FFFFFF',C.steel);nd(1150,797,6,'#FFFFFF',C.steel);nd(1128,825,6,'#FFFFFF',C.steel);
tx('2 heads, corr. mask',1006,848,161,22,17);
ln(713,895,1087,895);route([[900,915],[900,895]]);mod('LayerNorm',802,915,196,36,C.blue,21);
route([[900,968],[900,951]]);
route([[900,965],[1189,965],[1189,600],[913,600]],C.ink,1.6);
route([[900,577],[614,577],[614,430],[887,430]],C.ink,1.6);
tx('residual',1034,936,115,23,17,{italic:true,color:C.grey});
tx('residual',650,550,111,23,17,{italic:true,color:C.grey});

// Embedding and typed graph priors.
route([[900,998],[900,979]]);op('+',900,1011);
route([[900,1054],[900,1024]]);
mod('Grouped Linear + GELU\nMean aggregation',710,1054,380,56,C.blue,22);
route([[900,1134],[900,1110]]);
for(let i=2;i>0;i--)box(820+i*9,1142-i*7,160,44,C.blue,'#B5C3CF',.7,'Historical tensor layer');
matrix(820,1142,4,16,10,blues);
tx('Historical features X (30 × 38 × 27)',632,1195,544,32,23);
tx('Time + Laplacian\n+ node embeddings',998,992,238,42,20);
route([[997,1011],[913,1011]],C.grey,1.3);
const groupShades=['#D7E3EB','#A7BCCD','#E1E9EF','#6D8CA2','#BBCBD7','#91AABB'];
for(let i=0;i<6;i++)box(488+i*27,1071,25,20,groupShades[i],'#FFFFFF',.7,'Feature group');
tx('6 feature groups',477,1094,183,26,19,{italic:true});route([[659,1082],[710,1082]],C.grey,1.2);

// Detail leaders are dashed and have no arrowheads.
route([[620,254],[540,254]],C.line,1.3,true,false);
route([[900,724],[900,708],[1230,708],[1250,708]],C.line,1.2,true,false);

// (a) Expanded event head: two additive conditioning stages, five prediction
// heads, and hot/cold selection for event occurrence.
box(35,176,505,653,C.detail,C.ink,1.5,'Event-head detail',true,true);
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
vector(343,494,8,10,oranges);
matrix(91,660,4,7,10,blues);tx('H(t)',78,709,119,26,22,{italic:true});
route([[127,660],[127,570],[193,570]]);
// Regime identifiers and the corresponding learned embedding.
for(let i=0;i<7;i++)nd(216+i*20,681,6.5,i===3?C.orange:'#FFFFFF',C.orange);
tx('History regime',197,709,163,26,20);
tx('Embedding',207,596,142,27,20);vector(230,627,8,12,oranges);
route([[277,669],[277,640]]);route([[277,596],[277,570],[219,570]]);
// Local resource graph followed by an editable small MLP network.
neighbourhood(444,707,.79,C.orange);tx('Precursor cues',369,753,149,28,20);
tx('Local + neighbour MLP',363,556,163,25,17);
const mlpRows=[[400,444,488],[385,423,462,500],[400,444,488]],ys=[635,610,585];
for(let r=0;r<2;r++)for(const x1 of mlpRows[r])for(const x2 of mlpRows[r+1])ln(x1,ys[r],x2,ys[r+1],'#D3C3B6',.7);
for(let r=0;r<3;r++)mlpRows[r].forEach(x=>nd(x,ys[r],4.6,r===2?C.orange:'#FFFFFF',C.orange));
route([[444,696],[444,641]]);route([[444,580],[444,516],[219,516]]);

// (b) Enlarged delay-conditioned geographic attention. Qp/Kp/Vp are learned
// pattern projections. Context is added only to geographic K.
box(1250,398,515,756,C.detail,C.ink,1.5,'Geographic-attention detail',true,true);
tx('(b) Delay-conditioned geographic attention',1268,412,480,34,24,{bold:true});
tx('History patch',1281,468,170,27,21);
patchTrace(1292,503,126,45,[.2,.8,.48],C.steel);
tx('Pattern bank (16)',1510,468,225,27,21);
const snippets=[[.1,.8,.3],[.7,.5,.2],[.1,.35,.85],[.2,.25,.65],[.7,.1,.8],[.8,.7,.2],[.1,.8,.7],[.6,.2,.1],[.4,.7,.45]];
snippets.forEach((v,i)=>patchTrace(1530+(i%3)*67,502+Math.floor(i/3)*23,48,16,v,C.teal));
tx('…',1722,534,25,24,22);
matrix(1308,594,4,7,9,blues);matrix(1482,594,4,7,9,greens);matrix(1656,594,4,7,9,greens);
tx('Qp',1303,636,72,26,22,{italic:true});tx('Kp',1478,636,72,26,22,{italic:true});tx('Vp',1652,636,72,26,22,{italic:true});
route([[1355,555],[1355,575],[1340,575],[1340,594]]);
route([[1635,567],[1635,578],[1514,578],[1514,594]]);route([[1635,578],[1688,578],[1688,594]]);
tx('Linear',1266,566,70,24,16,{italic:true,color:C.grey});
mod('softmax(Qp Kpᵀ / √d)',1321,680,273,42,C.green,23);
route([[1340,632],[1286,632],[1286,701],[1321,701]]);
route([[1514,662],[1514,680]]);
route([[1457,722],[1457,751]]);vector(1318,751,16,16,greens);
tx('Matching weights',1330,776,244,24,19,{italic:true});
op('×',1621,759);route([[1574,759],[1608,759]]);route([[1688,662],[1688,759],[1634,759]]);
route([[1621,772],[1621,803],[1518,803],[1518,849]],C.teal,1.8);
tx('C(pattern)',1624,785,121,25,19,{italic:true,color:C.teal});
tx('Qg',1296,811,81,26,22,{italic:true});tx('Kg',1410,811,81,26,22,{italic:true});
tx('K̃g',1547,811,81,26,22,{italic:true,color:C.teal});tx('Vg',1664,811,81,26,22,{italic:true});
matrix(1306,842,4,6,10,blues);matrix(1420,842,4,6,10,blues);matrix(1554,842,4,6,10,greens);matrix(1670,842,4,6,10,blues);
op('+',1518,863);route([[1480,863],[1505,863]]);route([[1531,863],[1554,863]],C.teal,1.8);
mod('softmax(Qg K̃gᵀ / √d + Mg) Vg',1320,942,412,53,C.green,23);
route([[1336,882],[1336,918],[1376,918],[1376,942]]);route([[1584,882],[1584,942]]);route([[1700,882],[1700,942]]);
matrix(1266,951,5,5,7,blues,'mask');tx('Mg',1261,918,49,24,20,{italic:true});route([[1301,969],[1320,969]],C.grey,1.2);
route([[1552,995],[1552,1027]]);vector(1504,1027,8,12,greens);
tx('Geographic output',1408,1056,287,30,23);
tx('Qg, Kg, Vg = Linear(LN(H))',1288,1110,445,27,21,{italic:true});

// The two spatial masks are identified within their attention modules.
s.speakerNotes.text=`模型架构图修订 v3。中央从下到上完整展示输入、分组嵌入、位置/节点编码、五层pre-norm时空编码器、三条预测分支及报告输出。左侧(a)展开事件头：H_last依次加上历史regime embedding、包含邻域统计的precursor MLP，然后预测continue/onset、start、duration、prefix；history-end hot/cold选择发生概率。右侧(b)展开延迟条件地理注意力：历史patch与训练pattern bank分别投影为Qp/Kp/Vp，模式注意力生成C_pattern，仅加到地理K。当前图省略dropout和训练专用辅助损失。\n图中的主模型为PHAST-DP；代码类名仍BNPDFormer。依据论文dev_xwt ffcfbb7及isaac_factory origin/dev_tyx 29655baee57b9095119589a211ae1e2113b84078。主要代码factory_bn/backbone.py与model.py；_cluster_fused、_fuse_precursor、_combine_will_logit、_remain_decode、STSelfAttention.forward。\n颜色区分运算模块；虚线边界标识重复编码器或局部展开，虚线引出线表示对应关系。Times New Roman为用户指定。参考用户提供论文Fig.3的中央主干和局部展开层级，内容依据当前PHAST-DP实现。`;
s.speakerNotes.text += '\n网络节点、MLP单元、矩阵色块及短序列折线用于说明计算机制，均为示意，不代表实验测量、实际权重或真实节点/层宽数量。图中标注的输入维度、块数、头数及模式库大小依据当前配置。';
await (await PresentationFile.exportPptx(p)).save(path.join(BUILD,'candidate.pptx'));
const png=await p.export({slide:s,format:'png',scale:1.3});await fs.writeFile(path.join(OUT,'PHAST_DP_model_v3.png'),new Uint8Array(await png.arrayBuffer()));
const layout=await s.export({format:'layout'});await fs.writeFile(path.join(BUILD,'layout.json'),await layout.text());
console.log('Created model revision:',OUT);
