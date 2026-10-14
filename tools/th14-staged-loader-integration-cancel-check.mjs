// Real private resource/Battle/ANM cancellation under declared waiting tickets.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),revision=process.env.TH14_STAGED_REVISION||'',home=resolve(root,'artifacts/th14/staged-loader-integration-oct14',revision||'.'),sha=b=>createHash('sha256').update(b).digest('hex');
const buildBytes=readFileSync(resolve(home,'private-build.json')),build=JSON.parse(buildBytes),rt=resolve(home,revision?'source/runtimes/th12/th12_web':'private/runtimes/th12/th12_web'),bytes=readFileSync(resolve(home,'staged-loader-integration.wasm'));assert.equal(sha(bytes),build.wasmSha256);
for(const [p,h] of Object.entries(build.privateSourceHashes))assert.equal(sha(readFileSync(resolve(rt,p))),h,p);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);
const cases=[];
for(let i=0;i<8;i++){
 const pointer=c.integration_cancel_case(i),words=Array.from(new Uint32Array(c.memory.buffer,pointer,16)),scenario=i%4,hud=scenario===0||scenario===2;
 const expected=[1,1,1,scenario>=2?0:1,scenario===0?3:scenario===1?5:8,hud?0:1,1,1,1,hud?1:7,1,1,1,1,0,i<4?4:2];
 if(JSON.stringify(words)!==JSON.stringify(expected)){const p=c.error(),data=new Uint8Array(c.memory.buffer);console.log(JSON.stringify({scenario:i,words,expected,error:new TextDecoder().decode(data.subarray(p,data.indexOf(0,p)))}));}
 assert.deepEqual(words,expected,'Cancellation scenario '+i);cases.push({restart:i<4?'direct stage3 replacement':'fresh begin stage1',waitingPhase:scenario===0?'Hud':scenario===1?'Timeline':scenario===2?'HUD prepare failure':'Timeline prepare failure',words});
}
const report={privateCancellationVerified:true,productionChanged:false,productionVerified:false,nativeEquivalent:false,completeGame:false,cases,sourceBuildSha256:sha(buildBytes),privateSourceHashes:build.privateSourceHashes,wasmSha256:sha(bytes),archiveSha256:sha(archive),toolSha256:sha(readFileSync(import.meta.filename)),scope:'Actual private GameSession/Battle/ANM/resource replacement runs on original DAT resources, with explicitly declared headless pending prepare references for HUD and already-published Timeline and partial first-HUD/Timeline preparation failures. Eight valid direct stage3 replacements/fresh begin stage1 restarts cancel the actual phase owner after all ANM retirement, clear held reference, and accept the next stage request. Repeating already-recorded stage1 through direct start_stage retains its old Recorder rejection; the earlier failure is not changed into a pass. The waiting GPU ticket is a controlled unit dependency, not Native host/GPU execution. No forced progression or clear proof.'};
writeFileSync(resolve(home,'cancellation-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({privateCancellationVerified:true,cases:cases.length}));
