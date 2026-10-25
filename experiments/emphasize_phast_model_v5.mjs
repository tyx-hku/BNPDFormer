// Preserve v5's editable layout while strengthening contrast and typography.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const RUNTIME='/Users/xuwantong/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const SKILL='/Users/xuwantong/.codex/plugins/cache/openai-primary-runtime/presentations/26.1007.11041/skills/presentations';
process.env.RUNTIME_NODE_MODULES=path.join(RUNTIME,'node/node_modules');
const req=createRequire(path.join(RUNTIME,'node/package.json'));
const JSZip=req('jszip');
const {FileBlob,PresentationFile}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')));
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')));
const SOURCE=path.join(ROOT,'figures/drafts/phast_model_v5/PHAST_DP_model_v5_editable.pptx');
const BUILD=path.join(ROOT,'build/phast_model_v5_emphasis');
const FINAL=path.join(ROOT,'figures/drafts/phast_model_v5/PHAST_DP_model_v5_emphasis.pptx');
await fs.mkdir(BUILD,{recursive:true});
const sourceBytes=await fs.readFile(SOURCE);
const zip=await JSZip.loadAsync(sourceBytes);
const colors={
 '242424':'1B1B1B','202A39':'17202D','3F6D8A':'315B79','986844':'805431',
 '467760':'315F46','7B8188':'5C636B','606C77':'344453',
 '657386':'536779','7C858D':'657482',
 'F1F5F8':'E9F0F5','D7E3EB':'BDCFDE','A7BCCD':'8DAAC1','6D8CA2':'547A98','3D617B':'294D6A',
 'C3D6E3':'A7C4D8','E3EDF3':'D3E2EC','A5BECE':'7EA4BE','D5E3EC':'B8D0DF',
 'EDF3F7':'E1EBF2','B4C7D4':'8EAEC3','EAF1F8':'CFDFEB',
 '91AABD':'728FA4','8FA4B1':'6D8AA0','A9B9C4':'8BA3B4','AAB9C4':'829DAF',
 'FCF6EF':'F5ECE2','EDDBCA':'DFC8B3','D8B89B':'BE936F','BB8A61':'9B6840','95633F':'734624',
 'F7EEE4':'E6D2BE','FCF8F4':'EFE0D1','F7F0EA':'F1E6DB','D4B496':'BE936F',
 'B2815A':'9B6840','8B5C39':'734624','F6F0E9':'EADAC9',
 'A67B58':'805431','EFE4D9':'E6D2BE',
 'F2F6F2':'EAF1E9','DCE9DE':'C4D8C7','ACC5B1':'92B398','799E81':'557F60','4F7658':'295A39',
 'EAF4EB':'D7E8D9','C3DCC8':'A0C4A8','90BB9A':'67996F','599368':'3E7549','2C643B':'1D4D2A',
 'EEF6F0':'D2E3D7','EAF2EB':'D2E3D7','F6F6F4':'E7EBEF',
 '657C8C':'4F6678','758A99':'5E788B','E9EEF1':'E1E7EB',
 'E8EFF3':'D5E3EC','AEC2CF':'8CAABF','84A8BE':'537F9D',
};
const decode=s=>s.replace(/&#10;|&#xA;/g,'\n').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&apos;/g,"'");
const fontExceptions=new Map([
 ['M: machine/workbench  H: worker  G: gantry  R: robot  B: buffer',1.14],
 ['Regime + precursor\nfusion (b)',1.12],
 ['Skip + order-progress\nfusion',1.12],
 ['Graph pooling\n+ node evidence',1.12],
 ['Pattern context Cᴾ\n38 × 20',1.12],
 ['Resource i*',1.14],
 ['+',1.10],['×',1.10],['…',1.10],
 ['Grouped Linear + GELU\nMean aggregation',1.14],
 ['Feed-forward network',1.10],
 ['Event decoding\nand report assembly',1.10],
 ['attention',1.15],
]);
const boldNames=new Set(['LayerNorm','Concat + Linear','Feed-forward network','Event decoding\nand report assembly']);
const audit=[];
for(const name of Object.keys(zip.files)){
 if(!/^ppt\/slides\/slide\d+\.xml$/.test(name))continue;
 const original=await zip.file(name).async('string');
 let xml=original.replace(/<p:sp\b[\s\S]*?<\/p:sp>/g,sp=>{
   const nm=decode(sp.match(/<p:cNvPr\b[^>]*\bname="([^"]*)"/)?.[1]||'');
   const off=sp.match(/<a:off\b[^>]*\bx="(\d+)"[^>]*\by="(\d+)"/);
   const ext=sp.match(/<a:ext\b[^>]*\bcx="(\d+)"[^>]*\bcy="(\d+)"/);
   const x=+(off?.[1]||0)/9525,y=+(off?.[2]||0)/9525;
   const w=+(ext?.[1]||0)/9525,h=+(ext?.[2]||0)/9525;
   const text=sp.includes('<p:txBody>');
   const origColors=[...sp.matchAll(/<a:srgbClr\b[^>]*val="([A-Fa-f0-9]{6})"/g)].map(m=>m[1]);
   sp=sp.replace(/(<a:srgbClr\b[^>]*val=")([A-Fa-f0-9]{6})(")/g,(m,a,c,b)=>a+(colors[c.toUpperCase()]||c)+b);
   if(text){
     const sizes=[...sp.matchAll(/<(?:a:rPr|a:defRPr)\b[^>]*\bsz="(\d+)"/g)].map(m=>+m[1]);
     if(sizes.length){
       const size=Math.max(...sizes)/75;
       const factor=fontExceptions.get(nm)??(size>=27?1.15:size>=20?1.20:1.25);
       sp=sp.replace(/(<a:(?:rPr|defRPr|endParaRPr)\b[^>]*\bsz=")(\d+)(")/g,(m,a,n,b)=>a+Math.round(+n*factor)+b);
       audit.push({name:nm,beforePx:size,afterPx:Math.round(size*factor*100)/100});
     }
     if(boldNames.has(nm))sp=sp.replace(/(<a:(?:rPr|defRPr|endParaRPr)\b[^>]*\bb=")0(")/g,(_,a,b)=>a+'1'+b);
     // Explicit compact leading gives enlarged two-line labels breathing room
     // inside their existing boxes without moving or resizing the diagram.
     if((sp.match(/<a:p>/g)||[]).length>1){
       sp=sp.replace(/(<a:pPr\b[^>]*>)(?!<a:lnSpc>)/g,'$1<a:lnSpc><a:spcPct val="95000"/></a:lnSpc>');
     }
   }else{
     // Keep cell-grid strokes and pale separators quiet; strengthen computational routes.
     sp=sp.replace(/(<a:ln\b[^>]*\bw=")(\d+)(")/g,(m,a,n,b)=>{
       let px=+n/9525;
       if(px===0)return m;
       let factor=px>=1.1?1.24:1;
       if(origColors.includes('202A39')&&x>=610&&x+w<=1275&&y>=440)factor=1.5;
       if(nm==='Prediction network')factor=1.48;
       if(nm==='Five encoder blocks')factor=1.23;
       return a+Math.round(+n*factor)+b;
     });
     if(nm==='Feed-forward network')sp=sp.replace('val="E7EBEF"','val="D9E3EB"');
     // Shared attention functions now have a visible fill, while geographic attention
     // retains its green emphasis and direct correspondence with panel (c).
     if(Math.abs(y-572)<1&&Math.abs(w-174)<1&&Math.abs(h-132)<1){
       sp=sp.replace(/(<a:solidFill><a:srgbClr val=")FFFFFF("\/><\/a:solidFill>)/,'$1E4ECF2$2');
     }
   }
   return sp;
 });
 // Geometry and text are intentionally unchanged.
 const textTags=s=>s.match(/<a:t>[\s\S]*?<\/a:t>/g)||[];
 const geomTags=s=>s.match(/<a:(?:xfrm|off|ext)\b[^>]*>/g)||[];
 if(JSON.stringify(textTags(original))!==JSON.stringify(textTags(xml)))throw Error('Text changed');
 if(JSON.stringify(geomTags(original))!==JSON.stringify(geomTags(xml)))throw Error('Geometry changed');
 zip.file(name,xml);
}
const candidate=path.join(BUILD,'candidate.pptx');
await fs.writeFile(candidate,await zip.generateAsync({type:'nodebuffer',compression:'DEFLATE'}));
await fs.writeFile(path.join(BUILD,'typography-audit.json'),JSON.stringify(audit,null,2));
const finalizing=process.argv.includes('--finalize');
if(finalizing){
 await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:FINAL,
  pythonExecutable:path.join(RUNTIME,'python/bin/python3'),
  integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','19050000,13144500','--validate-bullet-geometry','--validate-heading-fit'],
  explicitTotalSlideCount:1,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],
  fontPolicy:{basis:'reference',families:['Times New Roman'],referencePath:SOURCE,referenceSha256:crypto.createHash('sha256').update(sourceBytes).digest('hex')},
  verifyArtifactToolImport:true,receiptPath:path.join(BUILD,'validation.json')});
}
const p=await PresentationFile.importPptx(await FileBlob.load(finalizing?FINAL:candidate));
const png=await p.export({slide:p.slides.items[0],format:'png',scale:1.2});
await fs.writeFile(finalizing?FINAL.replace('.pptx','.png'):path.join(BUILD,'preview.png'),new Uint8Array(await png.arrayBuffer()));
if(!sourceBytes.equals(await fs.readFile(SOURCE)))throw Error('Original changed');
console.log(JSON.stringify({file:finalizing?FINAL:candidate,textBoxes:audit.length,originalUnchanged:true,geometryUnchanged:true}));
