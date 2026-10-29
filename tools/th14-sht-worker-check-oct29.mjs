import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir,statfs} from 'node:fs/promises';
import {resolve,relative,isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import {Worker} from 'node:worker_threads';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WebGpuRuntime} from '../runtimes/th12/portable/sdl/Th14WebGpuRuntime.mjs';
import {ArchiveDecodeClient} from '../runtimes/th12/portable/sdl/Th14ArchiveDecodeClient.mjs';
import {ArchiveReadAhead} from '../runtimes/th12/portable/sdl/Th14ArchiveReadAhead.mjs';
const root=resolve(import.meta.dirname,'..'),options=new Map();
for(let i=2;i<process.argv.length;i+=2){const key=process.argv[i];assert(['--worker-build','--consumer','--output'].includes(key)&&process.argv[i+1]&&!options.has(key));options.set(key,process.argv[i+1]);}
assert.equal(options.size,3);const build=resolve(root,options.get('--worker-build')),consumer=resolve(root,options.get('--consumer')),out=resolve(root,options.get('--output'));
for(const path of [build,consumer,out]){const scope=relative(resolve(root,'artifacts/th14'),path);assert(scope&&!scope.startsWith('..')&&!isAbsolute(scope));}
await mkdir(out);const disk=await statfs(out);assert(disk.bavail*disk.bsize>=100*1024**3);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex'),workerBuildRaw=await readFile(resolve(build,'build.json')),workerBuild=JSON.parse(workerBuildRaw),consumerRaw=await readFile(resolve(consumer,'build.json')),consumerBuild=JSON.parse(consumerRaw);
assert(workerBuild.compiled&&workerBuild.actualProductionShtParser&&workerBuild.browserRuntimeModules&&consumerBuild.productionConsumer&&consumerBuild.workerFeatureEnabled);
const wasm=await readFile(resolve(consumer,'consumer.wasm'));assert.equal(sha(wasm),consumerBuild.wasmSha256);
for(const name of ['Th14ArchiveDecodeClient.mjs','Th14ArchiveReadAhead.mjs','Th14ArchiveDecodeEndpoint.mjs','Th14ArchiveDecodeWorker.mjs'])assert.equal(sha(await readFile(resolve(build,name))),sha(await readFile(resolve(root,'runtimes/th12/portable/sdl',name))));
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const archive=new Uint8Array(await readFile('H:/Games/th/14/th14.dat'));assert.equal(sha(archive),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
const archivePointer=c.fixture_allocate(archive.length);new Uint8Array(c.memory.buffer,archivePointer,archive.length).set(archive);assert.equal(c.fixture_open(archivePointer,archive.length),1);
let invoke=()=>{},worker,rawReads=0,parsedCopies=0,report;const rows=[],controls=[],names=['pl00a.sht','pl00b.sht','pl01a.sht','pl01b.sht','pl02a.sht','pl02b.sht'];
const makeWorker=fault=>new Worker(new URL('./th14-sht-worker-host-oct29.mjs',import.meta.url),{type:'module',workerData:{build,fault}});
const runtime=new Th14WebGpuRuntime({ccall:()=>invoke()},{createArchiveWorker:()=>worker=makeWorker()});
const deadline=setTimeout(()=>void worker?.terminate(),90000);
function upload(bytes){const pointer=c.fixture_allocate(bytes.length);assert(pointer);new Uint8Array(c.memory.buffer,pointer,bytes.length).set(bytes);assert.equal(c.fixture_packet(pointer,bytes.length),1);c.fixture_release(pointer);}
function importPacket(bytes,mode=1){upload(bytes);const result=c.fixture_import(mode),reads=c.fixture_value(3);rawReads+=reads;assert.equal(reads,0,'No prefetched raw bytes may be copied by the consumer');return result;}
function rehash(packet){packet.writeUInt32LE(packet.length,8);let hash=2166136261;for(const byte of packet.subarray(36))hash=Math.imul(hash^byte,16777619)>>>0;packet.writeUInt32LE(hash,32);return packet;}
const originalCopy=runtime.archiveParsedCopy.bind(runtime);runtime.archiveParsedCopy=(...args)=>{const result=originalCopy(...args);if(result===1)++parsedCopies;return result;};
try{
    runtime.openArchive(archive);assert.equal(await runtime.archiveOpening,227);
    for(let index=0;index<6;++index){
        const name=names[index];assert.equal(c.fixture_select(index),1);
        const canonical=Buffer.from(new Uint8Array(c.memory.buffer,c.fixture_canonical_data(),c.fixture_canonical_size()));let packet;
        invoke=()=>{
            assert.equal(runtime.archiveStatus(),1);const size=runtime.archiveParsedSize(3,name);assert(size>=680);packet=new Uint8Array(size);
            assert.equal(runtime.archiveParsedCopy(3,name,packet),1);assert.deepEqual(Buffer.from(packet),canonical);
            assert.equal(importPacket(packet),1);assert.equal(c.fixture_compare(),1);assert.equal(c.fixture_value(2),1);assert.equal(c.fixture_value(4),1);
        };
        await runtime.scheduleArchive(1,0,[name]).delivered;
        rows.push({name,groups:c.fixture_value(0),shots:c.fixture_value(1),packetBytes:packet.length,packetSha256:sha(packet),allHeaderAndShotBytesEqual:true,canonicalPacketBytesEqual:true,consumerRawReads:0});
        const mutations=[['magic',p=>p.writeUInt32LE(0,0)],['version',p=>p.writeUInt32LE(2,4)],['raw-size',p=>p.writeUInt32LE(0,12)],['groups-zero',p=>p.writeUInt32LE(0,20)],['groups-over-limit',p=>p.writeUInt32LE(11,20)],['spec-total',p=>p.writeUInt32LE(0xffffffff,24)],['header-words',p=>p.writeUInt32LE(160,28)],['header-version',p=>p.writeUInt32LE(3,36)],['power-step',p=>p.writeUInt32LE(0,76)],['group-count',p=>p.writeUInt32LE(0xffffffff,684)],['interval-zero',p=>p.writeUInt32LE(0,688)],['signed-byte-canonical',p=>p.writeUInt32LE(0x80,688)],['signed-short-canonical',p=>p.writeUInt32LE(0x8000,696)],['angle-nan',p=>p.writeUInt32LE(0x7fc00000,716)]];
        for(const[kind,mutate]of mutations){const bad=Buffer.from(packet);mutate(bad);rehash(bad);assert.equal(importPacket(bad),0,kind);assert.equal(c.fixture_compare(),1,'Rejected packet must preserve prior output');assert.equal(importPacket(packet),1);controls.push({name,kind,rejected:true,outputPreserved:true,noRawFallback:true});}
        for(const[kind,bad]of [['truncated',Buffer.from(packet).subarray(0,packet.length-1)],['trailing',Buffer.concat([Buffer.from(packet),Buffer.from([0])])]]){rehash(bad);assert.equal(importPacket(bad),0,kind);assert.equal(c.fixture_compare(),1);assert.equal(importPacket(packet),1);controls.push({name,kind,rejected:true,outputPreserved:true,noRawFallback:true});}
        const checksum=Buffer.from(packet);checksum[checksum.length-1]^=1;assert.equal(importPacket(checksum),0);assert.equal(c.fixture_compare(),1);assert.equal(importPacket(packet),1);controls.push({name,kind:'checksum',rejected:true,outputPreserved:true,noRawFallback:true});
        for(const mode of [2,3,4]){assert.equal(importPacket(packet,mode),0);assert.equal(c.fixture_compare(),1);assert.equal(importPacket(packet),1);controls.push({name,kind:['','','worker-failed','copy-failed','parsed-missing'][mode],rejected:true,noRawFallback:true});}
    }
    const batches=[];
    for(let character=0;character<3;++character){
        const selected=names.slice(character*2,character*2+2),mixed=[`pl0${character}.anm`,...selected,...(character===2?['default.ecl']:[])];
        invoke=()=>{
            assert.equal(runtime.archiveStatus(),1);assert(runtime.archiveAnmSize(mixed[0])>0);if(character===2)assert(runtime.archiveParsedSize(2,'default.ecl')>0);
            for(const name of selected){const index=names.indexOf(name);assert.equal(c.fixture_select(index),1);const packet=new Uint8Array(runtime.archiveParsedSize(3,name));assert.equal(runtime.archiveParsedCopy(3,name,packet),1);assert.equal(sha(packet),rows[index].packetSha256);assert.equal(importPacket(packet),1);assert.equal(c.fixture_compare(),1);}
        };
        await runtime.scheduleArchive(1,0,mixed).delivered;batches.push({names:mixed,shtImports:2,independentPacketOwnership:true});
    }
    invoke=()=>{for(let index=0;index<6;++index){const name=names[index];assert.equal(c.fixture_select(index),1);const packet=new Uint8Array(runtime.archiveParsedSize(3,name));assert.equal(runtime.archiveParsedCopy(3,name,packet),1);assert.equal(sha(packet),rows[index].packetSha256);assert.equal(importPacket(packet),1);assert.equal(c.fixture_compare(),1);}};
    await runtime.scheduleArchive(1,0,names).delivered;batches.push({names:[...names],shtImports:6,independentPacketOwnership:true});
    let cancelled=false;invoke=()=>{assert.equal(runtime.archiveStatus(),0);assert.equal(runtime.archiveParsedSize(3,names[0]),-2);cancelled=true;};
    const cancelledJob=runtime.scheduleArchive(1,0,[names[0]]);runtime.cancelArchive();await cancelledJob.delivered;assert(cancelled);controls.push({kind:'cancelled-batch',callbackStillDelivered:true,parsedStateUnavailable:true});
    invoke=()=>{assert.equal(runtime.archiveStatus(),1);assert(runtime.archiveParsedSize(3,names[0])>0);};await runtime.scheduleArchive(1,0,[names[0]]).delivered;controls.push({kind:'new-generation-after-cancel',passed:true});
    const missing=new ArchiveReadAhead({decode:async()=>[{name:names[0],bytes:new Uint8Array(16)}],close:()=>{}},{run:async action=>action()});
    await missing.schedule([names[0]],()=>assert.throws(()=>missing.parsedSize('sht',names[0]),/missing/)).delivered;missing.close();controls.push({kind:'raw-only-batch',testPayloadMalformed:true,parsedMissingRejected:true});
    assert.equal(runtime.failure,null);runtime.archive.close();await worker.terminate();
    worker=makeWorker('decoded-sht-version');const client=new ArchiveDecodeClient(worker);assert.equal(await client.open(archive),227);
    await assert.rejects(client.decode([names[0]]),/SHT rejected/);controls.push({kind:'decoded-input-version',actualWorkerProductionParserRejected:true,testInputCorruptionDeclared:true,originalDatUnmodified:true});
    const recovered=await client.decode([names[0]]);assert(recovered[0].sht instanceof Uint8Array);controls.push({kind:'valid-after-parser-rejection',passed:true});client.close();await worker.terminate();
    const sourceBindings={};for(const name of ['Th14WebGpuRuntime.mjs','Th14ArchiveReadAhead.mjs','Th14ArchiveDecodeClient.mjs','Th14ArchiveDecodeEndpoint.mjs'])sourceBindings['runtimes/th12/portable/sdl/'+name]=sha(await readFile(resolve(root,'runtimes/th12/portable/sdl',name)));
    report={passed:true,cases:rows.length,rows,batches,controls,parsedCopies,consumerRawReads:rawReads,allParsedFieldsAndCanonicalBytesEqual:true,actualIndependentCpuWorker:true,actualProductionShtParser:true,actualProductionGameResourcesConsumer:true,mainConsumerUsesTestPacketProvider:true,actualApplicationControllerTest:false,noGpuAudioOrGameState:true,workerBuildSha256:sha(workerBuildRaw),consumerBuildSha256:sha(consumerRaw),checkerSha256:sha(await readFile(fileURLToPath(import.meta.url))),workerAdapterSha256:sha(await readFile(new URL('./th14-sht-worker-host-oct29.mjs',import.meta.url))),sourceBindings,browserAcceptance:false,completeGame:false,nativeEquivalent:false};
}catch(error){report={passed:false,error:String(error.stack??error),rows,controls,completeGame:false,nativeEquivalent:false};process.exitCode=1;}
finally{clearTimeout(deadline);runtime.archive?.close();if(worker)await worker.terminate();c.fixture_release(archivePointer);}
const encoded=JSON.stringify(report,null,2)+'\n';assert(Buffer.byteLength(encoded)<=128*1024**2);await writeFile(resolve(out,'check.json'),encoded,{flag:'wx'});console.log(JSON.stringify(Object.fromEntries(Object.entries(report).filter(([name])=>!['rows','controls'].includes(name)))));
