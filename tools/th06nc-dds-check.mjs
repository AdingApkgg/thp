// Read-only retail texture census; publishes metadata, never original assets.
import {readFileSync,writeFileSync,openSync,readSync,closeSync,statSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {openPkgl} from '../shared/th06nc/pkgl.mjs';
import {readDds} from '../shared/th06nc/dds.mjs';
const root=new URL('../',import.meta.url),sha=b=>createHash('sha256').update(b).digest('hex');
const target=JSON.parse(readFileSync(new URL('runtimes/th06nc/target.json',root)));
if(sha(readFileSync(target.executable))!==target.sha256)throw Error('Executable changed');
const files=[],formats={};
for(const [name,ref]of Object.entries(target.dataArchives)){
 const fd=openSync(ref.path,'r');
 try{
  const size=statSync(ref.path).size;if(size!==ref.bytes)throw Error('Archive size changed');
  const archive=await openPkgl((o,n)=>{const b=Buffer.alloc(n);let done=0;while(done<n){const k=readSync(fd,b,done,n-done,o+done);if(!k)throw Error('Short archive read');done+=k;}return b;},size,name);
  for(const e of archive.entries){
   if(!e.name.toLowerCase().endsWith('.dds'))continue;
   const b=await archive.readEntry(e.index),r=readDds(b);
   formats[r.format]=(formats[r.format]??0)+1;
   files.push({archive:name,name:e.name,sha256:sha(b),width:r.width,height:r.height,format:r.format,colorSpace:r.colorSpace,levels:r.levels.map(l=>({width:l.width,height:l.height,bytes:l.data.length,sha256:sha(l.data)}))});
  }
  console.log(`${name}: textures loaded`);
 }finally{closeSync(fd);}
}
const report={scope:'Retail DDS parsing and BGRA conversion; BC7 blocks preserved, not decompressed. No GPU, rendered-pixel or gameplay equivalence claim.',executableSha256:target.sha256,readerSha256:sha(readFileSync(new URL('shared/th06nc/dds.mjs',root))),formats,count:files.length,completeGame:false,nativeEquivalent:false,files};
writeFileSync(new URL('docs/porting/th06nc-dds-verified.json',root),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({count:files.length,formats}));
