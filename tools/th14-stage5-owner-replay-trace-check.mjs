// Pair actual retail playback of a port-written intact campaign with ordinary
// production playback. No invulnerability or power override in either run.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web');
const option=(name,fallback)=>{const i=process.argv.indexOf(name);return i<0?fallback:process.argv[i+1];},sha=b=>createHash('sha256').update(b).digest('hex');
const label=option('--label','');assert(/^[a-z0-9-]{0,64}$/.test(label));const out=resolve(root,'artifacts/th14/custom-replay-reference',label||'baseline');mkdirSync(out,{recursive:true});
const tracePath=resolve(root,option('--native','artifacts/th14/native-campaign-reference-oct11.json')),traceBytes=readFileSync(tracePath),native=JSON.parse(traceBytes);
const manifestPath=resolve(root,option('--manifest','artifacts/th14/native-campaign-assets/57d84a5cbe82-cd2f2e3549c0/manifest.json')),manifestBytes=readFileSync(manifestPath),manifest=JSON.parse(manifestBytes);
assert.equal(manifest.passed,true);assert.equal(manifest.unchangedEntries,226);assert.equal(native.error,'');assert(native.frames.length>0);assert.equal(native.files.find(x=>x.name==='th14.dat').sha256,manifest.referenceArchiveSha256);
const replay=readFileSync(manifest.replayPath);assert.equal(sha(replay),manifest.replaySha256);
const selection=Number(option('--selection',0)),difficulty=Number(option('--difficulty',1)),stage=Number(option('--stage',difficulty===4?7:1));assert(Number.isInteger(stage)&&stage>=1&&stage<=7);assert(Number.isInteger(selection)&&selection>=0&&selection<6);assert(Number.isInteger(difficulty)&&difficulty>=0&&difficulty<=4);assert.deepEqual(native.frames[0].selection,[Math.floor(selection/2),selection%2,difficulty,stage],'native actually selected the replaced complete campaign');
assert(native.frames.every(r=>JSON.stringify(r.selection)===JSON.stringify(native.frames[0].selection)),'do not combine distinct attract selections');
const engine=JSON.parse(readFileSync(resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json')));
for(const [name,hash] of Object.entries(engine.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,name))),hash,'changed engine '+name);
const fixture='tests/cpp/th14-stage5-owner-replay-fixture.cpp',objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'reference.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasm],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const upload=b=>{const p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);return p;},target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path);assert.equal(c.open_archive(upload(archive),archive.length),1);assert.equal(c.begin_custom_reference(upload(replay),replay.length),1);
const keys=['stageFrame','held','pressed','x','y','lifeState','stateAge','transitionAge','shootingAge','invincibility','shotAge','focused','score','graze','pointValue','power','lives','lifePieces','bombs','bombPieces','rank','scriptSeed','scriptCalls','replaySeed','replayCalls','enemyCount','shots','character','subtype','difficulty','stage','scaleFlags'];
const normalize=n=>{const g=n.globals,p=n.player;return [n.stageFrame,n.held,n.pressed,...p.slice(0,9),g[2],g[6],g[9],g[12],g[15],g[16],g[18],g[19],g[5],n.scriptRng[0],n.scriptRng[2],n.replayRng[0],n.replayRng[2],n.enemyCount,n.shots,...n.selection,n.scaleFlags].map(x=>x>>>0);};
const byFrame=new Map(native.frames.map(r=>[r.stageFrame,r])),differences=[],startupVisualDifferences=[],detailDifferences=[],portableStates=[],nativeStates=[];let comparedFrames=0;
const sorted=a=>a.map(r=>JSON.stringify(r)).sort(),words=(ptr,n)=>Array.from(new Uint32Array(c.memory.buffer,ptr,n));
for(let i=1;i<=Math.max(...byFrame.keys());++i){assert.equal(c.tick(0),1);assert.equal(c.draw(),1);const actual=words(c.reference_data(),32),row=byFrame.get(actual[0]);if(!row)continue;++comparedFrames;
 const expected=normalize(row);portableStates.push(...actual);nativeStates.push(...expected);for(let k=0;k<32;++k)if(actual[k]!==expected[k]){const d={frame:actual[0],field:keys[k],port:actual[k],native:expected[k]};(k===21||k===22?startupVisualDifferences:differences).push(d);}
 const detail=(kind,ptr,n,width,nativeWords,unordered=false)=>{if(!nativeWords)return;const data=words(ptr,n),port=width?Array.from({length:n/width},(_,j)=>data.slice(j*width,(j+1)*width)):data;const equal=JSON.stringify(unordered?sorted(port):port)===JSON.stringify(unordered?sorted(nativeWords):nativeWords);if(!equal)detailDifferences.push({frame:actual[0],kind,port,native:nativeWords});};
 detail('popupWords',c.reference_popup_data(),324,0,row.popupWords);
 if(c.reference_popup_cursor()!==row.popupCursor)detailDifferences.push({frame:actual[0],kind:'popupCursor',port:c.reference_popup_cursor(),native:row.popupCursor});
 detail('enemies',c.reference_enemy_data(),c.reference_enemy_words(),10,row.enemyDetails);
 detail('phases',c.reference_phase_data(),c.reference_phase_words(),23,row.enemyPhaseDetails);
 detail('shots',c.reference_shot_data(),c.reference_shot_words(),11,row.liveShots);
 detail('items',c.reference_item_data(),c.reference_item_words(),12,row.itemDetails,true);
 detail('bullets',c.reference_bullet_data(),c.reference_bullet_words(),16,row.bulletDetails,true);
 detail('damageAreas',c.reference_area_data(),c.reference_area_words(),20,row.damageAreas);
 detail('enemyIds',c.reference_id_data(),c.reference_id_words(),0,row.enemyIds);
 detail('shotRewards',c.reference_reward_data(),3,0,row.shotRewardCounters);
 if(c.reference_next_id()!==row.enemyNextId)detailDifferences.push({frame:actual[0],kind:'enemyNextId',port:c.reference_next_id(),native:row.enemyNextId});
}
assert.equal(comparedFrames,native.frames.length);const portableBytes=Buffer.from(new Uint32Array(portableStates).buffer),nativeBytes=Buffer.from(new Uint32Array(nativeStates).buffer);writeFileSync(resolve(out,'portable-state.u32'),portableBytes);writeFileSync(resolve(out,'native-state.u32'),nativeBytes);
const report={selection,difficulty,stage,fieldNames:keys,portableStateSha256:sha(portableBytes),nativeStateSha256:sha(nativeBytes),stateWordsPerFrame:32,passed:!differences.length&&!detailDifferences.length,completeGame:false,nativeEquivalent:false,comparedFrames,differences,detailDifferences,startupVisualDifferences,nativeTracePath:tracePath,nativeTraceSha256:sha(traceBytes),archiveManifestSha256:sha(manifestBytes),replaySha256:sha(replay),wasmSha256:sha(bytes),engineBuild:engine,fixtureSha256:sha(readFileSync(resolve(rt,fixture))),includedFixtureSha256:sha(readFileSync(resolve(rt,'tests/cpp/th14-stage5-owner-reference-fixture.cpp'))),toolSha256:sha(readFileSync(import.meta.filename)),scope:'Real isolated retail process reads the data-only stage slice of the ordinary-input natural clear replay through a private archive with only demo0 changed. Both real retail and production playback use ordinary collision, no invulnerability/power override. Before-player boundary and exact stage clocks paired; selected state, native-detail windows,18 score/bonus slots compared. Startup visual RNG differences retained separately, never seeded to match. Attract control still limits native duration; not full six-stage native playback, GPU/audio or whole-game equivalence.'};
writeFileSync(resolve(root,`docs/porting/th14-natural-replay-native-trace${label?'-'+label:''}-observed-oct13.json`),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:report.passed,comparedFrames,differences:differences.length,detailDifferences:detailDifferences.length,firstDifference:differences[0],firstDetail:detailDifferences[0]?.kind,startupVisualDifferences:startupVisualDifferences.length}));if(!report.passed)process.exitCode=1;
