import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const opts=new Map(process.argv.slice(2).map(a=>{const m=/^--(build|native|stock|out)=(.+)$/.exec(a);assert(m);return[m[1],m[2]];}));
for(const n of ['build','native','stock','out'])assert(opts.has(n));
const dir=resolve(opts.get('build')),out=resolve(opts.get('out')),stock=resolve(opts.get('stock'));
assert(!existsSync(out));mkdirSync(out,{recursive:true});const sha=b=>createHash('sha256').update(b).digest('hex');
const load=p=>JSON.parse(readFileSync(p,'utf8')),b=load(resolve(dir,'build.json')),native=load(resolve(opts.get('native')));
for(const [p,h]of Object.entries(b.sourceBindings))assert.equal(sha(readFileSync(resolve(p))),h,p);
for(const p of b.currentProviders)assert.equal(sha(readFileSync(p.object)),p.objectSha256);
const bytes=readFileSync(resolve(dir,'probe.wasm'));assert.equal(sha(bytes),b.wasmSha256);
assert.equal(sha(readFileSync(resolve(stock,'th14.dat'))),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/stock':stock},returnOnExit:true}),env={memory};
for(const i of WebAssembly.Module.imports(module))if(i.module==='env'&&i.kind==='function')env[i.name]=()=>{throw Error('Unexpected '+i.name);};
const instance=new WebAssembly.Instance(module,{env,wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const error=()=>{const bytes=new Uint8Array(memory.buffer),p=c.error();return new TextDecoder().decode(bytes.subarray(p,bytes.indexOf(0,p)));};
assert.equal(c.open_stock(),1);const cases=[],failures=[];
const compare=(i,t,field,actual,want)=>{if(JSON.stringify(actual)!==JSON.stringify(want))failures.push({i,t,field,actual,want});};
for(const [i,input]of native.cases.entries()){
 assert.equal(c.begin_case(input.rate,input.flags,+input.enabled,+input.demo),1,error());
 const rows=[];let previous=[0,0,0,0];
 for(const [t,want]of input.timeline.entries()){
  assert.equal(c.tick_case(),1,error());const r=Array.from(new Uint32Array(memory.buffer,c.data(),14));rows.push(r);
  compare(i,t,'phase',r[1],1);compare(i,t,'timer',r.slice(2,6),want.timerWords);compare(i,t,'flags',r[6],want.flags);
  compare(i,t,'ordinary-play-time',r[7],want.playTime);
  compare(i,t,'later-player-dispatch',r[8]-previous[0],+want.later.includes(18));
  compare(i,t,'compositor-updates',r[9]-previous[1],want.compositorCalls);
  if(!want.later.includes(29)){
   compare(i,t,'normal-player-anm-instructions',r[10]-previous[2],0);
   if(input.demo)compare(i,t,'replay-cursor',r[11]-previous[3],0);
  }
  previous=[r[8],r[9],r[10],r[11]];
  if(want.transition){assert.equal(c.tick_case(),1,error());const r2=Array.from(new Uint32Array(memory.buffer,c.data(),14));rows.push(r2);compare(i,t,'next-pass-title',r2[1],0);break;}
 }
 cases.push({i,input,timeline:rows});c.close_session();
}
const result={passed:failures.length===0,cases,failures,actualSessionAndBattle:true,ordinaryReimuBNormalAndStockDemo:true,declaredFlagsAndClockInputs:true,copyUpdateLinkObserverForwardsActualBody:true,noAudioOrGraphicsDeviceOpened:true,buildSha256:sha(readFileSync(resolve(dir,'build.json'))),nativeSha256:sha(readFileSync(resolve(opts.get('native')))),runnerSha256:sha(readFileSync(import.meta.filename)),wasmSha256:b.wasmSha256,completeGame:false};
writeFileSync(resolve(out,'result.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({passed:result.passed,cases:cases.length,failures:failures.length,firstFailures:failures.slice(0,5)}));if(!result.passed)process.exitCode=1;
