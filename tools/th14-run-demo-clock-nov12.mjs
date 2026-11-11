import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const opts=new Map(process.argv.slice(2).map(a=>{const m=/^--(build|native|stock|out)=(.+)$/.exec(a);assert(m);return[m[1],m[2]];}));
for(const n of ['build','native','stock','out'])assert(opts.has(n),n);
const root=process.cwd(),dir=resolve(opts.get('build')),out=resolve(opts.get('out'));
assert(!existsSync(out),'Choose a new output directory');mkdirSync(out,{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(readFileSync(p,'utf8'));
const build=load(resolve(dir,'build.json')),native=load(resolve(opts.get('native')));
for(const [p,h]of Object.entries(build.sourceBindings))assert.equal(sha(readFileSync(resolve(root,p))),h,p);
assert.equal(sha(readFileSync(resolve(root,build.fixturePath))),build.fixtureSha256);
for(const row of build.currentProviders)assert.equal(sha(readFileSync(row.object)),row.objectSha256);
const bytes=readFileSync(resolve(dir,'probe.wasm'));assert.equal(sha(bytes),build.wasmSha256);
const stock=resolve(opts.get('stock'));assert.equal(sha(readFileSync(resolve(stock,'th14.dat'))),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/stock':stock},returnOnExit:true}),env={memory};
for(const i of WebAssembly.Module.imports(module))if(i.module==='env'&&i.kind==='function')env[i.name]=()=>{throw Error('Unexpected platform service '+i.name);};
const instance=new WebAssembly.Instance(module,{env,wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const error=()=>{const b=new Uint8Array(memory.buffer),p=c.error();return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
assert.equal(c.open_stock(),1);const cases=[],failures=[];
for(const [index,input]of native.cases.entries()){
 assert.equal(c.begin(input.clock,input.frame,input.rate,+input.enabled),1,error());const rows=[];
 for(const [step,want]of input.timeline.entries()){
  assert.equal(c.tick(input.raw),1,error());const row=Array.from(new Uint32Array(memory.buffer,c.data(),12));rows.push(row);
  if(row[1]!==1)failures.push({index,step,field:'same-pass-stage',want:1,actual:row[1]});
  if(JSON.stringify(row.slice(4,8))!==JSON.stringify(want.timerWords))failures.push({index,step,field:'control-timer',want:want.timerWords,actual:row.slice(4,8)});
  if(row[8]!==want.fades.length)failures.push({index,step,field:'fade-factory-calls',want:want.fades.length,actual:row[8]});
  if(row[8]&&JSON.stringify(row.slice(9,12))!==JSON.stringify([60,0,48]))failures.push({index,step,field:'fade-parameters',actual:row.slice(9,12)});
  // Supervisor consumes the request on its next pass; never keep running a
  // frozen-clock native timeline after the C++ owner correctly retires.
  if(want.transition){assert.equal(c.tick(0),1,error());const next=Array.from(new Uint32Array(memory.buffer,c.data(),12));rows.push(next);if(next[1]!==0)failures.push({index,step,field:'next-pass-title',want:0,actual:next[1]});break;}
 }
 cases.push({index,input,timeline:rows});c.close_session();
}
const report={passed:failures.length===0,cases,failures,wasmSha256:build.wasmSha256,buildSha256:sha(readFileSync(resolve(dir,'build.json'))),nativeSha256:sha(readFileSync(resolve(opts.get('native')))),runnerSha256:sha(readFileSync(import.meta.filename)),actualGameSession:true,realStockDemoReplay:true,fixtureClocksAndRateDeclared:true,noAudioOrGraphicsDeviceOpened:true,completeGame:false};
writeFileSync(resolve(out,'result.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:report.passed,cases:cases.length,failures:failures.length}));if(failures.length){console.log(JSON.stringify(failures.slice(0,8)));process.exitCode=1;}
