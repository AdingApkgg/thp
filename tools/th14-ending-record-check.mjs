import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/ending-record-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-ending-record-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),fixture='tests/cpp/th14-ending-record-fixture.cpp',path=resolve(out,'ending-record.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',path],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/ending-record-native.json'),'utf8'));
for(const [i,row] of proof.rows.entries()){
 const p=c.run(row.selection,row.difficulty,row.continues,row.initial);
 assert.equal(c.ending_index(),row.index,`index${i}`);assert.equal(c.seen(),row.seen,`seen${i}`);
 assert.equal(Buffer.from(new Uint8Array(c.memory.buffer,p,0x42c)).toString('hex'),row.settings,`all status bytes${i}`);
 assert.equal(proof.files[c.ending_index()],`e${String(c.ending_index()).padStart(2,'0')}.msg`);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-ending-record-verified.json'),JSON.stringify({passed:true,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Unmodified retail41fbca..41fc37 index/seen/status block versus production Ending::record_progress, including all six equipment choices/four ordinary difficulties, zero/nonzero/negative continues, preserved incoming bits and all42c settings bytes. Retail4d1d6c filename table checked. Does not prove the ending interpreter, text/animation/audio rendering or staff roll.',sourceHashes:Object.fromEntries([fixture,'cpp/game/Ending.cpp','cpp/game/Ending.hpp'].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),toolHashes:Object.fromEntries(['tools/th14-ending-record-native.py','tools/th14-ending-record-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.rows.length} retail TH14 ending selection/status cases`);
