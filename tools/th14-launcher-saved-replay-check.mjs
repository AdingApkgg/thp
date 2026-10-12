// Read a real browser-exported recording through the production C++ decoder.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex');
const proof=JSON.parse(readFileSync(resolve(root,'docs/porting/th14-custom-replay-native-extended-observed-oct11.json')));
assert.equal(proof.passed,true);
for(const [name,hash] of Object.entries(proof.engineBuild.sourceHashes))assert.equal(sha(readFileSync(resolve(root,'runtimes/th12/th12_web',name))),hash);
const wasmPath=resolve(root,'artifacts/th14/custom-replay-reference/extended/reference.wasm'),wasm=readFileSync(wasmPath);assert.equal(sha(wasm),proof.wasmSha256);
const replayPath=resolve(root,'artifacts/th14/launcher-saved-th14_01-oct11.rpy'),replay=readFileSync(replayPath),target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const upload=b=>{const p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);return p;};
assert.equal(c.open_archive(upload(archive),archive.length),1);assert.equal(c.begin_custom_reference(upload(replay),replay.length),1);
const checkpoints=[];let frames=0;
for(;frames<10000&&c.phase()===1;++frames){assert.equal(c.tick(0),1);assert.equal(c.draw(),1);if(frames%120===0)checkpoints.push({frame:frames+1,state:Array.from(new Uint32Array(c.memory.buffer,c.reference_data(),32))});}
assert(frames>0&&frames<10000);assert.equal(c.bullet_skipped_mask(),0);assert.equal(c.bullet_unsupported_native_mask(),0);
const report={passed:true,completeGame:false,nativeEquivalent:false,replayPath,replayBytes:replay.length,replaySha256:sha(replay),wasmPath,wasmSha256:sha(wasm),frames,phase:c.phase(),checkpoints,forcedInvulnerability:false,syntheticPower:false,scope:'Real normal-play browser recording saved through the original pause/name UI, persisted across Launcher reload, then exported by the Launcher. Production C++ ReplayFile decode and ordinary collision playback terminate without ECL/draw errors or unsupported bullet masks. Not retail-native equality or a complete campaign.'};
writeFileSync(resolve(root,'docs/porting/th14-launcher-saved-replay-observed-oct11.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,frames,phase:report.phase,bytes:replay.length,sha256:report.replaySha256}));
