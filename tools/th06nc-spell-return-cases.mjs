import {readFileSync} from 'node:fs';
import {readSpellPracticeTable} from '../shared/th06nc/spell-practice-table.mjs';
import {createSpellRecord} from '../shared/th06nc/spell-record.mjs';
import {prepareSpellPracticeReturn} from '../shared/th06nc/spell-practice-return.mjs';
const table=readSpellPracticeTable(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/spellpractice.msgpack')),cases=[],recordSets=[];
for(let mode=0;mode<3;mode++){
 const records=new Map(Array.from({length:134},(_,id)=>{const r=createSpellRecord();r.attempts=1;r.practiceCaptures.fill(mode===2?1:0);return [id,r];}));
 if(mode===1)for(const row of table)records.get(row.id).practiceCaptures[row.difficulty*4]=1;
 recordSets.push(Buffer.concat([...records.values()].map(r=>r.bytes)).toString('hex'));
 const add=(id,profile,flags={})=>{
  const {startup=false,...changes}=flags,environment={character:profile>>1,shot:profile&1,resumeSpell:true,titleLaunchPending:true,lastSpellProfile:profile,lastSpellId:id,spellPracticeIndex:id,spellWasCaptured:false,spellStageWasComplete:false,...changes},before={...environment},state=prepareSpellPracticeReturn(environment,{table,records,startup});cases.push({mode,startup,environment:before,after:environment,state});
 };
 for(const row of table)for(let profile=0;profile<4;profile++)add(row.id,profile);
 for(const id of [0,5,121,129,130,133,134,255])for(const profile of [0,1,2,3])for(const flags of [{startup:true},{resumeSpell:false},{titleLaunchPending:false},{spellWasCaptured:true},{spellStageWasComplete:true},{lastSpellProfile:(profile+1)%4},{spellPracticeIndex:(id+1)&255}])add(id,profile,flags);
}
console.log(JSON.stringify({table,recordSets,cases}));
