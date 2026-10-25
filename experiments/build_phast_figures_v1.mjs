import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const runtimeModules=process.env.RUNTIME_NODE_MODULES;
const resolveFrom=createRequire(runtimeModules ? path.join(runtimeModules,'package.json') : import.meta.url);
const {Presentation, PresentationFile}=await import(pathToFileURL(resolveFrom.resolve('@oai/artifact-tool')).href);

// Scientific figure draft. All graphs, modules, labels and arrows are native
// PowerPoint objects. The factory photograph is an embedded repository asset.
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const HERE=path.join(ROOT,'build/phast_figures_v1');
await fs.mkdir(HERE,{recursive:true});
const OUT=path.join(ROOT,'figures/drafts/phast_figures_v1');
await fs.mkdir(OUT,{recursive:true});
const W=1440,H=820;
const p=Presentation.create({slideSize:{width:W,height:H}});
const C={ink:'#252525',grey:'#666666',light:'#D5D7D8',pale:'#F5F5F3',blue:'#396B88',bluep:'#EAF0F4',teal:'#488778',tealp:'#EAF3EF',ochre:'#B28A44',ochrep:'#F6F0E5',rust:'#B46954',rustp:'#F8ECE7',purple:'#8A789A',purplep:'#F0ECF5'};
let serial=0;
function shape(s,g,x,y,w,h,fill='none',stroke=C.ink,sw=1,name=''){
 return s.shapes.add({geometry:g,name:name||`${g}-${++serial}`,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:sw,style:'solid'}});
}
function text(s,t,x,y,w,h=30,size=22,opt={}){
 const q=shape(s,'textbox',x,y,w,h,opt.bg||'none','none',0,opt.name||t.slice(0,50));
 q.text=t;q.text.style={typeface:'Times New Roman',fontSize:size,color:opt.color||C.ink,bold:!!opt.bold,italic:!!opt.italic,alignment:opt.align||'left',verticalAlignment:opt.valign||'middle',autoFit:'none',wrap:'none',insets:0,...opt.style};return q;
}
function line(s,x1,y1,x2,y2,color=C.ink,width=1.4,dashed=false){
 const dx=x2-x1,dy=y2-y1,l=Math.hypot(dx,dy);
 return s.shapes.add({geometry:'line',position:{left:(x1+x2-l)/2,top:(y1+y2)/2,width:l,height:0,rotation:Math.atan2(dy,dx)*180/Math.PI},fill:'none',line:{fill:color,width,style:dashed?'dashed':'solid'}});
}
function arrow(s,pts,color=C.ink,width=1.6,dashed=false){
 for(let i=1;i<pts.length;i++)line(s,...pts[i-1],...pts[i],color,width,dashed);
 const [a,b]=pts.slice(-2),ang=Math.atan2(b[1]-a[1],b[0]-a[0]),k=8;
 line(s,b[0],b[1],b[0]-k*Math.cos(ang-.47),b[1]-k*Math.sin(ang-.47),color,width);
 line(s,b[0],b[1],b[0]-k*Math.cos(ang+.47),b[1]-k*Math.sin(ang+.47),color,width);
}
function module(s,t,x,y,w,h,color=C.blue,fill=C.bluep,size=21){
 const q=shape(s,'rect',x,y,w,h,fill,color,1.2,t);text(s,t,x+6,y+2,w-12,h-4,size,{align:'center'});return q;
}
function section(s,letter,t,x,y,w){text(s,`(${letter})`,x,y,36,32,23,{bold:true});text(s,t,x+39,y,w-39,32,23,{bold:true});}
function plus(s,x,y){shape(s,'ellipse',x-12,y-12,24,24,'#FFFFFF',C.grey,1.2);text(s,'+',x-11,y-12,22,24,21,{align:'center'});}
function title(s,t){text(s,t,42,28,1350,40,31,{bold:true});}
function grid(s,x,y,rows,cols,cw,ch,colors){
 for(let r=0;r<rows;r++)for(let c=0;c<cols;c++)shape(s,'rect',x+c*cw,y+r*ch,cw,ch,colors[(r*7+c*3+r*c)%colors.length],'#FFFFFF',.7);
}
function tensor(s,x,y,w,h,rows=6,cols=10){
 for(let d=2;d>0;d--)shape(s,'rect',x+d*11,y-d*9,w,h,C.bluep,C.light,.8);
 grid(s,x,y,rows,cols,w/cols,h/rows,['#E8EEF2','#B6CCD9','#7FA5BC','#CFDFE8']);
 shape(s,'rect',x,y,w,h,'none',C.blue,.9);
}
const TYPES={M:['rect',C.blue,C.bluep],G:['hexagon',C.ochre,C.ochrep],R:['diamond',C.rust,C.rustp],H:['ellipse',C.teal,C.tealp],B:['rect',C.purple,C.purplep]};
function node(s,id,x,y,r=20){const [g,c,f]=TYPES[id[0]];const q=shape(s,g,x-r,y-r,2*r,2*r,f,c,1.7,id);text(s,id,x-r,y-r,2*r,2*r,r*.8,{align:'center'});return q;}
function graphMini(s,x,y,k=1){
 const N={M1:[0,65],M2:[100,65],M3:[200,65],G1:[65,-10],R1:[150,145],H1:[-5,145],B1:[48,25],B2:[148,25]};
 const E=[['M1','M2'],['M2','M3'],['M1','B1'],['M2','B2'],['G1','M1'],['G1','M2'],['G1','M3'],['R1','M1'],['R1','M2'],['R1','M3'],['H1','M1'],['H1','M2']];
 for(const [a,b] of E)line(s,x+N[a][0]*k,y+N[a][1]*k,x+N[b][0]*k,y+N[b][1]*k,a[0]==='M'?C.blue:C.light,a[0]==='M'?1.8:1);
 for(const [a,xy]of Object.entries(N))node(s,a,x+xy[0]*k,y+xy[1]*k,17*k);
}
const sources=`依据：论文 main.tex（dev_xwt，ffcfbb7）；实验代码 origin/dev_tyx（29655baee57b9095119589a211ae1e2113b84078）。代码路径 source/isaaclab_tasks/isaaclab_tasks/direct/hc_factory/PDFormer/factory_bn/。模型命名使用论文 PHAST-DP；代码类名仍为 BNPDFormer。Times New Roman 为用户指定。`;

// FIGURE 1: an asymmetric flow, with a separate lower training lane.
{
const s=p.slides.add();s.background.fill='#FFFFFF';title(s,'Overall methodology for dynamic bottleneck prediction');
section(s,'a','Factory observations',45,105,400);
section(s,'b','Resource representation',480,105,355);
section(s,'c','Prediction and reporting',855,105,530);
const img=await fs.readFile(path.join(ROOT,'figures/camera_views/env_screen_shot.png'));
s.images.add({blob:img,contentType:'image/png',alt:'Isaac Sim factory scene from the project repository',fit:'contain',position:{left:45,top:162,width:390,height:157}});
text(s,'Digital-twin production line',50,331,380,28,22,{italic:true});
text(s,'Resource states at 1-minute intervals',49,386,405,28,21);
const rowNames=['Queue','Stall','Logistics'];
rowNames.forEach((nm,r)=>{text(s,nm,50,430+r*34,93,24,20);for(let j=0;j<16;j++)shape(s,'rect',150+j*17,435+r*34,15,15,[C.bluep,'#B6CCD9','#759DB4'][((j+2*r)*(r+2))%3],'none',0);});
arrow(s,[[150,553],[425,553]],C.grey,1.1);text(s,'t − 29',148,566,70,23,19);text(s,'t',411,566,30,23,19,{italic:true});text(s,'Observed history',215,560,170,27,20,{align:'center'});
arrow(s,[[437,239],[509,239]],C.grey);text(s,'windowing',442,199,105,25,18,{italic:true});
tensor(s,530,212,185,104,6,9);
text(s,'X: 30 × 38 × 27',507,336,248,33,24,{align:'center',italic:true});
text(s,'time × resources × features',483,371,300,29,20,{align:'center'});
graphMini(s,529,462,.70);
text(s,'Shared resource graph',492,580,300,28,21,{align:'center'});
arrow(s,[[740,495],[812,495],[812,300],[846,300]],C.grey,1.3);text(s,'Topology + resource types',505,411,283,25,18,{align:'center',color:C.grey});
arrow(s,[[740,269],[846,269]],C.ink,1.8);
for(let i=2;i>=0;i--)shape(s,'rect',866+i*9,201-i*8,197,119,i===0?C.bluep:'#FFFFFF',i===0?C.blue:C.light,1.2);
text(s,'PHAST-DP',877,227,175,33,27,{bold:true,align:'center'});text(s,'spatiotemporal encoder',867,266,195,26,18,{align:'center'});
arrow(s,[[964,323],[964,372]],C.ink);
module(s,'Process-informed heads',853,381,222,61,C.teal,C.tealp,21);
text(s,'history regime + precursor cues',824,463,282,29,18,{align:'center',italic:true,color:C.grey});
text(s,'Bottleneck report',1151,171,247,33,25,{bold:true});
line(s,1150,213,1390,213,C.ink,1.1);
['Affected resource','Onset and duration','Future bottleneck state','Process cause','Remaining order time'].forEach((t,i)=>{text(s,t,1166,229+i*49,228,31,20);line(s,1151,267+i*49,1390,267+i*49,C.light,.7);});
arrow(s,[[1075,411],[1118,411],[1118,351],[1146,351]],C.teal,1.4);
text(s,'20-window forecast',1150,504,245,29,21,{italic:true});
line(s,46,626,1390,626,C.light,1);
text(s,'Training supervision',46,650,230,30,23,{bold:true,color:C.rust});
text(s,'Future operational states',47,711,286,29,21);arrow(s,[[319,728],[388,728]],C.rust,1.4,true);
text(s,'Process-based event labels',410,689,308,30,22);text(s,'resource rules + persistence',410,728,300,27,20,{italic:true,color:C.grey});
arrow(s,[[731,728],[810,728]],C.rust,1.4,true);
text(s,'Joint training objectives',834,689,288,30,22);text(s,'events · states · time · cause',834,728,310,27,20,{color:C.grey});
arrow(s,[[966,680],[798,680],[798,351],[869,351],[869,325]],C.rust,1.3,true);
line(s,1183,690,1225,690,C.ink,1.5);text(s,'prediction flow',1235,675,170,30,18);
line(s,1183,735,1225,735,C.rust,1.5,true);text(s,'training supervision',1235,720,175,30,18);
s.speakerNotes.text=`图1：方法整体流程。左侧为项目真实 Isaac Sim 截图及历史窗口示意；中部为输入张量和共享资源图；右侧为 PHAST-DP 编码器、过程信息预测头和报告输出。底部虚线表示训练监督，未来状态只用于构造标签和损失。时间条的色块仅为窗口示意，不代表某次实验观测。监督目标包括事件、状态、时间与原因。\n${sources}\n图片：figures/camera_views/env_screen_shot.png。相关代码 dataset.py、graph.py、model.py、causes.py、train.py。`;
}

// FIGURE 2: large encoder cross-section, smaller conditioning and output branches.
{
const s=p.slides.add();s.background.fill='#FFFFFF';title(s,'PHAST-DP model architecture');
section(s,'a','Input embedding',40,103,328);section(s,'b','Spatiotemporal encoder',406,103,580);section(s,'c','Prediction heads',1030,103,375);
tensor(s,63,195,190,102,6,10);text(s,'30 × 38 × 27',75,317,188,29,23,{italic:true,align:'center'});
arrow(s,[[158,349],[158,386]],C.ink);
module(s,'Group-wise Linear + GELU',43,395,264,49,C.blue,C.bluep,20);
text(s,'queue · stall · logistics',56,460,258,26,19);text(s,'shortage · context · type',56,489,258,26,19);
arrow(s,[[158,529],[158,552]],C.ink);module(s,'Mean of six groups',58,563,235,45,C.blue,C.bluep,21);
arrow(s,[[158,611],[158,637]],C.ink);plus(s,158,651);
text(s,'Time + Laplacian + node ID',36,696,300,28,21,{align:'center'});arrow(s,[[158,696],[158,666]],C.grey,1.1);
arrow(s,[[173,651],[344,651],[344,501],[432,501]],C.ink,1.7);
text(s,'d = 80',257,657,73,28,21,{italic:true});

// The enclosing outline denotes one encoder block, not a layout card.
shape(s,'rect',388,369,549,417,'none',C.light,1.1);
shape(s,'rect',381,362,549,417,'none',C.light,1.1);
shape(s,'rect',374,355,549,417,'none',C.blue,1.5);
text(s,'Encoder block × 5',431,304,273,29,24,{bold:true});
module(s,'LN',432,465,53,68,C.grey,C.pale,20);
arrow(s,[[488,500],[514,500]],C.ink,1.3);
line(s,516,418,516,580,C.grey,1.2);line(s,516,418,542,418,C.grey,1.2);line(s,516,500,542,500,C.grey,1.2);line(s,516,580,542,580,C.grey,1.2);
module(s,'Temporal attention\n4 heads',545,386,227,64,C.blue,C.bluep,20);
module(s,'Geographic attention\n2 heads',545,468,227,64,C.teal,C.tealp,20);
module(s,'Semantic attention\n2 heads',545,548,227,64,C.ochre,C.ochrep,20);
line(s,866,418,866,580,C.grey,1.2);for(const y of[418,500,580])line(s,773,y,866,y,C.grey,1.1);
arrow(s,[[866,500],[897,500]],C.ink,1.3);text(s,'Concat',846,616,70,25,18,{italic:true});
// The residual/FFN sequence is below the parallel attention body.
arrow(s,[[898,500],[898,704],[727,704]],C.ink,1.5);
module(s,'Project',634,683,88,43,C.blue,C.bluep,20);arrow(s,[[634,705],[610,705]],C.ink);plus(s,597,705);
arrow(s,[[579,705],[552,705]],C.ink);module(s,'LN + FFN',438,683,109,43,C.blue,C.bluep,19);
arrow(s,[[438,705],[413,705]],C.ink);plus(s,399,705);
arrow(s,[[419,504],[380,504],[380,765],[597,765],[597,720]],C.grey,1,true);
arrow(s,[[581,717],[581,747],[399,747],[399,720]],C.grey,1,true);
arrow(s,[[399,690],[399,338],[960,338]],C.blue,1.8);
text(s,'H(t)',977,326,51,27,20,{italic:true,color:C.blue});

// Delay context enters geographic keys only.
text(s,'Delay-pattern context',443,163,294,30,23,{bold:true,color:C.teal});
for(let i=0;i<4;i++){
 let bx=454+i*31;shape(s,'rect',bx,207-i*4,23,51,C.tealp,C.teal,.8);
 line(s,bx+4,246-i*4,bx+9,231-i*4,C.teal,1);line(s,bx+9,231-i*4,bx+15,239-i*4,C.teal,1);line(s,bx+15,239-i*4,bx+19,218-i*4,C.teal,1);
}
text(s,'16 patterns',431,271,145,25,18,{align:'center'});
arrow(s,[[576,230],[614,230]],C.teal,1.2);module(s,'Pattern matching',623,207,185,48,C.teal,C.tealp,20);
text(s,'history query',822,192,153,24,19,{italic:true,color:C.grey});arrow(s,[[865,220],[813,230]],C.grey,1.1);
arrow(s,[[716,258],[716,292],[790,292],[790,454],[717,454],[717,470]],C.teal,1.2);
text(s,'key context',799,263,120,25,18,{color:C.teal,italic:true});

// Right output branches. H_last fans out without claiming order progress in cause head.
line(s,968,234,968,632,C.blue,1.5);arrow(s,[[961,338],[968,338]],C.blue,1.5);
arrow(s,[[968,234],[1027,234]],C.blue,1.4);
module(s,'Station events',1032,208,317,52,C.blue,C.bluep,23);
text(s,'continuation / onset · duration · prefix',1007,275,394,28,19);
text(s,'History regime + precursor cues',1012,161,388,27,20,{color:C.teal,italic:true});arrow(s,[[1178,192],[1178,205]],C.teal,1.2);
arrow(s,[[968,418],[1027,418]],C.blue,1.4);module(s,'Future state + remaining time',1032,392,317,52,C.teal,C.tealp,21);
text(s,'Layer skips + order progress',1048,454,331,28,20,{italic:true,color:C.grey});
arrow(s,[[968,594],[1027,594]],C.blue,1.4);module(s,'Process cause',1032,568,317,52,C.ochre,C.ochrep,23);
text(s,'Graph pooling + gated node evidence',1010,632,390,27,20,{italic:true,color:C.grey});
text(s,'Decoding and report',1100,708,288,30,23,{bold:true});
text(s,'events · states · causes · remaining time',1005,751,408,27,20);
for(const y of [234,418,594])line(s,1349,y,1386,y,C.grey,1.1);
arrow(s,[[1386,234],[1386,691],[1205,691],[1205,704]],C.grey,1.1);
s.speakerNotes.text=`图2：主模型结构。输入按六个特征组分别 Linear+GELU 后取均值，加入时间位置、Laplacian 与节点标识嵌入。五层编码器中每层并行时间4头、地理2头、语义2头，拼接投影和两次残差/FFN；虚线路径表示残差。延迟模式上下文只加到 geographic keys。事件头使用最后一步隐表示、历史regime和前兆特征；状态/订单剩余时间分支还使用跨层skip及订单进度；原因分支使用graph pooling和门控节点证据，不把订单进度画入原因头。绘图省略了各MLP内部层数。16个模式来自训练数据。\n${sources}\n代码：backbone.py, model.py, train.py, dataset.py, PDFormer.py。`;
}

// FIGURE 3: variable-sized panels with a large, directly labelled typed graph.
{
const s=p.slides.add();s.background.fill='#FFFFFF';title(s,'Heterogeneous representation of factory resources');
section(s,'a','Resource types',43,103,330);section(s,'b','Shared resource graph',417,103,568);section(s,'c','Model inputs',1020,103,370);
const rows=[['M','Machines / workbenches',7,180],['G','Gantries',4,265],['R','Transport robots',4,350],['H','Workers',5,465],['B','Buffers',18,550]];
for(const [id,nm,count,y] of rows){node(s,id,73,y+15,20);text(s,nm,115,y-5,276,31,21);text(s,`${count} nodes`,115,y+28,200,25,20,{color:C.grey});}
line(s,42,412,354,412,C.light,.9);
text(s,'15 prediction targets',44,633,316,31,24,{bold:true,color:C.blue});text(s,'38 nodes with contextual resources',44,675,359,29,21);
text(s,'Material availability is a feature',44,755,355,25,19,{italic:true,color:C.grey});
const N={M1:[459,369],M2:[611,369],M3:[763,369],M4:[915,369],B1:[474,272],B2:[620,271],B3:[765,271],B4:[902,273],G1:[627,189],H1:[460,177],R1:[547,531],R2:[826,531]};
// Service relations are shown as selected examples; graph.py connects each agent to machines.
for(const a of ['G1','H1','R1','R2'])for(const b of ['M1','M2','M3','M4'])line(s,...N[a],...N[b],C.light,.9);
[['M1','M2'],['M2','M3'],['M3','M4']].forEach(([a,b])=>line(s,...N[a],...N[b],C.blue,2.5));
[['B1','M1'],['B2','M2'],['B3','M3'],['B4','M4']].forEach(([a,b])=>line(s,...N[a],...N[b],C.purple,1.8));
line(s,...N.R1,...N.R2,C.rust,1.6,true);
for(const [id,xy]of Object.entries(N))node(s,id,...xy,id[0]==='M'?25:22);
text(s,'Process chain',629,405,205,28,21,{color:C.blue,italic:true,align:'center'});
text(s,'Resource–machine service',557,476,320,30,21,{bg:'#FFFFFF',color:C.grey,align:'center'});
text(s,'Buffer association',685,222,249,27,20,{color:C.purple,italic:true});
text(s,'Illustrative subgraph',537,583,369,29,22,{align:'center',italic:true});
text(s,'Weighted, undirected connectivity',454,629,480,30,24,{align:'center'});
line(s,448,700,486,700,C.blue,2.3);text(s,'process / equipment relations',498,684,428,30,20);
line(s,448,750,486,750,C.light,1.4);text(s,'service / context relations',498,734,425,30,20);

text(s,'Historical node features',1030,165,356,30,24,{bold:true});
const groups=[['Q',4,C.bluep],['S',6,C.bluep],['L',4,C.tealp],['A',1,C.ochrep],['C',7,C.purplep],['T',5,C.rustp]];
let gx=1040;for(const [t,n,c] of groups){const ww=Math.max(26,n*10.5);shape(s,'rect',gx,215,ww,42,c,'#FFFFFF',1);text(s,t,gx,217,ww,36,19,{align:'center'});gx+=ww;}
text(s,'Queue · Stall · Logistics · Availability',1028,274,379,25,18);text(s,'Context · Resource type',1028,301,360,25,18);
tensor(s,1054,354,242,115,7,12);text(s,'X: 30 × 38 × 27',1028,498,363,30,25,{align:'center',italic:true});
arrow(s,[[967,374],[1015,374]],C.grey,1.4);
text(s,'Topology',1040,562,126,29,22,{bold:true});arrow(s,[[1167,577],[1211,577]],C.grey,1.2);text(s,'Geographic mask',1225,558,182,37,20);
text(s,'hop distance < 4',1224,602,183,26,19,{color:C.grey,italic:true});
text(s,'Training histories',1018,660,177,29,21,{bold:true});arrow(s,[[1199,675],[1223,675]],C.grey,1.2);text(s,'Semantic mask',1233,657,174,37,20);
text(s,'top-5 correlation neighbours',1102,703,306,27,19,{color:C.grey,italic:true});
s.speakerNotes.text=`图3：突出多实体资源表示贡献。资源总数38：机器/工作台7、行车4、运输机器人4、工人5、缓冲区18；预测目标为机器、行车和机器人共15个，工人和缓冲区提供上下文。中部为示意子图，不是全部节点/全部边。graph.py 为加权无向图：工艺链1、同设备族0.8、缓冲区机器0.6、各服务agent（人/行车/机器人）至机器0.5、同类行车/机器人弱边0.3、自环1；图上省略权重/自环及部分边以便阅读。材料不是独立节点。特征组为Queue4、Stall6、Logistics4、Shortage1（图中A为availability/shortage）、Context7、Type5；色块和张量深浅是示意，不代表测量值。地理mask取hop<4，语义mask由训练轨迹相关性top5得到。\n${sources}\n代码：graph.py、dataset.py、backbone.py、FactoryBN_dense_bestmodel_start5.json。`;
}

await (await PresentationFile.exportPptx(p)).save(path.join(HERE,'candidate.pptx'));
for(let i=0;i<p.slides.items.length;i++){
 const s=p.slides.items[i],stem=['01_methodology','02_model_architecture','03_heterogeneous_resources'][i];
 const png=await p.export({slide:s,format:'png',scale:1.5});
 await fs.writeFile(path.join(OUT,`${stem}.png`),new Uint8Array(await png.arrayBuffer()));
 const layout=await s.export({format:'layout'});await fs.writeFile(path.join(HERE,`${stem}.layout.json`),await layout.text());
 console.log(`Rendered ${stem}`);
}
// Export the vector PDF from the final PPTX with LibreOffice after finalization.
console.log('Candidate:',path.join(HERE,'candidate.pptx'));
