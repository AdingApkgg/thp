// Self-contained wire-format checks; no game assets or audio device required.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const R=resolve(import.meta.dirname,'..'),O=resolve(R,'artifacts/th14/current-concurrent-mixer-nov14/beam-replay-rules/metadata-unit');mkdirSync(O,{recursive:true});
const sources=['runtimes/th12/th12_web/tests/cpp/th14-replay-beam-rules-fixture.cpp',...['Replay.cpp','ReplayRecorder.cpp','ResourceCrypt.cpp','Lzss.cpp'].map(n=>'runtimes/th12/th12_web/cpp/game/'+n)];
const compiler=process.env.WASI_CXX??resolve(R,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
const file=resolve(O,'metadata.wasm'),args=['--target=wasm32-wasip1','-std=c++17','-DPORT_TITLE=14','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',...sources.map(n=>resolve(R,n)),'-o',file];
execFileSync(compiler,args,{cwd:R,env:{...process.env,TEMP:O,TMP:O},stdio:'pipe',windowsHide:true});
const bytes=readFileSync(file),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const sha=b=>createHash('sha256').update(b).digest('hex'),cases=[];
function record(touch){const n=c.policy_record(touch);assert(n>0);return Buffer.from(new Uint8Array(c.memory.buffer,c.policy_record_data(),n));}
function open(b){const p=c.viewer_alloc(b.length);assert(p);try{new Uint8Array(c.memory.buffer,p,b.length).set(b);return c.policy_open(p,b.length);}finally{c.viewer_free(p);}}
function block({version=1,rule=1,length=20,kind=0x42343154}={}){const b=Buffer.alloc(20);b.writeUInt32LE(0x52455355);b.writeUInt32LE(length,4);b.writeUInt32LE(kind,8);b.writeUInt32LE(version,12);b.writeUInt32LE(rule,16);return b;}
function check(name,b,expected){assert.equal(open(b),expected,name);cases.push({name,expected});}
const own=record(0);assert(own.subarray(-20).equals(block()));
// Synthetic untagged data tests parser defaults, never original-game fidelity.
const untagged=Buffer.from(own.subarray(0,-20)),inputHash=sha(untagged);
check('untagged parser input stays native',untagged,0);
check('explicit bounded rule',Buffer.concat([untagged,block()]),1);
assert.equal(c.policy_retain(),1);cases.push({name:'rule survives metadata retention',expected:1});
check('new open resets rule',untagged,0);
check('explicit native rule',Buffer.concat([untagged,block({rule:0})]),0);
for(const[name,tail]of [['unknown version',block({version:2})],['unknown rule',block({rule:2})],['short known block',block({length:16})],['truncated known block',block({length:24})],['duplicate blocks',Buffer.concat([block(),block()])],['conflicting blocks',Buffer.concat([block(),block({rule:0})])]])check(name,Buffer.concat([untagged,tail]),-1);
check('unrelated USER block',Buffer.concat([untagged,block({kind:0x12345678})]),0);
for(const touch of [0,1]){const b=record(touch);check(`real recorder ${touch?'touch':'keyboard'}`,b,1);let offset=0x24+b.readUInt32LE(0x1c);const kinds=[];while(offset<b.length){assert.equal(b.toString('ascii',offset,offset+4),'USER');const n=b.readUInt32LE(offset+4);assert(n>=12&&offset+n<=b.length);kinds.push(b.readUInt32LE(offset+8));offset+=n;}assert.deepEqual(kinds,touch?[0x11,0x42343154]:[0x42343154]);}
assert.equal(sha(untagged),inputHash);
const report={passed:true,cases,sourceHashes:Object.fromEntries(sources.map(n=>[n,sha(readFileSync(resolve(R,n)))])),wasmSha256:sha(bytes),syntheticParserControlsOnly:true,noGameAssetReads:true,silent:true,completeGame:false};
writeFileSync(resolve(O,'qualified.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,cases:cases.length,noGameAssetReads:true,silent:true}));
