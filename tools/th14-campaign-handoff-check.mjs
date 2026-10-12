import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/campaign-handoff');mkdirSync(out,{recursive:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),path=resolve(out,'handoff.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','tests/cpp/th14-campaign-handoff-fixture.cpp',...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',path],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const text=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
const load=bytes=>{const p=c.allocate(bytes.length);new Uint8Array(c.memory.buffer,p,bytes.length).set(bytes);return p;},target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path);assert.equal(c.open_archive(load(archive),archive.length),1);
const records=[],replays=[],end=11960;
for(const replay of [false,true]){
 if(replay){const bytes=readFileSync(resolve(root,'artifacts/th14/campaign-replay/reimu-a-normal-pools-oct11/campaign.rpy'));assert.equal(c.campaign_load_saved(load(bytes),bytes.length),1,text(c.error()));}else assert.equal(c.campaign_begin(0,1),1);
 for(let frame=1;frame<=end;++frame){assert.equal(c.combat_tick(replay?0:513),1,text(c.error()));assert.equal(c.draw(),1,text(c.error()));assert.equal(c.campaign_clock((replay?100:0)+frame/(replay?30:60)),1);
  if(frame<11803)continue;const row={frame,active:!!c.campaign_state(18),stage:c.campaign_state(0),score:c.replay_observation(15),rng:[c.campaign_state(2),c.campaign_state(3)],combo:Array.from({length:7},(_,i)=>c.campaign_combo(i)),pools:[]};
  for(let kind=0;kind<6;++kind){const ptr=c.campaign_pool_read(kind),length=c.campaign_pool_words();row.pools.push(Array.from(new Uint32Array(c.memory.buffer,ptr,length)));}(replay?replays:records).push(row);
 }
}
writeFileSync(resolve(out,'rows.json'),JSON.stringify({records,replays},null,2)+'\n');
for(let i=0;i<records.length;++i){const a=records[i],b=replays[i],different=a.pools.map((p,k)=>JSON.stringify(p)!==JSON.stringify(b.pools[k])?k:-1).filter(k=>k>=0);if(different.length)console.log(JSON.stringify({frame:a.frame,active:a.active,different,recordCombo:a.combo,replayCombo:b.combo,recordItems:a.pools[3],replayItems:b.pools[3]}));}
