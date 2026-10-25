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
const BUILD=path.join(ROOT,'build/phast_model_portrait');
const OUT=path.join(ROOT,'figures/drafts/phast_model_portrait');
const FINAL=path.join(OUT,'PHAST_DP_model_portrait_3x4_editable.pptx');
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
const coreY=interp([[365,360],[441,420],[450,429],[478,457],[486,459],[520,493],
 [550,516],[572,536],[704,668],[721,685],[738,695],[776,733],
 [785,739],[797,751],[810,764],[821,769],[836,784],[870,818],
 [900,844],[940,884],[947,891],[964,902],[976,914],[989,927],
 [1006,944],[1026,964],[1051,989],[1096,1034],[1120,1055],[1173,1108],
 [1197,1132],[1222,1160],[1279,1217],[1340,1240]]);
const supY=interp([[365,360],[450,445],[481,456],[876,851],[894,870],
 [910,875],[950,915],[990,955],[1028,990],[1064,1026],[1093,1030],
 [1107,1045],[1136,1074],[1154,1087],[1198,1131],[1211,1136],
 [1290,1215],[1298,1218],[1325,1245],[1340,1250]]);
function flowMap(sp,dx,ymap){
 const[x,y,w,h]=rect(sp);
 // Only lines use the full coordinate map. Text, circles and matrix cells retain
 // their dimensions and font sizes, instead of being squeezed into the new ratio.
 let nh=h;
 if(sp.includes('<a:custGeom>'))nh=Math.max(.01,ymap(y+h)-ymap(y));
 return place(sp,x+dx,ymap(y),w,nh);
}

const removed=new Set([ ...Array.from({length:5},(_,i)=>183+i),
 319,320,321,...Array.from({length:5},(_,i)=>375+i),
 ...Array.from({length:5},(_,i)=>511+i),...Array.from({length:5},(_,i)=>539+i),
 898,...Array.from({length:5},(_,i)=>951+i),1038]);
const moved=[];
for(let i=0;i<shapes.length;i++){
 if(removed.has(i))continue;
 let sp=shapes[i];const[x,y,w,h]=rect(sp);
 if(i===0)sp=place(sp,0,14,1500,44);
 else if(i===1)sp=place(sp,35,80,1430,250);
 else if(i===2)sp=place(sp,55,92,1390,h);
 else if(i===3)sp=place(sp,55,138,1390,h);
 else if(i===4)sp=place(sp,35,360,620,880);
 else if(i===5)sp=place(sp,55,372,580,h);
 else if(i===6)sp=place(sp,55,445,580,h);
 else if(i===7)sp=place(sp,700,360,765,880);
 else if(i===8)sp=place(sp,720,372,725,h);
 else if(i===9)sp=place(sp,720,418,725,h);
 else if(i===10)sp=place(sp,35,1270,1430,445);
 else if(i===11)sp=place(sp,55,1282,1390,h);
 else if(i===12)sp=place(sp,55,1328,1390,h);
 else if(i===13)sp=place(sp,35,1740,1430,240);
 else if(i===14)sp=place(sp,55,1752,1390,h);
 else if(i===15)sp=place(sp,55,1798,1390,h);
 else if(i<183){
   // Factory graph / history / group encoding retain their local geometry.
   if(i<77)sp=shift(sp,0,-5);
   else if(i<162)sp=shift(sp,110,-5);
   else if(i===162)sp=place(sp,x+110,y-5,w+80,h);
   else if(i<165)sp=shift(sp,190,-5);
   else if(i<172)sp=shift(sp,135,-5);
   else sp=shift(sp,190,-5);
 }else if(i===188)sp=place(sp,1101,380,w,h);
 else if(i===189)sp=place(sp,x+140,420,w,525);
 else if(i<380)sp=flowMap(sp,140,coreY);
 else if(i<620){
   sp=flowMap(sp,40,supY);
   if(i===619)sp=place(sp,x+40,1208,w,h);
 }else if(i<640){
   // Lag illustration above the geographic-key update, on the right.
   sp=shift(sp,-545,1187);
 }else if(i<898){
   // Full pattern matching pathway in the lower-left half.
   sp=shift(sp,-1285,1061);
 }else if(i<997){
   sp=shift(sp,-545,834);
 }else if(i===997)sp=place(sp,1300,1763,w,h);
 else if(i<1038)sp=shift(sp,-1285,813);
 else if(i<1045)sp=shift(sp,-505,628);
 else if(i<1048)sp=shift(sp,-505,635);
 else sp=shift(sp,-505,643);
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
route([[1294,288],[1294,345],[1080,345],[1080,459]],'315B79',2.1);
route([[575,supY(844)],[670,supY(844)],[670,coreY(1252)],[785,coreY(1252)]],'805431',1.6,true);
route([[470,955],[690,955],[690,coreY(1073)],[780,coreY(1073)]],'805431',1.8);
route([[1358,coreY(1250)],[1482,coreY(1250)],[1482,1865],[1465,1865]],'315B79',2.3);
route([[375,1663],[375,1699],[735,1699],[735,1525],[1050,1525],[1050,1537]],'315F46',1.9);
line(755,1343,755,1697,'C5D7CB',.8);
line(785,1815,785,1958,'CCD9E1',.9);
// Reference (c) is also carried by the geographic-attention label; the expansion
// leader follows the exterior of the encoder and ends at the lower detail panel.
route([[1390,944],[1448,944],[1448,1254],[1370,1254],[1370,1270]],'315F46',1.5,true,false);

let next=xml;
let first=true;
next=next.replace(/<p:sp\b[\s\S]*?<\/p:sp>/g,()=>{if(first){first=false;return moved.join('')+extra.join('');}return '';});
const getTexts=x=>x.match(/<a:t>[\s\S]*?<\/a:t>/g)||[];
if(JSON.stringify(getTexts(next))!==JSON.stringify(getTexts(xml)))throw Error('Text content changed');
zip.file('ppt/slides/slide1.xml',next);
const pres=await zip.file('ppt/presentation.xml').async('string');
zip.file('ppt/presentation.xml',pres.replace(/<p:sldSz\b[^>]*\/>/,`<p:sldSz cx="${E(1500)}" cy="${E(2000)}"/>`));
// Keep the technical provenance while updating the descriptive layout note.
const notesName='ppt/notesSlides/notesSlide1.xml';
if(zip.file(notesName)){
 let notes=await zip.file(notesName).async('string');
 notes=notes.replace(/PHAST-DP editable architecture revision 5[\s\S]*?All typography is Times New Roman\./,m=>
  'PHAST-DP editable portrait architecture, 3:4 canvas. Resource representation spans the top; process-informed supervision and the prediction network occupy the middle; delay-conditioned interaction is unfolded horizontally below them; the structured report spans the bottom. Original blue, brown and green palette, Times New Roman, and all technical content are retained.');
 zip.file(notesName,notes);
}
const candidate=path.join(BUILD,'candidate.pptx');
await fs.writeFile(candidate,await zip.generateAsync({type:'nodebuffer',compression:'DEFLATE'}));
await fs.writeFile(path.join(BUILD,'reflow-audit.json'),JSON.stringify({
 source:SOURCE,slideSize:[1500,2000],aspectRatio:'3:4',sourceShapes:shapes.length,
 preservedShapes:moved.length,replacedConnectionShapes:removed.size,newConnectionShapes:extra.length,
 preservedTextRuns:getTexts(next).length,sourceTextRuns:getTexts(xml).length,
 sourceUnchanged:bytes.equals(await fs.readFile(SOURCE)),
},null,2));
const finalizing=process.argv.includes('--finalize');
if(finalizing)await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:FINAL,
 pythonExecutable:path.join(RUNTIME,'python/bin/python3'),
 integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu',`${E(1500)},${E(2000)}`,'--validate-bullet-geometry','--validate-heading-fit'],
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
 execFileSync(path.join(RUNTIME,'bin/override/soffice'),[
  '--headless','--convert-to',
  'pdf:impress_pdf_Export:{"UseTaggedPDF":{"type":"boolean","value":"false"}}',
  '--outdir',OUT,FINAL],{cwd:ROOT,stdio:'inherit'});
}
const layout=await p.slides.items[0].export({format:'layout'});
await fs.writeFile(path.join(BUILD,'layout.json'),await layout.text());
console.log(JSON.stringify({file:finalizing?FINAL:candidate,width:1500,height:2000,texts:getTexts(next).length}));
