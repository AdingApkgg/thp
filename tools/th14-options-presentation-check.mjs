import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/options-presentation-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-options-presentation-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,[resolve(root,'runtimes/th13/th13_web/scripts/cpp/build-engine.mjs'),'--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),fixture='tests/cpp/th14-options-presentation-fixture.cpp',wasmPath=resolve(out,'options.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasmPath],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasmPath),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,sha=b=>createHash('sha256').update(b).digest('hex');
const oraclePath='artifacts/th14/options-presentation-native-oct11.json',oracle=JSON.parse(readFileSync(resolve(root,oraclePath))),failures=[];
for(const [selected,cancel] of [[0,0],[1,0],[2,0],[3,0],[4,0],[0,1],[1,1],[2,1],[3,1]]){assert.equal(c.run(selected,cancel),1);const expected=new Map(oracle.rows[cancel?4:selected].interrupts);for(let script=23;script<=48;++script){const actual=c.value(script),value=expected.get(script)||0;if(actual!==value)failures.push({selected,cancel,script,actual,expected:value});}}
const report={passed:!failures.length,completeGame:false,nativeEquivalent:false,routes:9,failures,nativeExecutableSha256:oracle.executableSha256,oraclePath,oracleSha256:sha(readFileSync(resolve(root,oraclePath))),wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([fixture,'cpp/game/TitleOptions.cpp'].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),toolHashes:Object.fromEntries(['tools/th14-options-presentation-native.py','tools/th14-options-presentation-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))])),scope:oracle.scope+' Production synthetic label30/31 scripts expose each immediate target for five rows and four cancel-to-Quit routes. Production call order/GPU layout excluded.'};
writeFileSync(resolve(out,process.argv.includes('--before')?'before.json':'result.json'),JSON.stringify(report,null,2)+'\n');if(report.passed)writeFileSync(resolve(root,'docs/porting/th14-options-presentation-verified-oct11.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:report.passed,routes:report.routes,failureCount:failures.length,failures:failures.slice(0,6)}));if(!report.passed)process.exitCode=1;
