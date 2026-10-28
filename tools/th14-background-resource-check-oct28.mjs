// Component test: actual browser GameResources.o consumes a real worker batch.
import {readFile,writeFile} from 'node:fs/promises';
import {Worker} from 'node:worker_threads';
import {resolve} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {Th14WebGpuRuntime} from '../runtimes/th12/portable/sdl/Th14WebGpuRuntime.mjs';
const root=fileURLToPath(new URL('../',import.meta.url)),args=process.argv.slice(2);
assert.equal(args.length,4);assert.equal(args[0],'--build');assert.equal(args[2],'--fixture');
const buildHome=resolve(args[1]),fixture=resolve(args[3]),sha=raw=>createHash('sha256').update(raw).digest('hex');
const metadata=JSON.parse(await readFile(resolve(fixture,'build.json'))),buildRaw=await readFile(resolve(buildHome,'build.json'));
assert.equal(sha(buildRaw),metadata.browserBuildSha256);
for(const [name,field] of [['resources.mjs','loaderSha256'],['resources.wasm','wasmSha256']])
  assert.equal(sha(await readFile(resolve(fixture,name))),metadata[field]);
const {default:createModule}=await import(pathToFileURL(resolve(fixture,'resources.mjs')));
const module=await createModule();let invoke=()=>{},worker;
const adapter=resolve(fixture,'node-message-adapter.mjs');
await writeFile(adapter,`import {parentPort} from 'node:worker_threads';
globalThis.self={postMessage:(m,t)=>parentPort.postMessage(m,t),addEventListener:(_,accept)=>parentPort.on('message',data=>accept({data}))};
await import(${JSON.stringify(pathToFileURL(resolve(buildHome,'Th14ArchiveDecodeWorker.mjs')).href)});`);
const runtime=new Th14WebGpuRuntime({ccall:()=>invoke()},{createArchiveWorker:()=>worker=new Worker(pathToFileURL(adapter),{type:'module'})});
module.th14WebGpuRuntime=runtime;
const deadline=setTimeout(()=>{void worker?.terminate();},60000);const rows=[];let report;
let cacheReads=0,cacheCopies=0,uncachedReads=0;
const size=runtime.archiveSize.bind(runtime),copy=runtime.archiveCopy.bind(runtime);
runtime.archiveSize=name=>{const result=size(name);if(result>=0)++cacheReads;else if(result===-1)++uncachedReads;return result;};
runtime.archiveCopy=(name,bytes)=>{const result=copy(name,bytes);if(result===1)++cacheCopies;return result;};
try {
  const bytes=new Uint8Array(await readFile('H:/Games/th/14/th14.dat'));
  assert.equal(sha(bytes),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
  const pointer=module._malloc(bytes.length);module.HEAPU8.set(bytes,pointer);
  assert.equal(module._fixture_open(pointer,bytes.length),1);
  runtime.openArchive(bytes);assert.equal(await runtime.archiveOpening,227);
  for(let stage=1;stage<=7;++stage)for(let selection=0;selection<6;++selection){
    assert.equal(module._fixture_prepare(stage,selection),1,module.UTF8ToString(module._fixture_error()));
    for(let step=0;step<8;++step){
      const names=module.UTF8ToString(module._fixture_names(step)).split('\n').filter(Boolean);
      invoke=()=>{assert.equal(runtime.archiveStatus(),1);assert.equal(module._fixture_step(step),1,`${stage}/${selection}/${step}: ${module.UTF8ToString(module._fixture_error())}`);};
      if(names.length)await runtime.scheduleArchive(1,step,names).delivered;else invoke();
    }
    assert.equal(module._fixture_compare(),1,`Decoded C++ values changed: ${stage}/${selection}`);
    assert.equal(runtime.archiveSize('st03enm.anm'),-1);
    rows.push({stage,selection,allParsedValuesAndBytesEqual:true});
  }
  const name=new TextEncoder().encode('st03.std\0'),namePointer=module._malloc(name.length);module.HEAPU8.set(name,namePointer);
  invoke=()=>{assert.equal(runtime.archiveStatus(),0);assert.equal(module._fixture_read(namePointer),0,'An errored batch must not silently decode synchronously');};
  await runtime.scheduleArchive(1,0,['__missing__']).delivered;
  assert.equal(module._fixture_read(namePointer),1,'Ordinary synchronous reads remain available outside a batch');
  assert(cacheReads>0);assert.equal(cacheCopies,cacheReads);assert.equal(runtime.failure,null);
  module._free(namePointer);module._free(pointer);
  report={passed:true,cases:rows.length,rows,actualProductionBrowserGameResourcesObject:true,
    actualIndependentCpuWorker:true,actualCxxParsedResourcesCompared:true,cacheReads,cacheCopies,uncachedReads,
    failedBatchCannotSilentlyFallback:true,synchronousReadOutsideBatchPassed:true,
    browserBuildSha256:sha(buildRaw),fixtureBuildSha256:sha(await readFile(resolve(fixture,'build.json'))),
    checkerSha256:sha(await readFile(fileURLToPath(import.meta.url))),
    noGraphicsOrAudioDevices:true,actualBrowserRun:false,completeGame:false,nativeEquivalent:false};
}catch(error){report={passed:false,error:String(error.stack??error),rows,cacheReads,cacheCopies,uncachedReads,completeGame:false,nativeEquivalent:false};process.exitCode=1;}
finally{clearTimeout(deadline);runtime.archive?.close();}
await writeFile(resolve(fixture,'check.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(Object.fromEntries(Object.entries(report).filter(([name])=>name!=='rows'))));
