import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/player-initialization-oracle-nov13/timer-oracle');
const sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>readFileSync(p),load=p=>JSON.parse(read(p));
const native=load(resolve(home,'native.json')),build=load(resolve(home,'build.json')),results={};
assert(native.originalNullPageUnmapped&&native.originalCodeUnmodified);
assert.equal(sha(read(resolve(root,'tools/th14-null-rate-timer-oracle-nov13.py'))),native.toolSha256);
for(const name of ['baseline','candidate']){
 const bytes=read(resolve(home,name+'.wasm'));assert.equal(sha(bytes),build[name].wasmSha256);
 const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{},returnOnExit:true});
 const instance=new WebAssembly.Instance(module,{env:{memory},wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
 const cases=[];let words=0;
 for(const [index,row]of native.rows.entries())for(const guard of [0,0x3e800000,0x3f800000,0x7fc01234]){
  new Uint32Array(memory.buffer,0,1)[0]=guard;
  let actual=null,error=null;
  try{const p=instance.exports.tick(row.current,row.fraction,row.flags,row.rate===null?0:1,row.rate??0);actual=Array.from(new Uint32Array(memory.buffer,p,5));}catch(e){error=String(e);}
  const differences=actual?actual.flatMap((v,i)=>v===row.expected[i]?[]:[{field:i,native:row.expected[i],cpp:v}]):[];
  words+=5;cases.push({index,nullRate:row.rate===null,guard,actual,error,differences});
 }
 results[name]={cases:cases.length,words,failedCases:cases.filter(c=>c.error||c.differences.length).length,
  liveRateFailedCases:cases.filter(c=>!c.nullRate&&(c.error||c.differences.length)).length,
  differences:cases.filter(c=>c.error||c.differences.length)};
}
assert(results.baseline.failedCases>0);assert.equal(results.baseline.liveRateFailedCases,0);
const report={passed:results.candidate.failedCases===0,results,nativeCases:native.rows.length,
 sentinelValuesAtWasmAddressZero:4,originalNullPageUnmapped:true,
 originalTimerTickCompared:true,timerAdvanceCompared:false,graphicsOrAudioDevicesOpened:0,completeGame:false,
 bindings:{native:sha(read(resolve(home,'native.json'))),build:sha(read(resolve(home,'build.json'))),runner:sha(read(import.meta.filename))}};
writeFileSync(resolve(home,'result.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({...report,results:Object.fromEntries(Object.entries(results).map(([k,{differences,...r}])=>[k,{...r,first:differences.slice(0,3)}]))}));
if(!report.passed)process.exitCode=1;
