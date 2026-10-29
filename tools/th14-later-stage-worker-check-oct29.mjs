// Real production stage owner/controller, CPU worker, and C++ packet importers.
import {readFile,writeFile} from 'node:fs/promises';
import {Worker} from 'node:worker_threads';
import {resolve} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {Th14WebGpuRuntime} from '../runtimes/th12/portable/sdl/Th14WebGpuRuntime.mjs';
const args=process.argv.slice(2);assert.deepEqual([args[0],args[2]],['--build','--fixture']);assert.equal(args.length,4);
const build=resolve(args[1]),home=resolve(args[3]),sha=b=>createHash('sha256').update(b).digest('hex');
const buildRaw=await readFile(resolve(build,'build.json')),fixtureRaw=await readFile(resolve(home,'build.json')),fixture=JSON.parse(fixtureRaw);
assert.equal(fixture.browserBuildSha256,sha(buildRaw));
for(const [name,key]of [['resources.mjs','loaderSha256'],['resources.wasm','wasmSha256']])assert.equal(sha(await readFile(resolve(home,name))),fixture[key]);
const {default:createModule}=await import(pathToFileURL(resolve(home,'resources.mjs'))),module=await createModule();
const adapter=resolve(home,'node-message-adapter.mjs');await writeFile(adapter,`import {parentPort} from 'node:worker_threads';
globalThis.self={postMessage:(m,t)=>parentPort.postMessage(m,t),addEventListener:(_,accept)=>parentPort.on('message',data=>accept({data}))};
await import(${JSON.stringify(pathToFileURL(resolve(build,'Th14ArchiveDecodeWorker.mjs')).href)});`,{flag:'wx'});
let invoke=()=>{},worker,pointer=0,report,imports=0,batches=0;const rows=[],controls=[];
const runtime=new Th14WebGpuRuntime({ccall:()=>invoke()},{createArchiveWorker:()=>worker=new Worker(pathToFileURL(adapter),{type:'module'})});module.th14WebGpuRuntime=runtime;
for(const method of ['archiveAnmCopy','archiveParsedCopy','archiveCopy']){const original=runtime[method].bind(runtime);runtime[method]=(...args)=>{const result=original(...args);if(result===1)++imports;return result;};}
const deadline=setTimeout(()=>void worker?.terminate(),90000),error=()=>module.UTF8ToString(module._fixture_error());
const names=()=>module.UTF8ToString(module._fixture_names()).split('\n').filter(Boolean);
async function deliver({replacement,inside}={}){
    const selected=names(),id=module._fixture_dispatch();assert(id>=0,'Expected a single dispatchable CPU step');
    invoke=()=>{inside?.(id);assert.equal(module._fixture_deliver(id,runtime.archiveStatus()),1,error());};
    if(selected.length||replacement){++batches;await runtime.scheduleArchive(1,0,replacement??selected).delivered;}else invoke();
    return id;
}
async function phase(phase){
    let result=module._fixture_advance(phase),steps=0;
    while(result===0){assert(++steps<10);await deliver();result=module._fixture_advance(phase);}
    assert.equal(result,1,error());if(phase===1)assert.equal(module._fixture_publish(),1);return steps;
}
const prepare=(stage=3,selection=5,sync=0)=>assert.equal(module._fixture_prepare(stage,selection,sync),1,error());
async function preceding(target){prepare();for(let p=0;p<target;++p)await phase(p);}
try{
    const bytes=new Uint8Array(await readFile('H:/Games/th/14/th14.dat'));assert.equal(sha(bytes),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
    pointer=module._malloc(bytes.length);module.HEAPU8.set(bytes,pointer);assert.equal(module._fixture_open(pointer,bytes.length),1);
    runtime.openArchive(bytes);assert.equal(await runtime.archiveOpening,227);
    for(let stage=2;stage<=6;++stage)for(let selection=0;selection<6;++selection){
        prepare(stage,selection);const steps=[];
        for(let p=0;p<3;++p)steps.push(await phase(p));
        assert.equal(module._fixture_compare(),1,`Worker fields changed ${stage}/${selection}`);assert.equal(module._fixture_counts(0),3);
        module._fixture_finish();assert.equal(module._fixture_dispatch(),-1);
        prepare(stage,selection,1);for(let p=0;p<3;++p){assert.equal(module._fixture_advance(p),1,error());if(p===1)assert.equal(module._fixture_publish(),1);}
        assert.equal(module._fixture_compare(),1,`Synchronous consumer changed ${stage}/${selection}`);module._fixture_finish();
        rows.push({stage,selection,steps,allParsedFieldsAndBytesEqual:true,synchronousConsumerPassed:true});
    }
    for(let p=0;p<3;++p){
        await preceding(p);assert.equal(module._fixture_advance(p),0);const before=imports,id=module._fixture_dispatch();assert(id>=0);
        assert.equal(module._fixture_counts(0),p,'CPU must finish before its GPU request');
        module._fixture_cancel();assert.equal(module._fixture_deliver(id,1),0,'Cancelled owner callback must not dereference a freed bundle');
        assert.equal(imports,before);assert.equal(module._fixture_counts(1),1);assert.equal(module._fixture_counts(2),p?1:0);
        controls.push({phase:p,cancelBeforeGpuAndStaleOwnerRejected:true,publishedSceneOwner:p===2});
        await preceding(p);assert.equal(module._fixture_advance(p),0);const oldNames=names(),old=module._fixture_dispatch();
        module._fixture_suspend();assert.equal(module._fixture_deliver(old,1),0);assert.equal(module._fixture_dispatch(),-1);
        module._fixture_resume();assert.deepEqual(names(),oldNames);await deliver();assert.equal(module._fixture_deliver(old,1),0);
        await phase(p);for(let q=p+1;q<3;++q)await phase(q);assert.equal(module._fixture_compare(),1);module._fixture_finish();
        controls.push({phase:p,suspendStaleRejectedAndResumeRequeued:true});
        await preceding(p);assert.equal(module._fixture_advance(p),0);await deliver({replacement:['__missing__']});
        assert.equal(module._fixture_advance(p),2);assert.equal(module._fixture_counts(0),p);module._fixture_cancel();
        controls.push({phase:p,failedBatchNoSynchronousFallback:true});
    }
    prepare();assert.equal(module._fixture_advance(0),0);assert.equal(module._fixture_wrong_owner(),2);assert.equal(module._fixture_dispatch(),-1);module._fixture_cancel();
    controls.push({wrongOwnerRejected:true});
    for(const [p,kind]of [[0,'anm'],[1,'std'],[1,'anm'],[2,'ecl'],[2,'anm']]){
        await preceding(p);assert.equal(module._fixture_advance(p),0);
        if(p===2&&kind==='anm')await deliver();
        const method=kind==='anm'?'archiveAnmCopy':'archiveParsedCopy',original=runtime[method];let corrupted=false;
        runtime[method]=(...args)=>{const result=original(...args);if(result===1&&!corrupted&&(kind!=='std'||args[0]===1)&&(kind!=='ecl'||args[0]===2)){args.at(-1)[args.at(-1).length-1]^=1;corrupted=true;}return result;};
        try{await deliver();}finally{runtime[method]=original;}
        assert(corrupted);assert.equal(module._fixture_advance(p),2,error());assert.equal(module._fixture_counts(0),p);module._fixture_cancel();
        controls.push({phase:p,corruptKind:kind,rejectedWithoutFallback:true});
    }
    prepare();assert.equal(module._fixture_advance(0),0);await deliver();module._fixture_gpu(0);
    const before=imports;assert.equal(module._fixture_advance(0),0);assert.equal(module._fixture_counts(0),1);
    assert.equal(module._fixture_advance(0),0);assert.equal(module._fixture_counts(0),1);assert.equal(imports,before);
    module._fixture_gpu(1);assert.equal(module._fixture_advance(0),1);await phase(1);await phase(2);assert.equal(module._fixture_compare(),1);module._fixture_finish();
    controls.push({gpuWaitDoesNotRepeatCpuOrGpuRequest:true,subsequentValidRunPassed:true});
    assert.equal(runtime.failure,null);
    report={passed:true,cases:rows.length,rows,controls,imports,batches,actualProductionControllerAndSessionOwner:true,
        actualIndependentCpuWorker:true,allParsedFieldsAndBytesEqual:true,synchronousConsumers:30,
        cancelBeforeAnyGpuRequestPassed:true,cancelAfterPublishedScenePassed:true,suspendResumeAllPhasesPassed:true,
        actualApplicationControllerTest:false,noGraphicsOrAudioDevices:true,browserBuildSha256:sha(buildRaw),fixtureBuildSha256:sha(fixtureRaw),
        checkerSha256:sha(await readFile(fileURLToPath(import.meta.url))),completeGame:false,nativeEquivalent:false};
}catch(error){report={passed:false,error:String(error.stack??error),rows,controls,imports,batches,completeGame:false,nativeEquivalent:false};process.exitCode=1;}
finally{clearTimeout(deadline);runtime.archive?.close();if(pointer)module._free(pointer);}
await writeFile(resolve(home,'check.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(Object.fromEntries(Object.entries(report).filter(([name])=>name!=='rows'))));
