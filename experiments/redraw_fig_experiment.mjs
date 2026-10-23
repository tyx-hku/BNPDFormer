/**
 * Editable redraw of Figure 3: same factory, operations, and graph relations.
 * Uses the original scene bytes from fig_experiment_final.pptx. No generated
 * scene imagery, measurements, or new graph edges are introduced.
 * Run with the bundled Node runtime. Outputs a candidate in build/figure3_redraw.
 * Add --pdf to export a vector PDF with LibreOffice. The task-local fontconfig
 * file makes the macOS Times New Roman fonts available to the export process.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const BUILD=path.join(ROOT,'build/figure3_redraw');
const DEPS=process.env.CODEX_FIGURE_DEPS || path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies');
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(DEPS,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')));
await fs.mkdir(BUILD,{recursive:true});
const scene=execFileSync('/usr/bin/unzip',['-p',path.join(ROOT,'figures/fig_experiment_final.pptx'),'ppt/media/image1.png'],{maxBuffer:10*1024*1024});

const W=1200,H=1400;
const C={ink:'#253C49',muted:'#586873',blue:'#4F7B98',blueLight:'#ECF2F6',
  ochre:'#B78B45',ochreLight:'#FBF6ED',violet:'#877BA6',violetLight:'#EDEAF3',
  coral:'#B66C59',rule:'#BEC9CF',agentLine:'#B8ADC9',white:'#FFFFFF'};
const presentation=Presentation.create({slideSize:{width:W,height:H}});
const s=presentation.slides.add();s.background.fill=C.white;
const textEntries=[];
function shape(name,x,y,w,h,fill='none',stroke='none',lw=0,geometry='rect'){
  return s.shapes.add({name,geometry,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:lw,style:'solid'}});
}
function txt(name,x,y,w,h,value,size=20,bold=false,color=C.ink,align='left'){
  size=Math.max(size,20); // At least 8 pt after scaling to the manuscript width.
  const a=shape(name,x,y,w,h);a.text=value;
  a.text.style={typeface:'Times New Roman',fontSize:size,bold,color,alignment:align,
    verticalAlignment:'top',insets:0,autoFit:'none',wrap:'none'};
  textEntries.push({name,x,y,w,h,value,size});return a;
}
function line(name,x1,y1,x2,y2,color=C.rule,lw=1.2,dashed=false){
  const x=Math.min(x1,x2),y=Math.min(y1,y2),w=Math.max(Math.abs(x2-x1),.01),h=Math.max(Math.abs(y2-y1),.01);
  return s.shapes.add({name,geometry:'custom',position:{left:x,top:y,width:w,height:h},fill:'none',
    line:{fill:color,width:lw,style:dashed?'dashed':'solid'},
    customPaths:[{width:w,height:h,commands:[{moveTo:{x:x1-x,y:y1-y}},{lineTo:{x:x2-x,y:y2-y}}]}]});
}
function title(letter,title,y){
  txt('Panel '+letter,18,y,1164,32,`(${letter})  ${title}`,26,true);
  line('Panel '+letter+' divider',18,y+38,1182,y+38,C.ink,1.4);
}
function disc(name,x,y,r,fill,stroke='none'){
  return shape(name,x-r,y-r,2*r,2*r,fill,stroke,1,'ellipse');
}
function number(n,x,y,color){
  disc('Task '+n,x,y,14,color);
  txt('Task number '+n,x-13,y-12,26,25,String(n),20,true,C.white,'center');
}

// (a) The source scene, displayed with exactly the original crop and aspect.
title('a','Digital-twin production environment and resource entities',15);
s.images.add({name:'Original Isaac Sim factory scene',blob:scene,contentType:'image/png',
  alt:'Original factory screenshot from the previous Figure 3',fit:'cover',
  crop:{left:0,top:.20,right:.32,bottom:.07},position:{left:18,top:66,width:770,height:332}});
function pin(label,fx,fy,tx,ty,fill,width=50){
  const x=18+770*fx,y=66+332*fy,px=18+770*tx,py=66+332*ty;
  line('Callout '+label,x,y+12,px,py,C.white,1.7);
  shape('Tag '+label,x-width/2,y-12,width,25,fill);
  txt('Scene '+label,x-width/2,y-11,width,24,label,19,true,C.white,'center');
}
pin('M1',.57,.51,.57,.65,C.blue,48);
pin('M2',.89,.51,.86,.68,C.blue,48);
pin('M3 / M4',.36,.15,.37,.28,C.blue,84);
pin('M5',.39,.51,.39,.65,C.blue,48);
pin('M6 / M7',.145,.51,.145,.66,C.blue,84);
pin('Human',.735,.115,.75,.28,C.violet,73);
pin('Buffer',.875,.115,.88,.28,C.ochre,73);
pin('Gantry',.39,.405,.47,.48,C.ochre,74);
pin('AGV',.40,.79,.315,.76,C.blue,50);
pin('Material',.235,.94,.16,.90,C.coral,82);

txt('Machine key',818,65,364,26,'Machine / workstation identifiers',22,true);
const machineLabels=[
  ['M1','CNC pipe intersection\ncutting machine',49],
  ['M2','Large pipe roll-grooving machine',33],
  ['M3','Workbench 0',31],['M4','Workbench 1',31],
  ['M5','Robotic root-welding station',33],
  ['M6','Rotary surface-welding station 0',33],
  ['M7','Rotary surface-welding station 1',33],
];
let my=106;
for(const [id,label,h] of machineLabels){
  txt(id+' key',818,my,33,h,id,20,true,C.blue);
  txt(id+' description',861,my,321,h,label,19.5);
  my+=h;
}
line('Key separator',818,354,1182,354);
txt('Shared workbenches',818,367,364,48,'M3 / M4 support spot welding and painting.\nAGV: automated guided vehicle.',19);

// (b) Six manufacturing operations at left; shared handling at right.
title('b','Manufacturing stages and shared material-handling subtasks',439);
txt('Manufacturing heading',18,493,650,28,'Manufacturing stages',23,true,C.coral);
txt('Handling heading',728,493,454,28,'Shared handling subtasks',23,true,C.blue);
line('Task column separator',699,494,699,981,C.rule,1);
const steps=[
  ['Pipe cutting at M1','Raw pipe delivered; worker operates the cutting machine.\nCut pipe is released for transfer.'],
  ['Roll grooving at M2','Cut pipe transferred; worker operates the grooving machine.\nGrooved pipe proceeds to assembly.'],
  ['Assembly and spot welding at M3 / M4','Pipe, flange and elbow supplied to a selected workbench.\nAssembly and spot welding yield a semi-finished pipe.'],
  ['Argon-arc root welding at M5','Semi-finished pipe delivered to the welding robot.\nWorker operates the station for root welding.'],
  ['MIG surface welding at M6 / M7','Root-welded pipe transferred to a rotary welding station.\nSurface welding prepares the pipe for painting.'],
  ['Rust-proof painting at M3 / M4','Welded pipe returned to a workbench for rust-proof treatment.\nThe finished water pipe is ready.'],
];
line('Manufacturing sequence',34,551,34,945,'#D4BBB2',1.5);
steps.forEach(([name,body],i)=>{
  const y=539+i*76;
  number(i+1,34,y+12,C.coral);
  txt('Stage '+(i+1)+' title',62,y-1,617,28,name,21.5,true);
  txt('Stage '+(i+1)+' detail',62,y+29,617,47,body,19.5);
});
const handling=[
 ['Processing and outbound handling',
  ['Worker approaches the station','Controls the machine during processing','Waits for a free gantry','Assists loading for outbound transfer']],
 ['Transfer within one gantry zone',
  ['Worker and gantry approach the material','Load onto gantry and carry to destination','Place at the station or storage area']],
 ['Transfer across gantry zones',
  ['Source gantry loads an AGV and is released','AGV travels to the destination','Free destination gantry unloads and places']],
];
handling.forEach(([name,actions],i)=>{
  const y=539+i*148;
  number(i+7,742,y+12,C.blue);
  txt('Handling '+(i+7)+' title',769,y-1,413,28,name,21,true);
  actions.forEach((action,j)=>{
    txt('Handling '+(i+7)+' action '+j,769,y+33+j*25,413,25,(j?'→ ':'')+action,19.5);
  });
  if(i<2)line('Handling separator '+i,728,y+132,1182,y+132,'#D7E0E5',1);
});

// (c) Same representative nodes and edge families as the existing figure.
title('c','Multi-entity structural graph',1012);
txt('Graph resources',18,1067,770,25,'G: gantries (4)     H: workers (5)     R: AGVs (4)',20,false,C.ink,'center');
const agents=[{id:'G',x:160,y:1120,c:C.ochre},{id:'H',x:397,y:1120,c:C.violet},{id:'R',x:634,y:1120,c:C.blue}];
const machines=Array.from({length:7},(_,i)=>({id:'M'+(i+1),x:55+114*i,y:1212+(i%2?14:-5)}));
const buffers=[{id:'B1',x:160,y:1311,target:[0,1]},{id:'B2',x:397,y:1311,target:[0,1,2]},{id:'B3',x:634,y:1311,target:[2,3,4,5,6]}];
agents.forEach(a=>machines.forEach(m=>line(a.id+' to '+m.id,a.x,a.y,m.x,m.y,C.agentLine,1.25)));
buffers.forEach(b=>b.target.forEach(i=>line(b.id+' to '+machines[i].id,b.x,b.y,machines[i].x,machines[i].y,C.ochre,1.5)));
machines.slice(1).forEach((m,i)=>line(machines[i].id+' backbone '+m.id,machines[i].x,machines[i].y,m.x,m.y,C.blue,2.6));
agents.forEach(a=>{disc('Representative '+a.id,a.x,a.y,19,a.c);txt('Node '+a.id,a.x-19,a.y-13,38,29,a.id,22,true,C.white,'center');});
machines.forEach(m=>{disc('Workstation '+m.id,m.x,m.y,21,C.blue);txt('Node '+m.id,m.x-23,m.y-13,46,29,m.id,21,true,C.white,'center');});
buffers.forEach(b=>{disc('Representative '+b.id,b.x,b.y,19,C.ochre);txt('Node '+b.id,b.x-21,b.y-13,42,29,b.id,21,true,C.white,'center');});
txt('Buffer family key',18,1344,770,25,'B1: BlackStorage     B2: GroundStorage     B3: YellowStorage',19.5,false,C.ink,'center');

txt('Graph key heading',818,1067,364,28,'Structural relations',22,true);
[[C.blue,'Workstation backbone',false],[C.agentLine,'Human / transport–station links',false],[C.ochre,'Buffer–station affinities',false]].forEach(([c,t,d],i)=>{
  line('Graph legend line '+i,818,1111+i*33,852,1111+i*33,c,i?1.5:2.6,d);
  txt('Graph legend '+i,866,1098+i*33,316,29,t,19.5);
});
txt('Graph size',818,1209,364,49,'38 nodes: 7 workstations, 4 gantries,\n5 workers, 4 AGVs and 18 buffers.',19.5,true);
txt('Graph interpretation',818,1271,364,94,'Undirected associations, with representative\nG / H / R and buffer nodes. Repeated nodes,\nself-loops and within-type transport links\nare omitted.',19);
line('Graph bottom rule',18,1371,1182,1371,C.rule,1);
txt('Material features note',18,1375,1164,24,'Material availability enters resource features through supply, waiting and buffer occupancy.',19,false,C.muted,'center');

s.speakerNotes.text=[
 'Figure 3 redraw: the original a/b/c content is retained. Scene image is byte-for-byte extracted from figures/fig_experiment_final.pptx with the original crop.',
 'Manufacturing stages 1–6 and handling subtasks 7–9 retain the original task semantics. The diagram is a representative undirected resource graph, not a task-precedence graph.',
 'Graph edge data: source/isaaclab_tasks/isaaclab_tasks/direct/hc_factory/PDFormer/factory_bn/graph.py, PROCESS_CHAIN and BUFFER_MACHINE_AFFINITY. Agent nodes connect to all seven stations. B1 targets M1/M2; B2 targets M1/M2/M3; B3 targets M3–M7.',
 'Layout reference: Safe reinforcement learning with online filtering for fatigue-predictive human-robot task planning and allocation in production, Figure 4. No artwork copied from the reference.',
].join('\n');
await (await PresentationFile.exportPptx(presentation)).save(path.join(BUILD,'candidate.pptx'));
for(const [format,scale] of [['png',1.5]]){
 const out=await s.export({format,scale});
 await fs.writeFile(path.join(BUILD,`candidate.${format}`),new Uint8Array(await out.arrayBuffer()));
}
await fs.writeFile(path.join(BUILD,'text_layout.json'),JSON.stringify(textEntries,null,2));
await fs.writeFile(path.join(BUILD,'figure_trace.json'),JSON.stringify({
 artifact_id:'fig:experiment',source_data:{file:'figures/fig_experiment_final.pptx',manuscript:'main.tex §5.1.1'},
 transformation:{script:'experiments/redraw_fig_experiment.mjs'},
 caption_claim:'Resource entities, six manufacturing stages and shared handling tasks, and a grouped structural view of 38 resources.',
 limitations:['The graph uses representative agent and buffer nodes; repeated nodes, self-loops and within-type transport links are omitted.'],
 output:'figures/fig_experiment.pdf',
},null,2));
console.log('Rendered Figure 3 candidate to '+BUILD);
if(process.argv.includes('--pdf')){
 const fontDir=process.env.FIGURE_FONT_DIR || '/System/Library/Fonts/Supplemental';
 await fs.access(path.join(fontDir,'Times New Roman.ttf'));
 const escapeXml=t=>t.replaceAll('&','&amp;').replaceAll('<','&lt;');
 const fc=path.join(BUILD,'fonts.conf');
 await fs.writeFile(fc,`<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">\n<fontconfig><dir>${escapeXml(fontDir)}</dir><cachedir>${escapeXml(path.join(BUILD,'fontcache'))}</cachedir></fontconfig>\n`);
 execFileSync('soffice',['--headless','--convert-to',
   'pdf:impress_pdf_Export:{"UseTaggedPDF":{"type":"boolean","value":"false"}}',
   '--outdir',BUILD,path.join(BUILD,'candidate.pptx')],
   {env:{...process.env,FONTCONFIG_FILE:fc,SAL_FONTPATH:fontDir},timeout:60000,maxBuffer:1024*1024});
 console.log('Exported vector PDF with the requested Times New Roman fonts.');
}
