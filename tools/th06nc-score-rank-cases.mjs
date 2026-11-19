import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {AnmBank} from '../shared/th06nc/anm-bank.mjs';
import {ResultState,resultAssets,resultTextAsset,advanceResultCommon} from '../shared/th06nc/result-state.mjs';
import {advanceScoreRank} from '../shared/th06nc/score-rank-update.mjs';
const refs=[...resultAssets,resultTextAsset],bank=new AnmBank();for(const ref of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});const state=new ResultState(bank),baseline=state.bytes.slice(),cases=[],sha=b=>createHash('sha256').update(b).digest('hex'),localization=Object.fromEntries([...['REIMU_A','REIMU_B','MARISA_A','MARISA_B'].map((n,i)=>['EXE_'+n+'_NAME','P'+i]),...['NORMAL','CHALLENGE'].map((n,i)=>['EXE_RESULT_MODE_'+n+'_NAME','M'+i])]);
for(const kind of [3,4,5,6,7])for(let selection=0;selection<4;selection++)for(const clock of [0,19,20,29,30,31])for(const held of [0,64,128,192,512,576])for(const previous of [0,held]){
 const index=cases.length,repeat=index%3===0?1:0,soundDisabled=index%5===0,displayed=index%2?-1:selection,sounds=index%4===0?[12,-1,-1]:index%4===1?[10,11,12]:[-1,-1,-1],beforeSounds=[...sounds],calls=[];state.bytes.set(baseline);const v=state.v;for(const [p,x]of [[0x9e94,kind],[0x9e7c,selection],[0x4450,clock],[4,displayed],[0xa8,kind-3]])v.setInt32(p,x,true);
 advanceScoreRank(state,{held,previous,repeat,localization,soundSlots:sounds,soundDisabled,processSecretUnlock:()=>calls.push({kind:'secret'}),publishText:(vm,r)=>{calls.push({kind:'font',...r});[1,1,120,36].forEach((x,i)=>vm.v.setInt32(0x10c+i*4,x,true));vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|1,true);}});advanceResultCommon(state,kind);cases.push({kind,selection,clock,held,previous,repeat,soundDisabled,displayed,beforeSounds,afterSounds:sounds,calls,ownerSha256:sha(state.bytes)});
}
console.log(JSON.stringify({refs,baseline:Buffer.from(baseline).toString('hex'),cases}));
