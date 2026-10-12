// Exercise browser-compatible readers against local original assets. This
// verifies archive structure and records decoded hashes, not gameplay fidelity.
import {openSync,readSync,closeSync,readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {openTfpk,openCg} from '../shared/tasofro/archives.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const output=resolve(root,'artifacts/tasofro');mkdirSync(output,{recursive:true});
const all=process.argv.includes('--verify-all');
for(const title of ['135','145','155','175']){
 const target=JSON.parse(readFileSync(resolve(root,`runtimes/th${title}/target.json`),'utf8'));
 const archives=[];
 for(const [file,record] of Object.entries(target.dataArchives)){
  // The local *c.pak files are translation overlays and can use different keys.
  // Default validation covers the original and official update archives.
  if(file===`th${title}c.pak`&&!process.argv.includes('--include-localized'))continue;
  const fd=openSync(record.path,'r');
  try{
   const readAt=(offset,length)=>{const b=Buffer.alloc(length);let done=0;
    while(done<length){const n=readSync(fd,b,done,length-done,offset+done);if(!n)throw Error('short read');done+=n;}return b;};
   const archive=await(title==='175'?openCg:openTfpk)(readAt,record.bytes);
   const indices=all?archive.entries.map(e=>e.index):[...new Set([0,1,2,Math.floor(archive.entries.length/2),archive.entries.length-1])];
   const decoded=[];
   for(const i of indices){const bytes=await archive.readEntry(i);decoded.push({index:i,bytes:bytes.length,
    sha256:createHash('sha256').update(bytes).digest('hex'),prefixHex:Buffer.from(bytes.subarray(0,64)).toString('hex')});}
   archives.push({file,format:archive.format,version:archive.version??null,entries:archive.entries.map(({key,...e})=>e),decoded});
   console.log(`th${title}/${file}: ${archive.entries.length} entries, decoded ${decoded.length}`);
  }finally{closeSync(fd);}
 }
 writeFileSync(resolve(output,`th${title}.json`),JSON.stringify({game:`th${title}`,readerSha256:
  createHash('sha256').update(readFileSync(resolve(root,'shared/tasofro/archives.mjs'))).digest('hex'),
  validation:'Directory bounds and decoded hashes; independent comparison is separate.',archives},null,2)+'\n');
}
