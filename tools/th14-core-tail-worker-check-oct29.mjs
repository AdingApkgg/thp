// Production core jobs with a real independent archive/ANM/ECL worker.
import {readFile,writeFile} from 'node:fs/promises';
import {Worker} from 'node:worker_threads';
import {resolve} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {Th14WebGpuRuntime} from '../runtimes/th12/portable/sdl/Th14WebGpuRuntime.mjs';
const args=process.argv.slice(2);assert.equal(args.length,4);assert.equal(args[0],'--build');assert.equal(args[2],'--fixture');
const build=resolve(args[1]),home=resolve(args[3]),sha=b=>createHash('sha256').update(b).digest('hex');
const buildRaw=await readFile(resolve(build,'build.json')),fixtureRaw=await readFile(resolve(home,'build.json')),fixture=JSON.parse(fixtureRaw);
assert.equal(fixture.browserBuildSha256,sha(buildRaw));
for(const [name,key]of [['resources.mjs','loaderSha256'],['resources.wasm','wasmSha256']])assert.equal(sha(await readFile(resolve(home,name))),fixture[key]);
const {default:createModule}=await import(pathToFileURL(resolve(home,'resources.mjs'))),module=await createModule();
const adapter=resolve(home,'node-message-adapter.mjs');await writeFile(adapter,`import {parentPort} from 'node:worker_threads';
globalThis.self={postMessage:(m,t)=>parentPort.postMessage(m,t),addEventListener:(_,accept)=>parentPort.on('message',data=>accept({data}))};
await import(${JSON.stringify(pathToFileURL(resolve(build,'Th14ArchiveDecodeWorker.mjs')).href)});`,{flag:'wx'});
let invoke=()=>{},worker,pointer=0,report;const rows=[],copies={raw:0,anm:0,ecl:0};
const runtime=new Th14WebGpuRuntime({ccall:()=>invoke()},{createArchiveWorker:()=>worker=new Worker(pathToFileURL(adapter),{type:'module'})});module.th14WebGpuRuntime=runtime;
for(const [method,kind]of [['archiveCopy','raw'],['archiveAnmCopy','anm'],['archiveParsedCopy','ecl']]){
    const copy=runtime[method].bind(runtime);runtime[method]=(...args)=>{const result=copy(...args);if(result===1)++copies[kind];return result;};
}
const jobs=[{index:3,names:['enemy.anm']},{index:6,names:['pl00.anm','pl00a.sht','pl00b.sht']},{index:7,names:['pl01.anm','pl01a.sht','pl01b.sht']},{index:8,names:['pl02.anm','pl02a.sht','pl02b.sht','default.ecl']}];
const deadline=setTimeout(()=>void worker?.terminate(),60000);
async function deliver(job){invoke=()=>{assert.equal(runtime.archiveStatus(),1);assert.equal(module._fixture_load(job.index),1,module.UTF8ToString(module._fixture_error()));};await runtime.scheduleArchive(1,job.index,job.names).delivered;}
try{
    const bytes=new Uint8Array(await readFile('H:/Games/th/14/th14.dat'));assert.equal(sha(bytes),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
    pointer=module._malloc(bytes.length);module.HEAPU8.set(bytes,pointer);assert.equal(module._fixture_open(pointer,bytes.length),1);assert.equal(module._fixture_empty(),1);
    runtime.openArchive(bytes);assert.equal(await runtime.archiveOpening,227);
    assert.equal(module._fixture_load(9),0);assert.equal(module._fixture_empty(),1);
    for(const job of jobs){await deliver(job);const before={...copies};assert.equal(module._fixture_load(job.index),1);assert.deepEqual(copies,before);rows.push({...job,duplicateDoesNotRead:true});}
    assert.equal(module._fixture_compare(),1);assert.deepEqual(copies,{raw:6,anm:4,ecl:1});
    assert.equal(module._fixture_reset(),1);assert.equal(module._fixture_empty(),1);
    const before={...copies};invoke=()=>{assert.equal(runtime.archiveStatus(),0);assert.equal(module._fixture_load(3),0);assert.equal(module._fixture_empty(),1);};
    await runtime.scheduleArchive(1,0,['__missing__']).delivered;assert.deepEqual(copies,before);
    const original=runtime.archiveAnmCopy;invoke=()=>{
        runtime.archiveAnmCopy=(name,bytes)=>{const result=original(name,bytes);if(result===1)bytes[bytes.length-1]^=1;return result;};
        try{assert.equal(module._fixture_load(3),0);assert.equal(module._fixture_empty(),1);}finally{runtime.archiveAnmCopy=original;}
    };await runtime.scheduleArchive(1,0,['enemy.anm']).delivered;
    assert.equal(module._fixture_reset(),1);for(const job of jobs)await deliver(job);assert.equal(module._fixture_compare(),1);assert.equal(runtime.failure,null);
    assert.deepEqual(copies,{raw:12,anm:9,ecl:2});
    report={passed:true,rows,actualProductionCoreOwner:true,actualIndependentCpuWorker:true,allCoreAnmAndShtFieldsAndEclDefinitionsEqual:true,validCoreBatches:8,rawShtCopies:12,parsedAnmCopies:9,parsedEclCopies:2,invalidJobRejected:true,duplicateJobsDoNotRead:true,failedBatchCannotFallback:true,corruptPacketCannotFallback:true,subsequentValidCoreLoadsPassed:true,shotParsingRemainsOnMainConsumer:true,actualApplicationControllerTest:false,browserBuildSha256:sha(buildRaw),fixtureBuildSha256:sha(fixtureRaw),checkerSha256:sha(await readFile(fileURLToPath(import.meta.url))),completeGame:false,nativeEquivalent:false};
}catch(error){report={passed:false,error:String(error.stack??error),rows,copies,completeGame:false,nativeEquivalent:false};process.exitCode=1;}
finally{clearTimeout(deadline);runtime.archive?.close();if(pointer)module._free(pointer);}
await writeFile(resolve(home,'check.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(Object.fromEntries(Object.entries(report).filter(([key])=>key!=='rows'))));
