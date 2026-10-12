import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync,spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/dialogue-text-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-dialogue-text-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
nativePython('tools/th14-dialogue-initialize-native.py',{cwd:root,stdio:'ignore',windowsHide:true});
nativePython('tools/th14-dialogue-position-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
nativePython('tools/th14-dialogue-speaker-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
nativePython('tools/th14-dialogue-lifecycle-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const compiler=resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),oldObjects=resolve(root,'artifacts/th14/campaign-handoffs-all-oct11/objects'),env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
const flags=['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14'];
// Recompile the full engine because Dialogue.hpp changes class storage.
const build=JSON.parse(readFileSync(resolve(oldObjects,'../engine-build.json')));
const sourceHashes=Object.fromEntries(Object.keys(build.sourceHashes).map(n=>[n,createHash('sha256').update(readFileSync(resolve(rt,n))).digest('hex')]));
const sha=b=>createHash('sha256').update(b).digest('hex');
const objects=build.sources.map(source=>resolve(out,source.replaceAll('/','_')+'.o')),cachePath=resolve(out,'objects.json'),signature=sha(Buffer.from(JSON.stringify({sourceHashes,flags,compiler:sha(readFileSync(compiler))})));let cursor=0;
const cache=existsSync(cachePath)?JSON.parse(readFileSync(cachePath)):null;
const headerHashes=Object.fromEntries(Object.entries(sourceHashes).filter(([n])=>!build.sources.includes(n))),commonKey=sha(Buffer.from(JSON.stringify({headerHashes,flags,compiler:sha(readFileSync(compiler))}))),compileKeys=Object.fromEntries(build.sources.map((n,i)=>[objects[i],sha(commonKey+sourceHashes[n])])),pending=build.sources.map((_,i)=>i).filter(i=>cache?.compileKeys?.[objects[i]]!==compileKeys[objects[i]]||!existsSync(objects[i])||sha(readFileSync(objects[i]))!==cache?.objectHashes?.[objects[i]]);
if(pending.length){
 await Promise.all(Array.from({length:4},async()=>{while(cursor<pending.length){const i=pending[cursor++];await new Promise((accept,reject)=>{const p=spawn(compiler,[...flags,'-c',build.sources[i],'-o',objects[i]],{cwd:rt,env,windowsHide:true,stdio:['ignore','pipe','pipe']});let log='';p.stdout.on('data',b=>log+=b);p.stderr.on('data',b=>log+=b);p.on('error',reject);p.on('exit',n=>n?reject(Error(log)):accept());});}}));}
for(const [n,h] of Object.entries(sourceHashes))assert.equal(sha(readFileSync(resolve(rt,n))),h,'source changed during build '+n);
writeFileSync(cachePath,JSON.stringify({signature,compileKeys,sourceHashes,objectHashes:Object.fromEntries(objects.map(p=>[p,sha(readFileSync(p))]))},null,2)+'\n');
const fixture='tests/cpp/th14-dialogue-text-fixture.cpp',wasm=resolve(out,'dialogue.wasm');
execFileSync(compiler,[...flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',fixture,...objects,'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const archive=JSON.parse(readFileSync(resolve(root,'artifacts/archive-differential/th14.json'))),front=readFileSync(resolve(archive.extraction,'front.anm')),ptr=c.allocate(front.length);new Uint8Array(c.memory.buffer,ptr,front.length).set(front);assert.equal(c.load_front(ptr,front.length),1);
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/dialogue-text-native.json')));
assert.equal(proof.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
const init=JSON.parse(readFileSync(resolve(root,'artifacts/th14/dialogue-initialize-native.json'))).constructor;
assert.equal(c.initialize(),1);assert.deepEqual(Array.from(new Uint32Array(c.memory.buffer,c.data(),c.words())),[...init.lines.flatMap(([dimensions,flags,callback],i)=>[init.scripts[i],init.interrupts.find(([handle])=>handle===100+i)?.[1]??0,dimensions,flags,callback?1:0]),...init.state]);
const positions=JSON.parse(readFileSync(resolve(root,'artifacts/th14/dialogue-position-native.json')));
for(const r of positions.cases){assert.equal(c.position_callback(...r.input),1,JSON.stringify(r.input));assert.deepEqual(Array.from(new Uint32Array(c.memory.buffer,c.data(),c.words())),r.position,JSON.stringify(r.input));}
const speakers=JSON.parse(readFileSync(resolve(root,'artifacts/th14/dialogue-speaker-native.json')));
assert.equal(speakers.executableSha256,proof.executableSha256);
for(const r of speakers.cases){assert.equal(c.speaker_command(...r.input),0,JSON.stringify(r.input));const expected=[...r.state,...r.lines.flat()];for(const handle of [90,95,100,101,102,103]){const i=r.interrupts.findLastIndex(([id])=>id===handle),label=i<0?0:r.interrupts[i][1];expected.push(label,label);}assert.deepEqual(Array.from(new Uint32Array(c.memory.buffer,c.data(),c.words())),expected,JSON.stringify(r.input));}
const lifecycle=JSON.parse(readFileSync(resolve(root,'artifacts/th14/dialogue-lifecycle-native.json')));assert.equal(lifecycle.executableSha256,proof.executableSha256);for(const r of lifecycle.cases){assert.equal(c.lifecycle_command(...r.input),0,JSON.stringify(r.input));const expected=[...r.handles];for(let i=0;i<13;i++){const label=r.interrupts.findLast(([h])=>h===100+i)?.[1]??0;expected.push(label,label,...r.retired[i]);}assert.deepEqual(Array.from(new Uint32Array(c.memory.buffer,c.data(),c.words())),expected,JSON.stringify(r.input));}
for(const r of proof.cases){assert.equal(c.run(...r.input),0,JSON.stringify(r.input));const actual=Array.from(new Uint32Array(c.memory.buffer,c.data(),c.words()));
 const expected=r.writes.flatMap(([slot,color,offset,font,style,hex,plain])=>{const b=Buffer.from(hex,'hex');return [slot,color,offset>>>0,font>>>0,style>>>0,plain,b.length,...b];});
 expected.push(0xffffffff,...r.state);
 for(let n=0;n<4;n++){const last=r.interrupts.filter(([slot])=>slot===n+3).at(-1);expected.push(...r.positions[n],last?last[1]:0);}
 expected.push(r.allocations.length);if(r.allocations.length)expected.push(...r.allocations[0],...r.widths);expected.push(...r.retired,r.backgroundPresent);
 assert.deepEqual(actual,expected,JSON.stringify(r.input));}
writeFileSync(resolve(root,'docs/porting/th14-dialogue-text-verified-oct11.json'),JSON.stringify({passed:true,cases:proof.cases.length,constructorCases:1,lifecycleCases:lifecycle.cases.length,positionCallbackCases:positions.cases.length,speakerExpressionCases:speakers.cases.length,objectManifestSha256:sha(readFileSync(cachePath)),nativeExecutableSha256:proof.executableSha256,frontAnmSha256:sha(front),wasmSha256:sha(bytes),sourceHashes,tools:Object.fromEntries(['tools/th14-dialogue-text-native.py','tools/th14-dialogue-initialize-native.py','tools/th14-dialogue-position-native.py','tools/th14-dialogue-speaker-native.py','tools/th14-dialogue-lifecycle-native.py','tools/th14-dialogue-text-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))])),fixtureSha256:sha(readFileSync(resolve(rt,fixture))),scope:'Complete retail constructor field/line initialization, MSG 7/8/9/13/14 state and deferred/synchronous family delivery requests (including 32-bit expression labels), original draw callback with parent position transform at three display scales, MSG 3/4/5/6/23/24/30 deferred family interrupt and panel retirement, and MSG 15/16/17/18/28 including original encrypted-text decoder, layout dispatch, panel replacement/close and child-variable sizing. ANM allocation/lookups/text delivery/interrupt, constructor template copy/ANM update, and CRT atoi/strchr are controlled boundaries. Callback cases omit parent rotation. Synthetic stopped portrait children verify that both delivery forms reach the full family; whole original synchronous/deferred handlers with real ANM scripts are checked separately by th14-dialogue-panel-family-check.mjs. Portable uses actual front.anm scripts and real ANM creation. Layout16 ordinary-text requests excluded because actual front.anm has no matching children. Compares text requests, plain flag, line positions, layout/width state, final interrupts and old panel retirement; no full-game pixels claim.'},null,2)+'\n');console.log(`PASS: ${proof.cases.length} native TH14 dialogue text/layout cases, ${positions.cases.length} draw callbacks, ${speakers.cases.length} speaker/expression cases and constructor.`);
