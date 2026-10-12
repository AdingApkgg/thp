import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/score-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-score-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'score.wasm'),fixture='tests/cpp/th14-score-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/score-native.json'),'utf8'));
const hex=(p,n)=>Buffer.from(new Uint8Array(c.memory.buffer,p,n)).toString('hex');
assert.equal(hex(c.initialize_character(),0x5298),proof.initial,'all character bytes');
for(const r of proof.cases){
 assert.equal(hex(c.initialize_settings(r.seed,r.calls),0x42c),r.settings,`all settings bytes seed=${r.seed} calls=${r.calls}`);
 assert.equal(c.final_seed()>>>0,r.finalSeed);
 assert.equal(c.final_calls()>>>0,r.finalCalls);
}
for(const [index,r] of proof.insertions.entries()){
 assert.equal(c.insert(r.difficulty,r.score,r.stage,r.continues,r.ratio),r.rank,`ranking ${index}`);
 assert.equal(hex(c.rows(),60*28),r.rows,`all ranking rows ${index}`);
}
for(const [index,r] of proof.names.entries()){
 const name=Buffer.from(r.name+'\0'),p=c.allocate(name.length);new Uint8Array(c.memory.buffer,p,name.length).set(name);
 assert.equal(c.commit_name(r.selection,r.difficulty,r.rank,p),1);c.release(p);
 assert.equal(hex(c.file_character(r.selection)+0x10+(r.difficulty*10+r.rank)*28,28),r.row,`all name row bytes ${index}`);
 assert.equal(hex(c.file_settings()+12,10),r.lastName,`all last-name bytes ${index}`);
}
const nativeFile=readFileSync(resolve(root,'artifacts/th14/score-native-default.dat'));
c.initialize_file(904,0);
const packedPointer=c.save_file();assert(packedPointer);
const portFile=Buffer.from(new Uint8Array(c.memory.buffer,packedPointer,c.saved_size()));
assert.deepEqual(portFile,nativeFile,'complete original checksum/LZSS/encryption bytes');
const nativePointer=c.allocate(nativeFile.length);new Uint8Array(c.memory.buffer,nativePointer,nativeFile.length).set(nativeFile);
assert.equal(c.open_file(nativePointer,nativeFile.length),1,'load native writer output');c.release(nativePointer);
const loaded=Array.from({length:7},(_,n)=>hex(c.file_character(n),0x5298)),loadedSettings=hex(c.file_settings(),0x42c);
c.sync_file();
assert.deepEqual(Array.from({length:7},(_,n)=>hex(c.file_character(n),0x5298)),loaded,'record sync preserves full defaults');
assert.equal(hex(c.file_settings(),0x42c),loadedSettings);
assert.deepEqual(Buffer.from(new Uint8Array(c.memory.buffer,c.save_file(),c.saved_size())),nativeFile,'native load/sync/save bytes');
writeFileSync(resolve(out,'port-default.dat'),portFile);
execFileSync(process.env.TH_NATIVE_PYTHON||'py',[...(process.env.TH_NATIVE_PYTHON?[]:['-3']),'tools/th14-score-native.py','--load',resolve(out,'port-default.dat')],{cwd:root,stdio:'inherit',windowsHide:true});
const nonemptyFile=readFileSync(resolve(root,'artifacts/th14/score-native-records.dat')),nonemptyRaw=readFileSync(resolve(root,'artifacts/th14/score-native-records.raw'));
const nonemptyPointer=c.allocate(nonemptyFile.length);new Uint8Array(c.memory.buffer,nonemptyPointer,nonemptyFile.length).set(nonemptyFile);
assert.equal(c.open_file(nonemptyPointer,nonemptyFile.length),1);c.release(nonemptyPointer);
const namePointer=c.inspect_file(),nameBytes=new Uint8Array(c.memory.buffer,namePointer,128);
assert.equal(Buffer.from(nameBytes.subarray(0,nameBytes.indexOf(0))).toString(),'oracle '+'A'.repeat(90));
assert.deepEqual(Array.from({length:7},(_,n)=>c.inspect_value(n)),[99,12,345,678,123,1,17],'native ordinary/practice records and Extra practice flags');
c.sync_file();
for(let index=0;index<7;index++)assert.equal(hex(c.file_character(index),0x5298),nonemptyRaw.subarray(index*0x5298,(index+1)*0x5298).toString('hex'),`all nonempty character bytes ${index}`);
assert.equal(hex(c.file_settings(),0x42c),nonemptyRaw.subarray(7*0x5298).toString('hex'));
const nonemptySaved=Buffer.from(new Uint8Array(c.memory.buffer,c.save_file(),c.saved_size()));
assert.deepEqual(nonemptySaved,nonemptyFile,'nonempty native load/sync/save bytes');writeFileSync(resolve(out,'port-records.dat'),nonemptySaved);
execFileSync(process.env.TH_NATIVE_PYTHON||'py',[...(process.env.TH_NATIVE_PYTHON?[]:['-3']),'tools/th14-score-native.py','--load',resolve(out,'port-records.dat'),resolve(root,'artifacts/th14/score-native-records.raw')],{cwd:root,stdio:'inherit',windowsHide:true});
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-score-verified.json'),JSON.stringify({passed:true,title:14,completeGame:false,characterBytes:0x5298,settingsBytes:0x42c,defaultCodecBytes:nativeFile.length,nonemptyCodecBytes:nonemptyFile.length,codecFiles:2,defaultDecodedBytes:0x24654,retailLoaderPassed:true,settingsCases:proof.cases.length,insertions:proof.insertions.length,nameCommits:proof.names.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Complete retail4567a0 character defaults: six ten-row rankings and120 spell index/difficulty defaults. Complete456b20 status defaults with494 gameplay next16 calls, incoming seed/counter boundaries and unsigned counter wrap; visual RNG confirmed untouched by native. Complete447e00 rankings: unsigned comparison, equal-score placement, row shifts, retained byte15, byte stage/continue, controlled timestamp and supplied timing ratio; all60 rows compared. 108 original44ac80 name commits compare all row and last-name bytes, including the terminating byte and retained tail. Original456f60 writer checksum/LZSS/encryption compared byte-for-byte for default and nonempty files; production native-file load/record-sync/save preserves all bytes, including97-byte names, ordinary/practice counters, Extra practice flags, best scores and opaque ranking bytes. Retail456de0 also loads the port file into all seven character records and settings. Allocator, free, memcpy, memset and timestamp are controlled boundaries; actual filesystem/browser persistence, menu consumers and complete startup excluded. Production ScoreFile now uses native TH14 storage and GameSession initializes settings with the gameplay RNG.',sourceHashes:Object.fromEntries(['cpp/game/ScoreFile.cpp','cpp/game/ScoreFile.hpp','cpp/game/SpellController.cpp','cpp/game/SpellController.hpp','cpp/game/StageCompletion.cpp','cpp/game/StageCompletion.hpp','cpp/game/GameSession.cpp','cpp/game/TitleOptions.cpp','cpp/game/TitleRecords.cpp','cpp/game/TitleTh14.cpp','cpp/game/TitleText.cpp','cpp/game/PauseEnd.cpp','cpp/game/Lzss.cpp','cpp/game/Lzss.hpp','cpp/game/ResourceCrypt.cpp','cpp/game/ResourceCrypt.hpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),toolHashes:Object.fromEntries(['tools/th14-score-native.py','tools/th14-score-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS TH14 full character defaults and ${proof.cases.length} settings RNG cases and ${proof.insertions.length} native rankings and ${proof.names.length} name commits`);
