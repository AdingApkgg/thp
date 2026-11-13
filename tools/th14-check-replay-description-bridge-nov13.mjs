import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {runInNewContext} from 'node:vm';
import {WASI} from 'node:wasi';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/replay-description-bridge-nov13');
const sha=b=>createHash('sha256').update(b).digest('hex');
const build=JSON.parse(readFileSync(resolve(H,'build.json'))),bytes=readFileSync(resolve(H,'probe.wasm'));
assert.equal(sha(bytes),build.wasmSha256);
for(const [n,h]of Object.entries({...build.sources,...build.objectBindings}))assert.equal(sha(readFileSync(resolve(R,n))),h,n);
const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),imports={env:{memory},wasi_snapshot_preview1:wasi.wasiImport};
for(const i of WebAssembly.Module.imports(module)){imports[i.module]??={};if(i.kind==='function'&&!imports[i.module][i.name])imports[i.module][i.name]=()=>{throw Error('unexpected boundary '+i.module+'.'+i.name);};}
const instance=new WebAssembly.Instance(module,imports);wasi.initialize(instance);const c=instance.exports;
const string=p=>{const b=new Uint8Array(memory.buffer),end=b.indexOf(0,p);assert(p&&end>=p);return new TextDecoder().decode(b.subarray(p,end));};
const native=data=>{const p=c.allocate(data.length||1);assert(p);try{new Uint8Array(memory.buffer,p,data.length).set(data);const result=c.describe(p,data.length);return result?JSON.parse(string(result)):null;}finally{c.release(p);}};
const corpus=resolve(R,'artifacts/th14/replay-save-reopen-nov13/files'),rows=[];
for(let selection=0;selection<6;selection++)for(let difficulty=0;difficulty<5;difficulty++)for(let practice=0;practice<2;practice++){
 const name=`s${selection}-d${difficulty}-p${practice}`,data=readFileSync(resolve(corpus,name+'.rpy')),description=native(data),decoded=readFileSync(resolve(corpus,name+'.decoded'));
 assert(description);assert.equal(description.character,Math.floor(selection/2));assert.equal(description.shot,selection%2);assert.equal(description.difficulty,difficulty);
 assert.equal(description.mode,practice?'practice':'normal');assert.equal(description.stages.length,!practice&&difficulty<4?2:1);
 assert.deepEqual(description.nameBytes,[...decoded.subarray(0,8)]);
 assert.equal(description.timestamp,Number(decoded.readBigUInt64LE(12)));assert.equal(description.score,decoded.readUInt32LE(20)*10);
 assert(Math.abs(description.slowdown-decoded.readFloatLE(0x74))<0.000001);assert.equal(description.lastStage,decoded.readUInt32LE(0x88));
 let offset=0x94;for(const stage of description.stages){assert.equal(stage.id,decoded.readUInt16LE(offset));assert.equal(stage.frames,decoded.readUInt32LE(offset+4));assert.equal(stage.score,decoded.readUInt32LE(offset+0x1c)*10);offset+=0xdc+decoded.readUInt32LE(offset+8);}assert.equal(offset,decoded.length);
 assert(description.stages.every(s=>s.id>=1&&s.id<=7&&Number.isInteger(s.frames)&&s.frames>0&&Number.isFinite(s.score)&&s.score>=0));rows.push({name,description});
}
const saved=readFileSync(resolve(R,'artifacts/th14/ordinary-replay-menu-nov13/write-c0-s1-d1-v2/save/replay/th14_01.rpy')),d=native(saved);
assert.equal(new TextDecoder().decode(Uint8Array.from(d.nameBytes)).trim(),'A');assert.deepEqual([d.character,d.shot,d.difficulty],[0,1,1]);assert.deepEqual(d.stages.map(s=>[s.id,s.frames]),[[1,345]]);
const invalid=[new Uint8Array(),saved.subarray(0,35),Uint8Array.from(saved,(_,i)=>i<6?0:saved[i])];
for(const data of invalid)assert.equal(native(data),null);
// Exercise the actual canonical command body, with only its per-title path
// substitution (the normal runtime packaging step) and the native Wasm decoder.
let source=readFileSync(resolve(R,'runtimes/th12/th12_web/sdl-runtime/shell.mjs'),'utf8');
source=source.replaceAll('/savesth11','/savesth14').replaceAll('th11_','th14_');
const pathSource=source.match(/^function path\(value\).*$/m)[0];
const start=source.indexOf('async function command(m){'),end=source.indexOf('\nlet queue=',start);assert(start>=0&&end>start);
let allocations=0,frees=0;
const context={game:'th14',TextDecoder,Uint8Array,JSON,Error,coreError:()=>string(c.error_data()),
 Module:{get HEAPU8(){return new Uint8Array(memory.buffer);},FS:{readFile:path=>{assert.equal(path,'/savesth14/replay/th14_01.rpy');return saved;}}},
 core:{malloc:n=>{++allocations;return c.allocate(n);},free:p=>{++frees;c.release(p);}},
 callCore:async(name,...args)=>{assert.equal(name,'th14_replay_description');return c.describe(...args);}};
const command=runInNewContext(`(()=>{${pathSource}\n${source.slice(start,end)}\nreturn command;})()`,context);
const response=await command({command:'playback',action:'inspect',path:'replay/th14_01.rpy'});assert.deepEqual(JSON.parse(JSON.stringify(response.description)),d);
await assert.rejects(command({command:'playback',action:'inspect',path:'../th14_01.rpy'}));
await assert.rejects(command({command:'playback',action:'inspect',path:'scoreth14.dat'}));
assert.equal(allocations,frees);assert.equal(allocations,1);
const report={passed:true,validNativeMetadataCases:rows.length,ordinaryMenuSavedFile:true,malformedNativeFilesRejected:invalid.length,
 actualShellPlaybackInspectCommandExecuted:true,actualNativeDecoderUsed:true,pathTraversalAndNonReplayPathsRejected:true,
 allocatedPayloadsFreed:true,description:d,rows,fixtureWasmSha256:build.wasmSha256,
 browserRetestAccepted:false,playbackOpenPauseSeekRateImplemented:false,productionDeployed:false,completeGame:false};
writeFileSync(resolve(H,'qualified.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({...report,rows:undefined}));
