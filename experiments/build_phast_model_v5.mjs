import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
const runtime=process.env.RUNTIME_NODE_MODULES;
const req=createRequire(runtime?path.join(runtime,'package.json'):import.meta.url);
const {Presentation,PresentationFile}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')).href);
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const BUILD=path.join(ROOT,'build/phast_model_v5');
const OUT=path.join(ROOT,'figures/drafts/phast_model_v5');
await fs.mkdir(BUILD,{recursive:true});await fs.mkdir(OUT,{recursive:true});
const W=2000,H=1380;
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

// V5 follows the user's modular sketch: input above a downward model,
// supervision on the left, attention detail and report on the right.
const A='#3F6D8A',B='#986844',D='#467760',muted='#7B8188',neutral='#F6F6F4';
const greyCells=['#F4F5F5','#E4E8EA','#CCD4DA','#AAB8C1','#7B909E'];
const enhanced=['#EAF4EB','#C3DCC8','#90BB9A','#599368','#2C643B'];
function panel(t,x,y,w,h,color,lines=1){box(x,y,w,h,'#FFFFFF',color,1.35,t);tx(t,x+20,y+12,w-40,lines===1?37:66,27,{bold:true,color,align:'left'});ln(x+20,y+(lines===1?58:85),x+w-20,y+(lines===1?58:85),color,.8);}
function thinmod(t,x,y,w,h=36,size=20,fill=neutral,color=muted){mod(t,x,y,w,h,fill,size,color);}
function pulse(x,y,w,h,start,end,color){ln(x,y+h,x+w,y+h,'#D2DAD5',.7);const pts=[[x,y+h],[x+w*start,y+h],[x+w*start,y],[x+w*end,y],[x+w*end,y+h],[x+w,y+h]];for(let i=1;i<pts.length;i++)ln(...pts[i-1],...pts[i],color,1.8);}
function valuesMatrix(x,y,rows,cols,cell,palette,offset=0){for(let r=0;r<rows;r++)for(let c=0;c<cols;c++){const k=(r*3+c*2+r*c+offset*(r%3+1))%palette.length;box(x+c*cell,y+r*cell,cell,cell,palette[k],'#FFFFFF',.65);}box(x,y,cols*cell,rows*cell,'none',offset?D:C.line,offset?1.7:.7);}
function diamond(t,x,y,size,fill,stroke){s.shapes.add({geometry:'diamond',name:t,position:{left:x-size/2,top:y-size/2,width:size,height:size},fill,line:{fill:stroke,width:1.3}});tx(t,x-size/2,y-14,size,28,17,{color:fill===A?'#FFFFFF':A});}

// Module frames are placed first so all native shapes stay visible.
tx('PHAST-DP',678,15,645,44,33,{bold:true});
panel('(a) Heterogeneous resource representation',35,85,1240,250,A);
panel('(b) Process-informed supervision\nand pattern clustering',35,365,540,975,B,2);
panel('Prediction network',610,365,665,975,'#606C77');
panel('(c) Delay-conditioned interaction',1320,85,645,800,D);
panel('Structured bottleneck report',1320,925,645,415,A);

// (a) Typed factory graph, history and grouped embedding.
const nodes={M1:[117,240],M2:[264,240],M3:[408,240],B1:[183,186],B2:[335,294],H:[78,183],G:[444,184],R:[80,293]};
function edge(a,b,dash=false,sw=1.2){ln(...nodes[a],...nodes[b],dash?'#91AABD':A,sw,dash);}
edge('M1','M2',false,2);edge('M2','M3',false,2);edge('B1','M1');edge('B1','M2');edge('B2','M2');edge('B2','M3');edge('H','M1',true);edge('H','M2',true);edge('G','M2',true);edge('G','M3',true);edge('R','M1',true);edge('R','M2',true);
for(const k of['M1','M2','M3']){const[x,y]=nodes[k];box(x-21,y-16,42,32,'#C3D6E3',A,1.3,k);tx(k,x-21,y-14,42,28,17,{bold:true,color:A});}
for(const k of['B1','B2']){const[x,y]=nodes[k];box(x-18,y-12,36,24,'#E3EDF3',A,1.1,k);tx(k,x-18,y-11,36,22,16,{color:A});}
nd(...nodes.H,14,'#FFFFFF',A,'H');diamond('G',...nodes.G,35,'#A5BECE',A);diamond('R',...nodes.R,35,'#D5E3EC',A);
tx('M: machine/workbench  H: worker  G: gantry  R: robot  B: buffer',57,306,457,21,15,{color:A});
route([[468,241],[517,241]],A,1.5);matrix(527,213,5,5,11,blues,'mask');tx('Graph G',513,273,104,23,19,{italic:true,color:A});tx('Mᴳ, E_lap',512,299,108,22,16,{color:A});
ln(627,166,627,309,'#D0DCE3',.8);
for(let i=2;i>0;i--)box(671+i*8,203-i*6,144,50,'#EDF3F7','#B4C7D4',.7);
matrix(671,203,5,16,9,blues);tx('Node-aligned history',646,164,239,27,20,{color:A});tx('X: 30 × 38 × 27',652,264,224,27,21,{color:A});
route([[839,228],[956,228]],A,1.6);
tx('6 groups',841,183,118,27,18,{color:A});
for(let i=0;i<6;i++)box(850+i*17,208,14,14,blues[(i+1)%5],'#FFFFFF',.5);
thinmod('Grouped Linear + GELU\nMean aggregation',963,193,282,54,21,'#EAF1F8',A);
route([[1104,247],[1104,267]],A,1.5);op('+',1104,280);
tx('Time + Laplacian\n+ node embeddings',817,264,239,44,18,{color:A});route([[1054,280],[1091,280]],A,1.2);
route([[1104,293],[1104,321],[940,321],[940,486]],A,1.6);
tx('H⁽⁰⁾',961,393,70,27,21,{italic:true,color:A});

// Central model flows downward and remains computationally complete.
box(634,441,616,565,'none','#9FA7AE',1.1,'Five encoder blocks',true);
tx('Encoder block × 5',653,450,217,28,22,{bold:true});
thinmod('LayerNorm',853,486,174,34,20);
route([[940,520],[940,550]],C.ink,1.4);ln(744,550,1140,550);
const bx=[657,855,1053],cx=[744,942,1140];
for(let i=0;i<3;i++){
 route([[cx[i],550],[cx[i],572]],C.ink,1.4);
 box(bx[i],572,174,132,i===1?'#EEF6F0':'#FFFFFF',i===1?D:'#ABB4BC',i===1?1.7:1.0);
 tx(['Temporal','Geographic (c)','Semantic'][i],bx[i]+5,581,164,24,18,{bold:true,color:i===1?D:C.text});
 tx('attention',bx[i]+5,603,164,24,18,{color:i===1?D:C.text});
 route([[cx[i],704],[cx[i],721]],C.ink,1.4);
}
for(const[x,r]of[[676,25],[715,17],[754,10]])curve(x,662,795,662,r,'#8FA4B1',1);
for(const x of[676,715,754,795])nd(x,662,5.5,x===795?A:'#FFFFFF',A);
neighbourhood(942,656,.65,D);matrix(1077,636,5,5,9,blues,'similarity');
for(const[x,y]of[[1163,640],[1203,641],[1190,671]])ln(1176,655,x,y,'#A9B9C4',1);
for(const[x,y]of[[1163,640],[1203,641],[1190,671]])nd(x,y,4.7,'#FFFFFF',A);nd(1176,655,6,A,A);
tx('4 heads',669,677,150,23,17);tx('2 heads, Mᴳ',867,677,150,23,17,{color:D});tx('2 heads, Mˢ',1065,677,150,23,17);
ln(744,721,1140,721);route([[940,721],[940,738]]);
thinmod('Concat + Linear',831,738,218,38,21);
route([[940,776],[940,784]]);op('+',940,797);
route([[940,810],[940,836]]);thinmod('LayerNorm',853,836,174,34,20);
route([[940,870],[940,900]]);thinmod('Feed-forward network',826,900,228,40,20);
route([[940,940],[940,963]]);op('+',940,976);route([[940,989],[940,1026]]);
route([[940,473],[1236,473],[1236,797],[953,797]],'#7C858D',1.2);
route([[940,821],[646,821],[646,976],[927,976]],'#7C858D',1.2);
tx('residual',1084,772,110,22,16,{italic:true,color:muted});tx('residual',667,947,110,22,16,{italic:true,color:muted});
// Dashed correspondence connects the geographic branch to panel (c).
route([[1029,626],[1295,626],[1295,658],[1320,658]],D,1.3,true,false);

// Three prediction branches, followed by training loss or report decoding.
tx('H(t)',960,1006,69,24,20,{italic:true});ln(732,1026,1157,1026);
const heads=[{x:640,w:185,c:732,t:'Regime + precursor\nfusion (b)',h:'Event heads\nw, s, d, prefix',f:C.rose,st:B},{x:845,w:193,c:941,t:'Skip + order-progress\nfusion',h:'State / remaining\ntime decoders',f:neutral,st:muted},{x:1067,w:180,c:1157,t:'Graph pooling\n+ node evidence',h:'Process-cause\nclassifier',f:neutral,st:muted}];
for(const h of heads){route([[h.c,1026],[h.c,1051]]);thinmod(h.t,h.x,1051,h.w,45,18,h.f,h.st);route([[h.c,1096],[h.c,1120]]);thinmod(h.h,h.x,1120,h.w,53,19);route([[h.c,1173],[h.c,1197]]);}
ln(732,1197,1157,1197);
thinmod('Training loss',645,1233,145,39,19,'#FCF8F4',B);route([[732,1197],[718,1197],[718,1233]],B,1.3,true);
thinmod('Event decoding\nand report assembly',874,1222,344,57,22,'#EAF1F8',A);route([[1046,1197],[1046,1222]],A,1.6);
route([[1218,1250],[1297,1250],[1297,1129],[1320,1129]],A,2);

// (b) Labels and conditional inputs remain separate from the forward targets.
tx('Operational evidence',55,481,498,29,22,{bold:true,color:B});
patchTrace(79,545,102,34,[.1,.4,.85,.9,.85],B);patchTrace(248,545,102,34,[.1,.1,.75,.75,.7],B);patchTrace(417,545,102,34,[.1,.2,.15,.7,.9],B);
tx('Queue',73,516,110,24,18);tx('Stall / shortage',217,516,165,24,18);tx('Logistics',409,516,119,24,18);
route([[299,590],[299,609]],B,1.3);tx('Resource-specific rules + persistence',53,615,502,29,21,{color:B});
const raw=Array(28).fill(0),ret=Array(28).fill(0);for(let i=2;i<=3;i++)raw[i]=1;for(let i=7;i<=14;i++)raw[i]=1;for(let i=16;i<=23;i++)raw[i]=1;for(let i=7;i<=23;i++)ret[i]=1;
for(let i=0;i<28;i++){box(175+i*12,668,11,17,raw[i]?'#D4B496':'#F7F0EA','#FFFFFF',.4);box(175+i*12,704,11,17,ret[i]?B:'#F7F0EA','#FFFFFF',.4);}
tx('Raw',72,665,80,24,18,{align:'right'});tx('Sustained',48,701,104,24,18,{align:'right'});
tx('Remove short runs, then fill gaps',127,735,391,25,18,{italic:true,color:B});
route([[294,721],[294,728],[159,728],[159,773]],B,1.2);
vector(113,775,9,13,oranges);tx('Event / state targets',56,804,253,27,20);
route([[535,561],[550,561],[550,781],[506,781]],B,1.1);vector(428,775,6,13,oranges);tx('Cause targets',366,804,174,27,20);
route([[113,782],[79,782],[79,844],[535,844]],B,1.15,true,false);route([[506,782],[535,782],[535,844]],B,1.15,true,false);
route([[535,844],[589,844],[589,1252],[645,1252]],B,1.3,true);
tx('training supervision',263,851,268,25,18,{italic:true,color:B});
ln(56,894,552,894,'#DCCABB',.8);
tx('History-derived conditioning',54,910,501,29,22,{bold:true,color:B});
tx('Rule-based regime IDs',55,950,222,24,18);for(let i=0;i<6;i++)nd(92+i*22,990,6,i===3?B:'#FFFFFF',B);
route([[230,990],[323,990]],B,1.3);vector(326,983,8,13,oranges);tx('Regime embedding',303,950,218,25,19);
route([[430,990],[601,990],[601,1073],[640,1073]],B,1.4);
tx('Local + neighbour cues',54,1034,235,26,18);thinmod('Precursor MLP',334,1028,175,36,19,C.rose,B);route([[289,1046],[334,1046]],B,1.2);route([[509,1046],[531,1046],[531,990]],B,1.2);
ln(56,1093,552,1093,'#DCCABB',.8);
tx('Short-pattern clustering',54,1107,501,29,22,{bold:true,color:B});
tx('Activity patches\n(length 3)',60,1154,159,44,18);const pat=[[.1,.8,.4],[.8,.45,.1],[.1,.2,.9]];pat.forEach((v,i)=>patchTrace(80,1211+i*27,117,18,v,B));
route([[210,1250],[252,1250]],B,1.2);const cc=[[278,1224],[329,1245],[287,1282]],sh=['#D8B89B','#B2815A','#8B5C39'];
cc.forEach(([x,y],i)=>{for(const[dx,dy]of[[-9,-5],[8,-10],[12,7],[-7,12],[0,0]])nd(x+dx,y+dy,3,sh[i],sh[i]);nd(x,y,4.7,'#FFFFFF',B);});
tx('k-means',250,1168,112,28,21,{italic:true,color:B});route([[356,1250],[400,1250]],B,1.2);pat.forEach((v,i)=>patchTrace(421,1211+i*27,93,18,v,B));tx('…',523,1242,25,23,20,{color:B});tx('16 prototypes P',399,1298,153,27,19,{color:B});

// (c) Distinct matrix roles and an explicit before/context/after transformation.
// A small lag sketch establishes the prediction problem, without estimating tau.
tx('Earlier precursor',1347,158,165,24,18,{color:D});tx('Later constraint',1347,208,165,24,18,{color:D});
pulse(1535,157,367,25,.14,.38,D);pulse(1535,207,367,25,.56,.83,D);
ln(1586,152,1586,251,'#ABC2B3',.8,true);ln(1741,202,1741,251,'#ABC2B3',.8,true);route([[1586,247],[1741,247]],D,1.1);tx('lag',1640,251,64,21,16,{italic:true,color:D});
tx('Pattern matching',1345,279,281,28,22,{bold:true,color:D});
tx('Queue query patch',1352,314,172,24,18);tx('Activity prototypes P (b)',1640,314,279,24,18,{color:B});
patchTrace(1389,347,109,31,[.1,.7,.9],A);pat.forEach((v,i)=>patchTrace(1670+i*76,349,47,27,v,B));
// Patterns use warm projected matrices, visually distinct from geographic states.
valuesMatrix(1396,401,6,4,9,oranges);valuesMatrix(1658,410,4,4,9,oranges);valuesMatrix(1830,410,4,4,9,oranges);
tx('Qᴾ',1349,415,41,25,21,{italic:true,color:B});tx('Kᴾ',1609,415,43,25,21,{italic:true,color:B});tx('Vᴾ',1874,415,43,25,21,{italic:true,color:B});
tx('38 × 20',1370,461,91,23,17,{color:B});tx('16 × 20',1628,461,100,23,17,{color:B});tx('16 × 20',1800,461,100,23,17,{color:B});
route([[1444,379],[1444,388],[1414,388],[1414,401]],B,1.2);route([[1770,379],[1770,391],[1676,391],[1676,410]],B,1.2);route([[1770,391],[1848,391],[1848,410]],B,1.2);
thinmod('αᴾ = softmax(Qᴾ Kᴾᵀ / √dₕ)',1433,498,340,38,22,'#F6F0E9',B);
route([[1414,455],[1338,455],[1338,517],[1433,517]],B,1.15);route([[1676,484],[1676,498]],B,1.15);
route([[1554,536],[1554,549],[1486,549],[1486,560]],B,1.2);
valuesMatrix(1430,560,6,16,7,oranges);tx('Pattern weights 38 × 16',1370,608,243,22,17,{color:B});
op('×',1591,581);route([[1542,581],[1578,581]],B,1.25);route([[1848,484],[1848,550],[1591,550],[1591,568]],B,1.2);
valuesMatrix(1643,560,6,4,7,greens);route([[1604,581],[1643,581]],D,1.5);tx('Pattern context Cᴾ\n38 × 20',1690,562,228,43,19,{color:D});
// Geographic state matrices have the same N x dh dimensions. The updated key
// has visibly changed cells and a stronger green outline, not a recolored copy.
ln(1345,643,1940,643,'#C5D7CB',.8);tx('Geographic key update',1345,651,266,27,22,{bold:true,color:D});
valuesMatrix(1396,703,6,4,10,greyCells);tx('+',1489,715,43,36,30,{color:D});valuesMatrix(1575,703,6,4,10,greens);
route([[1660,602],[1660,683],[1595,683],[1595,703]],D,1.7);
route([[1615,733],[1806,733]],D,2);valuesMatrix(1807,703,6,4,10,enhanced,1);
tx('Base key Kᴳ',1349,772,151,24,19,{color:'#657C8C'});tx('Context Cᴾ',1534,772,125,24,19,{color:D});tx('Updated key K̃ᴳ',1730,772,201,24,20,{bold:true,color:D});
tx('K̃ᴳ = Kᴳ + Cᴾ',1653,687,142,28,19,{italic:true,color:D});
thinmod('softmax(Qᴳ K̃ᴳᵀ / √dₕ + Mᴳ) Vᴳ',1382,826,548,37,23,'#EAF2EB',D);
route([[1827,797],[1827,826]],D,1.5);tx('Qᴳ, Vᴳ',1328,814,69,24,17,{color:'#657C8C'});route([[1364,838],[1382,838]],'#758A99',1.2);

// Output report: a native, editable schematic with symbolic values.
tx('schematic',1813,951,129,24,18,{italic:true,color:muted});
tx('Resource i*',1346,1010,134,30,23,{bold:true,color:A});
// Forecast time axis and the occupancy sequence jointly encode onset/duration.
route([[1491,1028],[1922,1028]],A,1.2);
for(const x of[1491,1591,1791])ln(x,1022,x,1034,A,1.1);
tx('t',1476,997,31,24,19,{italic:true,color:A});tx('t + ŝ',1558,997,70,24,19,{italic:true,color:A});tx('t + ŝ + d̂',1745,997,104,24,19,{italic:true,color:A});
tx('State',1348,1059,121,27,20,{color:A});
for(let i=0;i<21;i++)box(1491+i*20,1058,19,27,(i>=5&&i<15)?D:'#E9EEF1','#FFFFFF',.7,'Predicted occupancy cell');
ln(1591,1036,1591,1114,D,1,true);ln(1791,1036,1791,1114,D,1,true);
ln(1591,1111,1791,1111,D,1.5);ln(1591,1105,1591,1117,D,1.5);ln(1791,1105,1791,1117,D,1.5);
tx('Occurrence ŵ',1346,1117,165,28,20,{color:A});tx('Duration d̂',1593,1117,198,29,22,{color:D});
tx('Onset ŝ',1549,1090,86,24,18,{color:D});
ln(1345,1170,1940,1170,'#CCD9E1',.8);
tx('Process cause ĉ',1346,1193,209,29,22,{color:A});
for(let i=0;i<4;i++)box(1667+i*41,1198,33,20,i===1?'#A67B58':'#EFE4D9','#FFFFFF',.7,'Process class indicator');
tx('process-evidence class',1608,1224,310,24,18,{italic:true,color:B});
tx('Order remaining time ℓ̂',1346,1265,287,30,22,{color:A});box(1656,1273,265,13,'#E8EFF3','#AEC2CF',.6);box(1656,1273,178,13,'#84A8BE','none',0);
tx('Minute-level prediction for the selected resource',1344,1307,590,24,18,{italic:true,color:muted});

s.speakerNotes.text=`PHAST-DP editable architecture revision 5, following the user's 2026-10-15 sketch. Panel (a) spans the top left and centre; panel (b) is left; the central complete model reads downward; panel (c) is at the upper right; a structured output report occupies the lower right. Each module has a thin flat rectangular boundary. All typography is Times New Roman.\nThe pattern projections and geographic projections are different objects, not successive transforms of the same matrix. At a fixed encoder time step, Q^P is 38 by 20, while K^P and V^P are 16 by 20. Pattern attention produces 38 by 16 weights and a 38 by 20 context. The base geographic key, context and updated key share dimensions 38 by 20 before head reshaping. The 20-channel geographic projection is split into two heads of width d_h=10. The source scales both pattern and geographic attention by 1/sqrt(d_h). The figure shows the addition explicitly and varies the updated key's cell pattern and outline. The drawn cell counts are compressed schematics; printed dimension labels define the actual meaning.\nThe report is a schematic prediction output, not an experimental result table: i*, w-hat, s-hat, d-hat, c-hat, ell-hat are symbolic. The highlighted event interval, one-hot process-class indicator and progress bar do not claim measured forecasts. No numerical performance values were invented. The causal/lag traces, graph, matrices, clustering points and feature patches are mechanism illustrations.\nSources: paper main.tex on dev_xwt at ffcfbb7 and isaac_factory origin/dev_tyx 29655baee57b9095119589a211ae1e2113b84078, factory_bn/graph.py, dataset.py, cause_cluster.py, model.py and backbone.py. Current dimensions: 30 history windows, 38 resource nodes, 27 channels, 6 feature groups, 5 pre-norm blocks with 4 temporal/2 geographic/2 semantic heads. The graph uses five node types and symmetric weighted adjacency. Material availability is a resource feature.\nEvent labels use process rules and persistence. Regime IDs for event conditioning are deterministic rule-based identifiers. The active k-means fits 16 prototypes from length-3 training activity patches; online pattern queries use queue patches. Pattern context is added only to geographic K. Offline exploratory K=8 descriptors with zero prediction-loss weight are omitted. Dashed brown lines convey training supervision and the loss path; a dashed green leader identifies the expanded geographic attention. The main diagram includes residuals, grouped embedding, event/regime/precursor fusion, state/order-progress decoding, graph-pooled cause decoding and event report assembly. Training-loss algebra and dropout are omitted.`;
await (await PresentationFile.exportPptx(p)).save(path.join(BUILD,'candidate.pptx'));
execFileSync('/Users/xuwantong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',[path.join(ROOT,'experiments/fix_phast_math_typography.py'),path.join(BUILD,'candidate.pptx')],{stdio:'inherit'});
const png=await p.export({slide:s,format:'png',scale:1.2});await fs.writeFile(path.join(OUT,'PHAST_DP_model_v5.png'),new Uint8Array(await png.arrayBuffer()));
const layout=await s.export({format:'layout'});await fs.writeFile(path.join(BUILD,'layout.json'),await layout.text());
console.log('Created modular model revision:',OUT);
