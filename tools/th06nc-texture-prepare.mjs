// Export a small, hash-checked texture intake fixture. Original assets stay ignored.
import {readFileSync,writeFileSync,openSync,readSync,closeSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {openPkgl} from '../shared/th06nc/pkgl.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex');
const target=JSON.parse(readFileSync('runtimes/th06nc/target.json'));
const evidence=JSON.parse(readFileSync('docs/porting/th06nc-dds-verified.json'));
if(sha(readFileSync(target.executable))!==target.sha256)throw Error('Executable changed');
const out='runtimes/th06nc/artifacts/textures';mkdirSync(out,{recursive:true});
const requests=[['th06IN.dat','ascii.dds'],...['eff00','etama3','etama3_2','etama4','player00','player01'].map(n=>['th06CM.dat',n+'.dds']),...['title00','title01','title01s','title02','title03','title04','title04s','title05','title06','slpl00a','slpl00b','slpl01a','slpl01b','select00','select00b','select00c','select00e','select01','select02','select05','select03','select04','select06','select07'].map(n=>['th06TL.dat',n+'.dds'])],files=[];
for(const [name,file]of requests){
 const ref=target.dataArchives[name],fd=openSync(ref.path,'r');
 try{
  const archive=await openPkgl((o,n)=>{const b=Buffer.alloc(n);let done=0;while(done<n){const k=readSync(fd,b,done,n-done,o+done);if(!k)throw Error('Short read');done+=k;}return b;},ref.bytes,name);
  const entry=archive.entries.find(e=>e.name===file);if(!entry)throw Error('Missing texture');
  const b=await archive.readEntry(entry.index),hash=sha(b),expected=evidence.files.find(f=>f.archive===name&&f.name===file);
  if(hash!==expected.sha256)throw Error('Texture changed');
  writeFileSync(`${out}/${file}`,b);files.push({name:file,sha256:hash,format:expected.format,width:expected.width,height:expected.height});
 }finally{closeSync(fd);}
}
writeFileSync(`${out}/manifest.json`,JSON.stringify({scope:'Texture intake fixture only; not a title screen or game.',files},null,2)+'\n');
console.log(files);
