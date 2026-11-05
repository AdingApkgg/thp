// Private oracle input: reuse generated resources, replace only the browser's intact replay.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync,realpathSync,lstatSync,statfsSync,openSync,closeSync,unlinkSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
import {writeImmutableArtifact} from './th14-immutable-artifacts.mjs';

const root=resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex');
const home=resolve(root,'artifacts/th14/browser-recording-native-nov05');
const base=resolve(root,'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f');
const priorRaw=readFileSync(resolve(base,'manifest.json')),prior=JSON.parse(priorRaw);
assert.equal(sha(priorRaw),'6a130d1335f3fca6c810beca755128d915c57034622c13981a3133bd0654999c');
assert(prior.passed&&prior.entries===227&&prior.unchangedEntries===226);
const replay=resolve(root,'artifacts/th14/browser-new-recording-nov05/saved-slot02.rpy'),data=readFileSync(replay);
assert.equal(data.length,1240);assert.equal(sha(data),'ec04b9bea043c092e4f7b2fd18f379cb38419c5597ed7d640193fbefc344434a');
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json')));
const original=target.dataArchives['th14.dat'].path,originalHash=sha(readFileSync(original));
assert.equal(originalHash,'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
const out=resolve(root,'artifacts/th14/native-campaign-assets/57d84a5cbe82-ec04b9bea043'),entries=resolve(out,'entries');
assert(!existsSync(out),'Retain existing and partial variants');mkdirSync(entries,{recursive:true});mkdirSync(home,{recursive:true});
const budget=()=>{const s=statfsSync(out);assert(s.bavail*s.bsize>100*1024**3+1024**3,'Preserve 100GiB plus temporary headroom');};
budget();
const decoder=readFileSync(resolve(root,'runtimes/th12/th12_web/artifacts/cpp/game-core-test.wasm'));
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const {instance}=await WebAssembly.instantiate(decoder,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
function inventory(path){
 const bytes=readFileSync(path),p=c.allocate(bytes.length),a=c.archive_create();
 new Uint8Array(c.memory.buffer,p,bytes.length).set(bytes);assert.equal(c.archive_open(a,p,bytes.length,14),1);
 const rows=[];
 for(let i=0;i<c.archive_count(a);++i){
  const q=c.archive_name(a,i),memory=new Uint8Array(c.memory.buffer),name=new TextDecoder().decode(memory.subarray(q,memory.indexOf(0,q)));
  const size=c.archive_field(a,i,1),dest=c.allocate(size);assert.equal(c.archive_read(a,i,dest,size),size,name);
  rows.push({name,bytes:size,sha256:sha(new Uint8Array(c.memory.buffer,dest,size))});c.release(dest);
 }
 c.archive_delete(a);c.release(p);return rows;
}
const originals=inventory(original);assert.deepEqual(originals,prior.originalEntries);
assert.equal(originals.filter(x=>x.name==='demo0.rpy').length,1);
let sharedGeneratedFiles=0,sharedGeneratedBytes=0,smallCopiedBytes=0;
for(const row of new Map(originals.map(x=>[x.name,x])).values()){
 assert(/^[^/\\]+$/.test(row.name)&&row.name!=='.'&&row.name!=='..');
 if(row.name==='demo0.rpy'){writeFileSync(resolve(entries,row.name),data,{flag:'wx'});continue;}
 const source=resolve(base,'entries',row.name);assert(!lstatSync(source).isSymbolicLink());
 assert(realpathSync(source).startsWith(realpathSync(resolve(base,'entries'))));
 const bytes=readFileSync(source);assert.equal(bytes.length,row.bytes);assert.equal(sha(bytes),row.sha256,row.name);
 writeImmutableArtifact(resolve(entries,row.name),bytes);
 if(bytes.length>=1024*1024){++sharedGeneratedFiles;sharedGeneratedBytes+=bytes.length;}else smallCopiedBytes+=bytes.length;
}
budget();
const archive=resolve(out,'th14.dat'),log=openSync(resolve(home,'asset-compression.log'),'wx');
try{execFileSync(resolve(root,'tools/thtk/extracted/thtk-bin-12/thdat.exe'),['-c14',archive,...originals.map(x=>x.name)],
 {cwd:entries,stdio:['ignore',log,log],windowsHide:true,env:{...process.env,OMP_NUM_THREADS:'1'}});}finally{closeSync(log);}
const rebuilt=inventory(archive);assert.equal(rebuilt.length,227);
for(let i=0;i<227;i++){
 assert.equal(rebuilt[i].name,originals[i].name);
 assert.equal(rebuilt[i].sha256,originals[i].name==='demo0.rpy'?sha(data):originals[i].sha256);
 assert.equal(rebuilt[i].bytes,originals[i].name==='demo0.rpy'?data.length:originals[i].bytes);
}
const packed=readFileSync(archive);assert(lstatSync(archive).isFile()&&!lstatSync(archive).isSymbolicLink());
// This exact file was just generated here; retain its verified bytes as an immutable alias.
unlinkSync(archive);writeImmutableArtifact(archive,packed);assert.equal(sha(readFileSync(archive)),sha(packed));
assert.equal(sha(readFileSync(original)),originalHash);budget();
const report={passed:true,originalArchiveSha256:originalHash,referenceArchiveSha256:sha(packed),replayPath:replay,replaySha256:sha(data),
 entries:227,changedEntries:['demo0.rpy'],unchangedEntries:226,originalEntries:originals,rebuiltEntries:rebuilt,
 decoderSha256:sha(decoder),toolSha256:sha(readFileSync(import.meta.filename)),baseManifestSha256:sha(priorRaw),
 originalFilesNeverHardlinked:true,noArchiveExtractionPerformed:true,allOrdinalDecodedBytesVerified:true,
 independentRoundtripExtractionBytesVerified:false,sharedGeneratedFiles,sharedGeneratedBytes,smallCopiedBytes,
 generatedArchiveBytes:packed.length,minimumFreeBytes:100*1024**3,
 recordingOrigin:'Actual ordinary browser new recording, slot02 B, intact file',nativePlaybackAccepted:false,
 completeGame:false,nativeEquivalent:false};
writeFileSync(resolve(out,'manifest.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
writeFileSync(resolve(home,'asset-plan.json'),JSON.stringify({assetHome:out,manifestSha256:sha(Buffer.from(JSON.stringify(report,null,2)+'\n')),
 replayBytes:data.length,generatedArchiveBytes:packed.length,sharedGeneratedBytes,smallCopiedBytes,
 noArchiveExtractionPerformed:true,originalInputsUnchanged:true,nativeProcessNotYetRun:true,completeGame:false},null,2)+'\n');
console.log(JSON.stringify({prepared:true,assetHome:out,replayBytes:data.length,archiveBytes:packed.length,sharedGeneratedBytes,
 smallCopiedBytes,all226UnchangedEntriesVerified:true,noArchiveExtractionPerformed:true,nativePlaybackAccepted:false}));
