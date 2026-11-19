import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {openPkgl} from '../shared/th06nc/pkgl.mjs';
import {readFontAtlas} from '../shared/th06nc/font-atlas.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex'),target=JSON.parse(readFileSync('runtimes/th06nc/target.json')),evidence=JSON.parse(readFileSync('artifacts/th06nc/pkgl-python.json')),language=process.argv[2]??'all';
if(sha(readFileSync(target.executable))!==target.sha256)throw Error('TH06nc executable changed');const name='th06FN.dat',bytes=readFileSync(target.dataArchives[name].path),archive=await openPkgl((o,n)=>bytes.subarray(o,o+n),bytes.length,name),expected=new Map(evidence.archives.find(a=>a.file===name).decoded.map(e=>[e.name,e.sha256])),directory=resolve('runtimes/th06nc/artifacts/fonts'),fonts=[];mkdirSync(directory,{recursive:true});
for(const entry of archive.entries.filter(e=>e.name.endsWith('.json')&&(language==='all'||e.name.endsWith('_'+language+'.json')))){
 const stem=entry.name.slice(0,-5),files={};for(const file of [stem+'.json','advance_'+stem+'.txt',stem+'.dds']){const e=archive.entries.find(e=>e.name===file);if(!e){if(file.endsWith('.dds'))continue;throw Error('Missing font companion '+file);}const raw=await archive.readEntry(e.index),hash=sha(raw);if(hash!==expected.get(file))throw Error('Font resource differs from independent PKGL evidence');writeFileSync(resolve(directory,file),raw);files[file]={bytes:raw.length,sha256:hash};}
 const atlas=readFontAtlas(readFileSync(resolve(directory,stem+'.json'),'utf8'),readFileSync(resolve(directory,'advance_'+stem+'.txt'),'utf8'));fonts.push({stem,width:atlas.width,height:atlas.height,glyphs:atlas.glyphs.size,bitmapAvailable:Boolean(files[stem+'.dds']),files});
}
if(!fonts.length)throw Error('No font atlases for '+language);writeFileSync('artifacts/th06nc/fonts.json',JSON.stringify({language,fonts},null,2)+'\n');console.log(JSON.stringify({language,fonts:fonts.length,missingBitmaps:fonts.filter(f=>!f.bitmapAvailable).length,glyphs:fonts.reduce((n,f)=>n+f.glyphs,0),bytes:fonts.reduce((n,f)=>n+Object.values(f.files).reduce((n,f)=>n+f.bytes,0),0),scope:'Original font atlas intake and metadata only; layout/GPU separately verified. Missing bitmap companions are recorded explicitly.'}));
