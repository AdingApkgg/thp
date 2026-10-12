// Production before-player snapshots aligned with an isolated retail trace.
import {readFileSync,writeFileSync,mkdirSync,readdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web');
const out=resolve(root,'artifacts/th14/session-reference-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'session-reference.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14','tests/cpp/th14-session-reference-fixture.cpp',...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th14.dat'].path);
const keys=['stageFrame','held','pressed','x','y','lifeState','stateAge','transitionAge','shootingAge','invincibility','shotAge','focused','score','graze','pointValue','power','lives','lifePieces','bombs','bombPieces','rank','scriptSeed','scriptCalls','replaySeed','replayCalls','enemyCount','shots','character','subtype','difficulty','stage','scaleFlags'];
const nativePath=resolve(root,process.argv[2]??'artifacts/th14/native-session-oct10.json');
const native=existsSync(nativePath)?JSON.parse(readFileSync(nativePath,'utf8')):null;
const frames=Math.max(600,...(native?.frames??[]).map(r=>r.stageFrame)),runs=[];
for(let demo=0;demo<3;demo++){
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
 const string=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
 const ptr=c.allocate(dat.length);new Uint8Array(c.memory.buffer,ptr,dat.length).set(dat);
 if(!c.open_archive(ptr,dat.length)||!c.begin_reference(demo))throw Error(string(c.error()));
 const rows=[];let error='',beamFailure=null;for(let frame=0;frame<frames;frame++){
  if(!c.tick(0)||!c.draw()){error=string(c.error());beamFailure=Array.from(new Float32Array(c.memory.buffer,c.reference_beam_failure(),12));break;}
  const raw=new Int32Array(c.memory.buffer,c.reference_data(),32);
  const row=Object.fromEntries(keys.map((name,n)=>[name,raw[n]]));
  const detail=(ptr,n,width)=>{const words=Array.from(new Uint32Array(c.memory.buffer,ptr,n));return Array.from({length:n/width},(_,i)=>words.slice(i*width,(i+1)*width));};
  if(row.stageFrame<=1000||(row.stageFrame>=1200&&row.stageFrame<=1400)||(row.stageFrame>=2920&&row.stageFrame<=2950)||(row.stageFrame>=3000&&row.stageFrame<=3120)||(row.stageFrame>=3690&&row.stageFrame<=3705)){row.liveShots=detail(c.reference_shot_data(),c.reference_shot_words(),11);row.enemyDetails=detail(c.reference_enemy_data(),c.reference_enemy_words(),10);row.enemyPhaseDetails=detail(c.reference_phase_data(),c.reference_phase_words(),23);}
  if(row.stageFrame>=3000&&row.stageFrame<=3120)row.damageAreas=detail(c.reference_area_data(),c.reference_area_words(),20);
  row.enemyIds=Array.from(new Uint32Array(c.memory.buffer,c.reference_id_data(),c.reference_id_words()));row.enemyNextId=c.reference_next_id();
  row.shotRewardCounters=Array.from(new Uint32Array(c.memory.buffer,c.reference_reward_data(),3));
  row.popupWords=Array.from(new Uint32Array(c.memory.buffer,c.reference_popup_data(),324));row.popupCursor=c.reference_popup_cursor();
  if(row.stageFrame>=900&&row.stageFrame<=1000)row.itemDetails=detail(c.reference_item_data(),c.reference_item_words(),12);
  if(row.stageFrame<=350)row.bulletDetails=detail(c.reference_bullet_data(),c.reference_bullet_words(),16);
  rows.push(row);
  if(c.phase()!==1)break;
 }
 const rngWords=Array.from(new Uint32Array(c.memory.buffer,c.reference_rng_read_data(),c.reference_rng_read_words()));
 const eclRngReads=Array.from({length:rngWords.length/8},(_,i)=>rngWords.slice(i*8,(i+1)*8));
 runs.push({demo,rows,error,beamFailure,eclRngReads});console.log(`demo${demo}: ${rows.length} production reference rows${error?' ERROR: '+error+' beam='+JSON.stringify(beamFailure):''}`);
}
const normalize=n=>{const g=n.globals,p=n.player;return {
 stageFrame:n.stageFrame,held:n.held,pressed:n.pressed,x:p[0],y:p[1],lifeState:p[2],stateAge:p[3],transitionAge:p[4],shootingAge:p[5],invincibility:p[6],shotAge:p[7],focused:p[8],
 score:g[2],graze:g[6],pointValue:g[9],power:g[12],lives:g[15],lifePieces:g[16],bombs:g[18],bombPieces:g[19],rank:g[5],
 scriptSeed:n.scriptRng[0],scriptCalls:n.scriptRng[2],replaySeed:n.replayRng[0],replayCalls:n.replayRng[2],enemyCount:n.enemyCount,shots:n.shots,
 character:n.selection[0],subtype:n.selection[1],difficulty:n.selection[2],stage:n.selection[3],scaleFlags:n.scaleFlags,
};};
let comparison=null;const comparisons=[];
if(native?.frames?.length){
 for(const run of runs){
  const first=run.rows[0];
  // No inferred frame offset: require a matching native stage clock.
  const paired=[],firstDifferences={},firstDetailDifferences={};let detailedFrames=0,popupFrames=0;
  for(const raw of native.frames){const n=normalize(raw);if(!['character','subtype','difficulty','stage'].every(k=>n[k]===first[k]))continue;
   const p=run.rows.find(row=>row.stageFrame===n.stageFrame);if(!p)continue;
   const differences=keys.filter(k=>p[k]!==n[k]).map(k=>({key:k,port:p[k],native:n[k]}));
   for(const d of differences)firstDifferences[d.key]??={frame:n.stageFrame,...d};
   if(raw.enemyDetails&&p.enemyDetails){
    ++detailedFrames;
    if(JSON.stringify(raw.enemyDetails)!==JSON.stringify(p.enemyDetails))firstDetailDifferences.enemies??={frame:n.stageFrame,native:raw.enemyDetails,port:p.enemyDetails};
    if(raw.enemyPhaseDetails&&JSON.stringify(raw.enemyPhaseDetails)!==JSON.stringify(p.enemyPhaseDetails))firstDetailDifferences.phases??={frame:n.stageFrame,native:raw.enemyPhaseDetails,port:p.enemyPhaseDetails};
    // Allocation slots differ; this diagnostic compares the multiset of live
    // shot fields without claiming equivalent pool links or processing order.
    const content=rows=>rows.map(row=>row.slice(1)).sort((a,b)=>JSON.stringify(a).localeCompare(JSON.stringify(b)));
    if(JSON.stringify(raw.liveShots)!==JSON.stringify(p.liveShots))firstDetailDifferences.shotSlots??={frame:n.stageFrame,native:raw.liveShots,port:p.liveShots};
    if(JSON.stringify(content(raw.liveShots))!==JSON.stringify(content(p.liveShots)))firstDetailDifferences.shotContents??={frame:n.stageFrame,native:content(raw.liveShots),port:content(p.liveShots)};
   }
   if(raw.itemDetails&&p.itemDetails){const sorted=a=>a.toSorted((a,b)=>JSON.stringify(a).localeCompare(JSON.stringify(b)));if(JSON.stringify(sorted(raw.itemDetails))!==JSON.stringify(sorted(p.itemDetails)))firstDetailDifferences.items??={frame:n.stageFrame,native:sorted(raw.itemDetails),port:sorted(p.itemDetails)};}
   if(raw.bulletDetails&&p.bulletDetails){const sorted=a=>a.toSorted((a,b)=>JSON.stringify(a).localeCompare(JSON.stringify(b)));if(JSON.stringify(sorted(raw.bulletDetails))!==JSON.stringify(sorted(p.bulletDetails)))firstDetailDifferences.bullets??={frame:n.stageFrame,native:sorted(raw.bulletDetails),port:sorted(p.bulletDetails)};}
   if(raw.enemyIds&&JSON.stringify(raw.enemyIds)!==JSON.stringify(p.enemyIds))firstDetailDifferences.enemyIds??={frame:n.stageFrame,native:raw.enemyIds,port:p.enemyIds};
   if(raw.enemyNextId!==undefined&&raw.enemyNextId!==p.enemyNextId)firstDetailDifferences.enemyNextId??={frame:n.stageFrame,native:raw.enemyNextId,port:p.enemyNextId};
   if(raw.damageAreas&&JSON.stringify(raw.damageAreas)!==JSON.stringify(p.damageAreas))firstDetailDifferences.damageAreas??={frame:n.stageFrame,native:raw.damageAreas,port:p.damageAreas};
   if(raw.shotRewardCounters&&JSON.stringify(raw.shotRewardCounters)!==JSON.stringify(p.shotRewardCounters))firstDetailDifferences.rewardCounters??={frame:n.stageFrame,native:raw.shotRewardCounters,port:p.shotRewardCounters};
   if(raw.popupWords){++popupFrames;if(JSON.stringify(raw.popupWords)!==JSON.stringify(p.popupWords))firstDetailDifferences.popupWords??={frame:n.stageFrame,native:raw.popupWords,port:p.popupWords};}
   if(raw.popupCursor!==undefined&&raw.popupCursor!==p.popupCursor)firstDetailDifferences.popupCursor??={frame:n.stageFrame,native:raw.popupCursor,port:p.popupCursor};
   paired.push({frame:n.stageFrame,differences});
  }
  comparison={demo:run.demo,pairedFrames:paired.length,firstDifferences,allFieldsEqual:paired.length>0&&paired.every(r=>r.differences.length===0),paired};
  comparison.gameplayAggregate={fields:keys.filter(k=>k!=='scriptSeed'&&k!=='scriptCalls'),firstDifferenceFrame:paired.find(r=>r.differences.some(d=>d.key!=='scriptSeed'&&d.key!=='scriptCalls'))?.frame??null};
  comparison.detail={pairedFrames:detailedFrames,popupFrames,firstDifferences:firstDetailDifferences,scope:'Enemy list fields in order; shot contents as an unordered multiset with allocation slot removed. All eighteen score/bonus pool slots and cursor before player callback; timer pointers normalized to presence. Shot pool ownership/order, visuals and audio are separate.'};
  if(paired.length)comparisons.push(comparison);
 }
 comparison=comparisons[0]??null;
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={completeGame:false,nativeEquivalent:comparisons.length>0&&comparisons.every(c=>c.allFieldsEqual&&Object.keys(c.detail.firstDifferences).length===0)&&runs.every(r=>!r.error),nativeTracePath:nativePath,nativeCapturedFrames:native?.frames?.length??0,comparison,comparisons,runs,wasmSha256:sha(bytes),archiveSha256:sha(dat),scope:'Whole production replay snapshots before the priority-18 player callback, ordinary collision and real assets. Native frame offset is never guessed; matching character/subtype/difficulty/stage and stage clocks are required. Retail attract mode can switch demos before a decoded replay ends. GPU/audio excluded; no claim if retail startup yielded no reference frames.'};
report.sourceHashes=Object.fromEntries(['cpp/game/GameBattle.cpp','cpp/game/GameBattle.hpp','cpp/game/ScorePopups.cpp','cpp/game/ScorePopups.hpp','tests/cpp/th14-session-reference-fixture.cpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))]));
report.toolHashes=Object.fromEntries(['tools/th14-native-session-capture.py','tools/th14-session-reference-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]));
if(native)report.nativeTraceSha256=sha(readFileSync(nativePath));
const captureToolAt=process.argv.indexOf('--capture-tool');
report.nativeCaptureToolSha256=captureToolAt>=0?sha(readFileSync(resolve(root,process.argv[captureToolAt+1]))):native?.captureToolSha256??null;
const popupFrames=comparisons.reduce((n,c)=>n+c.detail.popupFrames,0);
if(popupFrames){
 const popupReport={passed:comparisons.length===3&&comparisons.every(c=>c.detail.popupFrames===3901&&!c.detail.firstDifferences.popupWords&&!c.detail.firstDifferences.popupCursor)&&runs.every(r=>!r.error),comparedFrames:popupFrames,slotsPerFrame:18,wordsPerSlot:18,nativeTracePath:nativePath,nativeTraceSha256:report.nativeTraceSha256,wasmSha256:report.wasmSha256,sourceHashes:report.sourceHashes,toolHashes:report.toolHashes,comparisons:comparisons.map(c=>({demo:c.demo,comparedFrames:c.detail.popupFrames,firstDifferences:Object.fromEntries(Object.entries(c.detail.firstDifferences).filter(([k])=>k==='popupWords'||k==='popupCursor'))})),scope:'All ordinary/bonus pool words and rotating cursor before the production and retail priority-18 player callbacks across three untouched attract demos. Timer rate addresses normalized to pointer presence only. Includes inactive slot contents. Startup RNG differences and GPU/audio are separate; this result never implies whole-game equivalence.'};
 popupReport.nativeCaptureToolSha256=report.nativeCaptureToolSha256;
 writeFileSync(resolve(root,'docs/porting/th14-score-popup-session-progress-oct10.json'),JSON.stringify(popupReport,null,2)+'\n');
}
writeFileSync(resolve(root,'docs/porting/th14-session-reference-progress-oct10.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({nativeFrames:report.nativeCapturedFrames,comparisons:comparisons.map(c=>({demo:c.demo,pairedFrames:c.pairedFrames,popupFrames:c.detail.popupFrames,firstDifferences:c.firstDifferences,detailFirstFrames:Object.fromEntries(Object.entries(c.detail.firstDifferences).map(([k,v])=>[k,v.frame])),allFieldsEqual:c.allFieldsEqual}))}));
