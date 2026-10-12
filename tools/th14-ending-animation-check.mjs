import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/ending-animation-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-ending-animation-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),fixture='tests/cpp/th14-ending-animation-fixture.cpp',path=resolve(out,'ending-animation.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',path],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/ending-animation-native.json'),'utf8'));
for(const r of proof.loader){assert.equal(r.flags,1);assert.equal(r.resourcePresent,true);}
for(const [i,r] of proof.rows.entries()){
 const p=c.run(r.op,r.difficulty,r.file,r.slot,r.program);assert.notEqual(p,0,`run ${i}`);
 const expected=[r.offset,+r.retired,r.handle,+!!r.vm.length,...(r.vm.length?r.vm:Array(11).fill(0))];
 assert.deepEqual(Array.from(new Uint32Array(c.memory.buffer,p,15)),expected,`retail image ${i}: ${JSON.stringify(r)}`);
 if(r.vm.length){assert.deepEqual(r.bindings,[1]);assert.equal(c.file_id(),proof.loader[r.file].fileId,`resource file ${i}`);}
}
for(const [i,r] of proof.textRows.entries()){
 const plain=Buffer.from(r.plain,'hex');new Uint8Array(c.memory.buffer,c.text_input(),plain.length).set(plain);assert.equal(c.text_run(r.op,r.line,r.color,plain.length),0,`text ${i}`);
 assert.equal(c.text_state(0),r.finalLine);assert.equal(c.text_state(1),r.offset);assert.equal(c.text_state(2),r.texts.length);assert.deepEqual(Array.from({length:5},(_,n)=>c.text_state(n+3)),r.interrupts);
 for(const [n,t] of r.texts.entries()){const p=c.text_request(n),words=Array.from(new Uint32Array(c.memory.buffer,p,6));assert.deepEqual(words.slice(0,5),[t.handle,...t.args.slice(0,4)]);assert.equal(t.args[4],0);assert.equal(Buffer.from(new Uint8Array(c.memory.buffer,c.text_bytes(n),words[5])).toString('hex'),t.bytes,`decoded text ${i} request ${n}`);}
}
for(const r of proof.musicRows){const bytes=Buffer.from(r.path,'ascii');new Uint8Array(c.memory.buffer,c.text_input(),bytes.length).set(bytes);const p=c.music_run(bytes.length,r.initial);assert.notEqual(p,0);assert.equal(c.music_cue(),r.path.endsWith('_16')?15:16);assert.equal(Buffer.from(new Uint8Array(c.memory.buffer,p,0x42c)).toString('hex'),r.settings,'all BGM status bytes');}
for(const r of proof.switches){const p=c.staff_run(r.time,r.wait,r.line,r.flags,r.schedule,r.rate);assert.notEqual(p,0);assert.deepEqual(Array.from(new Uint32Array(c.memory.buffer,p,13)),[r.offset,r.finalFlags,r.finalLine,r.color,...r.timers],`staff switch ${JSON.stringify(r)}`);assert.deepEqual(Array.from({length:25},(_,n)=>c.staff_handle(n)),r.handles);}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-ending-animation-verified.json'),JSON.stringify({passed:true,cases:proof.rows.length,loaderCases:proof.loader.length,textCases:proof.textRows.length,musicCases:proof.musicRows.length,staffSwitchCases:proof.switches.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail420260/4202d0 image commands8/15/16/17 versus production Ending::update, all ordinary difficulties/four resource slots/image slots0/7/15 and three ANM programs. Allocation/resource binding/registration/retirement are controlled boundaries; the actual native first ANM update executes. Compares creation filtering, pointer advance, retirement request, registry handles, layer/origin/position/rotation/scale. Text commands3/4 compare five-line wrapping/clear requests, all raw text and color bytes, decoded by real434330; glyph delivery and registry interrupt services are controlled. BGM10 and actual445710 compare both original ending paths and all42c status bytes, audio delivery controlled. Staff switch12 compares timer resets, instruction/flags/line/color and all handle slots; loading and memset boundaries controlled. Retail420c50 records native loading file IDs and resource completion; actual asynchronous wall time/load implementation is excluded. No GPU proof.',sourceHashes:Object.fromEntries([fixture,'cpp/game/Ending.cpp','cpp/game/AnmManager.cpp','cpp/game/AnmInterpreter.cpp','cpp/game/EnemyAnimations.cpp'].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),toolHashes:Object.fromEntries(['tools/th14-ending-animation-native.py','tools/th14-ending-animation-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.rows.length} retail ending image cases, ${proof.loader.length} loading slots, ${proof.textRows.length} text cases, ${proof.musicRows.length} BGM cases, ${proof.switches.length} staff switches`);
