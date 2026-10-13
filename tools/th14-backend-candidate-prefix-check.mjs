// Diagnostic comparison against original-code emulator output. This input is
// not an independent real-process golden, and cannot certify native equivalence.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web');
const option=(name,fallback)=>{const i=process.argv.indexOf(name);return i<0?fallback:process.argv[i+1];};
const sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>readFileSync(resolve(root,p));
const receiptPath=resolve(root,option('--receipt','')),receiptBytes=readFileSync(receiptPath),receipt=JSON.parse(receiptBytes);
assert(receiptPath.startsWith(resolve(root,'artifacts/th14')+'/')||receiptPath.startsWith(resolve(root,'artifacts/th14')+'\\'));
assert.equal(receipt.completeGame,false);assert.equal(receipt.nativeEquivalent,false);assert.equal(receipt.stackRepairs,0);
assert.equal(sha(readFileSync(resolve(receiptPath,'../provider.py'))),receipt.sourceSha256);
const input=readFileSync(receipt.prefixCapture.file);assert.equal(sha(input),receipt.prefixCapture.sha256);
const rows=input.toString('utf8').trim().split('\n').map(x=>JSON.parse(x));assert.equal(rows.length,receipt.prefixCapture.capturedFrames);
const label=option('--label','backend-diagnostic');assert(/^[a-z0-9-]{1,64}$/.test(label));
const out=resolve(root,'artifacts/th14/backend-candidate-prefix',label);mkdirSync(out,{recursive:true});
const build=JSON.parse(read('runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'));
for(const [name,hash] of Object.entries(build.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,name))),hash,name);
const previous=JSON.parse(read('docs/porting/th14-natural-replay-native-trace-normal-bootstrap-3901-observed-oct13.json'));
const bytes=read('artifacts/th14/custom-replay-reference/normal-bootstrap-3901/reference.wasm');assert.equal(sha(bytes),previous.wasmSha256);
assert.equal(sha(readFileSync(resolve(rt,'tests/cpp/th14-custom-replay-reference-fixture.cpp'))),previous.fixtureSha256);
assert.equal(sha(readFileSync(resolve(rt,'tests/cpp/th14-session-reference-fixture.cpp'))),previous.includedFixtureSha256);
assert.deepEqual(build.sourceHashes,previous.engineBuild.sourceHashes);
const manifest=JSON.parse(read('artifacts/th14/native-campaign-assets/57d84a5cbe82-1dd45a2d2b0e/manifest.json'));
const replay=readFileSync(manifest.replayPath);assert.equal(sha(replay),manifest.replaySha256);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports,upload=b=>{const p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);return p;};
const target=JSON.parse(read('runtimes/th14/target.json')),archive=readFileSync(target.dataArchives['th14.dat'].path);
assert.equal(c.open_archive(upload(archive),archive.length),1);assert.equal(c.begin_custom_reference(upload(replay),replay.length),1);
const fields=previous.fieldNames,actualWords=[],expectedWords=[],counts={},first=[],visualFirst=[];
let gameplayDifferences=0,visualDifferences=0;
for(let i=0;i<rows.length;i++){
 const row=rows[i];assert.equal(row.index,i);assert.equal(row.stageFrame,i+1);assert.deepEqual(row.selection,[2,0,1,1]);
 assert.equal(c.tick(0),1);assert.equal(c.draw(),1);
 const actual=Array.from(new Uint32Array(c.memory.buffer,c.reference_data(),32)),g=row.globals,p=row.player;
 const expected=[row.stageFrame,row.held,row.pressed,...p.slice(0,9),g[2],g[6],g[9],g[12],g[15],g[16],g[18],g[19],g[5],row.scriptRng[0],row.scriptRng[2],row.replayRng[0],row.replayRng[2],row.enemyCount,row.shots,...row.selection,row.scaleFlags].map(x=>x>>>0);
 actualWords.push(...actual);expectedWords.push(...expected);
 for(let k=0;k<32;k++)if(actual[k]!==expected[k]){
  counts[fields[k]]=(counts[fields[k]]||0)+1;
  const record={frame:i+1,field:fields[k],port:actual[k],originalBackend:expected[k]};
  if(k===21||k===22){++visualDifferences;if(visualFirst.length<10)visualFirst.push(record);}
  else{++gameplayDifferences;if(first.length<30)first.push(record);}
 }
}
const portable=Buffer.from(new Uint32Array(actualWords).buffer),original=Buffer.from(new Uint32Array(expectedWords).buffer);
writeFileSync(resolve(out,'portable-state.u32'),portable);writeFileSync(resolve(out,'backend-state.u32'),original);
const report={passed:gameplayDifferences===0,diagnosticOnly:true,completeGame:false,nativeEquivalent:false,productionChanged:false,
 frames:rows.length,rawWords:rows.length*32,gameplayDifferences,retainedVisualDifferences:visualDifferences,fieldDifferences:counts,firstDifferences:first,firstVisualDifferences:visualFirst,
 receiptPath,receiptSha256:sha(receiptBytes),backendRowsSha256:sha(input),providerSha256:receipt.sourceSha256,modeInitialization:receipt.modeInitialization,
 portableStateSha256:sha(portable),backendStateSha256:sha(original),wasmSha256:sha(bytes),sourceHashes:build.sourceHashes,
 toolSha256:sha(readFileSync(import.meta.filename)),replaySha256:sha(replay),
 scope:'Diagnostic production core versus explicit warm original-code backend prefix, retaining all 32 raw words. Visual RNG differences counted separately without reseeding. Emulator beyond its independent retail-verified prefix remains experimental; this comparison is not a real-process golden or fresh ordinary Replay/complete-game proof.'};
writeFileSync(resolve(out,'report.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({frames:report.frames,gameplayDifferences,visualDifferences,firstDifferences:first.slice(0,10)}));
if(!report.passed)process.exitCode=1;
