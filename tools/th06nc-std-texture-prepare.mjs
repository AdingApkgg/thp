import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {openPkgl} from '../shared/th06nc/pkgl.mjs';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {stageEffectAssetPlan} from '../shared/th06nc/common-layout.mjs';
import {stdAssetPlan} from '../shared/th06nc/std-state.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex'),target=JSON.parse(readFileSync('runtimes/th06nc/target.json')),evidence=JSON.parse(readFileSync('docs/porting/th06nc-dds-verified.json')),requests=new Map(),archives=new Map(),files=[];if(sha(readFileSync(target.executable))!==target.sha256)throw Error('TH06nc executable changed');mkdirSync('runtimes/th06nc/artifacts/textures',{recursive:true});
for(let stage=1;stage<=7;stage++)for(const ref of [stdAssetPlan(stage),stageEffectAssetPlan(stage)]){const resource=readAnm(readFileSync(`runtimes/th06nc/artifacts/scripts/${ref.archive}/${ref.file}`));if(resource.textureName==='@')continue;const file=resource.textureName.split('/').at(-1).replace(/\.png$/,'.dds');requests.set(ref.archive+'/'+file,{archive:ref.archive,file});}
for(const ref of requests.values()){
 if(!archives.has(ref.archive)){const bytes=readFileSync(target.dataArchives[ref.archive].path);archives.set(ref.archive,await openPkgl((o,n)=>bytes.subarray(o,o+n),bytes.length,ref.archive));}const archive=archives.get(ref.archive),entry=archive.entries.find(e=>e.name===ref.file);if(!entry)throw Error('Missing STD texture');const raw=await archive.readEntry(entry.index),hash=sha(raw),expected=evidence.files.find(f=>f.archive===ref.archive&&f.name===ref.file);if(hash!==expected?.sha256)throw Error('STD texture changed');writeFileSync('runtimes/th06nc/artifacts/textures/'+ref.file,raw);files.push({...ref,bytes:raw.length,sha256:hash});
}
writeFileSync('runtimes/th06nc/artifacts/textures/std-manifest.json',JSON.stringify(files,null,2)+'\n');console.log(JSON.stringify({files:files.length,bytes:files.reduce((n,f)=>n+f.bytes,0),scope:'Original STD background texture intake, independent DDS hashes checked.'}));
