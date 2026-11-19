import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {TitleScene} from '../shared/th06nc/title-scene.mjs';
import {titleResources} from '../shared/th06nc/title-layout.mjs';
import {selectionResources} from '../shared/th06nc/title-selection-layout.mjs';
import {spellMenuAsset} from '../shared/th06nc/spell-practice-layout.mjs';
import {spellInfoTextAsset} from '../shared/th06nc/spell-practice-info-text.mjs';
import {spellDifficultyAsset} from '../shared/th06nc/spell-practice-presentation.mjs';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {readMessagePack} from '../shared/th06nc/messagepack.mjs';
import {readSpellPracticeTable} from '../shared/th06nc/spell-practice-table.mjs';
import {createSpellRecord} from '../shared/th06nc/spell-record.mjs';
import {publishAnmText} from '../shared/th06nc/font-publish.mjs';
import {readFontAtlas} from '../shared/th06nc/font-atlas.mjs';
import {anmQuad} from '../shared/th06nc/anm-quad.mjs';
const sources=['title-scene','spell-practice-presentation','title-owner-advance','spell-practice-menu','spell-practice-entry','spell-practice-draw','spell-practice-profile','spell-practice-profile-draw','spell-practice-stage-info','spell-practice-card-info','font-publish','anm-quad'].map(s=>'shared/th06nc/'+s+'.mjs'),sha=b=>createHash('sha256').update(b).digest('hex'),snapshot=()=>Object.fromEntries(sources.map(p=>[p,sha(readFileSync(p))])),sourceSha256=snapshot();
const refs=[...titleResources,...selectionResources,spellMenuAsset,spellInfoTextAsset,spellDifficultyAsset],resources=new Map(refs.map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+(r.archive??'th06TL.dat')+'/'+r.file))]));
const table=readSpellPracticeTable(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/spellpractice.msgpack')),raw=readMessagePack(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/localization.msgpack')),localization=Object.fromEntries(Object.entries(raw).map(([k,v])=>[k,v['zh-CN']??k])),fonts=new Map();
for(const color of ['00FFFFFF','00E0FFFF']){const key='15_0x'+color+'_0x00000000_0x00010101_0x00040202_zh-CN';fonts.set(key,readFontAtlas(readFileSync('runtimes/th06nc/artifacts/fonts/'+key+'.json','utf8'),readFileSync('runtimes/th06nc/artifacts/fonts/advance_'+key+'.txt','utf8')));}
let publications=0,drawRequests=0,visibleQuads=0,cases=0;const digest=createHash('sha256'),draw=vm=>{drawRequests++;const quad=anmQuad(vm);if(quad){visibleQuads++;assert.ok([...quad].every(Number.isFinite));digest.update(Buffer.from(quad.buffer));}};
function make(profile,unlocked){
 const records=new Map(Array.from({length:134},(_,id)=>{const r=createSpellRecord();if(unlocked){r.attempts=1;r.practiceCaptures.fill(1);}return[id,r];})),environment={character:profile>>1,shot:profile&1,configuredSpellStage:0};
 const scene=new TitleScene(resources,{spellServices:{table,records,environment,localization,publishText:(vm,r)=>{const p=publishAnmText(vm,{...r,fonts,paint:()=>{}});assert.ok(p,'menu font must be present');publications++;}}});Object.assign(scene.state,{configuredCharacter:profile>>1,configuredShot:profile&1});
 const step=(frames,mask=0)=>{let event=null;for(let i=0;i<frames;i++){event=scene.tick(mask);scene.draw(draw,()=>{},()=>{});if(event)break;}return event;},tap=(mask,frames=20)=>{const event=step(1,mask);step(frames);return event;};
 return {scene,environment,step,tap};
}
for(let profile=0;profile<4;profile++)for(const unlocked of [false,true]){
 const {scene,environment,step,tap}=make(profile,unlocked);step(360);tap(32);tap(32);assert.equal(scene.state.selection,3);tap(256,110);assert.equal(scene.state.state,28);assert.equal(scene.background,'select00e');assert.equal(scene.state.configuredCharacter,profile>>1);assert.equal(scene.state.configuredShot,profile&1);
 tap(256);assert.equal(scene.state.state,unlocked?29:28);
 if(unlocked){
  const count=table.filter(r=>r.stageIndex===0).reduce((n,r)=>Math.max(n,r.order+1),0);for(let i=0;i<count+1;i++)tap(32,1);assert.equal(scene.state.spellOrder,1);assert.equal(scene.state.spellScroll,0);
  step(20);tap(256);assert.equal(scene.state.state,30);tap(128);assert.equal(environment.character*2+environment.shot,(profile+1)%4);tap(64);assert.equal(environment.character*2+environment.shot,profile);
  tap(32);assert.ok(table.some(r=>r.stageIndex===0&&r.order===1&&r.difficulty===scene.state.spellDifficulty));tap(512);assert.equal(scene.state.state,29);tap(512);assert.equal(scene.state.state,28);
 }
 for(let stage=1;stage<7;stage++){
  tap(32);assert.equal(scene.state.spellStage,stage);
  if(unlocked){tap(256);assert.equal(scene.state.state,29);tap(256);assert.equal(scene.state.state,30);if(stage===6){assert.equal(scene.state.spellDifficulty,0);tap(32);assert.equal(scene.state.spellDifficulty,0);}tap(512);tap(512);assert.equal(scene.state.state,28);}
 }
 tap(512,100);assert.equal(scene.state.state,3);assert.equal(scene.state.selection,3);assert.equal(scene.state.configuredCharacter,profile>>1);assert.equal(scene.state.configuredShot,profile&1);
 tap(256,110);assert.equal(scene.state.state,28);assert.equal(scene.state.spellStage,unlocked?6:0);
 if(unlocked){tap(256);tap(256);tap(256,0);assert.equal(scene.state.state,31);const event=step(40);assert.equal(event.kind,'startSpellPractice');assert.equal(event.environment.spellPractice,true);assert.equal(event.environment.stageIndex,6);assert.equal(event.environment.difficulty,4);assert.equal(event.environment.character*2+event.environment.shot,profile);assert.equal(event.environment.gameState,2);}
 cases++;
}
assert.deepEqual(snapshot(),sourceSha256);
const report={scope:'TitleScene + SpellPracticePresentation CPU integration through real title input sampling, native-format catalog/CATK views, actual font metadata publication and geometry generation. Four profiles with locked/unlocked records, all seven stages, card scrolling, difficulty/Extra selection, profile switching, cancel-to-main/reentry and selected-card launch request. Controlled records and no GPU/physical browser input; application resource host and actual spell game launch/end/save remain incomplete.',cases,publications,drawRequests,visibleQuads,stateSha256:digest.digest('hex'),sourceSha256,passed:true,completeGame:false,nativeEquivalent:false};writeFileSync('docs/porting/th06nc-spell-practice-presentation-verified.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,cases,publications,drawRequests,visibleQuads}));
