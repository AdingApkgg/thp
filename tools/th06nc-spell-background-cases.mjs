import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {readEcl} from '../shared/th06nc/ecl.mjs';
import {readStd} from '../shared/th06nc/std.mjs';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {AnmBank} from '../shared/th06nc/anm-bank.mjs';
import {initializeStd,stdAssetPlan} from '../shared/th06nc/std-state.mjs';
import {readSpellPracticeTable} from '../shared/th06nc/spell-practice-table.mjs';
import {prepareSpellPracticeBackground} from '../shared/th06nc/spell-practice-background.mjs';
const table=readSpellPracticeTable(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/spellpractice.msgpack')),cases=[],stages=new Map(),hex=b=>Buffer.from(b).toString('hex'),sha=b=>createHash('sha256').update(b).digest('hex');
for(let stage=1;stage<=7;stage++){const ref=stdAssetPlan(stage);stages.set(stage,{ref,anm:readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),std:readStd(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/stage'+stage+'.std')),ecl:readEcl(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata'+stage+'.ecl'))});}
for(const row of table){const stage=row.stageIndex+1,asset=stages.get(stage),bank=new AnmBank();bank.load(asset.anm,asset.ref.base,{slot:asset.ref.slot});const state=initializeStd(asset.std,{anmBank:bank});state.direction=[0,0,0];const fog=[],result=prepareSpellPracticeBackground(state,asset.ecl,table,{spellPracticeIndex:row.id},{setFogColor:rgb=>fog.push(Buffer.from([99,...rgb])),setFogRange:range=>{const b=Buffer.alloc(9);b[0]=114;range.forEach((v,i)=>b.writeFloatLE(v,1+i*4));fog.push(b);}});cases.push({id:row.id,stage,ref:asset.ref,primitives:asset.std.primitiveCount,owner:hex(state.owner),poolSha256:sha(state.storage),fileSha256:sha(state.bytes),direction:state.direction,fogSha256:sha(Buffer.concat(fog)),fogRequests:fog.length,result});}
writeFileSync('tools/tmp/th06nc-spell-background-cases.json',JSON.stringify({table,cases}));console.log(JSON.stringify({cases:cases.length,frames:cases.reduce((n,c)=>n+c.result.frames,0)}));
