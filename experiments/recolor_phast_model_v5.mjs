// Recolour the current editable source without rebuilding its native objects.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const RUNTIME = '/Users/xuwantong/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const SKILL = '/Users/xuwantong/.codex/plugins/cache/openai-primary-runtime/presentations/26.1007.11041/skills/presentations';
const require = createRequire(path.join(RUNTIME, 'node/package.json'));
const JSZip = require('jszip');
const {FileBlob, PresentationFile} = await import(pathToFileURL(require.resolve('@oai/artifact-tool')));
const {finalizePresentation} = await import(pathToFileURL(path.join(SKILL, 'container_tools/artifact_tool_utils.mjs')));
const SOURCE = path.join(ROOT, 'figures/drafts/phast_model_v5/PHAST_DP_model_v5_editable.pptx');
const BUILD = path.join(ROOT, 'build/phast_model_v5_palette');
const OUT = path.join(ROOT, 'figures/drafts/phast_model_v5');
const FINAL = path.join(OUT, 'PHAST_DP_model_v5_scientific_palette.pptx');
await fs.mkdir(BUILD, {recursive:true});

// Reference anchors: CB001C, F26121, FCB84D, FFF2C7, A6DCED, 5BA7D9, 3D6EB4.
// Derived tints keep the existing matrix intensities and text/background hierarchy.
const colors = {
  '3F6D8A':'3D6EB4', '55768D':'3D6EB4',
  'F1F5F8':'F0F8FC', 'D7E3EB':'D4ECF5', 'A7BCCD':'A6DCED',
  '6D8CA2':'5BA7D9', '3D617B':'3D6EB4', 'C3D6E3':'A6DCED',
  'E3EDF3':'E8F6FB', 'A5BECE':'5BA7D9', 'D5E3EC':'D4ECF5',
  'EDF3F7':'F0F8FC', 'B4C7D4':'A6DCED', 'EAF1F8':'EAF5FB',
  '91AABD':'8DC5E5', 'D0DCE3':'D4ECF5', '8FA4B1':'8DC5E5',
  'A9B9C4':'AED8EC', 'AAB9C4':'AED8EC', 'C7D1D8':'D4ECF5',
  'CCD9E1':'D4ECF5', 'E8EFF3':'EAF5FB', 'AEC2CF':'A6DCED',
  '84A8BE':'5BA7D9',

  '986844':'F26121', 'B48358':'F26121',
  'FCF6EF':'FFFBEF', 'EDDBCA':'FFF2C7', 'D8B89B':'FCDA95',
  'BB8A61':'FCB84D', '95633F':'F26121',
  'F7EEE4':'FFF2C7', 'FCF8F4':'FFFAED', 'F7F0EA':'FFF8E6',
  'D4B496':'FCB84D', 'DCCABB':'F7D9B6',
  'B2815A':'FCB84D', '8B5C39':'F26121',
  'F6F0E9':'FFF6DD', 'A67B58':'F26121', 'EFE4D9':'FFF2C7',

  '467760':'CB001C', '527C64':'CB001C',
  'F2F6F2':'FFF6ED', 'DCE9DE':'FFE1C8', 'ACC5B1':'F8B698',
  '799E81':'EE725D', '4F7658':'D8303C',
  'EAF4EB':'FFE2DF', 'C3DCC8':'F6B4AA', '90BB9A':'EB8077',
  '599368':'DC4552', '2C643B':'CB001C',
  'EEF6F0':'FFF3ED', 'EAF2EB':'FFF1EC',
  'D2DAD5':'F1D9D4', 'ABC2B3':'E6B2AB', 'C5D7CB':'F1D9D4',
};

const sourceBytes = await fs.readFile(SOURCE);
const zip = await JSZip.loadAsync(sourceBytes);
const sourceEntries = new Map();
for (const [name, entry] of Object.entries(zip.files)) {
  if (!entry.dir) sourceEntries.set(name, await entry.async('nodebuffer'));
}
const changed = [];
let replacements = 0;
const colorRE = /(<(?:[\w.-]+:)?srgbClr\b[^>]*\bval=")([0-9A-Fa-f]{6})(")/g;
for (const [name, bytes] of sourceEntries) {
  if (!/^ppt\/slides\/slide\d+\.xml$/.test(name)) continue;
  const before = bytes.toString('utf8');
  let n = 0;
  const after = before.replace(colorRE, (all, prefix, value, suffix) => {
    const next = colors[value.toUpperCase()];
    if (!next) return all;
    n++;
    return prefix + next + suffix;
  });
  const withoutColors = text => text.replace(colorRE, '$1COLOR$3');
  if (withoutColors(before) !== withoutColors(after)) throw Error('Non-colour XML changed');
  if (n) {zip.file(name, after); changed.push({name, replacements:n}); replacements += n;}
}
const CANDIDATE = path.join(BUILD, 'candidate.pptx');
await fs.writeFile(CANDIDATE, await zip.generateAsync({type:'nodebuffer', compression:'DEFLATE'}));

await finalizePresentation({
  workspaceDir: ROOT,
  candidatePath: CANDIDATE,
  finalPath: FINAL,
  pythonExecutable: path.join(RUNTIME, 'python/bin/python3'),
  integrityValidatorPath: path.join(SKILL, 'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath: path.join(SKILL, 'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs: ['--expected-slide-size-emu', '19050000,13144500', '--validate-bullet-geometry', '--validate-heading-fit'],
  explicitTotalSlideCount: 1,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  fontPolicy: {basis:'reference', families:['Times New Roman'], referencePath:SOURCE,
    referenceSha256:crypto.createHash('sha256').update(sourceBytes).digest('hex')},
  verifyArtifactToolImport: true,
  receiptPath: path.join(BUILD, 'validation.json'),
});

// Confirm every package part is identical except for explicit slide RGB values.
const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL));
for (const [name, before] of sourceEntries) {
  const after = await finalZip.file(name).async('nodebuffer');
  if (before.equals(after)) continue;
  if (!/^ppt\/slides\/slide\d+\.xml$/.test(name)) throw Error(`Changed non-slide part: ${name}`);
  if (before.toString().replace(colorRE,'$1COLOR$3') !== after.toString().replace(colorRE,'$1COLOR$3')) {
    throw Error(`Non-colour change in ${name}`);
  }
}
const sourceNow = await fs.readFile(SOURCE);
if (!sourceBytes.equals(sourceNow)) throw Error('Source changed during edit');
await fs.writeFile(path.join(BUILD, 'colour-only-audit.json'), JSON.stringify({
  source:SOURCE, output:FINAL, changed, replacements, palette:colors,
  onlyRgbValuesChanged:true, originalFileUnchanged:true,
}, null, 2));

const deck = await PresentationFile.importPptx(await FileBlob.load(FINAL));
const slide = deck.slides.items[0];
const png = await deck.export({slide, format:'png', scale:1.2});
await fs.writeFile(FINAL.replace('.pptx','.png'), new Uint8Array(await png.arrayBuffer()));
const layout = await slide.export({format:'layout'});
await fs.writeFile(path.join(BUILD, 'final.layout.json'), await layout.text());
console.log(JSON.stringify({output:FINAL, replacements, slides:deck.slides.items.length}));
