import assert from 'node:assert/strict';
// Bring-up diagnostic using the actual production archive and session. A successful
// probe is only entry/update/draw evidence, never a claim that title-specific semantics match.
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const title=16,frames=0;
const held=0;if(!Number.isInteger(held)||held<0||held>255)throw Error('invalid held buttons');
if(![12,13,14,16,17,18].includes(title))throw Error('supported engine titles: 12, 13, 14, 16, 17, 18');
if(!Number.isSafeInteger(frames)||frames<0||frames>60000)throw Error('invalid frame count');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/options-session-check');
mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title',String(title)],{cwd:root,env,stdio:'inherit',windowsHide:true});
const engineBuild=JSON.parse(readFileSync(resolve(root,`runtimes/th13/th13_web/artifacts/cpp/engine-th${title}-build.json`),'utf8'));
const dir=resolve(root,`runtimes/th13/th13_web/artifacts/cpp/objects-th${title}`),wasm=resolve(out,'session.wasm');
const fixture='tests/cpp/th16-options-session-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',`-DPORT_TITLE=${title}`,fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const target=JSON.parse(readFileSync(resolve(root,title===12?'runtimes/th12/th12_web/target.json':`runtimes/th${title}/target.json`),'utf8'));
const dat=readFileSync(target.dataArchives[`th${title}.dat`].path),bytes=readFileSync(wasm);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
if(c.build_title()!==title)throw Error('wrong engine title');
const string=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
const p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);

const cases=[];assert.equal(c.open_archive(p,dat.length),1);
const sha=b=>createHash('sha256').update(b).digest('hex');
const levels=[0,99,100,229,230,389,390,589,590,839,840,1139,1140];
for(let character=0;character<4;character++)for(let season=0;season<5;season++){
 assert.equal(c.begin_season(character,season),1,string(c.error()));
 for(const [index,energy] of levels.entries()){
  const power=[0,99,100,200,300,399,400][index%7];assert.equal(c.upgrade(power,energy),1,`upgrade ${character}/${season}/${power}/${energy}`);
  const expected=levels.filter(v=>[100,230,390,590,840,1140].includes(v)&&energy>=v).length;
  assert.equal(c.option_count(0),Math.trunc(power/100));assert.equal(c.option_count(1),expected);
  for(let n=0;n<4;n++)assert.equal(c.option_valid(n),n<Math.trunc(power/100)?1:-1,`main ${character}/${season}/${n}`);
  for(let n=0;n<8;n++)assert.equal(c.option_valid(n+4),n<expected?1:-1,`season ${character}/${season}/${n}`);
  for(let frame=0;frame<4;frame++){assert.equal(c.tick_input(index%2?8:0,0),1,string(c.error()));assert.equal(c.draw(),1,string(c.error()));}
  assert.equal((c.body_word(0)>>>18)&3,1);cases.push({character,season,power,energy,main:c.option_count(0),satellites:c.option_count(1),frame:c.value(1)});
 }
}
writeFileSync(resolve(root,'docs/porting/th16-options-session-progress-oct10.json'),JSON.stringify({title:16,completeGame:false,cases,archiveSha256:sha(dat),wasmSha256:sha(bytes),engineBuild,scope:'Actual production archive, four characters/five explicitly selected resource families, thirteen manually injected power/season threshold transitions each, own upgrade/rebuild/HUD, registration/resource/file checks, 1040 non-shooting updates and real ANM draw submissions, alternating focus. Synthetic economy inputs; season title selection UI, actual seasonal firing, natural progression, original pixels and full gameplay excluded.'},null,2)+'\n');console.log(`PASS: ${cases.length} actual-resource main/season upgrades across twenty combinations.`);
