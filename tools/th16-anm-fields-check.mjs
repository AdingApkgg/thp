import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/anm-fields-check');mkdirSync(out,{recursive:true});
const python=process.env.TH_NATIVE_PYTHON;if(!python)throw Error('set TH_NATIVE_PYTHON');
execFileSync(python,['tools/th16-anm-fields-native.py'],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/anm-fields-native.json'),'utf8'));
const sources=['AnmInterpreter','AnmVm','AnmGeometry','Interpolation','AnmResource'].map(n=>`cpp/game/${n}.cpp`),fixture='tests/cpp/th16-anm-fields-fixture.cpp',wasm=resolve(out,'fields.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',...sources,fixture,'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
for(const op of proof.noops)assert.equal(c.canonical(op),op===5?64:0,`native default opcode ${op}`);
assert.equal(c.canonical(411),0xffff,'unimplemented scalar rotation interpolation must fail loading');
assert.equal(c.canonical(214),0,'214 exceeds the incremented low-band guard');
assert.notEqual(c.canonical(300),0,'300 has a special retail sprite handler');
assert.notEqual(c.canonical(300),0xffff,'300 binding is implemented');
const string=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
for(const row of proof.cases){
 const label=`op=${row.op} seed=${row.seed} value=${row.value} second=${row.second} refs=${row.refs}`;
 assert.equal(c.run(row.op,row.value,row.second,row.flags,row.flags2,row.refs),0,label+' status');
 ['afterFlags','afterFlags2','layer','advance','mode10Calls'].forEach((key,n)=>assert.equal(c.word(n)>>>0,row[key],label+' '+key));
 assert.equal(c.word(5),c.word(6),label+' canonical unrelated flags preserved');
}
const sha=b=>createHash('sha256').update(b).digest('hex'),tracked=[...sources,fixture,'cpp/game/AnmOpcodes.hpp','cpp/game/AnmVm.hpp','cpp/game/AnmResource.hpp','cpp/game/Th16AnmDispatch.hpp','cpp/game/Timer.hpp','cpp/game/PortTitle.hpp',...['AnmTrace','Interpolation','AnmGeometry','Rng','Types'].map(n=>`cpp/game/${n}.hpp`)];
for(const row of proof.shapes){const label=`op=${row.op} flags=${row.flags} value=${row.value} second=${row.second} refs=${row.refs}`;assert.equal(c.run_shape(row.op,row.flags,row.value,row.second,row.refs),0,label+' controlled stop');row.words.forEach((n,i)=>assert.equal(c.shape_word(i)>>>0,n,label+` shape field ${i}`));}
for(const row of proof.flips){const label=JSON.stringify(row);assert.equal(c.run_flip(row.op,row.flags,row.valueBits),0,label+' controlled stop');row.words.forEach((n,i)=>assert.equal(c.flip_word(i)>>>0,n,label+` flip word ${i}`));}
for(const row of proof.pivots){const label=JSON.stringify(row);assert.equal(c.run_pivot(row.value,row.second,row.refs),0,label+' controlled stop');row.words.forEach((n,i)=>assert.equal(c.pivot_word(i)>>>0,n,label+` pivot word ${i}`));}
for(const row of proof.rings){const label=JSON.stringify(row);assert.equal(c.run_ring(row.op,row.flags,row.value,row.refs),0,label+' controlled stop');row.words.forEach((n,i)=>assert.equal(c.ring_word(i)>>>0,n,label+` allocation word ${i}`));}
const archive=JSON.parse(readFileSync(resolve(root,'artifacts/archive-differential/th16.json'),'utf8')),resourceRows=[];
for(const row of archive.decoded.filter(n=>n.name.endsWith('.anm'))){
 const data=readFileSync(resolve(archive.extraction,row.name));assert.equal(sha(data),row.sha256,`${row.name}: original extraction hash`);
  const counts=new Map();let base=0;
 do{const sprites=data.readUInt16LE(base+4),scripts=data.readUInt16LE(base+6),stride=data.readUInt32LE(base+36),end=stride?base+stride:data.length;assert.ok(end<=data.length&&end>=base+64);
  for(let n=0;n<scripts;++n){let at=base+data.readUInt32LE(base+64+sprites*4+n*8+4);while(at+8<=end){const op=data.readInt16LE(at),length=data.readUInt16LE(at+2);if(op===-1)break;assert.ok(length>=8&&length%4===0&&at+length<=end);counts.set(op,(counts.get(op)??0)+1);at+=length;}}
  if(!stride)break;base=end;
 }while(base<data.length);
 const unresolvedOpcodes=[...counts].filter(([op])=>c.canonical(op)===0xffff).map(([opcode,instructions])=>({opcode,instructions}));
 const p=c.allocate(data.length);new Uint8Array(c.memory.buffer,p,data.length).set(data);
 try{const result=c.open_resource(p,data.length);resourceRows.push({name:row.name,result,detail:string(c.resource_error()),unresolvedOpcodes});}finally{c.release(p);}
}
const report={passed:true,title:16,completeGame:false,cases:proof.cases.length,shapeInitializerCases:proof.shapes.length,scaleFlipCases:proof.flips.length,pivotCases:proof.pivots.length,ringAllocationRequestCases:proof.rings.length,nativeDefaultClassifications:proof.noops.length,scope:proof.scope,mode10Factory:'Recorded native call and controlled production environment; real geometry initializer remains explicitly unsupported.',nativeExecutableSha256:proof.executableSha256,handlers:proof.handlers,wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(tracked.map(n=>[n,sha(readFileSync(resolve(rt,n)))])),toolHashes:Object.fromEntries(['tools/th16-anm-fields-check.mjs','tools/th16-anm-fields-native.py','tools/th16-anm-dispatch-header.py'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))};
writeFileSync(resolve(root,'docs/porting/th16-anm-fields-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS ${proof.cases.length} native TH16 ANM field cases; ${proof.shapes.length} shape initializer cases; ${proof.flips.length} scale flips; ${proof.pivots.length} pivots; ${proof.rings.length} ring/arc allocation requests`);
writeFileSync(resolve(root,'docs/porting/th16-anm-resource-gaps-oct10.json'),JSON.stringify({title:16,completeGame:false,scope:'First loader failure per original ANM, after rejecting unimplemented native handlers. Successful loading does not verify remaining mapped semantics.',resources:resourceRows.length,loaded:resourceRows.filter(n=>n.result>=0).length,rows:resourceRows,sourceHashes:report.sourceHashes},null,2)+'\n');
console.log(`${resourceRows.filter(n=>n.result>=0).length}/${resourceRows.length} ANM load; unresolved first opcodes: ${[...new Set(resourceRows.filter(n=>n.result<0).map(n=>n.detail))].join('; ')}`);
