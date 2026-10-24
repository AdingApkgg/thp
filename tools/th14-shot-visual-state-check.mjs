import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/shot-visual-state-check');mkdirSync(out,{recursive:true});
assert(process.argv[2],'Pass a source-bound core-build.json object manifest.');const manifest=resolve(process.argv[2]),build=JSON.parse(read(manifest)),sha=b=>createHash('sha256').update(b).digest('hex');
for(const row of build.objectBindings)assert.equal(sha(read(row.path)),row.sha256,row.path);
const label=process.argv[3]??'current',wasm=resolve(out,label+'.wasm');assert(/^[a-z0-9-]+$/.test(label));
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14','tests/cpp/th14-shot-visual-state-fixture.cpp',...build.objectBindings.map(x=>x.path),'-o',wasm],{cwd:rt,env:{...process.env,TEMP:out,TMP:out},stdio:'inherit',windowsHide:true});
const bytes=read(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const differences=[];for(const layer of[0,7,13,23]){const actual=c.template_layer(layer);if(actual!==layer)differences.push({case:'copied-template-layer',layer,actual});}
const word=f=>{const b=Buffer.alloc(4);b.writeFloatLE(f);return b.readUInt32LE();};
for(let active=0;active<4;++active)for(let advanced=0;advanced<2;++advanced)for(let duplicate=0;duplicate<4;++duplicate){
 assert.equal(c.last_hit(active,advanced,duplicate),1);const hits=advanced?active&~duplicate&3:0,xy=hits&2?[-10,-12]:hits&1?[10,12]:[-77,88],expected=[...xy.map(word),7*((hits&1)+((hits>>1)&1))],actual=Array.from({length:3},(_,i)=>c.hit_value(i)>>>0);
 if(actual.some((x,i)=>x!==expected[i]))differences.push({case:'last-hit-position',active,advanced,duplicate,expected,actual});
}
const report={passed:differences.length===0,templateLayerCases:4,lastHitConnectionCases:32,differences,wasmSha256:sha(bytes),objectManifestSha256:sha(read(manifest)),fixtureSha256:sha(read(resolve(rt,'tests/cpp/th14-shot-visual-state-fixture.cpp'))),scope:'Production ShotManager connections: retain declared copied ANM template layer; wire the actual damage collector last-hit output into EnemyState.death_reference, preserving it when no new hit occurs. Two controlled circle areas exercise pool order, inactive entries, frozen frames and duplicate stamps. Expected layer and area positions are declared inputs; no original game assets or original computed states are injected. Original retail evidence is separately supplied by live VM registry snapshots and collector/death disassembly. These connection tests do not certify full GPU rendering, complete original factories or complete gameplay.',completeGame:false,nativeEquivalent:false};
write(resolve(out,label+'-report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:report.passed,differences:report.differences.length,first:report.differences[0]}));
if(label==='current'){assert(report.passed);write(resolve(root,'docs/porting/th14-shot-visual-state-verified-oct24.json'),JSON.stringify(report,null,2)+'\n');}
