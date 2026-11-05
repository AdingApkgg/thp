// Actual Node Worker entry + shared C++ Wasm allocation. No game assets.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {Worker} from 'node:worker_threads';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(process.argv[2]),out=resolve(process.argv[3]);
assert(home.startsWith(resolve(root,'artifacts/th14')+'/')||home.startsWith(resolve(root,'artifacts/th14')+'\\'));
assert(out.startsWith(resolve(root,'artifacts/th14')+'/')||out.startsWith(resolve(root,'artifacts/th14')+'\\'));
mkdirSync(out);
const sha=data=>createHash('sha256').update(data).digest('hex'),build=JSON.parse(readFileSync(resolve(home,'build.json')));
for(const [name,row]of Object.entries(build.sharedSceneModuleFiles))assert.equal(sha(readFileSync(resolve(home,name))),row.sha256);
const {Th14SharedSceneCopy,SceneCopyWords:w}=await import(pathToFileURL(resolve(home,'Th14SharedSceneCopy.mjs')));
const probe=resolve(root,'artifacts/th14/shared-scene-copy-nov05/compiler-probe-retry1');
const probeBuild=JSON.parse(readFileSync(resolve(probe,'build.json'))),bytes=readFileSync(resolve(probe,'probe.wasm'));
assert.equal(sha(bytes),probeBuild.wasmSha256);
const memory=new WebAssembly.Memory({initial:256,maximum:8192,shared:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});let cppSpawns=0;
const {instance}=await WebAssembly.instantiate(bytes,{env:{memory},wasi_snapshot_preview1:wasi.wasiImport,
 wasi:{'thread-spawn':()=>{++cppSpawns;throw new Error('Unexpected C++ thread spawn');}}});
wasi.initialize(instance);const c=instance.exports;assert.equal(c.exercise_cpp(),0x1234);
const readWord=(pointer,index)=>c.read_word(pointer,index)>>>0;
const source=c.allocate(300),destination=c.allocate(300);assert(source&&destination);
const layout=Array.from({length:75},(_,index)=>index*4),threads=[],errors=[],cases=[];
function createWorker(url){
 const worker=new Worker(`const {parentPort,workerData}=require('node:worker_threads');
 globalThis.self={postMessage:data=>parentPort.postMessage(data),close:()=>parentPort.close()};
 import(workerData.url).then(()=>parentPort.on('message',data=>self.onmessage({data})));`,{eval:true,workerData:{url:url.href}});
 const terminal=new Promise(resolve=>worker.on('exit',resolve));threads.push(terminal);
 const facade={onmessage:null,onerror:null,terminal,postMessage:data=>worker.postMessage(data),terminate:()=>worker.terminate()};
 worker.on('message',data=>facade.onmessage?.({data}));worker.on('error',error=>facade.onerror?.({message:String(error)}));return facade;
}
const reader=new Th14SharedSceneCopy({createWorker,onError:error=>errors.push(String(error))});
async function prepared(){assert(reader.prepare());const task=reader.current;let timeout;
 try{assert.equal(await Promise.race([task.prepared,new Promise((_,reject)=>{timeout=setTimeout(()=>reject(new Error('Worker preparation watchdog')),5000);})]),true);}
 finally{clearTimeout(timeout);}return task;
}
function fill(base){for(let index=0;index<75;++index)c.write_word(source,index,base+index);}
function assertSource(base){for(let index=0;index<75;++index)assert.equal(readWord(source,index),base+index);}
try{
 fill(0x1000);for(let index=0;index<75;++index)c.write_word(destination,index,0xabcdef00+index);
 const first=await prepared();assert([0,1].includes(reader.read(memory.buffer,source,layout,0,0)));
 await first.worker.terminal;assert.equal(reader.read(memory.buffer,source,layout,0,0),1);
 assert.equal(Atomics.load(first.state,w.copied),75);
 for(let index=0;index<75;++index){assert.equal(reader.value(index),0x1000+index);assert.equal(readWord(destination,index),0xabcdef00+index);}
 assertSource(0x1000);cases.push('worker reads C++ allocation; destination remains private');
 fill(0x2000);
 for(let index=0;index<75;++index){assert.equal(reader.value(index),0x1000+index);c.write_word(destination,index,reader.value(index));assert.equal(readWord(destination,index),0x1000+index);}
 cases.push('completed capture immutable; explicit main-thread C++ writeback');
 reader.cancel();const cancelled=await prepared();reader.cancel();
 assert.equal(Atomics.load(cancelled.state,w.command),1);assert.equal(Atomics.load(cancelled.state,w.copied),0);
 assert.equal(reader.read(memory.buffer,source,layout,0,0),2);cases.push('prepared task cancellation exposes no data');
 const successor=await prepared();cancelled.worker.onmessage({data:{generation:cancelled.generation,error:'stale error'}});
 assert.equal(reader.current,successor);assert.equal(successor.failed,false);assert.equal(Atomics.load(successor.state,w.status),0);
 cases.push('old worker messages cannot mutate successor');reader.cancel();
 await prepared();assert.equal(reader.read(new ArrayBuffer(300),source,layout,0,0),2);assert.throws(()=>reader.value(0));
 cases.push('unshared source rejected');reader.cancel();
 await prepared();assert.equal(reader.read(memory.buffer,memory.buffer.byteLength-296,layout,0,0),2);
 cases.push('source range rejected before capture');reader.cancel();
 await prepared();const duplicate=layout.slice();duplicate[74]=duplicate[0];
 assert.equal(reader.read(memory.buffer,source,duplicate,0,0),2);cases.push('duplicate camera offsets rejected');reader.cancel();
 const owner=await prepared();reader.read(memory.buffer,source,layout,0,0);await owner.worker.terminal;
 assert.equal(reader.read(memory.buffer,source+4,layout,0,0),2);
 Atomics.store(owner.state,w.status,2);assert.equal(reader.read(memory.buffer,source,layout,0,0),2);assert.throws(()=>reader.value(0));
 cases.push('owner-change failure remains failed after late ready');reader.cancel();assertSource(0x2000);
 assert.equal(errors.length,4);assert.equal(cppSpawns,0);
}finally{reader.cancel();c.release(source);c.release(destination);}
const exits=await Promise.all(threads);assert(exits.every(code=>Number.isInteger(code)));
const result={cases:cases.length,caseNames:cases,workersTerminal:exits.length,workerExitCodes:exits,
 expectedFailureReports:errors.length,actualCppSharedAllocation:true,actualWorkerEntry:true,
 perWordAcknowledgements:false,workerWritesCppDestination:false,gameSessionExecuted:false,
 originalSchedulingAccepted:false,completeGame:false,buildSha256:sha(readFileSync(resolve(home,'build.json'))),
 probeWasmSha256:sha(bytes),moduleBindings:build.sharedSceneModuleFiles,toolSha256:sha(readFileSync(import.meta.filename))};
writeFileSync(resolve(out,'verified.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({cases:cases.length,workersTerminal:exits.length,expectedFailureReports:errors.length,completeGame:false}));
