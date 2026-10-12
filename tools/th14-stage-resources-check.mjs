// Resource integration, not proof of STD/ECL/MSG execution semantics.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/stage-resources-check');
mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync('py',['-3','tools/th14-ecl-animation-slots-native.py'],{cwd:root,stdio:'inherit',windowsHide:true});
const nativeSlots=JSON.parse(readFileSync(resolve(root,'artifacts/th14/ecl-animation-slots-native.json'),'utf8'));
execFileSync(process.execPath,[resolve(root,'runtimes/th13/th13_web/scripts/cpp/build-engine.mjs'),'--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'stages.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14',
 'tests/cpp/th14-stage-resources-fixture.cpp',...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const sha=b=>createHash('sha256').update(b).digest('hex'),archive=JSON.parse(readFileSync(resolve(root,'artifacts/archive-differential/th14.json'),'utf8'));
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th14.dat'].path);
// Archive retains this buffer until the resource checks finish.
const p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);assert.equal(c.open_archive(p,dat.length),1);
const string=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
const resources=[],stages=[];
for(let stage=1;stage<=7;++stage){
 assert.equal(c.load_stage(stage),1,`stage ${stage}: ${string(c.last_file())}: ${string(c.error())}`);
 assert.equal(string(c.background_name()),`st0${stage}wl.anm`);assert.ok(c.ecl_count()>0);
 const animations=nativeSlots.stages[stage-1].animations.map(row=>{
  assert.equal(row.enemySlot,row.file-8);const i=row.enemySlot-2;
  assert.equal(string(c.ecl_animation_name(i)),row.name);assert.equal(string(c.provider_animation_name(row.file)),row.name);
  assert.ok(c.ecl_animation_scripts(i)>0,row.name);return {...row,scripts:c.ecl_animation_scripts(i)};
 });
 for(let character=0;character<3;++character)for(let subtype=0;subtype<2;++subtype){
  const index=character*2+subtype,name=`st0${stage}${String.fromCharCode(97+index)}.msg`,row=archive.decoded.find(r=>r.name===name);
  assert.equal(c.dialogue_index(character,subtype),index);const data=new Uint8Array(c.memory.buffer,c.message_data(index),c.message_size(index));
  assert.equal(sha(data),row.sha256,name);resources.push({name,sha256:row.sha256});
 }
 stages.push({stage,subroutines:c.ecl_count(),animations});
}
assert.equal(c.load_stage(0),0);assert.equal(c.load_stage(8),0);
const report={passed:true,scope:'Seven original stage resource bundles and all 42 message identities; STD names and six character/equipment dialogue selections. Runtime command semantics, pixel equivalence and complete gameplay remain separate.',stages,resources,archiveSha256:sha(dat),wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries(['StageFiles.hpp','GameResources.cpp','GameSessionResources.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,'cpp/game',p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-stage-resources-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log('PASS: seven TH14 stage bundles and 42 original dialogue resource identities.');
