import {readFileSync,readdirSync,writeFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {openPkgl} from '../shared/th06nc/pkgl.mjs';
import {localizedAssetName} from '../shared/th06nc/localized-asset.mjs';
const directory='runtimes/th06nc/artifacts/textures';
const language='zh-CN';
const target=JSON.parse(readFileSync('runtimes/th06nc/target.json'));
const native=JSON.parse(readFileSync('docs/porting/th06nc-dds-verified.json'));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
if(sha(readFileSync(target.executable))!==target.sha256)throw Error('Original executable changed');
const names=readdirSync(directory).filter(name=>name.endsWith('.dds'));
const archives=new Map(),selected=[];
for(const name of names){
 const localized=localizedAssetName(name,language);
 const matches=native.files.filter(file=>file.name===localized);
 if(!matches.length)continue;
 if(matches.some(file=>file.sha256!==matches[0].sha256))throw Error('Ambiguous localized texture '+localized);
 const expected=matches[0];
 if(!archives.has(expected.archive)){
  const raw=readFileSync(target.dataArchives[expected.archive].path);
  archives.set(expected.archive,await openPkgl((offset,length)=>raw.subarray(offset,offset+length),raw.length,expected.archive));
 }
 const archive=archives.get(expected.archive);
 const entry=archive.entries.find(entry=>entry.name===localized);
 if(!entry)throw Error('Localized texture missing '+localized);
 const raw=await archive.readEntry(entry.index);
 if(sha(raw)!==expected.sha256)throw Error('Localized texture differs from native DDS evidence '+localized);
 const path=directory+'/'+localized;
 if(existsSync(path)&&sha(readFileSync(path))!==expected.sha256)throw Error('Existing localized artifact differs '+localized);
 if(!existsSync(path))writeFileSync(path,raw);
 selected.push({base:name,name:localized,archive:expected.archive,bytes:raw.length,sha256:expected.sha256});
}
const entries=readdirSync(directory).filter(name=>name.endsWith('.dds')).map(name=>({name}));
writeFileSync(directory+'/localized-manifest.json',JSON.stringify({language,entries,selected},null,2)+'\n');
console.log(JSON.stringify({language,textures:selected.length,available:entries.length}));
