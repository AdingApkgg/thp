// Prepare script resources for the TH06nc port using its browser reader.
// Assets stay under ignored artifacts. Only verified metadata enters target.json.
import {readFileSync,writeFileSync,openSync,readSync,closeSync,mkdirSync} from 'node:fs';
import {resolve,dirname,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {openPkgl} from '../shared/th06nc/pkgl.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const targetPath=resolve(root,'runtimes/th06nc/target.json'),target=JSON.parse(readFileSync(targetPath,'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
if(sha(readFileSync(target.executable))!==target.sha256)throw Error('TH06nc executable changed');
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th06nc/pkgl-python.json'),'utf8'));
const result=JSON.parse(readFileSync(resolve(root,'artifacts/th06nc/pkgl-comparison.json'),'utf8'));
if(!result.passed||result.readerSha256!==sha(readFileSync(resolve(root,'shared/th06nc/pkgl.mjs'))))throw Error('run PKGL differential first');
const output=resolve(root,'runtimes/th06nc/artifacts/scripts');mkdirSync(output,{recursive:true});
const manifest=[],records={};
for(const reference of proof.archives){
 const path=resolve(dirname(target.executable),'data',reference.file),fd=openSync(path,'r');
 try{
  const readAt=(o,n)=>{const b=Buffer.alloc(n);let done=0;while(done<n){const k=readSync(fd,b,done,n-done,o+done);if(!k)throw Error('short read');done+=k;}return b;};
  const archive=await openPkgl(readAt,reference.bytes,reference.file);
  records[reference.file]={path:path.replaceAll('\\','/'),bytes:reference.bytes,format:'PKGL',entries:archive.entries.length};
  for(const entry of archive.entries){
   if(!/\.(ecl|anm|std|msgpack|json)$/i.test(entry.name))continue;
   const destination=resolve(output,reference.file,entry.name);
   if(!destination.startsWith(output+sep))throw Error('unsafe PKGL export path');
   const bytes=await archive.readEntry(entry.index);
   if(sha(bytes)!==reference.decoded[entry.index].sha256)throw Error('resource changed');
   mkdirSync(dirname(destination),{recursive:true});writeFileSync(destination,bytes);
   manifest.push({archive:reference.file,name:entry.name,bytes:bytes.length,sha256:sha(bytes),path:destination});
  }
 }finally{closeSync(fd);}
}
target.dataArchives=records;
target.resourceReader='shared/th06nc/pkgl.mjs';
target.blockers=['PKGL resource reader verified; x64 gameplay, ECL/ANM semantics, DDS rendering and custom audio containers still require porting and acceptance.'];
writeFileSync(targetPath,JSON.stringify(target,null,2)+'\n');
writeFileSync(resolve(root,'artifacts/th06nc/scripts.json'),JSON.stringify(manifest,null,2)+'\n');
console.log(`Prepared ${manifest.length} scripts and recorded ${Object.keys(records).length} PKGL archives.`);
