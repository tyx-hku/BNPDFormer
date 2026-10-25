// Reuse the editable v5 objects in a 3:4 portrait layout; preserve native text,
// matrices and diagrams, and reroute connections between relocated modules.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const RUNTIME='/Users/xuwantong/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const SKILL='/Users/xuwantong/.codex/plugins/cache/openai-primary-runtime/presentations/26.1007.11041/skills/presentations';
process.env.RUNTIME_NODE_MODULES=path.join(RUNTIME,'node/node_modules');
const req=createRequire(path.join(RUNTIME,'node/package.json'));
const JSZip=req('jszip');
const {PresentationFile,FileBlob}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')));
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')));
const SOURCE=path.join(ROOT,'figures/drafts/phast_model_v5/PHAST_DP_model_v5_emphasis.pptx');
const BUILD=path.join(ROOT,'build/phast_model_portrait_spine');
const OUT=path.join(ROOT,'figures/drafts/phast_model_portrait_spine');
const FINAL=path.join(OUT,'PHAST_DP_model_portrait_spine_3x4_editable.pptx');
await fs.mkdir(BUILD,{recursive:true});await fs.mkdir(OUT,{recursive:true});
const bytes=await fs.readFile(SOURCE),zip=await JSZip.loadAsync(bytes);
const xml=await zip.file('ppt/slides/slide1.xml').async('string');
const shapes=[...xml.matchAll(/<p:sp\b[\s\S]*?<\/p:sp>/g)].map(m=>m[0]);
if(shapes.length!==1049)throw Error('Unexpected source revision; inspect before reflow.');
const E=v=>Math.round(v*9525);
function rect(sp){
 const o=sp.match(/<a:off\b[^>]*\bx="(\d+)"[^>]*\by="(\d+)"/);
 const e=sp.match(/<a:ext\b[^>]*\bcx="(\d+)"[^>]*\bcy="(\d+)"/);
 return [+o[1]/9525,+o[2]/9525,+e[1]/9525,+e[2]/9525];
}
function place(sp,x,y,w,h){
 return sp.replace(/<a:xfrm\b[\s\S]*?<\/a:xfrm>/,xf=>xf
  .replace(/(<a:off\b[^>]*\bx=")[^"]+("[^>]*\by=")[^"]+("[^>]*\/>)/,`$1${E(x)}$2${E(y)}$3`)
  .replace(/(<a:ext\b[^>]*\bcx=")[^"]+("[^>]*\bcy=")[^"]+("[^>]*\/>)/,`$1${E(w)}$2${E(h)}$3`));
}
function shift(sp,dx,dy){const[x,y,w,h]=rect(sp);return place(sp,x+dx,y+dy,w,h);}
function interp(knots){return v=>{
 for(let i=1;i<knots.length;i++)if(v<=knots[i][0]){
  const[a,b]=knots[i-1],[c,d]=knots[i];return b+(v-a)*(d-b)/(c-a);
 }
 const[a,b]=knots.at(-1);return v-a+b;
};}
// A wide continuous inference column takes precedence over the narrower
// detail column. All objects come from the user-edited, editable source.
const W=1800,H=2400;
function scaleStyle(sp,k){
 return sp.replace(/\bsz="(\d+)"/g,(_,v)=>`sz="${Math.round(+v*k)}"`)
  .replace(/(<a:ln\b[^>]*\bw=")(\d+)(")/g,(_,a,v,b)=>a+Math.round(+v*k)+b);
}
function affine(sp,ox,oy,dx,dy,k=1){
 const[x,y,w,h]=rect(sp);
 return place(scaleStyle(sp,k),dx+(x-ox)*k,dy+(y-oy)*k,w*k,h*k);
}
function pointMain(x,y){return [560+(x-940)*1.35,450+(y-365)*1.35];}
function main(sp){return affine(sp,940,365,560,450,1.35);}
function detailB(sp){return affine(sp,35,365,1183,435,.94);}
function detailC(sp,dy){return affine(sp,1320,85,1130,dy,.98);}
const removed=new Set([76,...Array.from({length:3},(_,i)=>162+i),
 ...Array.from({length:3},(_,i)=>174+i),...Array.from({length:8},(_,i)=>180+i),
 319,320,321,...Array.from({length:4},(_,i)=>366+i),
 ...Array.from({length:8},(_,i)=>372+i),
 ...Array.from({length:5},(_,i)=>511+i),...Array.from({length:5},(_,i)=>539+i),
 ...Array.from({length:5},(_,i)=>951+i)]);
const moved=[];
for(let i=0;i<shapes.length;i++){
 if(removed.has(i))continue;
 let sp=shapes[i];const[x,y,w,h]=rect(sp);
 if(i===0)sp=place(scaleStyle(sp,1.2),0,15,1800,60);
 else if(i===1)sp=place(sp,1130,95,635,315);
 else if(i===2)sp=place(sp,1150,110,595,75);
 else if(i===3)sp=place(sp,1150,187,595,h);
 else if(i===4)sp=place(sp,1130,435,635,950);
 else if(i===5)sp=place(sp,1150,447,595,70);
 else if(i===6)sp=place(sp,1150,527,595,h);
 else if(i===7){sp=main(sp);sp=sp.replace('<a:srgbClr val="FFFFFF"/>','<a:srgbClr val="F7F9FA"/>');}
 else if(i===8||i===9)sp=main(sp);
 else if(i===10)sp=place(sp,1130,1420,635,950);
 else if(i===11)sp=place(sp,1150,1432,595,42);
 else if(i===12)sp=place(sp,1150,1482,595,h);
 else if(i>=13&&i<=15)sp=affine(sp,1320,925,125,1810,1.35);
 else if(i<77){
   sp=shift(sp,1103,47);
   if(i===44)sp=place(sp,1150,365,590,40);
 }else if(i<162){
   sp=affine(sp,760,164,560,91,1.35);
   if(i===161)sp=place(sp,414.2,216,302.4,36.45);
 }else if(i===165)sp=place(scaleStyle(sp,1.15),630,264,155,34);
 else if(i<172)sp=affine(sp,850,208,499,272,1.25);
 else if(i===172)sp=place(scaleStyle(sp,1.35),310,307,500,74);
 else if(i===173)sp=place(scaleStyle(sp,1.35),315,310,490,68);
 else if(i===177||i===178)sp=affine(sp,1104,280,560,417,1.35);
 else if(i===179)sp=place(scaleStyle(sp,1.2),155,389,335,61);
 else if(i===188)sp=place(scaleStyle(sp,1.35),585,531,94.5,36.5);
 else if(i<380){
   sp=main(sp);
   if(i===364)sp=place(sp,806,1622,196,52.65);
   if(i===365)sp=place(sp,811,1625,186,47.25);
   if(i===370||i===371)sp=shift(sp,-106*1.35,0);
 }else if(i<620){
   sp=detailB(sp);
 }else if(i<640){
   sp=detailC(sp,1420);
 }else if(i<899){
   sp=detailC(sp,1465);
 }else if(i<997){
   sp=detailC(sp,1520);
 }else sp=affine(sp,1320,925,125,1810,1.35);
 moved.push(sp);
}

// Native custom-path connections, positioned before the diagram's foreground.
let newId=20000;const extra=[];
function line(x1,y1,x2,y2,color,width=1.8,dash=false){
 const x=Math.min(x1,x2),y=Math.min(y1,y2),w=Math.max(.01,Math.abs(x2-x1)),h=Math.max(.01,Math.abs(y2-y1));
 const px=v=>Math.round(v*1000);
 extra.push(`<p:sp><p:nvSpPr><p:cNvPr id="${newId++}" name="Portrait connection"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="${E(x)}" y="${E(y)}"/><a:ext cx="${E(w)}" cy="${E(h)}"/></a:xfrm><a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/><a:rect l="0" t="0" r="r" b="b"/><a:pathLst><a:path w="${px(w)}" h="${px(h)}" fill="none"><a:moveTo><a:pt x="${px(x1-x)}" y="${px(y1-y)}"/></a:moveTo><a:lnTo><a:pt x="${px(x2-x)}" y="${px(y2-y)}"/></a:lnTo></a:path></a:pathLst></a:custGeom><a:noFill/><a:ln w="${E(width)}"><a:solidFill><a:srgbClr val="${color}"/></a:solidFill>${dash?'<a:prstDash val="dash"/>':''}</a:ln></p:spPr></p:sp>`);
}
function route(pts,color,width=1.8,dash=false,arrow=true){
 for(let i=1;i<pts.length;i++)line(...pts[i-1],...pts[i],color,width,dash);
 if(arrow){const[a,b]=pts.slice(-2),ang=Math.atan2(b[1]-a[1],b[0]-a[0]);
  for(const d of[-.48,.48])line(...b,b[0]-7*Math.cos(ang+d),b[1]-7*Math.sin(ang+d),color,width);}
}
// Main inference arrows share x=560 from input through decoding to output.
route([[560,289.5],[560,307]],'315B79',2.8);
route([[560,381],[560,400.8]],'315B79',2.8);
route([[490,417],[543.8,417]],'315B79',2.4);
route([[560,433.2],pointMain(940,486)],'315B79',3.0);
route([pointMain(940,1197),[560,1606.95]],'17202D',3.0);
route([[560,1683.9],[560,1810]],'315B79',3.2);
// The training loss remains a side branch, outside the inference spine.
route([pointMain(1157,1197),[904,1573.2],[904,1622]],'805431',1.8,true);
const bx=x=>1183+(x-35)*.94,by=y=>435+(y-365)*.94;
route([[bx(79),by(844)],[1080,by(844)],[1080,1648],[1002,1648]],'805431',1.6,true);
route([[bx(430),by(990)],[bx(570),by(990)]],'805431',1.8);
// Delayed pattern context enters the geographic key update in detail (c).
const cx=x=>1130+(x-1320)*.98;
const cy=(y,base)=>base+(y-85)*.98;
route([[cx(1660),cy(602,1465)],[cx(1660),cy(683,1520)],
 [cx(1595),cy(683,1520)],[cx(1595),cy(703,1520)]],'315F46',1.8);
// Small cross references identify the expansions without adding a second flow.
function reference(source,x,y,w,h,text){
 let sp=place(source,x,y,w,h);
 sp=sp.replace(/<p:cNvPr\b[^>]*\bid="\d+"/,`<p:cNvPr id="${newId++}"`)
  .replace(/<a:t>[\s\S]*?<\/a:t>/,`<a:t>${text}</a:t>`);
 extra.push(sp);
}
reference(shapes[165],826,325,55,35,'(a)');
reference(shapes[165].replaceAll('315B79','805431'),bx(574),by(975),50,32,'(b)');

let next=xml;
let first=true;
next=next.replace(/<p:sp\b[\s\S]*?<\/p:sp>/g,()=>{if(first){first=false;return moved.join('')+extra.join('');}return '';});
const getTexts=x=>x.match(/<a:t>[\s\S]*?<\/a:t>/g)||[];
if(JSON.stringify(getTexts(next).slice(0,126))!==JSON.stringify(getTexts(xml)))throw Error('Original text content changed');
zip.file('ppt/slides/slide1.xml',next);
const pres=await zip.file('ppt/presentation.xml').async('string');
zip.file('ppt/presentation.xml',pres.replace(/<p:sldSz\b[^>]*\/>/,`<p:sldSz cx="${E(W)}" cy="${E(H)}"/>`));
// Keep the technical provenance while updating the descriptive layout note.
const notesName='ppt/notesSlides/notesSlide1.xml';
if(zip.file(notesName)){
 let notes=await zip.file(notesName).async('string');
 notes=notes.replace(/PHAST-DP editable architecture revision 5[\s\S]*?All typography is Times New Roman\./,m=>
  'PHAST-DP editable portrait architecture, 3:4 canvas. The inference path runs vertically through input embedding, the full encoder, prediction heads, decoding, and the structured report in the wide main column. Panels (a), (b), and (c) are subordinate expansions in a narrow side column. Original blue, brown and green palette, Times New Roman, and all technical content are retained.');
 zip.file(notesName,notes);
}
const candidate=path.join(BUILD,'candidate.pptx');
await fs.writeFile(candidate,await zip.generateAsync({type:'nodebuffer',compression:'DEFLATE'}));
await fs.writeFile(path.join(BUILD,'reflow-audit.json'),JSON.stringify({
 source:SOURCE,slideSize:[W,H],aspectRatio:'3:4',sourceShapes:shapes.length,
 preservedShapes:moved.length,replacedConnectionShapes:removed.size,newConnectionShapes:extra.length,
 preservedTextRuns:getTexts(next).length,sourceTextRuns:getTexts(xml).length,
 sourceUnchanged:bytes.equals(await fs.readFile(SOURCE)),
},null,2));
const finalizing=process.argv.includes('--finalize');
if(finalizing)await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:FINAL,
 pythonExecutable:path.join(RUNTIME,'python/bin/python3'),
 integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu',`${E(W)},${E(H)}`,'--validate-bullet-geometry','--validate-heading-fit'],
 explicitTotalSlideCount:1,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],
 fontPolicy:{basis:'reference',families:['Times New Roman'],referencePath:SOURCE,referenceSha256:crypto.createHash('sha256').update(bytes).digest('hex')},
 verifyArtifactToolImport:true,receiptPath:path.join(BUILD,'validation.json')});
const p=await PresentationFile.importPptx(await FileBlob.load(finalizing?FINAL:candidate));
for(const format of ['png']){
 const blob=await p.export({slide:p.slides.items[0],format,scale:1.3});
 await fs.writeFile(finalizing?FINAL.replace('.pptx',`.${format}`):path.join(BUILD,'preview.png'),new Uint8Array(await blob.arrayBuffer()));
}
if(finalizing){
 // The bundled Artifact Tool PDF renderer lacks its standard-font module;
 // LibreOffice exports the same native PPTX as a vector PDF with embedded fonts.
 const fontConfig=path.join(BUILD,'fonts.conf');
 await fs.writeFile(fontConfig,`<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><dir>/System/Library/Fonts/Supplemental</dir><cachedir>${BUILD}/fontcache</cachedir></fontconfig>`);
 execFileSync(path.join(RUNTIME,'bin/override/soffice'),[
  '--headless','--convert-to',
  'pdf:impress_pdf_Export:{"UseTaggedPDF":{"type":"boolean","value":"false"}}',
  '--outdir',OUT,FINAL],{cwd:ROOT,stdio:'inherit',env:{...process.env,FONTCONFIG_FILE:fontConfig,SAL_FONTPATH:'/System/Library/Fonts/Supplemental'}});
}
const layout=await p.slides.items[0].export({format:'layout'});
await fs.writeFile(path.join(BUILD,'layout.json'),await layout.text());
console.log(JSON.stringify({file:finalizing?FINAL:candidate,width:W,height:H,texts:getTexts(next).length}));
