// Large generated TH14 assets share immutable content; paths and bytes stay intact.
import assert from'node:assert/strict';
import{existsSync,readFileSync,writeFileSync,mkdirSync,linkSync,chmodSync}from'node:fs';
import{resolve,dirname,relative,isAbsolute}from'node:path';
import{createHash}from'node:crypto';
const root=resolve(import.meta.dirname,'..'),cache=resolve(root,'artifacts/th14/shared-runtime-asset-cache'),verified=new Set();
const inside=(base,path)=>{const r=relative(base,path);return r!==''&&!r.startsWith('..')&&!isAbsolute(r);};
export function writeImmutableArtifact(path,bytes){
 path=resolve(path);assert(inside(resolve(root,'artifacts/th14'),path)||inside(resolve(root,'runtimes/th14/th14_web/artifacts'),path),'TH14 generated path required');assert(!existsSync(path));mkdirSync(dirname(path),{recursive:true});
 if(bytes.byteLength<1024*1024){writeFileSync(path,bytes,{flag:'wx'});return;}
 const digest=createHash('sha256').update(bytes).digest('hex'),canonical=resolve(cache,digest+'.bin');mkdirSync(cache,{recursive:true});
 if(!existsSync(canonical))writeFileSync(canonical,bytes,{flag:'wx'});
 if(!verified.has(digest)){assert.equal(createHash('sha256').update(readFileSync(canonical)).digest('hex'),digest);verified.add(digest);}
 chmodSync(canonical,0o444);linkSync(canonical,path);
}
