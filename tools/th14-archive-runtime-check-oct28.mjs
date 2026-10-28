// Actual production queue/client/endpoint/worker under Node's message adapter.
// The frame fence is a component control, not an observed GPU/browser frame.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {Worker} from 'node:worker_threads';
import {resolve,sep} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {Th14WebGpuRuntime} from '../runtimes/th12/portable/sdl/Th14WebGpuRuntime.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const args=process.argv.slice(2);
assert.equal(args.length,4);assert.equal(args[0],'--build');assert.equal(args[2],'--output');
const buildHome=resolve(args[1]),out=resolve(args[3]);
for(const path of [buildHome,out])assert(path.startsWith(resolve(root,'artifacts/th14')+sep));
await mkdir(out);const sha=raw=>createHash('sha256').update(raw).digest('hex');
const build=JSON.parse(await readFile(resolve(buildHome,'build.json')));
const sourceBindings={};
for(const name of ['Th14WebGpuRuntime.mjs',...Object.keys(build.archiveWorkerFiles)]) {
  const raw=await readFile(resolve(buildHome,name));sourceBindings[name]={bytes:raw.length,sha256:sha(raw)};
  if(name.startsWith('Th14'))assert.equal(sha(await readFile(resolve(root,'runtimes/th12/portable/sdl',name))),sha(raw),name);
  else assert.equal(sha(raw),build.archiveWorkerFiles[name].sha256,name);
}
const bootstrap=`import {parentPort} from 'node:worker_threads';
globalThis.self={postMessage:(m,t)=>parentPort.postMessage(m,t),addEventListener:(_,accept)=>parentPort.on('message',data=>accept({data}))};
await import(${JSON.stringify(pathToFileURL(resolve(buildHome,'Th14ArchiveDecodeWorker.mjs')).href)});`;
const adapter=resolve(out,'node-message-adapter.mjs');await writeFile(adapter,bootstrap);
let callback=()=>{},worker;
const runtime=new Th14WebGpuRuntime({ccall:(name,result,types,args,options)=>{
  assert.equal(name,'th14_webgpu_invoke');assert.equal(options.async,true);return callback(args);
}},{createArchiveWorker:()=>worker=new Worker(pathToFileURL(adapter),{type:'module'})});
const deadline=setTimeout(()=>{void worker?.terminate();},60000);let report;
try {
  const bytes=new Uint8Array(await readFile('H:/Games/th/14/th14.dat'));
  assert.equal(sha(bytes),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
  runtime.openArchive(bytes);assert.equal(await runtime.archiveOpening,227);
  assert.equal(bytes.byteLength,90776747);assert.equal(runtime.archiveSize('st03enm.anm'),-1);
  let enter,release;const entered=new Promise(r=>enter=r),fence=new Promise(r=>release=r),events=[];
  const frame=runtime.run(async()=>{events.push('frame-enter');enter();await fence;events.push('frame-exit');});
  await entered;
  const expectations=JSON.parse(await readFile(resolve(root,'artifacts/th14/native-frame-readback-oct27/archive-worker-public-v2/check.json')));
  const byName=new Map(expectations.comparisons.map(row=>[row.name,row]));let copied=0;
  callback=args=>{
    assert.deepEqual(args,[123,456]);events.push('decode-callback');assert.equal(runtime.archiveStatus(),1);
    for(const name of ['st03.std','st03wl.anm']){
      const expected=byName.get(name),output=new Uint8Array(runtime.archiveSize(name));
      assert.equal(output.length,expected.bytes);assert.equal(runtime.archiveCopy(name,output),1);
      assert.equal(sha(output),expected.sha256);copied+=output.length;
      output.fill(0);assert.equal(runtime.archiveCopy(name,output),1);assert.equal(sha(output),expected.sha256);
      assert.equal(runtime.archiveCopy(name,new Uint8Array(output.length+1)),0);
    }
    assert.equal(runtime.archiveSize('st03enm.anm'),-1);
    const parsedSize=runtime.archiveAnmSize('st03wl.anm');assert(parsedSize>=36);
    const parsed=new Uint8Array(parsedSize);assert.equal(runtime.archiveAnmCopy('st03wl.anm',parsed),1);
    assert.equal(new DataView(parsed.buffer).getUint32(0,true),0x314d4e41);
    const original=sha(parsed);parsed.fill(0);assert.equal(runtime.archiveAnmCopy('st03wl.anm',parsed),1);assert.equal(sha(parsed),original);
    assert.equal(runtime.archiveAnmCopy('st03wl.anm',new Uint8Array(parsedSize+1)),0);
    assert.equal(runtime.archiveAnmSize('st03.std'),-1);
  };
  const first=runtime.scheduleArchive(123,456,['st03.std','st03wl.anm']);
  assert.equal((await first.ready).ok,true);assert.deepEqual(events,['frame-enter']);
  release();await frame;await first.delivered;
  assert.deepEqual(events,['frame-enter','frame-exit','decode-callback']);assert.equal(runtime.archiveSize('st03wl.anm'),-1);
  assert.equal(runtime.archiveAnmSize('st03wl.anm'),-1);
  callback=()=>{assert.equal(runtime.archiveStatus(),0);assert.equal(runtime.archiveSize('__missing__'),-2);};
  await runtime.scheduleArchive(1,2,['__missing__']).delivered;
  let stale=0;callback=()=>{++stale;assert.equal(runtime.archiveStatus(),0);assert.equal(runtime.archiveSize('st03enm.anm'),-2);assert.equal(runtime.archiveAnmSize('st03enm.anm'),-2);};
  const cancelled=runtime.scheduleArchive(1,2,['st03enm.anm']);runtime.cancelArchive();await cancelled.delivered;
  assert.equal(stale,1);assert.equal(runtime.archiveStatus(),1);
  callback=()=>assert.equal(runtime.archiveSize('st03enm.anm'),byName.get('st03enm.anm').bytes);
  await runtime.scheduleArchive(3,4,['st03enm.anm']).delivered;
  let ownedDependencies=0;
  callback=()=>{
    for(const name of ['st04.ecl','st04mbs2.ecl','st04bs2.ecl','default.ecl']){
      const length=runtime.archiveParsedSize(2,name);assert(length>=36,name);
      const parsed=new Uint8Array(length);assert.equal(runtime.archiveParsedCopy(2,name,parsed),1);
      assert.equal(new DataView(parsed.buffer).getUint32(0,true),0x314c4345);
      const output=new Uint8Array(runtime.archiveSize(name));assert.equal(runtime.archiveCopy(name,output),1);
      assert.equal(sha(output),byName.get(name).sha256);++ownedDependencies;
    }
    assert.equal(runtime.archiveParsedSize(3,'st04.ecl'),-2);
  };
  await runtime.scheduleArchive(5,6,['st04.ecl']).delivered;
  assert.equal(ownedDependencies,4);assert.equal(runtime.archiveParsedSize(2,'st04bs2.ecl'),-1);
  assert.equal(runtime.failure,null);assert.equal(runtime.archiveSize('st03enm.anm'),-1);
  assert.equal(sha(bytes),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
  report={passed:true,actualProductionRuntimeAndBrowserWorkerSource:true,nodeMessageTransportAdapter:true,
    actualCpuWorker:true,actualBrowserRun:false,declaredFrameFence:true,cpuFinishedDuringPendingFrame:true,
    callbackWaitedForFrame:true,events,comparedBytes:copied,expectedBytesViaFrozenDigests:true,
    immutableInputAndTransferredResults:true,wrongDestinationRejected:true,cacheClearedAfterCallback:true,
    workerFailureDeliveredToCppStatus:true,staleCallbackDeliveredOnceForCppTokenCleanup:true,
    resumedGenerationPassed:true,sourceBindings,completeGame:false,nativeEquivalent:false};
  report.parsedAnmTransferredAndOwned=true;report.parsedAnmFailureAndGenerationClearingPassed=true;
  report.parsedStdEclDependencyClosureOwned=true;report.eclClosureDirectByteCases=ownedDependencies;
}catch(error){report={passed:false,error:String(error.stack??error),completeGame:false,nativeEquivalent:false};process.exitCode=1;}
finally{clearTimeout(deadline);runtime.archive?.close();}
await writeFile(resolve(out,'report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
