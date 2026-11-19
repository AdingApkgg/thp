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
import {refreshSpellPracticeCardInfo} from '../shared/th06nc/spell-practice-card-info.mjs';
import {spellInfoTextAsset} from '../shared/th06nc/spell-practice-info-text.mjs';
import {TitleAnimations} from '../shared/th06nc/title-animations.mjs';
import {titleResources} from '../shared/th06nc/title-layout.mjs';
import {selectionResources} from '../shared/th06nc/title-selection-layout.mjs';
import {spellMenuAsset,initializeSpellMenuAnimations} from '../shared/th06nc/spell-practice-layout.mjs';

const sha=b=>createHash('sha256').update(b).digest('hex'),sources=['spell-practice-card-info','spell-practice-info-text','spell-practice-layout','title-selection-layout','title-animations','title-layout','spell-practice-table','spell-record','anm-bank','anm-rebind','anm-vm','messagepack','font-publish','font-atlas'].map(s=>'shared/th06nc/'+s+'.mjs'),snapshot=()=>Object.fromEntries(sources.map(p=>[p,sha(readFileSync(p))])),sourceSha256=snapshot(),capturePath=process.argv.includes('--native-font')?'artifacts/th06nc/spell-info-native-font-cases.json':'artifacts/th06nc/spell-info-native-cases.json',captureBytes=readFileSync(capturePath),capture=JSON.parse(captureBytes),localizationBytes=readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/localization.msgpack'),rawLocalization=readMessagePack(localizationBytes),table=readSpellPracticeTable(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/spellpractice.msgpack'));
assert.equal(sha(localizationBytes),capture.localizationSha256);
const fonts=new Map();for(const [key,evidence]of Object.entries(capture.fontFiles??{})){const meta=readFileSync('runtimes/th06nc/artifacts/fonts/'+key+'.json'),advance=readFileSync('runtimes/th06nc/artifacts/fonts/advance_'+key+'.txt');assert.equal(sha(meta),evidence.metadataSha256);assert.equal(sha(advance),evidence.advanceSha256);fonts.set(key,readFontAtlas(meta.toString('utf8'),advance.toString('utf8')));}
const resources=new Map([...titleResources,...selectionResources,spellMenuAsset,spellInfoTextAsset].map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+(r.archive??'th06TL.dat')+'/'+r.file))]));
const digest=createHash('sha256');let cases=0,requests=0;
for(const c of capture.cases.filter(c=>[29,30].includes(c.owner))){
 const group=new TitleAnimations(resources);initializeSpellMenuAnimations(group,resources);group.bank.load(resources.get('text.anm'),spellInfoTextAsset.base,{slot:0});const state={state:c.owner,spellStage:c.stage,spellOrder:c.order,spellScroll:c.scroll,infoRecordGap:0},events=[],records=new Map(Array.from({length:134},(_,id)=>{const r=createSpellRecord(),row=table.find(row=>row.id===id);if(c.unlocked&&row){const attempted=[1,4].includes(c.recordMode)||(c.recordMode===2&&Boolean(row.midboss))||(c.recordMode===3&&id%3!==0),captured=attempted&&c.recordMode!==4&&(c.recordMode!==3||id%2!==0);r.attempts=attempted?17:0;r.captures=attempted?5:0;const index=row.difficulty*4+c.profile;r.practiceAttempts[index]=11;r.practiceCaptures[index]=captured?3:0;new DataView(r.bytes.buffer,r.bytes.byteOffset,r.bytes.byteLength).setBigUint64(0x40+index*8,0x123456789abcn+BigInt(id)*100n,true);}return[id,r];}));
 const localization=Object.fromEntries(Object.entries(rawLocalization).map(([key,value])=>[key,value[c.language]??key]));
 refreshSpellPracticeCardInfo(group,state,{table,records,character:c.profile>>1,shot:c.profile&1,localization,publishText:(vm,r)=>{events.push({offset:r.offset,sprite:r.sprite,text:r.text,colors:r.colors,size:r.size});if(capture.publicationMode==='native-font')publishAnmText(vm,{...r,language:c.language,fonts,paint:()=>{}});}});
 assert.deepEqual(events,c.requests,JSON.stringify({language:c.language,stage:c.stage,profile:c.profile,unlocked:c.unlocked}));
 for(const slot of c.vms){const actual=group.slots.get(slot.offset).state,expected=Buffer.from(slot.bytes,'hex');assert.deepEqual(Buffer.from(actual),expected,JSON.stringify({offset:slot.offset,language:c.language,profile:c.profile}));digest.update(actual);}
 cases++;requests+=events.length;
}
assert.equal(cases,560);assert.deepEqual(snapshot(),sourceSha256);
const report={publicationMode:capture.publicationMode??'no-op',scope:'Card/difficulty information refresh compared against actual 50ab7..52362 captures: ordered localized publication requests and complete post-layout text VMs. Two languages, seven selected stages, four profiles, empty, all captured, midboss-only attempts, mixed attempts/captures and attempted-but-uncaptured records. Publication uses either a controlled no-op or actual native 7530 with independently evaluated glyph metadata according to publicationMode; GPU painting is excluded; stage-selection branch, native font-cache construction/GPU pixels, drawing and overall title integration are excluded.',cases,requests,sourceSha256,referenceCapture:capturePath,referenceSha256:sha(captureBytes),executableSha256:capture.executableSha256,stateSha256:digest.digest('hex'),passed:true,completeGame:false,nativeEquivalent:false};writeFileSync(capture.publicationMode==='native-font'?'docs/porting/th06nc-spell-practice-card-info-font-verified.json':'docs/porting/th06nc-spell-practice-card-info-verified.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,cases,requests,stateSha256:report.stateSha256}));
