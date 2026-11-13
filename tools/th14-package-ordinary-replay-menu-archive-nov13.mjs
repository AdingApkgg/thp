// Reuse existing verified decoded entries; package one actually browser-recorded replay.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,linkSync,existsSync,statfsSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex');
const proofHome=resolve(root,'artifacts/th14/ordinary-replay-menu-nov13');
const replay=resolve(proofHome,'write-c0-s1-d1-v2/save/replay/th14_01.rpy'),data=readFileSync(replay),proof=JSON.parse(readFileSync(resolve(proofHome,'qualified.json')));
assert.equal(sha(data),proof.encodedSha256);assert.equal(proof.recordedFrames,344);
const source=resolve(root,'artifacts/th14/native-campaign-assets/57d84a5cbe82-1d1b7da60739');
const prior=JSON.parse(readFileSync(resolve(source,'manifest.json')));
assert(prior.passed&&prior.unchangedEntries===226&&prior.changedEntries.join(',')==='demo0.rpy');
const out=resolve(root,'artifacts/th14/native-campaign-assets/57d84a5cbe82-'+sha(data).slice(0,12));
assert(!existsSync(out));assert(statfsSync(root,{bigint:true}).bavail*statfsSync(root,{bigint:true}).bsize>=101n*1024n**3n);
const entries=resolve(out,'entries');mkdirSync(entries,{recursive:true});
for(const row of new Map(prior.originalEntries.map(r=>[r.name,r])).values()){
 assert(/^[^/\\]+$/.test(row.name));
 if(row.name==='demo0.rpy'){writeFileSync(resolve(entries,row.name),data);continue;}
 const path=resolve(source,'entries',row.name),bytes=readFileSync(path);
 assert.equal(bytes.length,row.bytes);assert.equal(sha(bytes),row.sha256);
 linkSync(path,resolve(entries,row.name));
}
const archive=resolve(out,'th14.dat'),names=prior.originalEntries.map(r=>r.name);
execFileSync(resolve(root,'tools/thtk/extracted/thtk-bin-12/thdat.exe'),['-c14',archive,...names],
 {cwd:entries,stdio:'pipe',windowsHide:true,env:{...process.env,OMP_NUM_THREADS:'1'}});
const decoder=readFileSync(resolve(root,'runtimes/th12/th12_web/artifacts/cpp/game-core-test.wasm'));
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const {instance}=await WebAssembly.instantiate(decoder,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports,bytes=readFileSync(archive),p=c.allocate(bytes.length),a=c.archive_create();
new Uint8Array(c.memory.buffer,p,bytes.length).set(bytes);assert.equal(c.archive_open(a,p,bytes.length,14),1);
assert.equal(c.archive_count(a),227);const rebuilt=[];
for(let i=0;i<227;i++){
 const q=c.archive_name(a,i),mem=new Uint8Array(c.memory.buffer),name=new TextDecoder().decode(mem.subarray(q,mem.indexOf(0,q)));
 const size=c.archive_field(a,i,1),dest=c.allocate(size);assert.equal(name,names[i]);
 assert.equal(c.archive_read(a,i,dest,size),size);const digest=sha(new Uint8Array(c.memory.buffer,dest,size));
 assert.equal(digest,name==='demo0.rpy'?sha(data):prior.originalEntries[i].sha256);
 rebuilt.push({name,bytes:size,sha256:digest});c.release(dest);
}
c.archive_delete(a);c.release(p);
const report={passed:true,originalArchiveSha256:prior.originalArchiveSha256,referenceArchiveSha256:sha(bytes),
 replayPath:replay,replaySha256:sha(data),entries:227,changedEntries:['demo0.rpy'],unchangedEntries:226,
 originalEntries:prior.originalEntries,rebuiltEntries:rebuilt,decoderSha256:sha(decoder),
 existingDecodedEntriesReused:true,newArchiveExtractions:0,duplicateOrdinalsPreserved:true,
 actualOrdinaryMenuRecordedInput:true,physicalNewArchiveBytes:bytes.length,toolSha256:sha(readFileSync(import.meta.filename)),
 nativePlaybackValidated:false,completeGame:false,nativeEquivalent:false};
writeFileSync(resolve(out,'manifest.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,out,archive,replaySha256:sha(data),bytes:bytes.length,newExtractions:0,completeGame:false}));
