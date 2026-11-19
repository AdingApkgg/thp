import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {openPkgl} from '../shared/th06nc/pkgl.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex'),target=JSON.parse(readFileSync('runtimes/th06nc/target.json')),evidence=JSON.parse(readFileSync('artifacts/th06nc/pkgl-python.json'));
if(sha(readFileSync(target.executable))!==target.sha256)throw Error('TH06nc executable changed');
const archiveName='th06ST.dat',ref=target.dataArchives[archiveName],bytes=readFileSync(ref.path),archive=await openPkgl((o,n)=>bytes.subarray(o,o+n),bytes.length,archiveName),files=[],directory=resolve('runtimes/th06nc/artifacts/scripts',archiveName);mkdirSync(directory,{recursive:true});
for(let stage=1;stage<=7;stage++){
 const name=`msg${stage}.dat`,entry=archive.entries.find(e=>e.name===name);if(!entry)throw Error('Missing message resource');const raw=await archive.readEntry(entry.index),hash=sha(raw),expected=evidence.archives.find(a=>a.file===archiveName).decoded.find(e=>e.name===name);
 if(hash!==expected?.sha256)throw Error('Message resource differs from independent PKGL evidence');const path=resolve(directory,name);writeFileSync(path,raw);files.push({archive:archiveName,name,bytes:raw.length,sha256:hash,path});
}
writeFileSync('artifacts/th06nc/messages.json',JSON.stringify(files,null,2)+'\n');console.log(JSON.stringify({files:files.length,bytes:files.reduce((n,f)=>n+f.bytes,0),scope:'Original message resource intake only.'}));
