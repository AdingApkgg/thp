import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/hud-text-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-hud-text-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/hud-text-native.json'),'utf8')),sha=b=>createHash('sha256').update(b).digest('hex'),sources=['cpp/game/HudTh14Text.cpp','cpp/game/AsciiText.cpp','cpp/game/AnmVm.cpp','cpp/game/SpellTiming.cpp','tests/cpp/th14-hud-text-fixture.cpp'],path=resolve(out,'hud-text.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',path],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(path),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;let glyphs=0;
for(const [n,row] of proof.rows.entries()){
 assert.equal(c.run(row.high,row.displayed,row.alpha,row.power,row.continues,row.lifeFragments,row.bombFragments,row.pointValue,row.graze,row.lifeAwards),row.glyphs.length,`case ${n}`);
 row.glyphs.forEach((g,i)=>{for(const [k,key] of ['sprite','color','filtered'].entries())assert.equal(c.word(i,k)>>>0,Number(g[key]),`case ${n} glyph ${i} ${key}`);assert.equal(c.real(i,0),g.x,`case ${n} glyph ${i} x`);assert.equal(c.real(i,1),g.y,`case ${n} glyph ${i} y`);});glyphs+=row.glyphs.length;
}
const report={passed:true,cases:proof.rows.length,glyphs,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 43144a..4318b6 HUD sidebar block, actual 40bb60/40bc70 grouping and 40bf20 glyph layout. Score/high-score comma thresholds and Continue suffix, life/bomb fragments including the 49-extend sentinel, power/fractions/max power, PIV and graze: glyph indices, positions, scale, colors and right alignment at resolution factor 1. CRT formatting/ASCII queue/atlas/GPU boundaries controlled. Excludes practice high-score selection, live HUD alpha source, result/spell/timer layouts, icons and pixels.',sourceHashes:Object.fromEntries([...sources,'cpp/game/HudTh14Text.hpp','cpp/game/Th14LifeFragments.hpp','cpp/game/Hud.cpp','cpp/game/AsciiText.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-hud-text-native.py','tools/th14-hud-text-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-hud-text-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} native HUD cases, ${glyphs} glyph submissions.`);
