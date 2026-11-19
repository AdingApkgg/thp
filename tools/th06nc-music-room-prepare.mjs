import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {openPkgl} from '../shared/th06nc/pkgl.mjs';
const sha=bytes=>createHash('sha256').update(bytes).digest('hex'),target=JSON.parse(readFileSync('runtimes/th06nc/target.json')),evidence=JSON.parse(readFileSync('docs/porting/th06nc-music-room-table-native-verified.json'));
if(!evidence.passed||evidence.executableSha256!==target.sha256||sha(readFileSync(target.executable))!==target.sha256)throw Error('TH06nc music table: native executable evidence missing or changed');
const name='th06MD.dat',bytes=readFileSync(target.dataArchives[name].path),archive=await openPkgl((offset,length)=>bytes.subarray(offset,offset+length),bytes.length,name),entry=archive.entries.find(entry=>entry.name==='musiccmt.txt');if(!entry)throw Error('TH06nc music table: archive entry missing');
const raw=await archive.readEntry(entry.index);if(sha(raw)!==evidence.inputSha256)throw Error('TH06nc music table: original content changed');const directory='runtimes/th06nc/artifacts/scripts/'+name;mkdirSync(directory,{recursive:true});writeFileSync(directory+'/musiccmt.txt',raw);
const manifest={archive:name,archiveSha256:sha(bytes),file:entry.name,bytes:raw.length,sha256:sha(raw),tracks:evidence.records.length,executableSha256:target.sha256};writeFileSync(directory+'/music-room-manifest.json',JSON.stringify(manifest,null,2)+'\n');console.log(JSON.stringify(manifest));
