// Actual C++ selected-player ownership API consumes a real worker's packets.
import {readFile,writeFile} from 'node:fs/promises';
import {Worker} from 'node:worker_threads';
import {resolve} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {Th14WebGpuRuntime} from '../runtimes/th12/portable/sdl/Th14WebGpuRuntime.mjs';
const root=fileURLToPath(new URL('../',import.meta.url)),args=process.argv.slice(2);
assert.equal(args.length,4);assert.equal(args[0],'--build');assert.equal(args[2],'--fixture');
const buildHome=resolve(args[1]),home=resolve(args[3]),sha=b=>createHash('sha256').update(b).digest('hex');
const buildRaw=await readFile(resolve(buildHome,'build.json')),metadata=JSON.parse(await readFile(resolve(home,'build.json')));
assert.equal(sha(buildRaw),metadata.browserBuildSha256);
for(const [name,field]of [['resources.mjs','loaderSha256'],['resources.wasm','wasmSha256']])assert.equal(sha(await readFile(resolve(home,name))),metadata[field]);
const {default:createModule}=await import(pathToFileURL(resolve(home,'resources.mjs'))),module=await createModule();
const adapter=resolve(home,'node-message-adapter.mjs');await writeFile(adapter,`import {parentPort} from 'node:worker_threads';
globalThis.self={postMessage:(m,t)=>parentPort.postMessage(m,t),addEventListener:(_,accept)=>parentPort.on('message',data=>accept({data}))};
await import(${JSON.stringify(pathToFileURL(resolve(buildHome,'Th14ArchiveDecodeWorker.mjs')).href)});`,{flag:'wx'});
let invoke=()=>{},worker,report,pointer=0;const rows=[];
const runtime=new Th14WebGpuRuntime({ccall:()=>invoke()},{createArchiveWorker:()=>worker=new Worker(pathToFileURL(adapter),{type:'module'})});module.th14WebGpuRuntime=runtime;
const deadline=setTimeout(()=>{void worker?.terminate();},60000);let copies=0;
const copy=runtime.archiveAnmCopy.bind(runtime);runtime.archiveAnmCopy=(name,bytes)=>{const result=copy(name,bytes);if(result===1)++copies;return result;};
const name=selection=>module.UTF8ToString(module._fixture_name(selection));
function select(selection){assert.equal(module._fixture_select(selection),1,module.UTF8ToString(module._fixture_error()));assert.equal(module._fixture_empty(),1,'Selection must not parse on the caller');}
async function deliver(selection,expected=1){
  invoke=()=>{assert.equal(runtime.archiveStatus(),1);assert.equal(module._fixture_load(selection),expected,module.UTF8ToString(module._fixture_error()));};
  await runtime.scheduleArchive(1,selection,[name(selection)]).delivered;
  if(expected)assert.equal(module._fixture_compare(),1);else assert.equal(module._fixture_empty(),1);
}
try{
  const bytes=new Uint8Array(await readFile('H:/Games/th/14/th14.dat'));assert.equal(sha(bytes),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
  pointer=module._malloc(bytes.length);module.HEAPU8.set(bytes,pointer);assert.equal(module._fixture_open(pointer,bytes.length),1);
  runtime.openArchive(bytes);assert.equal(await runtime.archiveOpening,227);
  for(let selection=0;selection<6;++selection){
    select(selection);const before=copies;await deliver(selection);assert.equal(copies,before+1);
    assert.equal(module._fixture_load(selection),0,'Duplicate completion must lose ownership');assert.equal(copies,before+1);
    rows.push({selection,name:name(selection),allParsedFieldsAndBytesEqual:true,callerDidNotParse:true,duplicateRejected:true});
  }
  select(0);let before=copies;
  invoke=()=>{assert.equal(module._fixture_load(1),0);assert.equal(module._fixture_empty(),1);assert.equal(copies,before);};
  await runtime.scheduleArchive(1,0,[name(0)]).delivered;await deliver(0);
  select(2);module._fixture_cancel();before=copies;await deliver(2,0);assert.equal(copies,before);
  select(3);await deliver(3);
  select(4);select(5);before=copies;await deliver(4,0);assert.equal(copies,before);await deliver(5);
  select(0);const ordinaryCopy=runtime.archiveAnmCopy;
  invoke=()=>{
    runtime.archiveAnmCopy=(name,bytes)=>{const result=ordinaryCopy(name,bytes);if(result===1)bytes[bytes.length-1]^=1;return result;};
    try{assert.equal(module._fixture_load(0),0,'A malformed owned packet cannot fall back');assert.equal(module._fixture_empty(),1);}
    finally{runtime.archiveAnmCopy=ordinaryCopy;}
  };
  await runtime.scheduleArchive(1,0,[name(0)]).delivered;select(0);await deliver(0);
  select(2);invoke=()=>{assert.equal(runtime.archiveStatus(),0);assert.equal(module._fixture_load(2),0);assert.equal(module._fixture_empty(),1);};
  await runtime.scheduleArchive(1,0,['__missing__']).delivered;await deliver(2);
  assert.equal(copies,12);for(let selection=0;selection<6;++selection)assert.equal(module._fixture_sync(selection),1,'Synchronous consumer '+selection);
  assert.equal(copies,12);assert.equal(runtime.failure,null);
  report={passed:true,selectionCases:6,rows,validWorkerImports:11,corruptPacketImports:1,totalParsedCopies:copies,wrongOwnerRejectedWithoutCopy:true,cancelledOwnerRejectedWithoutCopy:true,replacedOwnerRejectedWithoutCopy:true,duplicateCompletionsRejected:6,failedBatchCannotFallback:true,corruptPacketCannotFallback:true,subsequentValidLoadsPassed:true,synchronousConsumerCases:6,actualProductionGameSessionResourcesObject:true,actualIndependentCpuWorker:true,actualApplicationControllerTest:false,noGraphicsOrAudioDevices:true,browserBuildSha256:sha(buildRaw),fixtureBuildSha256:sha(await readFile(resolve(home,'build.json'))),checkerSha256:sha(await readFile(fileURLToPath(import.meta.url))),completeGame:false,nativeEquivalent:false};
}catch(error){report={passed:false,error:String(error.stack??error),rows,copies,completeGame:false,nativeEquivalent:false};process.exitCode=1;}
finally{clearTimeout(deadline);runtime.archive?.close();if(pointer)module._free(pointer);}
await writeFile(resolve(home,'check.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(Object.fromEntries(Object.entries(report).filter(([name])=>name!=='rows'))));
