import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {openPkgl} from '../shared/th06nc/pkgl.mjs';
import {soundFiles} from '../shared/th06nc/sound-queue.mjs';
const target=JSON.parse(readFileSync('runtimes/th06nc/target.json')),name='th06IN.dat',raw=readFileSync(target.dataArchives[name].path),archive=await openPkgl((offset,length)=>raw.subarray(offset,offset+length),raw.length,name),files=[];
mkdirSync('runtimes/th06nc/artifacts/audio',{recursive:true});
for(const file of soundFiles){const entry=archive.entries.find(entry=>entry.name===file);if(!entry)throw Error('Missing original sound '+file);const bytes=await archive.readEntry(entry.index);if(Buffer.from(bytes.subarray(0,4)).toString()!=='RIFF'||Buffer.from(bytes.subarray(8,12)).toString()!=='WAVE')throw Error('Invalid original WAV '+file);writeFileSync('runtimes/th06nc/artifacts/audio/'+file,bytes);files.push({archive:name,file,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});}
writeFileSync('runtimes/th06nc/artifacts/audio/sound-manifest.json',JSON.stringify(files,null,2)+'\n');console.log(JSON.stringify({files:files.length,bytes:files.reduce((n,file)=>n+file.bytes,0)}));
