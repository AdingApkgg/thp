import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/score-popup-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-score-popup-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out},wasm=resolve(out,'score-popup.wasm'),fixture='tests/cpp/th14-score-popup-fixture.cpp';
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,'cpp/game/ScorePopups.cpp','cpp/game/AsciiText.cpp','cpp/game/AnmVm.cpp','-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/score-popup-native.json'),'utf8'));
const put=values=>{const p=c.allocate(values.length*4);new Uint32Array(c.memory.buffer,p,values.length).set(values);return p;};
const pool=()=>Array.from(new Uint32Array(c.memory.buffer,c.pool(),18*18));
const bitBuffer=new ArrayBuffer(4),word=new Uint32Array(bitBuffer),real=new Float32Array(bitBuffer);const fbits=v=>{real[0]=v;return word[0];},float=v=>{word[0]=v;return real[0];};
const string=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
let frames=0,glyphs=0,requests=0,bonusGlyphs=0;
for(const row of proof.factories){const p=put(row.initial.flat()),xyz=put(row.position);try{c.initialize(p,row.cursor,1);c.add(row.bonus,xyz,row.value,row.color,float(row.multiplier));assert.deepEqual(pool(),row.result.flat(),`factory ${row.bonus} cursor ${row.cursor} value ${row.value}`);assert.equal(c.cursor(),row.nextCursor);}finally{c.release(p);c.release(xyz);}}
for(const row of proof.timelines){const p=put(row.initial.flat()),player=put(row.player);try{
 c.initialize(p,1,row.rate);
 for(let frame=0;frame<row.states.length;frame++){
  const s=row.states[frame],label=`value ${row.value} rate ${row.rate} frame ${frame}`;c.tick();assert.deepEqual(pool(),s.words.flat(),label);
  assert.equal(c.glyph_count(player),s.glyphs.length,label);for(let n=0;n<s.glyphs.length;n++)assert.deepEqual([0,1,2,3].map(k=>c.glyph_word(n,k)>>>0),s.glyphs[n],`${label} glyph ${n}`);
  assert.equal(c.queue(),s.requests.length,label);
  for(let n=0;n<s.requests.length;n++){
   const q=s.requests[n];assert.equal(string(c.text(n)),q.text,label);
   let x=float(q.position[0]);for(const ch of q.text)x=Math.fround(x-(ch==='.'?2:3.5));
   const position=[fbits(x),fbits(Math.fround(float(q.position[1])-5)),q.position[2]];
   assert.deepEqual([0,1,2,3,4,5,6,7].map(k=>c.request_word(n,k)>>>0),[...position,q.color,2,2,0,1],`${label} text ${n}`);
  }
  assert.equal(c.bonus_draw(),s.bonusGlyphs.length,label);for(let n=0;n<s.bonusGlyphs.length;n++)assert.deepEqual([0,1,2,3,4].map(k=>c.bonus_glyph_word(n,k)>>>0),s.bonusGlyphs[n],`${label} bonus glyph ${n}`);
  bonusGlyphs+=s.bonusGlyphs.length;
  ++frames;glyphs+=s.glyphs.length;requests+=s.requests.length;
 }
}finally{c.release(p);c.release(player);}}
for(const row of proof.glyphCases){const p=put(row.initial.flat()),player=put(row.player);try{
 c.initialize(p,1,1);const label=`glyph value ${row.value} age ${row.age} distance ${float(row.player[0])}`;
 assert.equal(c.glyph_count(player),row.glyphs.length,label);for(let n=0;n<row.glyphs.length;n++)assert.deepEqual([0,1,2,3].map(k=>c.glyph_word(n,k)>>>0),row.glyphs[n],`${label} glyph ${n}`);
}finally{c.release(p);c.release(player);}}
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:true,factories:proof.factories.length,timelines:proof.timelines.length,frames,glyphs,requests,bonusGlyphs,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([fixture,'cpp/game/ScorePopups.cpp','cpp/game/ScorePopups.hpp','cpp/game/AsciiText.cpp','cpp/game/AsciiText.hpp','cpp/game/AnmVm.cpp','cpp/game/GameBattle.cpp','cpp/game/GameBattle.hpp','cpp/game/Timer.hpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th14-score-popup-native.py','tools/th14-score-popup-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))])),scope:'Actual retail 457f00 ordinary / 458000 bonus factories, complete 4579c0 pool update and 457ae0 ordinary glyph/bonus request delivery. All eighteen 72-byte slots compared, rate pointers normalized; cursor wrapping, signed values, timer flags, reserved data, binary32 damping/position, digit-specific retreat and player-distance alpha. Bonus center-alignment translation also compared through complete native 40bf20 and production AsciiText glyph delivery. Five-slot full/occupied allocation tested. Valid nonnegative cursors, finite multiplier 1.2, synthetic atlas and controlled render/ASCII factory boundaries; GPU geometry remains separate. Birth-frame nonfinite ordinary glyphs remain omitted in the production renderer.'};
report.glyphCases=proof.glyphCases.length;report.scope+=' Includes ten-digit per-glyph retirement and both sides of squared player-distance alpha thresholds. Playfield camera selection follows 40b920; actual GPU clipping remains excluded.';
writeFileSync(resolve(root,'docs/porting/th14-score-popup-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.factories} factories / ${frames} pool frames / ${glyphs} score glyphs / ${requests} bonus requests / ${bonusGlyphs} bonus glyphs / ${report.glyphCases} alpha/retirement cases`);
