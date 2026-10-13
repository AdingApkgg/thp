// Read-only candidate observations; native memory is captured separately.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),sha=b=>createHash('sha256').update(b).digest('hex');
const replayPath=resolve(root,process.argv[2]),label=process.argv[3];assert(/^[a-z0-9-]{1,64}$/.test(label));
const out=resolve(root,'artifacts/th14/late-combat-candidate',label);mkdirSync(out,{recursive:true});
const replay=readFileSync(replayPath),build=JSON.parse(readFileSync(resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json')));
for(const [name,digest] of Object.entries(build.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,name))),digest,name);
const fixture='tests/cpp/th14-late-combat-fixture.cpp',objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'collision.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(name=>name.endsWith('.o')).map(name=>resolve(objects,name)),'-o',wasm],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports,upload=b=>{const p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);return p;};
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path);
assert.equal(c.open_archive(upload(archive),archive.length),1);assert.equal(c.begin_combat_reference(upload(replay),replay.length),1);
const words=(p,n)=>Array.from(new Uint32Array(c.memory.buffer,p,n)),frames=[];
for(let i=1;i<=14390;i++){
 assert.equal(c.tick(0),1);assert.equal(c.draw(),1);const state=words(c.reference_data(),32);
 if(state[0]>=14340&&state[0]<=14390){
  const bullets=words(c.reference_bullet_data(),c.reference_bullet_words());
  frames.push({stageFrame:state[0],state,shots:words(c.reference_shot_data(),c.reference_shot_words()),enemies:words(c.reference_enemy_data(),c.reference_enemy_words()),phases:words(c.reference_phase_data(),c.reference_phase_words()),areas:words(c.reference_area_data(),c.reference_area_words()),
   bulletDetails:Array.from({length:bullets.length/16},(_,j)=>bullets.slice(j*16,(j+1)*16))});
 }
}
assert.equal(frames.length,51);
writeFileSync(resolve(out,'observations.json'),JSON.stringify({diagnosticOnly:true,completeGame:false,nativeEquivalent:false,
 frames,sourceHashes:build.sourceHashes,replaySha256:sha(replay),wasmSha256:sha(bytes),
 fixtureSha256:sha(readFileSync(resolve(rt,fixture))),toolSha256:sha(readFileSync(import.meta.filename)),
 scope:'Production core with unchanged stage5 recording and ordinary physics; all raw late-window collision and bullet fields retained. No native equality or completion assertion.'},null,2)+'\n');
console.log(JSON.stringify({frames:frames.length,out}));
