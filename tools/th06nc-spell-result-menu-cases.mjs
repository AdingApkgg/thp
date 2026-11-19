import {readFileSync,writeFileSync} from 'node:fs';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {AnmBank} from '../shared/th06nc/anm-bank.mjs';
import {pauseAsset} from '../shared/th06nc/pause-menu.mjs';
import {SpellPracticeResultMenu} from '../shared/th06nc/spell-practice-result-menu.mjs';
import {NativeFade} from '../shared/th06nc/fade.mjs';
const refs=[pauseAsset,{archive:'th06IN.dat',file:'text.anm',slot:0,base:0x72f}],resources=refs.map(r=>readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file))),scenes=[],hex=b=>Buffer.from(b).toString('hex');
for(const path of [0,1,2,3,4,5,6])for(const captured of [false,true])for(const recordingAvailable of [false,true])for(const replayPlayback of [false,true])for(const soundDisabled of [false,true]){
 const bank=new AnmBank();refs.forEach((r,i)=>bank.load(resources[i],r.base,{slot:r.slot}));const fade=new NativeFade(),environment={spellResultVisible:true,resumeSpell:false,spellRestartRequested:false,gameState:3,replayPlayback},fonts=[],sounds=soundDisabled?[12,10,11]:[-1,-1,-1],frames=[];let present=path===6,opened=0,previous=0;
 const menu=new SpellPracticeResultMenu(bank,{captured,environment,fade,soundSlots:sounds,soundDisabled,replayServices:{recordingAvailable},resultServices:{present:()=>present,open:()=>{opened++;present=captured;return captured;}},publishText:(vm,r)=>{fonts.push({offset:vm.state.byteOffset,key:r.key,colors:r.colors});[1,1,120,36].forEach((x,i)=>vm.v.setInt32(0x10c+i*4,x,true));vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|1,true);}});
 for(let frame=1;frame<=120;frame++){
  let held=0,externalClose=false;
  if(path===1)held=({8:16,12:32,16:48,24:512,32:256})[frame]??0;
  if(path===2&&frame===8)held=16384;
  if(path===3){if(frame===8&&!captured)held=32;if(frame===16)held=256;}
  if(path===4){if(frame===8&&captured)held=16;if(frame===16)held=256;}
  if(path>=5){if(frame===8)held=captured?32:16;if(frame===16)held=256;if(frame===60){present=false;externalClose=true;fade.v.setInt32(0x34,2,true);fade.v.setInt32(0x28,255,true);}if(frame===80)held=16;if(frame===88)held=256;}
  fonts.length=0;fade.tick();menu.tick({held,previous});previous=held;const calls=[];menu.draw((vm,r)=>calls.push({offset:r.offset,state:hex(vm.state)}));frames.push({frame,held,externalClose,state:hex(menu.bytes),active:menu.active,event:menu.event,environment:{...environment},fonts:[...fonts],sounds:[...sounds],fade:hex(fade.state),present,opened,calls});if(!menu.active)break;
 }
 scenes.push({path,captured,recordingAvailable,replayPlayback,soundDisabled,initialSounds:soundDisabled?[12,10,11]:[-1,-1,-1],initialPresent:path===6,frames});
}
writeFileSync('tools/tmp/th06nc-spell-result-menu-cases.json',JSON.stringify({refs,scenes}));console.log(JSON.stringify({scenes:scenes.length,frames:scenes.reduce((n,s)=>n+s.frames.length,0)}));
