// Private retail oracle archive: replace demo0 only, attest all other entries.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex');
const replay=resolve(root,process.argv[2]??'artifacts/th14/campaign-replay/reimu-a-normal-pools-handoff-oct11/campaign.rpy');
const data=readFileSync(replay);assert.equal(data.subarray(0,6).toString('hex'),'743133720200');
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),original=target.dataArchives['th14.dat'].path,originalHash=sha(readFileSync(original));
const out=resolve(root,'artifacts/th14/native-campaign-assets',originalHash.slice(0,12)+'-'+sha(data).slice(0,12)),entries=resolve(out,'entries'),verified=resolve(out,'roundtrip');
for(const dir of [entries,verified])mkdirSync(dir,{recursive:true});
const thdat=resolve(root,'tools/thtk/extracted/thtk-bin-12/thdat.exe'),archive=resolve(out,'th14.dat'),manifest=resolve(out,'manifest.json');
const decoder=readFileSync(resolve(root,'runtimes/th12/th12_web/artifacts/cpp/game-core-test.wasm'));
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(decoder,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
function inventory(path){
 const bytes=readFileSync(path),p=c.allocate(bytes.length),a=c.archive_create();new Uint8Array(c.memory.buffer,p,bytes.length).set(bytes);assert.equal(c.archive_open(a,p,bytes.length,14),1);
 const rows=[];
 for(let i=0;i<c.archive_count(a);++i){const q=c.archive_name(a,i),memory=new Uint8Array(c.memory.buffer),name=new TextDecoder().decode(memory.subarray(q,memory.indexOf(0,q))),size=c.archive_field(a,i,1),dest=c.allocate(size);
  assert.equal(c.archive_read(a,i,dest,size),size,name);rows.push({name,bytes:size,sha256:sha(new Uint8Array(c.memory.buffer,dest,size))});c.release(dest);
 }
 c.archive_delete(a);c.release(p);return rows;
}
if(existsSync(manifest)){
 const prior=JSON.parse(readFileSync(manifest));assert.equal(sha(readFileSync(archive)),prior.referenceArchiveSha256);assert.equal(sha(data),prior.replaySha256);assert.equal(originalHash,prior.originalArchiveSha256);
 console.log(JSON.stringify({passed:true,out,archive,reused:true}));
}else{
 execFileSync(thdat,['-x14',original],{cwd:entries,stdio:'inherit',windowsHide:true,env:{...process.env,OMP_NUM_THREADS:'2'}});
 const originals=inventory(original),names=originals.map(r=>r.name);assert.equal(names.length,227);assert(names.includes('demo0.rpy'));
 // Retail contains se_cardget.wav twice. Verify both bytes, preserve both
 // ordinal entries, and never infer table count from extracted file count.
 for(const r of originals){assert(/^[^/\\]+$/.test(r.name));assert.equal(sha(readFileSync(resolve(entries,r.name))),r.sha256,r.name);}
 writeFileSync(resolve(entries,'demo0.rpy'),data);
 // thdat parallel compression writes entries in completion order. A single
 // compression thread keeps the native ordinal table, including duplicates.
 execFileSync(thdat,['-c14',archive,...names],{cwd:entries,stdio:'inherit',windowsHide:true,env:{...process.env,OMP_NUM_THREADS:'1'}});
 execFileSync(thdat,['-x14',archive],{cwd:verified,stdio:'inherit',windowsHide:true,env:{...process.env,OMP_NUM_THREADS:'2'}});
 assert.deepEqual(readdirSync(verified).sort(),[...new Set(names)].sort());
 const rebuilt=inventory(archive);assert.equal(rebuilt.length,originals.length);
 for(let i=0;i<originals.length;++i){assert.equal(rebuilt[i].name,originals[i].name);assert.equal(rebuilt[i].sha256,originals[i].name==='demo0.rpy'?sha(data):originals[i].sha256);}
 const report={passed:true,completeGame:false,nativeEquivalent:false,originalArchiveSha256:originalHash,referenceArchiveSha256:sha(readFileSync(archive)),replayPath:replay,replaySha256:sha(data),entries:names.length,changedEntries:['demo0.rpy'],unchangedEntries:226,originalEntries:originals,rebuiltEntries:rebuilt,decoderSha256:sha(decoder),toolSha256:sha(readFileSync(import.meta.filename)),scope:'Private diagnostic archive rebuilt with thdat14: only demo0.rpy replaced by an intact port recording. Every other ordinal entry byte-for-byte unchanged after archive roundtrip, including both identical se_cardget.wav entries; table order preserved. Original archive is read-only. Not a native playback success or full-game equivalence claim.'};
 writeFileSync(manifest,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,out,archive,unchangedEntries:226}));
}
