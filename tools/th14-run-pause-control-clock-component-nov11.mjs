import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const root=process.cwd(),home=resolve(root,'artifacts/th14/pause-control-clock-nov11');
const load=p=>JSON.parse(readFileSync(p)),sha=b=>createHash('sha256').update(b).digest('hex');
const build=load(resolve(home,'build.json')),results={};
for(const mode of ['baseline','candidate']){
 const bytes=readFileSync(resolve(home,mode+'.wasm'));assert.equal(sha(bytes),build.outputs[mode]);
 const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/stock':resolve(root,'artifacts/th14/node-gles-host-nov08/native-later/work')},returnOnExit:true});
 const env={memory};for(const i of WebAssembly.Module.imports(module))if(i.module==='env'&&i.kind==='function')env[i.name]=()=>{throw Error('Unexpected platform call '+i.name);};
 const instance=new WebAssembly.Instance(module,{env,wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);assert.equal(instance.exports.run(),10);
 const words=Array.from(new Uint32Array(memory.buffer,instance.exports.data(),60));results[mode]=Array.from({length:10},(_,n)=>words.slice(n*6,n*6+6));
}
writeFileSync(resolve(home,'cpp-results.json'),JSON.stringify({fields:['case','controlClock','physicalFrame','paused','menuExists','updateSucceeded'],...results},null,2)+'\n');
console.log(JSON.stringify({completed:true,casesPerMode:10,baselinePaused:results.baseline.map(r=>r[3]),candidatePaused:results.candidate.map(r=>r[3]),noAudioDevice:true}));
