import assert from 'node:assert/strict';
import{readFileSync,writeFileSync}from'node:fs';
import{resolve}from'node:path';
import{WASI}from'node:wasi';
import{createHash}from'node:crypto';
const root=resolve(import.meta.dirname,'..'),home=resolve(process.argv[2]);
const sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>readFileSync(resolve(home,p));
const buildRaw=read('build.json'),build=JSON.parse(buildRaw),nativeRaw=read('native.json'),native=JSON.parse(nativeRaw),wasm=read('component.wasm');
assert.equal(sha(wasm),build.wasmSha256);
for(const[p,digest]of Object.entries(build.sourceBindings))assert.equal(sha(readFileSync(resolve(root,p))),digest,p);
assert.equal(sha(readFileSync(resolve(root,'tools/th14-phased-shake-stack-native-nov02.py'))),native.toolSha256);
const wasi=new WASI({version:'preview1'}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const rows=native.cases.filter(r=>r.rngReturns.length);assert.equal(native.cases.length,2016);assert.equal(rows.length,480);
let wrongOffsetControls=0;
for(const[index,r]of rows.entries()){
 const pointer=c.stack_case(r.kind==='phased'?1:0,r.rate,r.seed,r.timer,r.prior);
 const actual=Array.from(new Uint32Array(c.memory.buffer,pointer,11)),expected=[r.stackWord,1,r.result,...r.rng,...r.timerWords,...r.offsetWords,1];
 assert.deepEqual(actual,expected,`current C++ producer ${index}`);
 if(r.kind==='phased'){assert.notEqual(r.neighborWord,r.stackWord);assert.equal(r.stackWord,r.rngReturns.at(-1).value&65535);++wrongOffsetControls;}
}
assert.equal(wrongOffsetControls,192);
const result={passed:true,nativeInstructionProfiles:2016,cppActiveRngProfiles:480,comparedWords:5280,differenceWords:0,
 wrongAdjacentStackOffsetControlsRejected:192,excludedInactiveProfiles:1536,
 inactiveProfileScope:'Original inactive cases are retained; C++ stack comparison here covers actual random draws. Retirement allocator addresses and full scheduler gating remain separate.',
 buildSha256:sha(buildRaw),nativeReportSha256:sha(nativeRaw),wasmSha256:sha(wasm),checkerSha256:sha(readFileSync(import.meta.filename)),
 actualOriginalNtdllLeaveExecuted:true,syntheticThreadAndUncontendedAcquisitionDeclared:true,
 actualControllerReaderExecuted:false,physicalAudioDevicesOpened:0,browserAcceptance:false,completeGame:false,nativeEquivalent:false};
writeFileSync(resolve(home,'verified.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
