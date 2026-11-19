import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {AnmBank} from '../shared/th06nc/anm-bank.mjs';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {ResultState,resultAssets,resultTextAsset,advanceResultCommon} from '../shared/th06nc/result-state.mjs';
import {advanceScoreMenu} from '../shared/th06nc/score-menu-update.mjs';
import {NativeFade} from '../shared/th06nc/fade.mjs';
const refs=[...resultAssets,resultTextAsset],bank=new AnmBank();for(const ref of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});const state=new ResultState(bank),baseline=state.bytes.slice(),cases=[],sha=b=>createHash('sha256').update(b).digest('hex');
for(const kind of [0,1])for(let selection=0;selection<7;selection++)for(const clock of [0,19,20])for(const pulse of [0,30,71])for(const held of [0,16,32,48,256,512,768,272])for(const previous of [0,held]){
 const index=cases.length,repeat=index%3===0?1:0,profile=index%4,page=index%16,extra=index%8,soundDisabled=index%5===0,sounds=index%4===0?[12,-1,-1]:index%4===1?[10,11,12]:[-1,-1,-1],beforeSounds=[...sounds],fade=index%7===0?null:new NativeFade();if(fade){fade.v.setInt32(0x34,index%4,true);fade.v.setUint32(0x20,0x123456,true);fade.v.setInt32(0x28,[0,127,255][index%3],true);}const beforeFade=fade?[...fade.state]:null;
 state.bytes.set(baseline);const v=state.v;for(const [p,x]of [[0x9e94,kind],[0x9e7c,selection],[0x4450,clock],[0x4454,pulse],[0x9e80,profile],[0x9e84,page]])v.setInt32(p,x,true);const records=new Map(Array.from({length:134},(_,id)=>[id,{attempts:id>=131?extra>>(id-131)&1:0}]));advanceScoreMenu(state,{held,previous,repeat,fade,spellRecords:records,soundSlots:sounds,soundDisabled});advanceResultCommon(state,kind);if(process.argv.includes('--dump='+index))writeFileSync('tools/tmp/th06nc-score-expected.bin',state.bytes);cases.push({kind,selection,clock,pulse,held,previous,repeat,profile,page,extra,soundDisabled,beforeSounds,afterSounds:sounds,beforeFade,afterFade:fade?[...fade.state]:null,ownerSha256:sha(state.bytes)});
}
console.log(JSON.stringify({refs,baseline:Buffer.from(baseline).toString('hex'),cases}));
