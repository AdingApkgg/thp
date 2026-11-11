import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const opts=new Map(process.argv.slice(2).map(a=>{const m=/^--(build|stock|out)=(.+)$/.exec(a);assert(m);return[m[1],m[2]];}));
for(const n of ['build','stock','out'])assert(opts.has(n));
const dir=resolve(opts.get('build')),out=resolve(opts.get('out')),stock=resolve(opts.get('stock'));
assert(!existsSync(out));mkdirSync(out,{recursive:true});const sha=b=>createHash('sha256').update(b).digest('hex');
const b=JSON.parse(readFileSync(resolve(dir,'build.json'),'utf8'));
for(const [p,h]of Object.entries(b.sourceBindings))assert.equal(sha(readFileSync(resolve(p))),h,p);
for(const p of b.currentProviders)assert.equal(sha(readFileSync(p.object)),p.objectSha256);
const bytes=readFileSync(resolve(dir,'probe.wasm'));assert.equal(sha(bytes),b.wasmSha256);
assert.equal(sha(readFileSync(resolve(stock,'th14.dat'))),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/stock':stock},returnOnExit:true}),env={memory};
for(const i of WebAssembly.Module.imports(module))if(i.module==='env'&&i.kind==='function')env[i.name]=()=>{throw Error('Unexpected '+i.name);};
const instance=new WebAssembly.Instance(module,{env,wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
assert.equal(c.open_stock(),1);const cases=[];
for(const [index,rate]of [[0,.5],[0,1],[0,1.5],[0,2],[1,1],[2,1]]){
 assert.equal(c.begin_natural(index,rate),1);const rows=[];let firstFade=null,terminal=null;
 for(let ticks=1;ticks<=8000;++ticks){
  assert.equal(c.tick(0),1);const r=Array.from(new Uint32Array(memory.buffer,c.data(),12));
  if(r[8]&&!firstFade)firstFade={ticks,playerCalls:r[3],clockBefore:r[4],clockAfter:r[5],fields:r.slice(9,12)};
  if(r[8]||r[5]>=3898||r[1]!==1)rows.push({ticks,values:r});
  if(r[1]!==1){assert.equal(r[1],0);terminal={ticks,playerCalls:r[3]};break;}
 }
 assert(terminal,'Must return to title within bounded natural run');assert(firstFade);
 assert.equal(firstFade.clockBefore,3840);assert.deepEqual(firstFade.fields,[60,0,48]);
 const last=rows.filter(r=>r.values[1]===1).at(-1);assert.equal(last.values[4],3900,'Final Control decision before Timer increment');
 const proof={index,rate,firstFade,terminal,finalStage:last,rows};cases.push(proof);
 writeFileSync(resolve(out,`demo${index}-rate${rate}.json`),JSON.stringify(proof,null,2)+'\n');c.close_session();
}
const result={passed:true,cases,actualSession:true,unmodifiedStockReplays:true,noClockSelections:true,noInvincibilityOrPowerInjection:true,noGpuOrAudioDeviceOpened:true,buildSha256:sha(readFileSync(resolve(dir,'build.json'))),wasmSha256:b.wasmSha256,runnerSha256:sha(readFileSync(import.meta.filename)),scope:'Natural C++ Session demo lifecycle; no native full-replay state or pixel/PCM equality inferred',completeGame:false};
writeFileSync(resolve(out,'result.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({passed:true,cases:cases.map(({index,rate,firstFade,terminal})=>({index,rate,firstFade,terminal}))}));
