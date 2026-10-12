// Capture all five inactive stage handoffs; diagnostic survival is explicit.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/campaign-handoffs-all-oct11');mkdirSync(out,{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex'),enginePath='artifacts/th14/campaign-handoffs-all-oct11/engine-build.json',engine=JSON.parse(readFileSync(resolve(root,enginePath)));
for(const [name,hash] of Object.entries(engine.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,name))),hash,'stale engine '+name);
const objects=resolve(out,'objects'),path=resolve(out,'handoffs.wasm'),fixture='tests/cpp/th14-campaign-handoff-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',path],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const text=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));},load=bytes=>{const p=c.allocate(bytes.length);new Uint8Array(c.memory.buffer,p,bytes.length).set(bytes);return p;};
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path),replayPath='artifacts/th14/campaign-replay/reimu-a-normal-pools-oct11/campaign.rpy',replayBytes=readFileSync(resolve(root,replayPath));assert.equal(c.open_archive(load(archive),archive.length),1);
const groups=[];
for(const replay of [false,true]){
 if(replay)assert.equal(c.campaign_load_saved(load(replayBytes),replayBytes.length),1,text(c.error()));else assert.equal(c.campaign_begin(0,1),1);
 let stage=1,current=null,previous=null,finished=0;
 for(let frame=1;frame<=76000;frame++){
  assert.equal(c.combat_tick(replay?0:513),1,text(c.error()));assert.equal(c.draw(),1,text(c.error()));assert.equal(c.campaign_clock((replay?100:0)+frame/(replay?30:60)),1);
  const currentStage=c.campaign_state(0),active=!!c.campaign_state(18),row={frame,stage:currentStage,active,score:c.replay_observation(15),combo:Array.from({length:7},(_,i)=>c.campaign_combo(i))};
  if(currentStage!==stage){assert.equal(currentStage,stage+1);stage=currentStage;if(replay){current=groups[stage-2];assert.equal(frame,current.transitionFrame);}else{current={stage,transitionFrame:frame,records:[previous],replays:[]};groups.push(current);}console.log(JSON.stringify({event:replay?'replay-handoff':'live-handoff',frame,stage}));}
  if(current){const ptr=c.campaign_pool_read(3),length=c.campaign_pool_words();row.items=Array.from(new Uint32Array(c.memory.buffer,ptr,length));(replay?current.replays:current.records).push(row);if(active){assert.equal(frame,current.transitionFrame+151);current=null;finished++;if(finished===5)break;}}
  previous=row;
 }
 assert.equal(finished,5);
}
const sources=Object.fromEntries([fixture,'tests/cpp/th14-campaign-pools-fixture.cpp','tests/cpp/th14-campaign-replay-fixture.cpp','tests/cpp/th14-replay-session-fixture.cpp','tests/cpp/th14-session-fixture.cpp','tests/cpp/render-fixture.hpp'].map(n=>[n,sha(readFileSync(resolve(rt,n)))]));
const report={generated:true,completeGame:false,nativeEquivalent:false,groups,replayPath,replaySha256:sha(replayBytes),archiveSha256:sha(archive),wasmSha256:sha(bytes),engineBuildPath:enginePath,engineBuildSha256:sha(readFileSync(resolve(root,enginePath))),sources,toolSha256:sha(readFileSync(import.meta.filename)),scope:'Current engine executes original archive ECL live and saved diagnostic replay through all five handoffs; explicit score,seven combo words,item pool words recorded from transition through first active frame. Fixture invulnerability/9 lives/7 bombs and fire-confirm held; no natural native campaign/GPU equivalence claim.'};
writeFileSync(resolve(out,'rows.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({generated:true,handoffs:5,liveRows:groups.reduce((n,g)=>n+g.records.length,0),replayRows:groups.reduce((n,g)=>n+g.replays.length,0)}));
