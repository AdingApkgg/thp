import {readFileSync,writeFileSync} from 'node:fs';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {AnmVm} from '../shared/th06nc/anm-vm.mjs';
import {TitleAnimations} from '../shared/th06nc/title-animations.mjs';
import {titleResources} from '../shared/th06nc/title-layout.mjs';
import {selectionResources} from '../shared/th06nc/title-selection-layout.mjs';
import {spellMenuAsset,initializeSpellMenuAnimations} from '../shared/th06nc/spell-practice-layout.mjs';
import {spellInfoTextAsset} from '../shared/th06nc/spell-practice-info-text.mjs';
import {drawSpellPractice} from '../shared/th06nc/spell-practice-draw.mjs';
import {readSpellPracticeTable} from '../shared/th06nc/spell-practice-table.mjs';
import {createSpellRecord} from '../shared/th06nc/spell-record.mjs';
const difficultyAsset={archive:'th06TL.dat',file:'difficulty.anm',slot:66,base:0x792},refs=[...titleResources,...selectionResources,spellMenuAsset,spellInfoTextAsset,difficultyAsset],resources=new Map(refs.map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+(r.archive??'th06TL.dat')+'/'+r.file))]));
const table=readSpellPracticeTable(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/spellpractice.msgpack')),capture=JSON.parse(readFileSync('artifacts/th06nc/spell-info-native-font-cases.json')),cases=[],trig={},sin=Math.sin,cos=Math.cos;
const bits=x=>new Uint32Array(new Float32Array([x]).buffer)[0],hex=vm=>Buffer.from(vm.state).toString('hex');
for(const [name,fn]of[['sin',sin],['cos',cos]])Math[name]=x=>{const result=fn(x);trig[name+':'+bits(x)]=bits(result);return result;};
let index=0;
for(const c of capture.cases){
 const states=c.owner===30?[30,31]:[c.owner];
 for(const owner of states){
  const group=new TitleAnimations(resources);initializeSpellMenuAnimations(group,resources);group.bank.load(resources.get('text.anm'),spellInfoTextAsset.base,{slot:0});
  for(const item of c.vms){const value=new AnmVm({scripts:[],sprites:[]},0,{allowMissing:true,resolveSprite:id=>group.bank.sprites.get(id)});value.state.set(Buffer.from(item.bytes,'hex'));const id=value.pointer(0x100)-1;value.boundBinding=group.bank.sprites.get(id);group.slots.set(item.offset,value);}
  group.bank.load(resources.get(difficultyAsset.file),difficultyAsset.base,{slot:difficultyAsset.slot});
  const scratch=new AnmVm({scripts:[],sprites:[]},0,{allowMissing:true,resolveSprite:id=>group.bank.sprites.get(id)});scratch.bindSprite(0x792);scratch.v.setUint32(0xc4,0x403,true);scratch.v.setInt32(0xb4,-1,true);group.slots.set(0x16050,scratch);
  const records=new Map(Array.from({length:134},(_,id)=>{const r=createSpellRecord(),row=table.find(row=>row.id===id);if(c.unlocked&&row){const attempted=[1,4].includes(c.recordMode)||(c.recordMode===2&&Boolean(row.midboss))||(c.recordMode===3&&id%3!==0),captured=attempted&&c.recordMode!==4&&(c.recordMode!==3||id%2!==0);r.attempts=attempted?17:0;r.practiceCaptures[row.difficulty*4+c.profile]=captured?3:0;}return[id,r];}));
  const row=table.find(r=>r.stageIndex===c.stage&&r.order===c.order),state={state:owner,spellStage:c.stage,spellOrder:c.order,spellScroll:c.scroll,spellDifficulty:c.stage===6?0:(index%4),pulse:[0,15,30,42,60,71,72][index%7],frame:[0,1,4,6,8,15,29,30,34,53,54][index%11],fastEntry:!!(index%2),profileTransition:index%25,difficultyTransition:index%11,orderDirection:index%3-1,completePending:index%7===0,completeStage:c.stage,completeProfile:c.profile,completeClock:index%61,completeFlags:Array.from({length:7},(_,stage)=>{const rows=table.filter(r=>r.stageIndex===stage);return rows.every(r=>records.get(r.id).attempts&&records.get(r.id).practiceCaptures[r.difficulty*4+c.profile]);}),noticePending:index%7===0,noticeProfile:c.profile,noticeClock:index%61,noticeRecord:row};
  const slots=[...group.slots].filter(([offset])=>offset>=0x16050&&offset<=0x1a4d8),before=slots.map(([offset,vm])=>({offset,state:hex(vm),file:[...resources].find(([,r])=>r===vm.resource)?.[0]??null})),requests=[];
  drawSpellPractice(group,state,(vm,o={})=>requests.push({state:hex(vm),snap:!!o.snap,topAlpha:o.topAlpha??255,bottomAlpha:o.bottomAlpha??255}),{table,records,character:c.profile>>1,shot:c.profile&1});
  cases.push({description:{language:c.language,stage:c.stage,profile:c.profile,recordMode:c.recordMode,owner},state:{...state,noticeRecord:row?.id??null},records:Buffer.concat([...records.values()].map(r=>r.bytes)).toString('hex'),before,after:slots.map(([offset,vm])=>({offset,state:hex(vm)})),requests});index++;
 }
}
writeFileSync('tools/tmp/th06nc-spell-practice-draw-cases.json',JSON.stringify({refs,table,trig,cases}));console.log(JSON.stringify({cases:cases.length,requests:cases.reduce((n,c)=>n+c.requests.length,0)}));
