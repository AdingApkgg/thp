import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/score-legacy-check');mkdirSync(out,{recursive:true});
const original=execFileSync('git',['show','HEAD:runtimes/th12/th12_web/cpp/game/ScoreFile.cpp'],{cwd:root,windowsHide:true});
const baseline=resolve(out,'baseline.cpp');writeFileSync(baseline,original);
const compiler=resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),fixture='tests/cpp/score-regression-fixture.cpp';
const sha=b=>createHash('sha256').update(b).digest('hex');
async function compile(source,title,name){
 const path=resolve(out,`${name}-${title}.wasm`);
 execFileSync(compiler,['--target=wasm32-wasip1',`-DPORT_TITLE=${title}`,'-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-Icpp/game',fixture,source,'cpp/game/Lzss.cpp','cpp/game/ResourceCrypt.cpp','-o',path],{cwd:rt,windowsHide:true,stdio:'inherit'});
 const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);return {c:instance.exports,sha256:sha(bytes)};
}
const rows=[];
for(const title of [11,12,13]){
 const prior=await compile(baseline,title,'baseline'),current=await compile('cpp/game/ScoreFile.cpp',title,'current'),a=prior.c,b=current.c;
 const bytes=(c,p,n)=>Buffer.from(new Uint8Array(c.memory.buffer,p,n));
 function compare(label){for(let n=0;n<8;n++)assert.deepEqual(bytes(a,a.data(n),n<7?0x68d4:0x448),bytes(b,b.data(n),n<7?0x68d4:0x448),`${title} ${label} record${n}`);}
 for(const seed of [0,1,904,0xffff])for(const calls of [0,97,0xffffffff]){
  a.initialize(seed,calls);b.initialize(seed,calls);compare('defaults');assert.equal(a.seed(),b.seed());assert.equal(a.calls(),b.calls());
 }
 let insertions=0,names=0;
 for(let selection=0;selection<7;selection++)for(let difficulty=0;difficulty<5;difficulty++)for(const score of [0,100000,1000000,1000001,0x7fffffff,-1]){
  a.initialize(904,0);b.initialize(904,0);
  const rank=a.insert(selection,difficulty,score,257,258);assert.equal(b.insert(selection,difficulty,score,257,258),rank);compare('ranking');++insertions;
  if(rank>=0)for(const text of ['', 'A', 'ABCDEFGH']){
   for(const c of [a,b]){const input=Buffer.from(text+'\0'),p=c.allocate(input.length);new Uint8Array(c.memory.buffer,p,input.length).set(input);assert.equal(c.name(selection,difficulty,rank,p),1);c.release(p);}
   compare('name');++names;
  }
 }
 // Include nonempty spell/clear/practice records and opaque bytes in a complete
 // codec round trip. Both modules link the current non-score dependencies.
 for(const c of [a,b]){c.initialize(1234,97);const record=new Uint8Array(c.memory.buffer,c.data(5),0x68d4);record.set(Buffer.from('nonempty regression'),0x664+174*0x90);record[0x6e4+174*0x90]=17;record[0x590+4*4]=3;record[0x5a0+24*8]=17;record[0x583]=0x9a;c.sync();}
 compare('records');const packed=bytes(a,a.save(),a.size());assert.deepEqual(bytes(b,b.save(),b.size()),packed,'complete encoded bytes');
 for(const c of [a,b]){const p=c.allocate(packed.length);new Uint8Array(c.memory.buffer,p,packed.length).set(packed);assert.equal(c.open(p,packed.length),1);c.release(p);}compare('reload');
 rows.push({title,defaultCases:12,insertions,names,codecBytes:packed.length,baselineWasm:prior.sha256,currentWasm:current.sha256});
}
writeFileSync(resolve(root,'docs/porting/th14-score-legacy-regression.json'),JSON.stringify({passed:true,rows,baselineCommit:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8',windowsHide:true}).trim(),baselineScoreSourceSha256:sha(original),scoreSourceSha256:sha(readFileSync(resolve(rt,'cpp/game/ScoreFile.cpp'))),scope:'Compiled PORT_TITLE11/12/13 ScoreFile regression against HEAD ScoreFile.cpp, using identical current headers/LZSS/crypt dependencies. Defaults, RNG, full records, ranking/name writes and nonempty codec round trip unchanged. This is source regression, not a retail TH11/12/13 oracle or whole-port proof.'},null,2)+'\n');
console.log('PASS unchanged legacy ScoreFile behavior in titles11/12/13');
