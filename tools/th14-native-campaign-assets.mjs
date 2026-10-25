// Private retail oracle archive: replace demo0 only, attest all other entries.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync,existsSync,statfsSync,lstatSync,realpathSync,unlinkSync} from 'node:fs';
import {resolve,dirname,relative,isAbsolute} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {writeImmutableArtifact} from './th14-immutable-artifacts.mjs';
const root=resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex');
const replay=resolve(root,process.argv[2]??'artifacts/th14/campaign-replay/reimu-a-normal-pools-handoff-oct11/campaign.rpy');
const data=readFileSync(replay);assert.equal(data.subarray(0,6).toString('hex'),'743133720200');
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),original=target.dataArchives['th14.dat'].path,originalHash=sha(readFileSync(original));
assert.equal(originalHash,'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
const out=resolve(root,'artifacts/th14/native-campaign-assets',originalHash.slice(0,12)+'-'+sha(data).slice(0,12)),entries=resolve(out,'entries'),verified=resolve(out,'roundtrip');
for(const dir of [entries,verified])mkdirSync(dir,{recursive:true});
const thdat=resolve(root,'tools/thtk/extracted/thtk-bin-12/thdat.exe'),archive=resolve(out,'th14.dat'),manifest=resolve(out,'manifest.json');
const minimumFree=100*1024**3;
function budget(phase,headroom=0){
 const disk=statfsSync(out),free=disk.bavail*disk.bsize;
 if(free<minimumFree+headroom){writeFileSync(resolve(out,'asset-storage-limit.json'),JSON.stringify({phase,freeBytes:free,minimumFreeBytes:minimumFree,reservedHeadroomBytes:headroom,originalInputsChanged:false})+'\n');throw new Error('TH14 asset preparation disk reserve exceeded');}
}
let sharedGeneratedFiles=0;
function verifyAndShare(folder,row){
 assert(/^[^/\\]+$/.test(row.name)&&row.name!=='.'&&row.name!=='..');const path=resolve(folder,row.name),rel=relative(out,path);
 assert(rel&&!rel.startsWith('..')&&!isAbsolute(rel));assert.equal(realpathSync(dirname(path)),resolve(dirname(path)));assert(lstatSync(path).isFile()&&!lstatSync(path).isSymbolicLink());
 const bytes=readFileSync(path);assert.equal(bytes.length,row.bytes);assert.equal(sha(bytes),row.sha256,row.name);
 // Only freshly generated, verified files are replaced by immutable aliases.
 // demo0 stays a private ordinary file so replacement cannot alter a cache.
 if(row.name!=='demo0.rpy'&&bytes.length>=1024*1024){unlinkSync(path);writeImmutableArtifact(path,bytes);assert.equal(sha(readFileSync(path)),row.sha256);++sharedGeneratedFiles;}
}
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
 assert(!existsSync(archive)&&readdirSync(entries).length===0&&readdirSync(verified).length===0,'Preserve partial attempts; use a fresh case directory');
 budget('before-original-extraction',1024**3);
 execFileSync(thdat,['-x14',original],{cwd:entries,stdio:'inherit',windowsHide:true,env:{...process.env,OMP_NUM_THREADS:'2'}});
 const originals=inventory(original),names=originals.map(r=>r.name);assert.equal(names.length,227);assert(names.includes('demo0.rpy'));
 // Retail contains se_cardget.wav twice. Verify both bytes, preserve both
 // ordinal entries, and never infer table count from extracted file count.
 for(const r of new Map(originals.map(row=>[row.name,row])).values())verifyAndShare(entries,r);
 writeFileSync(resolve(entries,'demo0.rpy'),data);
 // thdat parallel compression writes entries in completion order. A single
 // compression thread keeps the native ordinal table, including duplicates.
 budget('before-archive-compression',512*1024**2);
 execFileSync(thdat,['-c14',archive,...names],{cwd:entries,stdio:'inherit',windowsHide:true,env:{...process.env,OMP_NUM_THREADS:'1'}});
 budget('before-independent-roundtrip-extraction',512*1024**2);
 execFileSync(thdat,['-x14',archive],{cwd:verified,stdio:'inherit',windowsHide:true,env:{...process.env,OMP_NUM_THREADS:'2'}});
 assert.deepEqual(readdirSync(verified).sort(),[...new Set(names)].sort());
 const rebuilt=inventory(archive);assert.equal(rebuilt.length,originals.length);
 for(let i=0;i<originals.length;++i){assert.equal(rebuilt[i].name,originals[i].name);assert.equal(rebuilt[i].sha256,originals[i].name==='demo0.rpy'?sha(data):originals[i].sha256);}
 for(const r of new Map(rebuilt.map(row=>[row.name,row])).values())verifyAndShare(verified,r);
 budget('completed');
 const report={passed:true,completeGame:false,nativeEquivalent:false,originalArchiveSha256:originalHash,referenceArchiveSha256:sha(readFileSync(archive)),replayPath:replay,replaySha256:sha(data),entries:names.length,changedEntries:['demo0.rpy'],unchangedEntries:226,originalEntries:originals,rebuiltEntries:rebuilt,decoderSha256:sha(decoder),toolSha256:sha(readFileSync(import.meta.filename)),sharedGeneratedFiles,minimumFreeBytes:minimumFree,independentRoundtripExtractionBytesVerified:true,originalFilesNeverHardlinked:true,scope:'Private diagnostic archive rebuilt with thdat14: only demo0.rpy replaced by an intact input recording. Every other ordinal entry byte-for-byte unchanged after archive roundtrip, including both identical se_cardget.wav entries; table order preserved. Original and rebuilt thdat extractions are checked against decoded entry hashes. Large generated entries share immutable content; original archive is read-only and not hardlinked. Not a native playback success or full-game equivalence claim.'};
 writeFileSync(manifest,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,out,archive,unchangedEntries:226}));
}
