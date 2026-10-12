// Actual six-stage ECL completion, current lifecycle fixes, intact recording and playback. Invulnerability
// isolates progression; no forced boss defeat, clear, score, power or recorder reset.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web');
const option=(name,fallback)=>{const at=process.argv.indexOf(name);return at<0?fallback:process.argv[at+1];};
const selection=Number(option('--selection',0)),difficulty=Number(option('--difficulty',1));
assert(Number.isInteger(selection)&&selection>=0&&selection<6);assert(Number.isInteger(difficulty)&&difficulty>=0&&difficulty<=4);
const extra=difficulty===4,deep=process.argv.includes('--pools'),pattern=process.argv.includes('--pattern');assert(!pattern||deep,'input-pattern coverage includes deep pools');
const label=option('--label',`selection${selection}-difficulty${difficulty}-lifecycle-oct12`);assert(/^[a-z0-9-]{1,64}$/.test(label));
const out=resolve(root,'artifacts/th14/campaign-replay',label);mkdirSync(out,{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex'),engine=JSON.parse(readFileSync(resolve(root,'artifacts/th14/dialogue-text-check/objects.json')));
for(const [name,hash] of Object.entries(engine.objectHashes))assert.equal(sha(readFileSync(name)),hash,'stale object '+name);
for(const [name,hash] of Object.entries(engine.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,name))),hash,'stale engine '+name);
const fixture=pattern?'tests/cpp/th14-campaign-inputs-fixture.cpp':deep?'tests/cpp/th14-campaign-pools-fixture.cpp':'tests/cpp/th14-campaign-replay-fixture.cpp',objects=resolve(root,'artifacts/th14/dialogue-text-check'),wasm=resolve(out,'campaign.wasm');
const fixtureHash=sha(readFileSync(resolve(rt,fixture)));
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...Object.keys(engine.objectHashes),'-o',wasm],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
assert.equal(sha(readFileSync(resolve(rt,fixture))),fixtureHash,'fixture changed during compilation');
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);
const text=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
const fields=['stage','frame','gameRngSeed','gameRngCalls','battleFrame','enemies','enemiesCreated','bullets','spellFrames','spellFlags','lastSpellFrames','spellEncoded','spellIndex','pointValue','rank','pointItems','lifeFragments','bombFragments','lives','power','bombs','score','graze','playerX','playerY'];
const poolNames=['bullets','shots','enemies','items','lasers','damageAreas'],poolPeaks=Array(6).fill(0);let poolHashedBytes=0;
if(deep)fields.push(...poolNames.map(n=>n+'PoolSha256'));
if(pattern)fields.push(...['active','elapsedPrevious','elapsedCurrent','elapsedFractional','secondaryPrevious','secondaryCurrent','secondaryFractional','mode','x','y','z','radius','growth','startedDuringSpell'].map(n=>'bomb-'+n));
const observe=()=>{const values=[...Array.from({length:18},(_,i)=>c.campaign_state(i)>>>0),...[10,11,12,15,16,17,18].map(i=>c.replay_observation(i)>>>0)];
 if(deep)for(let kind=0;kind<6;++kind){const ptr=c.campaign_pool_read(kind),length=c.campaign_pool_words()*4;poolPeaks[kind]=Math.max(poolPeaks[kind],c.campaign_pool_count());poolHashedBytes+=length;values.push(sha(new Uint8Array(c.memory.buffer,ptr,length)));}if(pattern)values.push(...Array.from({length:14},(_,i)=>c.campaign_pattern_state(i)>>>0));return values;};
const itemWords=()=>{const ptr=c.campaign_pool_read(3),length=c.campaign_pool_words();return Array.from(new Uint32Array(c.memory.buffer,ptr,length));};
const transitions=[],states=[],transitionDifferences=[];let error='',comparedFrames=0,activeComparedFrames=0,replayFrames=0,recordFrames=[],decodedFrames=[],replaySha256='',endingWaitBegins=0,replayEndExpectedAt=0,inputPatternStats=null;
try{
 assert.equal(c.campaign_begin(selection,difficulty),1,text(c.error()));let stage=extra?7:1;
 for(let frame=1;frame<=240000;++frame){
  assert.equal(pattern?c.campaign_pattern_tick(frame):c.combat_tick(513),1,text(c.error()));assert.equal(c.draw(),1,text(c.error()));assert.equal(c.campaign_clock(frame/60),1);
  if(c.phase()!==1){assert.equal(c.phase(),extra?3:5,'actual ECL completion');if(extra)replayEndExpectedAt=frame;break;}
  const active=!!c.campaign_state(18);states.push({values:observe(),active,ending:!!c.campaign_state(19),items:deep&&!active?itemWords():undefined});if(!endingWaitBegins&&c.campaign_state(19))endingWaitBegins=frame;
  if(c.campaign_state(0)!==stage){stage=c.campaign_state(0);transitions.push({frame,stage});console.log(JSON.stringify({event:'record-stage',frame,stage}));}
 }
 assert.equal(c.phase(),extra?3:5,'campaign completes within frame limit');assert.deepEqual(transitions.map(r=>r.stage),extra?[]:[2,3,4,5,6]);assert.equal(c.recording_chunk_count(),0);if(!extra)replayEndExpectedAt=endingWaitBegins;
 if(pattern){inputPatternStats=Object.fromEntries(['keysSeen','actualBombStarts','focusedInputFrames','movementInputFrames','aboveCollectionLineFrames'].map((n,i)=>[n,c.campaign_pattern_stat(i)]));assert.equal(inputPatternStats.keysSeen,763);assert(inputPatternStats.actualBombStarts>=2);assert(inputPatternStats.focusedInputFrames>0&&inputPatternStats.movementInputFrames>0&&inputPatternStats.aboveCollectionLineFrames>0);}
 const stages=extra?[7]:[1,2,3,4,5,6];recordFrames=stages.map(i=>c.campaign_record_frames(i));assert(recordFrames.every(n=>n>0&&n<86400));
 assert.equal(c.campaign_save(),1,'save intact completed campaign');const replay=Buffer.from(new Uint8Array(c.memory.buffer,c.campaign_bytes(),c.campaign_size()));writeFileSync(resolve(out,'campaign.rpy'),replay);replaySha256=sha(replay);
 assert.equal(c.campaign_replay(),1,text(c.error()));decodedFrames=stages.map(i=>c.campaign_decoded_frames(i));assert.deepEqual(decodedFrames,recordFrames.map((n,i)=>n+(extra&&i===recordFrames.length-1?1:0)));
 for(let frame=1;frame<=states.length+3;++frame){
  assert.equal(c.combat_tick(0),1,text(c.error()));assert.equal(c.draw(),1,text(c.error()));assert.equal(c.campaign_clock(100+frame/30),1);replayFrames=frame;
  if(c.phase()!==1){assert.equal(frame,replayEndExpectedAt,'retail control-mode replay ends at actual stage clear');break;}
  if(frame<=states.length){const actual=observe(),expected=states[frame-1];assert.equal(!!c.campaign_state(18),expected.active);
   for(let i=0;i<fields.length;++i){
    // Retail456050 restores the activation globals before the inactive wait.
    // Exact retail combo settlement/factory/ticks verify the first transient
    // item in th14-campaign-handoff-native.py. Preserve every discrepancy;
    // all six pools must match once stage_active becomes true.
    const handoff=!expected.active&&!expected.ending&&actual[0]>=2&&actual[0]<=6;
    if(actual[i]!==expected.values[i]&&handoff&&['score','itemsPoolSha256'].includes(fields[i])){
     const difference={frame,stage:actual[0],field:fields[i],record:expected.values[i],replay:actual[i]};
     if(fields[i]==='itemsPoolSha256'){difference.recordWords=expected.items;difference.replayWords=itemWords();}
     transitionDifferences.push(difference);continue;
    }
    assert.equal(actual[i],expected.values[i],`frame${frame} ${fields[i]}`);
   }++comparedFrames;if(expected.active)++activeComparedFrames;}
 }
 assert.equal(c.phase(),4,'completed replay reaches native control-mode end');assert(transitionDifferences.every(r=>['score','itemsPoolSha256'].includes(r.field)),'only separately reported score/item divergences in inactive handoffs');assert.equal(c.bullet_skipped_mask(),0);assert.equal(c.bullet_unsupported_native_mask(),0);
}catch(e){error=e.message;console.error(e.stack);}
const report={passed:!error,completeGame:false,nativeEquivalent:false,selection,difficulty,extra,deepPools:deep,inputPattern:pattern,inputPatternStats,poolPeaks:Object.fromEntries(poolNames.map((n,i)=>[n,poolPeaks[i]])),poolHashedBytes,error,comparedFrames,activeComparedFrames,recordedFrames:states.length+1,replayFrames,endingWaitBegins,replayEndExpectedAt,transitions,transitionDifferences,recordFrames,decodedFrames,replaySha256,fields,finalState:observe(),phase:c.phase(),diagnostic:error?text(c.progression_diagnostic()):'',bulletSkippedMask:c.bullet_skipped_mask()>>>0,bulletUnsupportedNativeMask:c.bullet_unsupported_native_mask()>>>0,fixtureSha256:fixtureHash,includedFixtures:Object.fromEntries(['tests/cpp/th14-campaign-replay-fixture.cpp','tests/cpp/th14-replay-session-fixture.cpp','tests/cpp/th14-session-fixture.cpp','tests/cpp/render-fixture.hpp',...(deep?['tests/cpp/th14-campaign-pools-fixture.cpp']:[])].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),toolSha256:sha(readFileSync(import.meta.filename)),wasmSha256:sha(bytes),archiveSha256:sha(archive),engineBuild:engine,scope:`${pattern?'Recorded ordinary movement, focused/unfocused fire and stock-limited bomb inputs':'Ordinary fire/confirm held'} with fixture invulnerability through ${extra?'Extra to actual result':'six actual ECL stages to ending'}. No forced completion or power, no recorder chunk removal. Saves/decodes all recording sections and compares selected gameplay fields during playback using a different supplied clock. Inactive handoff score and explicit item-pool differences are preserved separately: native456050 restores the activation snapshot before the background wait. Active gameplay remains strict; inactive item equality is not claimed. Replay control mode ends at stage clear; normal live recording continues through the380-frame ending wait.${deep?' SHA256 compares explicit numerical bullet, shot, enemy, item, laser (including sampled curve tail) and damage-area pool fields on every compared frame. Addresses, padding, ANM handles and rendering fields excluded.':''} Diagnostic survival, selected state only; excludes native combat, whole replay state, visual RNG, GPU/audio and natural clear.`};
writeFileSync(resolve(out,'result.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:report.passed,selection,difficulty,deepPools:deep,inputPattern:pattern,inputPatternStats,comparedFrames,activeComparedFrames,poolHashedBytes,error,phase:report.phase,transitionDifferences:transitionDifferences.length}));if(error)process.exitCode=1;
