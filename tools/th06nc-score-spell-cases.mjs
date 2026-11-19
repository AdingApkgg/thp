import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {AnmBank} from '../shared/th06nc/anm-bank.mjs';
import {ResultState,resultAssets,resultTextAsset,advanceResultCommon} from '../shared/th06nc/result-state.mjs';
import {advanceScoreSpell} from '../shared/th06nc/score-spell-update.mjs';
const refs=[...resultAssets,resultTextAsset],bank=new AnmBank();for(const ref of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});const state=new ResultState(bank),baseline=state.bytes.slice(),cases=[],sha=b=>createHash('sha256').update(b).digest('hex'),localization=Object.fromEntries([...['REIMU_A','REIMU_B','MARISA_A','MARISA_B'].map((n,i)=>['EXE_'+n+'_NAME','P'+i]),...['NORMAL','CHALLENGE'].map((n,i)=>['EXE_RESULT_MODE_'+n+'_NAME','M'+i])]);
const spellRecords=new Map(Array.from({length:134},(_,id)=>[id,{attempts:id%3,key:'CARD_'+id}]));localization.EXE_UNKNOWN_SPELLCARD_NAME='UNKNOWN';for(let id=0;id<134;id++)if(id%2)localization['CARD_'+id]='NAME_'+id;
for(const count of [0,1,10,11,131,134])for(const selection of [...new Set([0,Math.max(0,Math.ceil(count/10)-1)])])for(const clock of [0,19,20,29,30,31])for(const held of [0,64,128,192,512,576])for(const previous of [0,held]){
 const kind=8,index=cases.length,repeat=index%3===0?1:0,soundDisabled=index%5===0,displayed=index%2?-1:selection,sounds=index%4===0?[12,-1,-1]:index%4===1?[10,11,12]:[-1,-1,-1],beforeSounds=[...sounds],calls=[];state.bytes.set(baseline);const v=state.v;for(const [p,x]of [[0x9e94,kind],[0x9e7c,selection],[0x4450,clock],[0x18,displayed],[0xa8,5],[0xa4,count]])v.setInt32(p,x,true);for(let id=0;id<count;id++)state.bytes[0x1c+id]=id;
 advanceScoreSpell(state,{held,previous,repeat,localization,spellRecords,soundSlots:sounds,soundDisabled,publishText:(vm,r)=>{calls.push({kind:'font',...r});[1,1,120,36].forEach((x,i)=>vm.v.setInt32(0x10c+i*4,x,true));vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|1,true);}});advanceResultCommon(state,kind);cases.push({kind,count,selection,clock,held,previous,repeat,soundDisabled,displayed,beforeSounds,afterSounds:sounds,calls,ownerSha256:sha(state.bytes)});
}
console.log(JSON.stringify({refs,baseline:Buffer.from(baseline).toString('hex'),cases}));
