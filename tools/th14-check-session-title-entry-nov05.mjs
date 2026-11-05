// Probe actual title idle/attract behavior; no preset RNG count or value.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(process.argv[2]),native=resolve(process.argv[3]);
const read=path=>readFileSync(path),load=path=>JSON.parse(read(path)),sha=bytes=>createHash('sha256').update(bytes).digest('hex');
for(const path of [home,native])assert(path.startsWith(resolve(root,'artifacts/th14')+'\\')||path.startsWith(resolve(root,'artifacts/th14')+'/'));
const build=load(resolve(home,'build.json')),bytes=read(resolve(home,'probe.wasm'));assert.equal(sha(bytes),build.wasmSha256);
const original=load(resolve(native,'report.json')),initial=load(resolve(native,'untouched-first-player.json'));
const assets=resolve(root,original.observerOptions.assets),manifest=load(resolve(assets,'manifest.json'));
const archive=read(resolve(assets,'th14.dat'));assert.equal(sha(archive),manifest.referenceArchiveSha256);
const expected=read(resolve(native,'selected-state.u32'));assert.equal(sha(expected),original.selectedSha256);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport,
 stagehost:{now_ms:()=>performance.now(),request_begin:()=>0,ready:()=>2,committed:()=>0,cancel:()=>{}}});
wasi.initialize(instance);const c=instance.exports,p=c.allocate(archive.length);assert(p);
new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);
const withLoading=['loading','queued'].includes(process.argv[4]),queued=process.argv[4]==='queued';
const resultCode=(queued?c.probe_queued_loading_entry:withLoading?c.probe_loading_entry:c.probe_title_entry)(initial.actualInitialTimeGetTimeInput,initial.actualOriginalSecurityCookie,0x1aec84);
const words=Array.from({length:12},(_,i)=>c.title_probe_value(i)>>>0);
const rowWords=c.rows_words()>>>0,actual=rowWords?new Uint32Array(c.memory.buffer,c.rows_data(),rowWords).slice():new Uint32Array();
const fields=[];
if(actual.length>=114)for(let field=0;field<32;++field)if(actual[1+field]!==expected.readUInt32LE(field*4))fields.push(field);
const result={schema:'th14/actual-title-entry-probe/1',resultCode,successfulEntry:resultCode===1,
 constructorScriptCalls:words[0],afterTitleCreationScriptCalls:words[1],actualTitleUpdates:words[2],phase:words[3],stage:words[4],
 scriptCallsAtEntry:words[5],nativeFirstScriptCalls:expected.readUInt32LE(22*4),
 entryScriptSeedMatchesNative:words[6]===expected.readUInt32LE(21*4),attractModeBeforeDeclaredClear:words[7]===1,
 callbacksBeforeFirstStageUpdate:words[8],callbacksAfterFirstStageUpdate:words[9],
 firstSelectedDifferenceFields:fields,scriptSeedCounterPreset:false,observedNativeFrameVmTimingReplayed:false,
 originalReplaySha256:manifest.replaySha256,nativeReportSha256:sha(read(resolve(native,'report.json'))),
 actualTitlePathOnly:!withLoading,declaredCpuReadyBootstrapLoadingPrelude:withLoading,oneRealTextureChunkPerUpdate:queued,fullColdApplicationAccepted:false,completeGame:false,
 buildSha256:sha(read(resolve(home,'build.json'))),toolSha256:sha(readFileSync(import.meta.filename))};
const output=resolve(process.argv[5]??resolve(home,'verified.json'));
assert(output.startsWith(home+'\\')||output.startsWith(home+'/'));
writeFileSync(output,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
c.close_session();c.release(p);
assert.equal(resultCode,1);console.log(JSON.stringify(result));
