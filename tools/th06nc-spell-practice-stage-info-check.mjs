import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {AnmBank} from '../shared/th06nc/anm-bank.mjs';
import {publishAnmText} from '../shared/th06nc/font-publish.mjs';
import {readFontAtlas} from '../shared/th06nc/font-atlas.mjs';
import {readMessagePack} from '../shared/th06nc/messagepack.mjs';
import {readSpellPracticeTable} from '../shared/th06nc/spell-practice-table.mjs';
import {createSpellRecord} from '../shared/th06nc/spell-record.mjs';
import {refreshSpellPracticeStageInfo,spellInfoTextAsset} from '../shared/th06nc/spell-practice-stage-info.mjs';

const sha=b=>createHash('sha256').update(b).digest('hex'),sources=['spell-practice-stage-info','spell-practice-info-text','spell-practice-table','spell-record','anm-bank','anm-rebind','anm-vm','messagepack','font-publish','font-atlas'].map(s=>'shared/th06nc/'+s+'.mjs'),snapshot=()=>Object.fromEntries(sources.map(p=>[p,sha(readFileSync(p))])),sourceSha256=snapshot(),capturePath=process.argv.includes('--native-font')?'artifacts/th06nc/spell-info-native-font-cases.json':'artifacts/th06nc/spell-info-native-cases.json',captureBytes=readFileSync(capturePath),capture=JSON.parse(captureBytes),localizationBytes=readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/localization.msgpack'),rawLocalization=readMessagePack(localizationBytes),table=readSpellPracticeTable(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/spellpractice.msgpack'));
assert.equal(sha(localizationBytes),capture.localizationSha256);
const fonts=new Map();for(const [key,evidence]of Object.entries(capture.fontFiles??{})){const meta=readFileSync('runtimes/th06nc/artifacts/fonts/'+key+'.json'),advance=readFileSync('runtimes/th06nc/artifacts/fonts/advance_'+key+'.txt');assert.equal(sha(meta),evidence.metadataSha256);assert.equal(sha(advance),evidence.advanceSha256);fonts.set(key,readFontAtlas(meta.toString('utf8'),advance.toString('utf8')));}
const digest=createHash('sha256');let cases=0,requests=0;
for(const c of capture.cases.filter(c=>c.owner===28)){
 const bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/text.anm')),spellInfoTextAsset.base,{slot:0});const group={bank,slots:new Map()},state={state:28,completeFlags:Array(7).fill(false)},events=[],records=new Map(Array.from({length:134},(_,id)=>{const r=createSpellRecord();if(c.unlocked){const row=table.find(row=>row.id===id),attempted=[1,4].includes(c.recordMode)||(c.recordMode===2&&Boolean(row?.midboss))||(c.recordMode===3&&id%3!==0),captured=attempted&&c.recordMode!==4&&(c.recordMode!==3||id%2!==0);r.attempts=attempted?17:0;r.captures=attempted?5:0;for(let difficulty=0;difficulty<5;difficulty++){r.practiceAttempts[difficulty*4+c.profile]=11;r.practiceCaptures[difficulty*4+c.profile]=captured?3:0;}}return[id,r];}));
 const localization=Object.fromEntries(Object.entries(rawLocalization).map(([key,value])=>[key,value[c.language]??key]));
 refreshSpellPracticeStageInfo(group,state,{table,records,character:c.profile>>1,shot:c.profile&1,localization,publishText:(vm,r)=>{events.push({offset:r.offset,sprite:r.sprite,text:r.text,colors:r.colors,size:r.size});if(capture.publicationMode==='native-font')publishAnmText(vm,{...r,language:c.language,fonts,paint:()=>{}});}});
 assert.deepEqual(events,c.requests,JSON.stringify({language:c.language,stage:c.stage,profile:c.profile,unlocked:c.unlocked}));
 for(const slot of c.vms){const actual=group.slots.get(slot.offset).state,expected=Buffer.from(slot.bytes,'hex');assert.deepEqual(Buffer.from(actual),expected,JSON.stringify({offset:slot.offset,language:c.language,profile:c.profile}));digest.update(actual);}
 assert.deepEqual(state.completeFlags.map(Number),c.completeFlags);cases++;requests+=events.length;
}
assert.equal(cases,280);assert.deepEqual(snapshot(),sourceSha256);
const report={publicationMode:capture.publicationMode??'no-op',scope:'Stage-selection information refresh compared against actual 4fdd0..50ab2 captures: ordered localized publication requests and complete post-layout text VMs. Two languages, seven selected stages, four profiles, empty, all captured, midboss-only attempts, mixed attempts/captures and attempted-but-uncaptured records. Publication uses either a controlled no-op or actual native 7530 with independently evaluated glyph metadata according to publicationMode; GPU painting is excluded; card/difficulty branches, native font-cache construction/GPU pixels, drawing and overall title integration are excluded.',cases,requests,sourceSha256,referenceCapture:capturePath,referenceSha256:sha(captureBytes),executableSha256:capture.executableSha256,stateSha256:digest.digest('hex'),passed:true,completeGame:false,nativeEquivalent:false};writeFileSync(capture.publicationMode==='native-font'?'docs/porting/th06nc-spell-practice-stage-info-font-verified.json':'docs/porting/th06nc-spell-practice-stage-info-verified.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,cases,requests,stateSha256:report.stateSha256}));
