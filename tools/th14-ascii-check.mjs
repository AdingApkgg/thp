import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/ascii-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-ascii-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/ascii-native.json'),'utf8')),sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['cpp/game/AsciiText.cpp','cpp/game/AnmVm.cpp','tests/cpp/th13-ascii-fixture.cpp'],path=resolve(out,'th14.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',path],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(path),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const run=(text,font,sx=1,sy=1,shadow=0)=>{const b=Buffer.from(text+'\0'),p=c.allocate(b.length);try{new Uint8Array(c.memory.buffer,p,b.length).set(b);return c.run(p,font,sx,sy,shadow);}finally{c.release(p);}};
let glyphs=0;
for(const row of proof.cases){
 const label=`font ${row.font} scale ${row.scale} shadow ${row.shadow} ${JSON.stringify(row.text)}`;
 assert.equal(run(row.text,row.font,...row.scale,Number(row.shadow)),row.glyphs.length,label);
 row.glyphs.forEach((g,i)=>{for(const [k,key] of ['sprite','color','filtered'].entries())assert.equal(c.word(i,k)>>>0,Number(g[key]),`${label} glyph ${i} ${key}`);assert.equal(c.real(i,0),g.x,`${label} glyph ${i} x`);assert.equal(c.real(i,1),g.y,`${label} glyph ${i} y`);});glyphs+=row.glyphs.length;
}
assert.equal(run('0',6),-1);assert.equal(run('0',-1),-1);
const report={passed:true,nativeExecutableSha256:proof.executableSha256,nativeStringCases:proof.cases.length,glyphs,wasmSha256:sha(bytes),scope:'Retail TH14 ASCII glyph selection, left/top positions, filtering, newlines and shadows at resolution multiplier 1.0. Controlled sprite/GPU boundaries; excludes pixels, other alignments/resolutions and full HUD formatting.',sourceHashes:Object.fromEntries([...sources,'cpp/game/AsciiText.hpp','cpp/game/PortTitle.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-ascii-native.py','tools/th14-ascii-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-ascii-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.nativeStringCases} native strings, ${glyphs} glyph submissions.`);
