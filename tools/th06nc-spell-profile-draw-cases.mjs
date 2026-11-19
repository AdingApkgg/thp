import {readFileSync,writeFileSync} from 'node:fs';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {TitleAnimations} from '../shared/th06nc/title-animations.mjs';
import {titleResources} from '../shared/th06nc/title-layout.mjs';
import {selectionResources} from '../shared/th06nc/title-selection-layout.mjs';
import {initializeSpellMenuAnimations,spellMenuAsset} from '../shared/th06nc/spell-practice-layout.mjs';
import {refreshSpellCharacter,refreshSpellProfile} from '../shared/th06nc/spell-practice-profile.mjs';
import {drawSpellProfilePreview,drawSpellProfileLabels} from '../shared/th06nc/spell-practice-profile-draw.mjs';
const refs=[...titleResources,...selectionResources,spellMenuAsset],resources=new Map(refs.map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06TL.dat/'+r.file))])),cases=[],hex=vm=>Buffer.from(vm.state).toString('hex');
let index=0;
for(const profile of [0,1,2,3])for(const owner of [28,30])for(const frame of [0,10,11,16,17,30,42,44,54])for(const ticks of [0,1,5,10,11])for(const direction of [-1,0,1]){
 const group=new TitleAnimations(resources);initializeSpellMenuAnimations(group,resources);const character=profile>>1,shot=profile&1,state={state:owner,fastEntry:true,frame,pulse:[0,15,30,42,60,71,72][index%7],stageTransition:ticks,orderTransition:ticks,stageDirection:direction,orderDirection:direction};
 refreshSpellCharacter(group,{},character);refreshSpellProfile(group,{},character,shot);
 for(let i=0;i<index%3*15;i++)for(const [offset,vm]of group.slots)if(offset>=0x122e0&&offset<0x133e0)vm.tick();
 const slots=[0x12400,0x12640,0x13060,0x13180,0x132a0,0x133c0,0x1a4d8,0x1a5f8].map(offset=>[offset,group.slots.get(offset)]),before=slots.map(([offset,vm])=>({offset,state:hex(vm),file:[...resources].find(([,r])=>r===vm.resource)?.[0]})),requests=[],options={width:[1920,1280,640][index%3],height:[1080,720,480][index%3],character,shot};
 const draw=(vm,o)=>requests.push({state:hex(vm),snap:!!o.snap,topAlpha:255,bottomAlpha:255});drawSpellProfilePreview(group,state,draw,options);drawSpellProfileLabels(group,state,draw,options);
 cases.push({state,options,before,after:slots.map(([offset,vm])=>({offset,state:hex(vm)})),requests});index++;
}
writeFileSync('tools/tmp/th06nc-spell-profile-draw-cases.json',JSON.stringify({refs,cases}));console.log(JSON.stringify({cases:cases.length,requests:cases.reduce((n,c)=>n+c.requests.length,0)}));
