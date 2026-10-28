// Actual production parser in an independent worker; actual C++ importer.
import {readFile,writeFile} from 'node:fs/promises';
import {Worker} from 'node:worker_threads';
import {resolve} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('../',import.meta.url)),args=process.argv.slice(2);
assert.equal(args.length,2);assert.equal(args[0],'--fixture');const home=resolve(args[1]);
const sha=b=>createHash('sha256').update(b).digest('hex'),build=JSON.parse(await readFile(resolve(home,'build.json'))),workerHome=resolve(root,build.workerBuildPath);
assert.equal(sha(await readFile(resolve(workerHome,'build.json'))),build.workerBuildSha256);
const workerBuild=JSON.parse(await readFile(resolve(workerHome,'build.json')));
for(const [name,field]of [['fixture.mjs','loaderSha256'],['fixture.wasm','wasmSha256']])assert.equal(sha(await readFile(resolve(home,name))),build[field]);
for(const [name,field]of [['archive-decoder.mjs','loaderSha256'],['archive-decoder.wasm','wasmSha256']])assert.equal(sha(await readFile(resolve(workerHome,name))),workerBuild[field]);
const {default:createFixture}=await import(pathToFileURL(resolve(home,'fixture.mjs'))),fixture=await createFixture();
const {default:createDecoder}=await import(pathToFileURL(resolve(workerHome,'archive-decoder.mjs'))),direct=await createDecoder();
const {ArchiveDecodeClient}=await import(pathToFileURL(resolve(workerHome,'Th14ArchiveDecodeClient.mjs')));
const adapter=resolve(home,'node-message-adapter.mjs');await writeFile(adapter,`import {parentPort} from 'node:worker_threads';
globalThis.self={postMessage:(m,t)=>parentPort.postMessage(m,t),addEventListener:(_,accept)=>parentPort.on('message',data=>accept({data}))};
await import(${JSON.stringify(pathToFileURL(resolve(workerHome,'Th14ArchiveDecodeWorker.mjs')).href)});`,{flag:'wx'});
const client=new ArchiveDecodeClient(new Worker(pathToFileURL(adapter),{type:'module'}));
const deadline=setTimeout(()=>client.close(),60000);const rows=[];let report,sourcePointer=0;
const fnv=bytes=>{let hash=2166136261;for(const byte of bytes)hash=Math.imul(hash^byte,16777619)>>>0;return hash;};
const fields=['textures','sprites','scripts','textureBytes','scriptBytes'];
function allocate(bytes){const pointer=fixture._malloc(bytes.length||1);assert(pointer);fixture.HEAPU8.set(bytes,pointer);return pointer;}
try{
  const archive=new Uint8Array(await readFile('H:/Games/th/14/th14.dat'));assert.equal(sha(archive),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
  sourcePointer=direct._malloc(archive.length);direct.HEAPU8.set(archive,sourcePointer);assert.equal(direct._decoder_open(sourcePointer,archive.length),227);
  const names=Array.from({length:227},(_,i)=>direct.UTF8ToString(direct._decoder_name(i)));assert.equal(await client.open(archive),227);
  let decodedBytes=0,transferredAnmBytes=0,rejectedPackets=0;
  for(let i=0;i<names.length;i+=4)for(const entry of await client.decode(names.slice(i,i+4))){
    decodedBytes+=entry.bytes.length;
    if(!entry.name.endsWith('.anm')){assert.equal(entry.anm,undefined);continue;}
    assert(entry.anm instanceof Uint8Array);transferredAnmBytes+=entry.anm.length;
    const input=allocate(entry.bytes),packet=allocate(entry.anm);
    try{
      assert.equal(fixture._fixture_compare(input,entry.bytes.length,packet,entry.anm.length),1,entry.name);
      const row={name:entry.name,decodedBytes:entry.bytes.length,packetBytes:entry.anm.length,rawSha256:sha(entry.bytes),packetSha256:sha(entry.anm),...Object.fromEntries(fields.map((name,i)=>[name,fixture._fixture_count(i)])),allFieldsAndBytesEqual:true};
      rows.push(row);
      // Corrupt every packet independently; no failure may partially replace
      // the destination object's previous state.
      const broken=entry.anm.slice();broken[broken.length-1]^=1;const damaged=allocate(broken);
      try{assert.equal(fixture._fixture_reject(damaged,broken.length),1);++rejectedPackets;}finally{fixture._free(damaged);}
      if(rows.length===1){
        for(const length of [0,1,35,entry.anm.length-1]){assert.equal(fixture._fixture_reject(packet,length),1);++rejectedPackets;}
        for(const [offset,value]of [[0,0],[4,2],[8,entry.anm.length+1],[12,0],[20,0xffffffff],[24,0xffffffff],[28,0xffffffff]]){
          const bytes=entry.anm.slice(),view=new DataView(bytes.buffer);view.setUint32(offset,value,true);view.setUint32(32,fnv(bytes.subarray(36)),true);
          const p=allocate(bytes);try{assert.equal(fixture._fixture_reject(p,bytes.length),1,`offset${offset}`);++rejectedPackets;}finally{fixture._free(p);}
        }
      }
    }finally{fixture._free(input);fixture._free(packet);}
  }
  assert(rows.length>0);assert.equal(decodedBytes,253480939);
  const again=await client.decode(['st03enm.anm']),before=sha(again[0].anm);again[0].anm.fill(0);
  assert.equal(sha((await client.decode(['st03enm.anm']))[0].anm),before);
  await assert.rejects(client.decode(['__missing__']),/Entry rejected/);
  assert.equal(sha((await client.decode(['st03enm.anm']))[0].anm),before);
  assert.equal(sha(archive),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
  report={passed:true,archiveEntries:227,decodedBytes,anmEntries:rows.length,transferredAnmBytes,rejectedPackets,rows,
    actualProductionAnmParser:true,actualIndependentCpuWorker:true,actualCppPacketImporter:true,
    explicitFloatBitsCompared:true,textureAndScriptBytesCompared:true,pointersAndTemplatesNotTransferred:true,
    failedImportPreservesDestination:true,transferredResultsOwnTheirBuffers:true,subsequentJobAfterFailurePassed:true,
    fixtureBuildSha256:sha(await readFile(resolve(home,'build.json'))),workerBuildSha256:build.workerBuildSha256,
    checkerSha256:sha(await readFile(fileURLToPath(import.meta.url))),productionIntegrated:false,actualBrowserRun:false,completeGame:false,nativeEquivalent:false};
}catch(error){report={passed:false,error:String(error.stack??error),rows,completeGame:false,nativeEquivalent:false};process.exitCode=1;}
finally{clearTimeout(deadline);client.close();direct._decoder_close();if(sourcePointer)direct._free(sourcePointer);}
await writeFile(resolve(home,'check.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(Object.fromEntries(Object.entries(report).filter(([name])=>name!=='rows'))));
