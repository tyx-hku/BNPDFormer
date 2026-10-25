import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const runtime=process.env.RUNTIME_NODE_MODULES;
const req=createRequire(runtime?path.join(runtime,'package.json'):import.meta.url);
const {Presentation,PresentationFile}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')).href);
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const BUILD=path.join(ROOT,'build/phast_model_v4');
const OUT=path.join(ROOT,'figures/drafts/phast_model_v4');
await fs.mkdir(BUILD,{recursive:true});await fs.mkdir(OUT,{recursive:true});
const W=1800,H=1320;
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

// V4: three contribution regions surround one compact bottom-up predictor.
const A='#3F6D8A',B='#986844',D='#467760',muted='#7B8188',neutral='#F5F5F3';
function section(t,x,y,w,color){tx(t,x,y,w,62,26,{bold:true,color,align:'left'});ln(x,y+67,x+w,y+67,color,2.2);}
function thinmod(t,x,y,w,h=36,size=20,fill=neutral,color=muted){mod(t,x,y,w,h,fill,size,color);}
function pulse(x,y,w,h,start,end,color){ln(x,y+h,x+w,y+h,'#CED5D9',.8);const pts=[[x,y+h],[x+w*start,y+h],[x+w*start,y],[x+w*end,y],[x+w*end,y+h],[x+w,y+h]];for(let i=1;i<pts.length;i++)ln(...pts[i-1],...pts[i],color,1.9);}

// Complete model: standard operators have deliberately low contrast.
tx('PHAST-DP',695,9,410,42,32,{bold:true});
tx('Resource, onset, duration, state, cause and remaining time',584,52,634,31,21);
thinmod('Event decoding and report assembly',709,103,382,46,23);
route([[900,103],[900,86]]);
const hx=[707,917,1120];ln(707,177,1120,177);route([[900,177],[900,149]]);
hx.forEach(x=>route([[x,223],[x,177]]));
thinmod('Event heads',620,223,174,57,22);
thinmod('State and remaining\ntime decoders',817,223,200,57,20);
thinmod('Cause\nclassifier',1043,223,155,57,20);
thinmod('Regime + precursor\nfusion (b)',620,296,174,44,18,C.rose,B);
thinmod('Skip + order-progress\nfusion',817,296,200,44,18);
thinmod('Graph pooling\n+ node evidence',1043,296,155,44,18);
hx.forEach(x=>route([[x,296],[x,280]]));
ln(707,362,1120,362);hx.forEach(x=>route([[x,362],[x,340]]));
route([[900,401],[900,362]]);tx('H(t)',949,368,84,26,21,{italic:true});

// Five pre-normalized attention / feed-forward blocks.
box(615,397,590,516,'none','#8C939A',1.2,'Spatiotemporal encoder',true);
tx('Encoder block × 5',631,368,239,29,23,{bold:true});
op('+',900,414);route([[900,454],[900,427]]);
thinmod('Feed-forward network',787,454,226,37,20);
route([[900,516],[900,491]]);thinmod('LayerNorm',811,516,178,32,19);
route([[900,568],[900,548]]);op('+',900,581);
route([[900,621],[900,594]]);thinmod('Concat + Linear',796,621,208,39,21);
route([[900,680],[900,660]]);ln(719,680,1081,680);
const bx=[632,813,994];
const titles=['Temporal attention','Geographic attention','Semantic attention'];
for(let i=0;i<3;i++){
 box(bx[i],713,174,125,i===1?'#F2F7F3':'#FFFFFF',i===1?D:'#B0B5BA',i===1?1.8:.9);
 tx(titles[i],bx[i]+3,719,168,24,17,{bold:true,color:i===1?D:C.text});
 route([[bx[i]+87,713],[bx[i]+87,680]],C.ink,1.3);
 route([[bx[i]+87,853],[bx[i]+87,838]],C.ink,1.3);
}
for(const [x,rise]of[[656,26],[695,18],[734,10]])curve(x,790,777,790,rise,'#8F9FA9',1);
for(const x of[656,695,734,777])nd(x,790,5.5,x===777?'#708897':'#FFFFFF','#708897');
tx('4 heads',651,811,137,21,17);
neighbourhood(900,780,.66,D);tx('2 heads, Mᴳ (a)',825,811,151,21,17,{color:D});
matrix(1008,761,5,5,10,blues,'similarity');
for(const [x,y]of[[1090,769],[1143,770],[1128,801]])ln(1114,785,x,y,'#A2AFB8',1);
for(const [x,y]of[[1090,769],[1143,770],[1128,801]])nd(x,y,5,'#FFFFFF','#8A9DA9');
nd(1114,785,6.5,'#6D8CA2','#6D8CA2');tx('2 heads, Mˢ',1009,811,145,21,17);
ln(719,853,1081,853);route([[900,869],[900,853]]);thinmod('LayerNorm',811,869,178,32,19);
route([[900,931],[900,901]]);
route([[900,905],[1190,905],[1190,581],[913,581]],'#7C858D',1.2);
route([[900,558],[628,558],[628,414],[887,414]],'#7C858D',1.2);
tx('residual',1044,882,115,22,16,{italic:true,color:muted});
tx('residual',646,530,115,22,16,{italic:true,color:muted});
// Only one correspondence leader to the expanded attention mechanism.
route([[987,754],[1232,754],[1232,618],[1250,618]],D,1.3,true,false);

// (b) Process supervision, rule-based regime conditioning, and prototype fitting.
section('(b) Process-informed supervision\nand pattern clustering',35,162,525,B);
tx('Operational evidence',73,250,415,28,22,{bold:true,color:B});
const ey=305;
patchTrace(78,ey,98,36,[.1,.5,.85,.9,.85],B);
patchTrace(248,ey,98,36,[.15,.15,.8,.8,.7],B);
patchTrace(416,ey,98,36,[.1,.2,.1,.75,.95],B);
tx('Queue',74,282,105,22,18);tx('Stall / shortage',218,282,163,22,18);tx('Logistics delay',392,282,145,22,18);
route([[295,351],[295,371]],B,1.5);
tx('Resource-specific rules + persistence',51,377,494,29,22,{color:B});
const raw=Array(28).fill(0);for(let i=2;i<=3;i++)raw[i]=1;for(let i=7;i<=14;i++)raw[i]=1;for(let i=16;i<=23;i++)raw[i]=1;
const retained=Array(28).fill(0);for(let i=7;i<=23;i++)retained[i]=1;
for(let i=0;i<28;i++){box(171+i*12,422,11,16,raw[i]?'#D5B497':'#F6F0EA','#FFFFFF',.5);box(171+i*12,452,11,16,retained[i]?B:'#F6F0EA','#FFFFFF',.5);}
tx('Raw',70,418,79,24,18,{align:'right'});tx('Sustained',49,448,100,24,18,{align:'right'});
tx('Remove short runs, then fill gaps',129,478,385,25,18,{italic:true,color:B});
route([[301,469],[301,474],[157,474],[157,519],[181,519],[181,527]],B,1.25);
vector(120,528,9,13,oranges);tx('Event / state targets',49,548,264,24,20);
// Process-cause evidence follows its own rules and bypasses occupancy filtering.
route([[528,328],[550,328],[550,534],[497,534]],B,1.1);
vector(419,528,6,13,oranges);tx('Cause targets',359,548,180,24,20);
// Dashed arrows denote training supervision of the corresponding prediction heads.
route([[510,573],[579,573],[579,201],[1120,201],[1120,223]],B,1.25,true);
route([[707,201],[707,223]],B,1.25,true);
route([[917,201],[917,223]],B,1.25,true);
ln(70,573,541,573,B,1.15,true);
route([[120,535],[70,535],[70,573]],B,1.15,true,false);
route([[497,535],[541,535],[541,573]],B,1.15,true,false);
tx('training supervision',263,582,263,23,18,{italic:true,color:B});

tx('History-derived conditioning',45,625,481,29,22,{bold:true,color:B});
for(let i=0;i<6;i++)nd(90+i*22,687,6.2,i===3?B:'#FFFFFF',B);
tx('Rule-based regime IDs',45,656,221,24,18);
route([[227,687],[311,687]],B,1.25);vector(314,680,8,13,oranges);
tx('Regime embedding',295,649,205,27,19);
route([[418,687],[589,687],[589,318],[620,318]],B,1.45);
tx('Local + neighbour cues',54,731,232,25,19);thinmod('Precursor MLP',320,723,173,34,19,C.rose,B);
route([[280,742],[320,742]],B,1.25);route([[493,740],[548,740],[548,687]],B,1.25);

tx('Short-pattern clustering',45,796,474,29,22,{bold:true,color:B});
tx('Training activity\npatches (length 3)',45,835,182,45,18);
const pat=[[.15,.8,.4],[.8,.45,.1],[.1,.2,.9]];
pat.forEach((v,i)=>patchTrace(75,887+i*26,120,19,v,B));
route([[210,916],[248,916]],B,1.3);
// Schematic clusters without quantitative axes.
const cc=[[273,889],[329,910],[288,949]],sh=['#E6CFBB','#BB8961','#8B5C39'];
cc.forEach(([x,y],i)=>{for(const[dx,dy]of[[-9,-5],[8,-10],[12,7],[-7,12],[0,0]])nd(x+dx,y+dy,3.1,sh[i],sh[i]);nd(x,y,5,'#FFFFFF',B);});
tx('k-means',249,847,116,27,21,{italic:true,color:B});
route([[354,916],[400,916]],B,1.3);
pat.forEach((v,i)=>patchTrace(421,887+i*26,93,19,v,B));
tx('…',522,919,28,24,20,{color:B});
tx('16 prototypes P',392,967,159,25,20,{color:B});

// (a) Heterogeneous input is visibly a typed resource graph.
section('(a) Heterogeneous resource representation',35,1006,1170,A);
// Native shapes encode entity types, while all relations use the same blue family.
const nodes={M1:[140,1171],M2:[296,1171],M3:[461,1171],B1:[218,1117],B2:[378,1231],H:[72,1122],G:[470,1127],R:[105,1240]};
function edge(a,b,dash=false,sw=1.2){ln(...nodes[a],...nodes[b],dash?'#91AABD':A,sw,dash);}
edge('M1','M2',false,2.1);edge('M2','M3',false,2.1);edge('B1','M1');edge('B1','M2');edge('B2','M2');edge('B2','M3');edge('H','M1',true);edge('H','M2',true);edge('G','M2',true);edge('G','M3',true);edge('R','M1',true);edge('R','M2',true);
for(const k of['M1','M2','M3']){const[x,y]=nodes[k];box(x-22,y-17,44,34,'#C3D6E3',A,1.5,k);tx(k,x-22,y-15,44,29,18,{bold:true,color:A});}
for(const k of['B1','B2']){const[x,y]=nodes[k];box(x-21,y-13,42,26,'#E3EDF3',A,1.2,k);tx(k,x-21,y-12,42,23,17,{color:A});}
nd(...nodes.H,15,'#FFFFFF',A,'H');
for(const k of['G','R']){const[x,y]=nodes[k];s.shapes.add({geometry:'diamond',name:k==='G'?'Gantry':'Transport robot',position:{left:x-20,top:y-20,width:40,height:40},fill:k==='G'?'#86A8BE':'#D5E3EC',line:{fill:A,width:1.3}});tx(k,x-17,y-14,34,28,18,{color:k==='G'?'#FFFFFF':A});}
tx('Worker',40,1081,76,23,17);tx('Gantry',434,1081,85,23,17);tx('Robot',52,1261,100,23,17);tx('Buffers',318,1257,124,23,17);
tx('M: machines / workbenches; 38 nodes in 5 types',48,1284,590,25,18,{color:A});
// Adjacency and temporal history remain separate inputs to representation.
route([[500,1171],[551,1171]],A,1.5);matrix(557,1139,6,6,11,blues,'mask');
tx('Graph G',541,1212,96,25,20,{italic:true,color:A});
tx('Mᴳ, E_lap',537,1243,112,24,19,{color:A});
tx('Node-aligned\nhistory',665,1153,140,46,19,{color:A});
for(let i=2;i>0;i--)box(810+i*9,1153-i*7,180,54,'#EAF1F8','#B5C3CF',.7,'History tensor layer');
matrix(810,1153,5,18,10,blues);tx('X (30 × 38 × 27)',760,1233,286,32,23,{color:A});
route([[900,1153],[900,1011]],A,1.6);
thinmod('Grouped Linear + GELU\nMean aggregation',725,960,350,51,21,'#EAF1F8',A);
for(let i=0;i<6;i++)box(976+i*29,1126,23,17,blues[(i+1)%5],'#FFFFFF',.6);
tx('6 feature groups',990,1159,179,26,19,{color:A});
route([[1067,1126],[1127,1126],[1127,986],[1075,986]],A,1.25);
op('+',900,937);route([[900,960],[900,950]]);
tx('Time + Laplacian\n+ node embeddings (a)',1033,913,185,38,17,{color:A});route([[1028,937],[913,937]],A,1.3);

// (c) Delayed association plus the actual pattern-conditioned key mechanism.
section('(c) Delay-aware\ncross-resource attention',1261,360,502,D);
tx('Earlier precursor at i',1266,447,178,44,19,{color:D,align:'left'});
tx('Later constraint at j',1266,519,178,43,19,{color:D,align:'left'});
pulse(1452,459,287,31,.12,.40,D);pulse(1452,531,287,31,.52,.83,D);
ln(1486,451,1486,584,'#A3BBAE',1,true);ln(1601,522,1601,584,'#A3BBAE',1,true);
route([[1486,580],[1601,580]],D,1.3);tx('lag',1514,583,74,22,17,{italic:true,color:D});
route([[1452,617],[1740,617]],'#8C9690',1.05);tx('time',1643,623,94,22,17,{italic:true,color:D});
tx('Illustrative cross-resource association',1275,651,472,26,19,{italic:true,color:D});
// Online queue query versus activity prototypes fitted offline in (b).
tx('Queue query patch',1264,698,189,26,20);tx('Prototype bank P (b)',1500,698,236,26,20,{color:D});
patchTrace(1282,736,129,38,[.12,.7,.9],A);
pat.forEach((v,i)=>patchTrace(1516+i*70,743,48,24,v,D));
matrix(1301,810,4,6,9,blues);matrix(1502,810,4,6,9,greens);matrix(1654,810,4,6,9,greens);
tx('Qᴾ',1255,815,40,26,21,{italic:true});tx('Kᴾ',1454,815,40,26,21,{italic:true});tx('Vᴾ',1733,815,40,26,21,{italic:true});
route([[1347,775],[1347,794],[1328,794],[1328,810]]);
route([[1610,772],[1610,796],[1529,796],[1529,810]]);route([[1610,796],[1681,796],[1681,810]]);
thinmod('softmax(Qᴾ Kᴾᵀ / √d)',1313,877,281,43,23,'#EAF2EB',D);
route([[1328,846],[1278,846],[1278,898],[1313,898]],D,1.4);route([[1529,846],[1529,877]],D,1.4);
route([[1454,920],[1454,945]],D,1.4);vector(1329,945,16,13,greens);
tx('Pattern weights',1316,967,237,24,19,{italic:true,color:D});
op('×',1611,952);route([[1537,952],[1598,952]],D,1.5);route([[1681,846],[1681,952],[1624,952]],D,1.4);
route([[1611,965],[1611,997],[1511,997],[1511,1049]],D,1.8);tx('Cᴾ',1645,980,65,29,22,{italic:true,color:D});
tx('Qᴳ',1296,1017,74,27,22,{italic:true});tx('Kᴳ',1404,1017,74,27,22,{italic:true});tx('K̃ᴳ',1549,1017,74,27,22,{italic:true,color:D});tx('Vᴳ',1670,1017,74,27,22,{italic:true});
matrix(1306,1056,4,6,10,blues);matrix(1420,1056,4,6,10,blues);matrix(1555,1056,4,6,10,greens);matrix(1672,1056,4,6,10,blues);
op('+',1511,1076);route([[1511,1049],[1511,1063]],D,1.8);route([[1480,1076],[1498,1076]],D,1.5);route([[1524,1076],[1555,1076]],D,1.8);
thinmod('softmax(Qᴳ K̃ᴳᵀ / √d + Mᴳ) Vᴳ',1289,1150,447,48,23,'#EAF2EB',D);
route([[1336,1096],[1336,1150]],D,1.4);route([[1585,1096],[1585,1150]],D,1.4);route([[1702,1096],[1702,1150]],D,1.4);
route([[1512,1198],[1512,1222]],D,1.4);vector(1454,1222,10,12,greens);
tx('Geographic attention output',1282,1250,459,31,23,{color:D});

s.speakerNotes.text=`PHAST-DP model architecture, revision 4. The three lettered, colored regions correspond to the manuscript contributions: (a) heterogeneous multi-entity representation, (b) process-informed supervision and pattern clustering, and (c) delay-aware cross-resource interaction. Standard model operators remain in the central bottom-up path. Dashed brown arrows indicate training supervision. The dashed green leader links geographic attention to its expanded calculation. The label P (b) identifies the same prototype bank across panels.\nScientific sources: paper main.tex dev_xwt at ffcfbb7, especially Introduction contributions and Methodology; isaac_factory origin/dev_tyx 29655baee57b9095119589a211ae1e2113b84078, factory_bn/graph.py, dataset.py, cause_cluster.py, model.py, backbone.py. Graph edges in the implementation form a symmetric weighted adjacency. Material availability is a resource feature, not a sixth graph-node type. There are 38 resource nodes and 27 channels; grouped embedding uses six feature groups.\nImportant implementation distinction: the event-head regime IDs come from deterministic process rules (seed_cluster_ids), not the offline K=8 k-means descriptors. The active k-means path fits 16 prototypes from length-three training activity patches. Online queries use queue patches. Pattern context is added only to geographic K. The figure therefore shows rule-based regime conditioning separately from prototype clustering. Offline exploratory K=8 descriptors with disabled prediction loss are omitted.\nAll networks, matrices, cluster points, event strips and traces are mechanism schematics, not experiment measurements or actual learned weights. The lag sketch illustrates the prediction problem; the model does not explicitly estimate a physical propagation delay or certify a causal edge. Five encoder blocks use 4 temporal, 2 geographic and 2 semantic heads. Input dimension is 30 by 38 by 27. The figure omits dropout and training-loss algebra. The five event heads are compressed into Event heads, with precursor/regime fusion retained separately. All diagram elements are editable native objects, with Times New Roman requested by the user.`;
await (await PresentationFile.exportPptx(p)).save(path.join(BUILD,'candidate.pptx'));
const png=await p.export({slide:s,format:'png',scale:1.25});await fs.writeFile(path.join(OUT,'PHAST_DP_model_v4.png'),new Uint8Array(await png.arrayBuffer()));
const layout=await s.export({format:'layout'});await fs.writeFile(path.join(BUILD,'layout.json'),await layout.text());
console.log('Created contribution-focused revision:',OUT);
